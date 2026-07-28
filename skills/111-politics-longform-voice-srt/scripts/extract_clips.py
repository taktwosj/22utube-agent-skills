#!/usr/bin/env python3
"""P02c-1 source clip extraction — 권위 대본의 13개 선정 구간 오디오 추출.

원본 mp4 무수정. ffmpeg으로 지정 구간 오디오만 WAV 추출 후 ffprobe 실측.
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# --- 에피소드 파라미터 (환경변수 필수) ---------------------------------------
# PL_EPISODE_DIR   : 로컬 미디어 정본 (OneDrive 에피소드 폴더, Git 미추적)
# PL_REPO_EPISODE  : Git 추적 산출물 (clean checkout 내 docs/.../episodes/<ID>)
# PL_VIDEO_DIR     : 원본 mp4 폴더 (S01.mp4~)
# PL_SCRIPT_SHA256 : 권위 대본 SHA-256 (staleness 탐지용)
import os


def _req(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"FAIL: 환경변수 {name} 미설정. 에피소드 경로를 명시해야 한다.")
    return v


EPISODE = Path(_req("PL_EPISODE_DIR"))
REPO_EPISODE = Path(_req("PL_REPO_EPISODE"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lock_preflight import require_gate

SCRIPT_LOCK = require_gate(EPISODE, "tts")
# ---------------------------------------------------------------------------

SCRIPT = REPO_EPISODE / "20_script" / os.environ.get(
    "PL_SCRIPT_NAME", "master_script_locked.md")
VIDEO_DIR = Path(_req("PL_VIDEO_DIR"))
SRT_DIR = EPISODE / "10_analysis" / "transcripts"
OUT = EPISODE / "30_audio_srt" / "source_clips"
REPORT = EPISODE / "30_audio_srt" / "source_clip_manifest.json"

LEGACY_CLIP_RE = re.compile(
    r"^▌\s*\*\*(S\d{2})\s+"
    r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})~(\d{2}):(\d{2}):(\d{2})\.(\d{3})\*\*",
    re.M,
)

CURRENT_CLIP_RE = re.compile(
    r"^###\s+\[원본\]\s+(S\d{2})\s+\|\s+"
    r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})~"
    r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s+\|",
    re.M,
)


def iter_clip_matches(text):
    hits = [(m.start(), m) for pattern in (LEGACY_CLIP_RE, CURRENT_CLIP_RE)
            for m in pattern.finditer(text)]
    return [m for _, m in sorted(hits, key=lambda item: item[0])]


def to_sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def probe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main():
    text = SCRIPT.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    clips = []
    for m in iter_clip_matches(text):
        src = m.group(1)
        start = to_sec(*m.group(2, 3, 4, 5))
        end = to_sec(*m.group(6, 7, 8, 9))
        line_no = text[: m.start()].count("\n") + 1
        speaker = purpose = None
        for ln in lines[line_no: line_no + 4]:
            if ln.startswith("화자:"):
                speaker = ln[3:].strip()
            elif ln.startswith("용도:"):
                purpose = ln[3:].strip()
        clips.append({
            "clip_index": len(clips) + 1,
            "source": src,
            "script_line": line_no,
            "source_start_sec": round(start, 3),
            "source_end_sec": round(end, 3),
            "duration_sec": round(end - start, 3),
            "speaker": speaker,
            "purpose": purpose,
        })

    expected = int((SCRIPT_LOCK.get("structure") or {}).get(
        "source_clip_count", 0))
    print(f"parsed clips: {len(clips)}", flush=True)
    if len(clips) != expected:
        print(f"FAIL expected {expected} clips, got {len(clips)}", flush=True)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    failed = 0
    for c in clips:
        mp4 = VIDEO_DIR / f"{c['source']}.mp4"
        srt = SRT_DIR / f"{c['source']}.srt"
        c["source_mp4"] = str(mp4)
        c["source_mp4_exists"] = mp4.is_file()
        c["source_srt_exists"] = srt.is_file()
        if not mp4.is_file():
            c["status"] = "FAIL_SOURCE_MISSING"
            failed += 1
            print(f"[{c['clip_index']:2d}/{expected}] FAIL missing "
                  f"{mp4.name}", flush=True)
            continue

        dest = OUT / f"clip_{c['clip_index']:02d}_{c['source']}.wav"
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{c['source_start_sec']:.3f}",
            "-to", f"{c['source_end_sec']:.3f}",
            "-i", str(mp4), "-vn",
            "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(dest),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            actual = probe_dur(dest)
            c.update({
                "status": "OK",
                "path": str(dest),
                "bytes": dest.stat().st_size,
                "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "extracted_duration_sec": round(actual, 6),
                "duration_delta_sec": round(actual - c["duration_sec"], 6),
            })
            print(f"[{c['clip_index']:2d}/{expected}] OK  {c['source']} "
                  f"{c['duration_sec']:6.2f}s -> {actual:6.2f}s", flush=True)
        except subprocess.CalledProcessError as e:
            c.update({"status": "FAIL_FFMPEG", "error": (e.stderr or "")[:300]})
            failed += 1
            print(f"[{c['clip_index']:2d}/{expected}] FAIL ffmpeg "
                  f"{c['source']}", flush=True)

    ok = [c for c in clips if c.get("status") == "OK"]
    manifest = {
        "schema_version": "yusimin-p02c-source-clip-manifest-v1",
        "status": "PASS" if failed == 0 else ("PARTIAL" if ok else "FAIL"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "authoritative_script_sha256": _req("PL_SCRIPT_SHA256"),
        "clip_count": len(clips),
        "clip_ok": len(ok),
        "clip_failed": failed,
        "source_scope": sorted({c["source"] for c in clips}),
        "total_clip_duration_sec": round(sum(c["duration_sec"] for c in clips), 3),
        "extraction": "ffmpeg -vn pcm_s16le 44100Hz stereo, source mp4 unmodified",
        "media_root": str(OUT),
        "git_tracked": False,
        "clips": clips,
    }
    REPORT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"\nstatus={manifest['status']} ok={len(ok)}/{len(clips)} "
          f"total={manifest['total_clip_duration_sec']:.2f}s")
    print(f"manifest -> {REPORT}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
