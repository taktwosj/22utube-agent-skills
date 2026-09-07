# -*- coding: utf-8 -*-
r"""잠근 쇼츠 구간을 실제 mp4 와 SRT 로 잘라낸다. 롱폼 조립이 끝난 뒤에 돌린다.

`-c copy` 를 쓰지 않는다. 키프레임에 붙어 수 초 어긋난다. 재인코딩한다.

산출물은 `E:\22utube\_shorts\<episode_id>\<slug>\` 에 슬러그 이름으로 셋이 나온다.

    <slug>.mp4        본편 구간
    <slug>.srt        원본 자막을 구간으로 자른 것
    <slug>_8자.srt    여덟 자 안팎으로 잘게 쪼갠 것 — CapCut 이 쓰는 쪽

자동자막 오탈자는 `<root>/work/corrections.json` 으로 고친다.
"""
from __future__ import annotations

import json
import subprocess

from _common import SHORTS_ROOT, root_parser

MAX_CHARS = 8
MIN_DUR = 0.22


def ts(sec: float) -> str:
    sec = max(sec, 0.0)
    return (f"{int(sec // 3600):02d}:{int(sec % 3600 // 60):02d}:"
            f"{sec % 60:06.3f}").replace(".", ",")


def load_cues(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["cues"] if isinstance(data, dict) else data
    out = []
    for cue in rows:
        start = cue.get("start", cue.get("s"))
        end = cue.get("end", cue.get("e"))
        text = (cue.get("text") or cue.get("t") or "").replace("\n", " ").strip()
        if start is None or end is None or not text:
            continue
        out.append((float(start), float(end), text))
    return out


def chunks(text: str, limit: int = MAX_CHARS):
    out, cur = [], ""
    for word in text.split():
        while len(word) > limit:
            if cur:
                out.append(cur)
                cur = ""
            out.append(word[:limit])
            word = word[limit:]
        cand = (cur + " " + word).strip()
        if len(cand) <= limit:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def write_srt(rows, dest) -> int:
    lines = [f"{i}\n{ts(a)} --> {ts(max(b, a + 0.15))}\n{t}\n"
             for i, (a, b, t) in enumerate(rows, 1)]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def split8(rows):
    """원 큐를 [start, 다음 start) 로 재구성해 사이의 빈틈을 없앤 뒤 여덟 자로 쪼갠다."""
    spans = []
    for i, (a, b, t) in enumerate(rows):
        end = rows[i + 1][0] if i + 1 < len(rows) else b
        if end - a >= 0.05 and t.strip():
            spans.append((a, end, t.strip()))

    out = []
    for a, b, t in spans:
        parts = chunks(t)
        if not parts:
            continue
        weights = [max(len(p), 1) for p in parts]
        total = sum(weights)
        cursor, span = a, b - a
        for part, weight in zip(parts, weights):
            dur = max(span * weight / total, MIN_DUR)
            out.append((cursor, cursor + dur, part))
            cursor += dur

    out.sort(key=lambda r: r[0])
    clean = []
    for i, (a, b, t) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else b
        clean.append((a, min(b, nxt) if nxt > a else a + MIN_DUR, t))
    return clean


def main() -> None:
    parser = root_parser("쇼츠 구간을 mp4 와 SRT 로 잘라낸다")
    parser.add_argument("--only", help="이 슬러그만 자른다")
    args = parser.parse_args()
    root = args.root
    if root is None:
        raise SystemExit("ROOT_REQUIRED: --root 또는 SPINE_EPISODE_ROOT")

    path = root / "work" / "shorts.json"
    if not path.is_file():
        raise SystemExit(f"SHORTS_JSON_MISSING: {path} — mark_shorts.py 를 먼저 돌린다")
    data = json.loads(path.read_text(encoding="utf-8"))
    episode = data["episode_id"]

    # corrections.json 은 [오인식, 정확표기] 쌍의 목록이다. 빈 쌍과 주석 줄은 버린다.
    fixes = []
    corrections = root / "work" / "corrections.json"
    if corrections.is_file():
        raw = json.loads(corrections.read_text(encoding="utf-8"))
        pairs = raw if isinstance(raw, list) else list(raw.get("replace", raw).items())
        fixes = [(a, b) for a, b in pairs if a and b]

    done = failed = 0
    for row in data["shorts"]:
        if args.only and row["slug"] != args.only:
            continue
        slug, start, end = row["slug"], row["start"], row["end"]
        src = root / "clips" / f"{row['source']}.mp4"
        if not src.is_file():
            raise SystemExit(f"SHORT_SOURCE_CLIP_MISSING: {src}")

        outdir = SHORTS_ROOT / episode / slug
        outdir.mkdir(parents=True, exist_ok=True)
        mp4 = outdir / f"{slug}.mp4"
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(mp4),
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"실패 {slug} — {result.stderr.strip()[:200]}")
            failed += 1
            continue

        cues = load_cues(root / "srt" / f"{row['source']}.cues.json")
        window = []
        for a, b, t in cues:
            if b <= start or a >= end:
                continue
            for wrong, right in fixes:
                t = t.replace(wrong, right)
            window.append((max(a, start) - start, min(b, end) - start, t))

        raw_n = write_srt(window, outdir / f"{slug}.srt")
        eight = split8(window)
        eight_n = write_srt(eight, outdir / f"{slug}_8자.srt")
        over = sum(1 for _, _, t in eight if len(t) > MAX_CHARS)
        size = mp4.stat().st_size / 1_000_000
        print(f"완료 {slug:24s} {end - start:5.1f}초 {size:6.1f}MB  "
              f"자막 {raw_n} → {eight_n}개  여덟자초과 {over}")
        done += 1

    print(f"\n완료 {done} / 실패 {failed} → {SHORTS_ROOT / episode}")


if __name__ == "__main__":
    main()
