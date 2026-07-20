#!/usr/bin/env python3
"""Validate the fixed Shorts caption beat and layout contract."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


PROFILES: dict[str, dict[str, int]] = {
    "tts_narration": {"y": -900, "max_chars_per_line": 10, "max_lines": 1},
    "tts_caption": {"y": -900, "max_chars_per_line": 10, "max_lines": 1},
    "speaker_quote": {"y": -500, "max_chars_per_line": 10, "max_lines": 1},
    "situation_caption": {"y": 700, "max_chars_per_line": 10, "max_lines": 1},
}


def validate(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GateFail("CAPTION_BEAT_MAP_REQUIRED")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateFail(f"FAIL_CAPTION_BEAT_MAP_INVALID:{exc}") from exc
    if data.get("status") != "PASS":
        raise GateFail("FAIL_CAPTION_BEAT_MAP_STATUS")
    if data.get("profile_version") != "caption_profiles_v2":
        raise GateFail("FAIL_CAPTION_PROFILE_VERSION")
    if data.get("video_scale") != 1.2:
        raise GateFail("FAIL_VIDEO_SCALE_REQUIRED:1.20")
    if data.get("face_avoidance") != "fixed_lower_safe_zone_v1":
        raise GateFail("FAIL_FACE_AVOIDANCE_PROFILE")

    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        raise GateFail("FAIL_CAPTION_BEAT_MAP_BEATS_MISSING")
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise GateFail(f"FAIL_CAPTION_BEAT_INVALID:{index}")
        role = str(beat.get("caption_role") or "")
        if role not in PROFILES:
            raise GateFail(f"FAIL_CAPTION_ROLE:{index}")
        for field in ("beat_id", "edit_id", "text", "timing_source"):
            if not str(beat.get(field) or "").strip():
                raise GateFail(f"FAIL_CAPTION_BEAT_FIELD:{index}:{field}")
        start = beat.get("start_sec")
        end = beat.get("end_sec")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end <= start:
            raise GateFail(f"FAIL_CAPTION_BEAT_TIME:{index}")
        profile = PROFILES[role]
        if beat.get("max_chars_per_line") != profile["max_chars_per_line"]:
            raise GateFail(f"FAIL_CAPTION_CHAR_LIMIT:{index}")
        if beat.get("max_lines") != profile["max_lines"]:
            raise GateFail(f"FAIL_CAPTION_LINE_LIMIT:{index}")
        if beat.get("y") != profile["y"]:
            raise GateFail(f"FAIL_CAPTION_Y_POSITION:{index}")
        lines = str(beat["text"]).splitlines() or [str(beat["text"])]
        if len(lines) > profile["max_lines"] or any(len(line) > profile["max_chars_per_line"] for line in lines):
            raise GateFail(f"FAIL_CAPTION_BEAT_TEXT_LIMIT:{index}")
        by_role[role].append(beat)

    for role, role_beats in by_role.items():
        ordered = sorted(role_beats, key=lambda item: float(item["start_sec"]))
        for previous, current in zip(ordered, ordered[1:]):
            if float(current["start_sec"]) < float(previous["end_sec"]):
                raise GateFail(f"FAIL_CAPTION_BEAT_OVERLAP:{role}")
    return {
        "status": "PASS",
        "profile_version": data["profile_version"],
        "video_scale": data["video_scale"],
        "face_avoidance": data["face_avoidance"],
        "beat_count": len(beats),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("caption_beat_map", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.caption_beat_map), ensure_ascii=False, indent=2))
    except GateFail as exc:
        print(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
