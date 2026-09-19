# -*- coding: utf-8 -*-
"""timeline.json -> asset_evidence.json (119 compile 입력, A/B/C/D lane 실측 증거)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (hyperframe_files, load_cards_def, require_hyperframes,
                     resolve_root, root_parser)  # noqa: E402


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def video_offsets(timeline: dict, moving: dict) -> dict[str, int]:
    """카드가 장면 영상의 어디서부터 가져갈지 정한다.

    한 장면을 나눠 쓰는 카드는 타임라인에서 붙어 있어야 한다. 붙어 있는 동안은
    구간이 이어지고, 끊기면 다시 0부터 시작한다. 같은 영상이 회차의 떨어진 두
    자리에 쓰이는 경우가 있다 — CTA 한 줄은 오프닝과 마지막에 두 번 놓인다.
    그때 두 번째 자리는 영상을 처음부터 다시 쓴다.
    """
    offsets: dict[str, int] = {}
    need: dict[str, int] = {}
    prev_clip: str | None = None
    prev_end: int | None = None
    held = 0
    for card in timeline["cards"]:
        if card["kind"] == "SRC":
            continue
        clip = moving.get(card["card_id"])
        if clip is None:
            prev_clip, prev_end = None, None
            continue
        key = str(clip)
        joined = (key == prev_clip and prev_end == card["target_start_us"])
        if not joined:
            held = 0
        offsets[card["card_id"]] = held
        held += card["target_duration_us"]
        need[key] = max(need.get(key, 0), held)
        prev_clip, prev_end = key, card["target_start_us"] + card["target_duration_us"]
    check_scene_lengths(moving, need)
    return offsets


def check_scene_lengths(moving: dict, needed: dict[str, int]) -> None:
    """장면이 그 장면을 나눠 쓰는 카드 전체보다 짧으면 뒤가 검게 빈다."""
    for key, want in needed.items():
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", key],
            capture_output=True, text=True)
        if probe.returncode != 0:
            raise SystemExit(f"HYPERFRAME_PROBE_FAILED: {Path(key).name}")
        have = int(float(probe.stdout.strip()) * 1_000_000)
        if have < want:
            raise SystemExit(
                f"HYPERFRAME_TOO_SHORT: {Path(key).name} "
                f"{have/1_000_000:.3f}s < 카드 합계 {want/1_000_000:.3f}s")


def main():
    args = root_parser("asset_evidence.json 생성").parse_args()
    root = resolve_root(args)
    tl = json.loads((root / "work" / "timeline.json").read_text(encoding="utf-8"))
    moving = hyperframe_files(root)
    require_hyperframes(root, load_cards_def(root), moving)
    offsets = video_offsets(tl, moving)
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
            common = {k: r[k] for k in ("card_id", "target_start_us", "target_duration_us", "narration_audio_file",
                                        "narration_audio_sha256", "audio_duration_us", "narration_srt_file",
                                        "narration_srt_sha256")}
            clip = moving.get(r["card_id"])
            if clip is not None:
                # 움직이는 설명카드. 한 장면이 여러 줄을 덮으면 카드마다 그 장면의
                # 다른 구간을 가져간다. 그래야 카드 경계에서 화면이 끊기지 않는다.
                cards.append(common | {"video_file": str(clip), "video_sha256": sha(clip),
                                       "video_start_us": offsets[r["card_id"]],
                                       "video_duration_us": r["target_duration_us"],
                                       "source_audio_mode": "OFF"})
                continue
            img = root / "cards" / f"{cid}.png"
            if not img.is_file():
                raise SystemExit(f"CARD_PNG_MISSING {cid}: render_cards.py 먼저")
            cards.append(common | {"image_file": str(img), "image_sha256": sha(img),
                                   "motion_profile": "SLOW_ZOOM_IN"})
    out = root / "asset_evidence.json"
    out.write_text(json.dumps({"status": "PASS", "lanes": {"A": "PASS", "B": "PASS", "C": "PASS", "D": "PASS"},
                               "cards": cards}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("evidence:", out, "cards", len(cards))


if __name__ == "__main__":
    main()
