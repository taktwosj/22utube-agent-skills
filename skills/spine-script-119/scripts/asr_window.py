# -*- coding: utf-8 -*-
"""원본 영상의 한 구간을 받아써서 컷 경계를 잡는다.

자동자막 cue 는 문장 중간에서 끊기는 일이 많다. 후보 구간만 단어 단위로 받아써서
말이 실제로 시작하고 끝나는 시각을 보고 final_cuts.py 의 in/out 을 적는다.

    python asr_window.py --root <root> --video 32uRfOiLT5I --start 1080 --end 1220
    python asr_window.py --root <root> --video 32uRfOiLT5I --start 18:00 --end 20:20 --model medium
    python asr_window.py --root <root> --video 32uRfOiLT5I --start 1080 --end 1220 --edges 8
    python asr_window.py --root <root> --batch work/asr_jobs.tsv --edges 8

--edges N   컷 경계만 필요할 때. 시작 앞뒤 N초·끝 앞뒤 N초 두 창만 받아쓴다. 컷이 2N초보다
            짧으면 한 창으로 합친다. 출력 파일 이름·형식은 같고 "edges"·"windows" 가 더 붙는다.
--batch F   탭 구분 텍스트 `video_id<TAB>start<TAB>end` 한 줄에 한 컷. `#` 줄은 무시.
            모델을 한 번만 올리고 컷을 이어서 받아쓴다. 컷마다 프로세스를 새로 띄우면
            large-v3 를 그때마다 다시 올려 컷 수만큼 느려진다.
--video=-abc  영상 ID 가 `-` 로 시작하면 `=` 로 붙인다. 띄어 쓰면 argparse 가 옵션으로 읽는다.

입력   <root>/clips/<video_id>.mp4|mkv|webm  전체 원본. --download-sections 조각은 시각이 어긋난다
출력   <root>/work/asr/<video_id>_<start>-<end>.json   segments + words, 원본 기준 절대 시각(초)
       화면에 `[mm:ss.s ~ mm:ss.s] 문장` 을 찍는다
모델   faster-whisper. 기본 large-v3. GPU 가 있으면 cuda/float16, 없으면 cpu/int8.
       cuda 로 돌리다 cuBLAS·cuDNN DLL 이 없으면 CPU 로 다시 돌린다(느리다). GPU 를 쓰려면
       사용자 터미널에서 `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`.
       첫 실행은 모델을 내려받는다. 설치가 필요하면 사용자 터미널에서 한다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import resolve_root, root_parser  # noqa: E402

MAX_WINDOW = 20 * 60
CUDA_KEYS = ("cublas", "cudnn", "cuda")


def parse_time(text: str) -> float:
    parts = text.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def mmss(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def find_clip(root: Path, video: str) -> Path:
    for ext in ("mp4", "mkv", "webm"):
        p = root / "clips" / f"{video}.{ext}"
        if p.is_file():
            return p
    raise SystemExit(f"CLIP_MISSING: {root / 'clips' / video}.mp4 — 전체 원본을 clips/ 에 받는다")


def add_cuda_dll_dirs() -> None:
    """pip 로 깐 nvidia-cublas-cu12 · nvidia-cudnn-cu12 의 DLL 폴더를 찾아 건다. 없으면 지나간다."""
    if os.name != "nt":
        return
    try:
        import nvidia  # type: ignore  # noqa: F401
    except ImportError:
        return
    for base in list(getattr(nvidia, "__path__", [])):
        for bin_dir in Path(base).glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def edge_windows(t0: float, t1: float, edges: float) -> list[tuple[float, float]]:
    """edges 가 0 이면 컷 전체 한 창. 아니면 시작·끝 경계 앞뒤 edges 초씩 두 창. 겹치면 하나로."""
    if edges <= 0:
        return [(t0, t1)]
    head = (max(0.0, t0 - edges), t0 + edges)
    tail = (max(0.0, t1 - edges), t1 + edges)
    if head[1] >= tail[0]:
        return [(head[0], tail[1])]
    return [head, tail]


def extract_wav(src: Path, wav: Path, a: float, b: float) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(src),
                    "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)


def load_model(WhisperModel, name: str, device: str):
    return WhisperModel(name, device=device, compute_type="float16" if device == "cuda" else "int8")


def transcribe(model, wav: Path, t0: float) -> list[dict]:
    segments, _info = model.transcribe(str(wav), language="ko", word_timestamps=True, vad_filter=True, beam_size=5)
    rows = []
    for seg in segments:  # 생성기라 여기서 실제 추론이 돈다. CUDA DLL 오류도 여기서 난다
        words = [{"w": w.word.strip(), "s": round(t0 + w.start, 2), "e": round(t0 + w.end, 2)} for w in (seg.words or [])]
        rows.append({"s": round(t0 + seg.start, 2), "e": round(t0 + seg.end, 2), "text": seg.text.strip(), "words": words})
    return rows


class Engine:
    """모델을 한 번 올려 두고 여러 창을 받아쓴다. cuda DLL 이 없으면 한 번만 CPU 로 갈아탄다."""

    def __init__(self, WhisperModel, name: str, device: str):
        self.WhisperModel, self.name, self.device = WhisperModel, name, device
        self.model = load_model(WhisperModel, name, device)

    def run(self, wav: Path, t0: float) -> list[dict]:
        try:
            return transcribe(self.model, wav, t0)
        except RuntimeError as exc:
            if self.device != "cuda" or not any(k in str(exc).lower() for k in CUDA_KEYS):
                raise
            print(f"CUDA_LIBS_MISSING: {exc}", flush=True)
            print("CPU int8 로 다시 돌린다(느리다). GPU 는 사용자 터미널에서 "
                  "`pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`", flush=True)
            self.device = "cpu"
            self.model = load_model(self.WhisperModel, self.name, "cpu")
            return transcribe(self.model, wav, t0)


def read_batch(path: Path) -> list[tuple[str, str, str]]:
    jobs = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        cols = [c.strip() for c in s.split("\t")]
        if len(cols) < 3:
            raise SystemExit(f"BATCH_LINE_INVALID: {path}:{n} — video_id<TAB>start<TAB>end")
        jobs.append((cols[0], cols[1], cols[2]))
    if not jobs:
        raise SystemExit(f"BATCH_EMPTY: {path}")
    return jobs


def run_job(engine: Engine, root: Path, video: str, start: str, end: str, edges: float) -> Path:
    src = find_clip(root, video)
    t0, t1 = parse_time(start), parse_time(end)
    if t1 <= t0:
        raise SystemExit(f"WINDOW_INVALID: {video} end 가 start 보다 커야 한다")
    if t1 - t0 > MAX_WINDOW and edges <= 0:
        raise SystemExit(f"WINDOW_TOO_LONG: {MAX_WINDOW // 60}분 이하로 자른다. 컷 후보 구간만 받아쓰거나 --edges 를 쓴다")

    out_dir = root / "work" / "asr"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{video}_{int(t0)}-{int(t1)}"
    out = out_dir / f"{stem}.json"
    windows = edge_windows(t0, t1, edges)
    rows: list[dict] = []
    for i, (a, b) in enumerate(windows):
        wav = out_dir / f"{stem}_{i}.wav"
        extract_wav(src, wav, a, b)
        try:
            rows += engine.run(wav, a)
        finally:
            wav.unlink(missing_ok=True)
    for r in rows:
        print(f"[{mmss(r['s'])} ~ {mmss(r['e'])}] {r['text']}", flush=True)
    out.write_text(json.dumps({"video": video, "clip": str(src), "window": [t0, t1], "edges": edges,
                               "windows": [list(w) for w in windows], "model": engine.name,
                               "device": engine.device, "segments": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"ASR_DONE {len(rows)} segments device={engine.device} -> {out}")
    return out


def main() -> int:
    p = root_parser("원본 구간 whisper 받아쓰기 — 컷 경계용")
    p.add_argument("--video", help="video_id. `-` 로 시작하면 --video=-abc")
    p.add_argument("--start", help="초 또는 mm:ss")
    p.add_argument("--end", help="초 또는 mm:ss")
    p.add_argument("--batch", help="탭 구분 `video_id<TAB>start<TAB>end` 목록. 모델 1회 로드")
    p.add_argument("--edges", type=float, default=0.0, help="경계 앞뒤 N초 두 창만. 0 이면 컷 전체")
    p.add_argument("--model", default="large-v3")
    p.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    args = p.parse_args()
    root = resolve_root(args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.batch:
        batch = Path(args.batch)
        if not batch.is_absolute():
            batch = root / batch
        jobs = read_batch(batch)
    elif args.video and args.start and args.end:
        jobs = [(args.video, args.start, args.end)]
    else:
        raise SystemExit("ARGS_MISSING: --video --start --end 세 개 또는 --batch 하나")
    for video, _s, _e in jobs:
        find_clip(root, video)  # 모델 올리기 전에 원본이 다 있는지 본다

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("FASTER_WHISPER_MISSING: 사용자 터미널에서 `pip install faster-whisper`")
    add_cuda_dll_dirs()
    device = args.device
    if device == "auto":
        try:
            import ctranslate2
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            device = "cpu"
    engine = Engine(WhisperModel, args.model, device)
    for video, start, end in jobs:
        run_job(engine, root, video, start, end, args.edges)
    print(f"ASR_BATCH_DONE {len(jobs)} jobs device={engine.device}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
