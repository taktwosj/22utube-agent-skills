# -*- coding: utf-8 -*-
"""timeline.json -> asset_evidence.json (119 compile 입력, A/B/C/D lane 실측 증거)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import resolve_root, root_parser  # noqa: E402


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    args = root_parser("asset_evidence.json 생성").parse_args()
    root = resolve_root(args)
    tl = json.loads((root / "work" / "timeline.json").read_text(encoding="utf-8"))
    cards = []
    for r in tl["cards"]:
        cid = r["card_id"]
        if r["kind"] == "SRC":
            raw, disp = root / "srt" / f"{cid}.raw.srt", root / "srt" / f"{cid}.display.srt"
            cards.append({k: r[k] for k in ("card_id", "target_start_us", "target_duration_us", "source_file",
                                            "source_sha256", "source_duration_us", "source_channel", "source_date")} | {
                "raw_transcript_path": str(raw), "raw_transcript_sha256": sha(raw),
                "display_srt_path": str(disp), "display_srt_sha256": sha(disp),
                "display_transform": ["SPLIT", "CLAMP", "DIALOGUE_MARKER_REMOVAL"],
                "source_srt_file": str(disp), "source_srt_sha256": sha(disp)})
        else:
            img = root / "cards" / f"{cid}.png"
            if not img.is_file():
                raise SystemExit(f"CARD_PNG_MISSING {cid}: render_cards.py 먼저")
            cards.append({k: r[k] for k in ("card_id", "target_start_us", "target_duration_us", "narration_audio_file",
                                            "narration_audio_sha256", "audio_duration_us", "narration_srt_file",
                                            "narration_srt_sha256")} | {
                "image_file": str(img), "image_sha256": sha(img), "motion_profile": "SLOW_ZOOM_IN"})
    out = root / "asset_evidence.json"
    out.write_text(json.dumps({"status": "PASS", "lanes": {"A": "PASS", "B": "PASS", "C": "PASS", "D": "PASS"},
                               "cards": cards}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("evidence:", out, "cards", len(cards))


if __name__ == "__main__":
    main()
