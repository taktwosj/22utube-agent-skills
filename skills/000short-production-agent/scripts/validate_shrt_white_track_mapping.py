#!/usr/bin/env python3
"""Validate shrt white semantic audio lane resolution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


EXPECTED_SHRT_WHITE_AUDIO_MAPPING = {
    "audio.narration_tts": "A9",
    "audio.speaker_source": "A10",
    "audio.sfx": "A11",
    "audio.bgm": "A12",
}


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "예"}
    return bool(value)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail("track mapping json root must be object")
    return data


def validate_shrt_white_track_mapping(data: dict[str, Any]) -> dict[str, Any]:
    profile = str(data.get("template_profile") or "")
    reference_project = str(data.get("reference_project_name") or "")
    if profile != "shrt_white_base_v1":
        raise GateFail("FAIL_SHRT_WHITE_BASE_NOT_CLONED: template_profile must be shrt_white_base_v1")
    if reference_project != "shrt white":
        raise GateFail("FAIL_SHRT_WHITE_BASE_NOT_CLONED: reference_project_name must be shrt white")
    if not truthy(data.get("derived_from_reference_project")):
        raise GateFail("FAIL_SHRT_WHITE_BASE_NOT_CLONED: derived_from_reference_project must be true")

    mapping = data.get("semantic_audio_resolution")
    if not isinstance(mapping, dict):
        raise GateFail("FAIL_AUDIO_TRACK_MAPPING: semantic_audio_resolution missing")
    for lane, expected_track in EXPECTED_SHRT_WHITE_AUDIO_MAPPING.items():
        if mapping.get(lane) != expected_track:
            raise GateFail(
                f"FAIL_AUDIO_TRACK_MAPPING: {lane} must resolve to {expected_track}; got {mapping.get(lane)!r}"
            )
    return {
        "shrt_white_track_mapping_status": "PASS",
        "semantic_audio_resolution": dict(EXPECTED_SHRT_WHITE_AUDIO_MAPPING),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    args = parser.parse_args()
    try:
        result = validate_shrt_white_track_mapping(load_json(Path(args.json_path)))
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
