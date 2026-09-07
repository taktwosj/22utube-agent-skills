# -*- coding: utf-8 -*-
"""Typecast 통합 MP3+SRT 를 나레이션 '한 줄' 단위 wav/txt 로 자른다.

Typecast 웹 에디터에 원고를 붙여 넣으면 SRT cue 하나가 원고 한 줄이 된다.
카드도 같은 단위로 쪼개면 화면이 평균 10초마다 바뀐다.
입력: <root>/narration/tts_raw.mp3, tts_raw.srt, 블록 원고 <root>/narration/<block>.txt
출력: <root>/narration/NL01.wav ... + NL01.txt ..., <root>/work/narration_lines.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import load_cards_def, resolve_root, root_parser  # noqa: E402


def norm(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", s)


def parse_srt(path: Path):
    raw = path.read_text(encoding="utf-8-sig")
    out = []
    for m in re.finditer(r"(\d\d:\d\d:\d\d[,.]\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d[,.]\d\d\d)\n(.*?)(?=\n\s*\n|\Z)", raw, re.S):
        def ts(t):
            h, mn, s = t.replace(",", ".").split(":")
            return int(h) * 3600 + int(mn) * 60 + float(s)
        out.append([ts(m.group(1)), ts(m.group(2)), " ".join(m.group(3).split())])
    return out


def probe(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nw=1:nk=1", str(p)],
                                capture_output=True, text=True, check=True).stdout.strip())


def main():
    args = root_parser("TTS mp3+srt -> 줄 단위 wav").parse_args()
    root = resolve_root(args)
    cd = load_cards_def(root)
    narr = root / "narration"
    cues = parse_srt(narr / "tts_raw.srt")
    total = probe(narr / "tts_raw.mp3")
    lines = []
    for block in cd.NARRATION_ORDER:
        for ln in (narr / f"{block}.txt").read_text(encoding="utf-8").strip().splitlines():
            if ln.strip():
                lines.append((block, ln.strip()))
    if len(lines) != len(cues):
        raise SystemExit(f"LINE_CUE_COUNT_MISMATCH lines={len(lines)} cues={len(cues)} — "
                         f"TTS 원고와 블록 txt 가 다르다. 어느 버전으로 합성했는지 확인")
    for i, ((block, ln), cue) in enumerate(zip(lines, cues), 1):
        if norm(ln) != norm(cue[2]):
            raise SystemExit(f"LINE_MISMATCH #{i} {block}\n  txt={ln[:70]}\n  srt={cue[2][:70]}")
    index = []
    for i, ((block, ln), cue) in enumerate(zip(lines, cues), 1):
        name = f"NL{i:02d}"
        a = cue[0]; b = total if i == len(cues) else cue[1]
        (narr / f"{name}.txt").write_text(ln + "\n", encoding="utf-8")
        dst = narr / f"{name}.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{a:.3f}",
                        "-i", str(narr / "tts_raw.mp3"), "-t", f"{b - a:.3f}",
                        "-ar", "48000", "-ac", "2", str(dst)], check=True)
        d = probe(dst)
        index.append({"name": name, "block": block, "start": a, "end": b, "duration": d, "text": ln})
        print(f"{name} {block:6s} {d:6.2f}s  {ln[:52]}")
    (root / "work" / "narration_lines.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"lines={len(index)} sum={sum(x['duration'] for x in index):.2f}s mp3={total:.2f}s")


if __name__ == "__main__":
    main()
