#!/usr/bin/env python3
"""Validate the standalone top5isu_v1 track and coordinate mapping."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


EXPECTED_TRACKS_V1 = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]
EXPECTED_TRACKS_V2 = ["IMAGE_EFFECT_PRESETS", "FRAME", "LOGO", "TTS_TEXT", "SOURCE_TEXT", "T2", "T1"]
EXPECTED_AUDIO_MAPPING = {
    "audio.narration_tts": "A_TTS",
    "audio.speaker_source": "A_SOURCE",
    "audio.sfx": "A_SFX",
    "audio.bgm": "A_BGM",
}
FORBIDDEN_SHRT_WHITE_AUDIO_ROWS = {"A9", "A10", "A11", "A12"}


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pass", "예"}
    return bool(value)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail("top5isu track mapping json root must be object")
    return data


def validate_top5isu_track_mapping(data: dict[str, Any]) -> dict[str, Any]:
    profile = str(data.get("template_profile") or "")
    reference_project = str(data.get("reference_project_name") or "")
    if profile not in {"top5isu_v1", "top5isu_v2_top55"} or reference_project != "top5isu":
        raise GateFail(
            "FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN: top5isu work must use "
            "an approved top5isu template_profile and reference_project_name=top5isu"
        )
    if data.get("fallback_allowed") is not False:
        raise GateFail("FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN: fallback_allowed must be false")
    if not truthy(data.get("derived_from_reference_project")):
        raise GateFail("FAIL_TOP5ISU_REFERENCE_NOT_CLONED: derived_from_reference_project must be true")
    expected_tracks = EXPECTED_TRACKS_V2 if profile == "top5isu_v2_top55" else EXPECTED_TRACKS_V1
    if data.get("required_tracks") != expected_tracks:
        raise GateFail(f"FAIL_TOP5ISU_TRACK_MAPPING: required_tracks must be {expected_tracks!r}")
    image_count = data.get("image_effect_segments")
    if profile == "top5isu_v2_top55":
        if data.get("image_prototype_segments") != 4:
            raise GateFail("FAIL_TOP5ISU_TRACK_MAPPING: image_prototype_segments must be 4")
        if not isinstance(image_count, int) or image_count < 1:
            raise GateFail("FAIL_TOP5ISU_TRACK_MAPPING: one or more image segments required")
        if data.get("image_transition_animation_required") is not True:
            raise GateFail("FAIL_TOP5ISU_IMAGE_TRANSITION_REQUIRED: every image requires an animation")
        high_impact_indices = data.get("high_impact_indices")
        if (
            not isinstance(high_impact_indices, list)
            or not 1 <= len(high_impact_indices) <= 2
            or len(set(high_impact_indices)) != len(high_impact_indices)
            or any(not isinstance(value, int) or value < 1 or value > image_count for value in high_impact_indices)
        ):
            raise GateFail("FAIL_TOP5ISU_HIGH_IMPACT_EFFECT: one or two valid image indices required")
    else:
        if image_count != 7:
            raise GateFail("FAIL_TOP5ISU_TRACK_MAPPING: image_effect_segments must be 7")
        if data.get("image_ui_y") != -600 or data.get("image_json_transform_y") != -0.15625:
            raise GateFail(
                "FAIL_TOP5ISU_COORDINATE_LOCK: image_ui_y=-600 must map to "
                "image_json_transform_y=-0.15625"
            )
        high_impact_indices = []
    mapping = data.get("semantic_audio_resolution")
    if not isinstance(mapping, dict) or set(mapping) != set(EXPECTED_AUDIO_MAPPING):
        raise GateFail("FAIL_AUDIO_TRACK_MAPPING: semantic audio lanes are incomplete or unknown")
    values = list(mapping.values())
    if len(values) != len(set(values)):
        raise GateFail("FAIL_AUDIO_TRACK_MAPPING: semantic audio lanes must resolve uniquely")
    if any(value in FORBIDDEN_SHRT_WHITE_AUDIO_ROWS for value in values):
        raise GateFail("FAIL_AUDIO_TRACK_MAPPING: shrt white A9-A12 rows are forbidden")
    for lane, expected_track in EXPECTED_AUDIO_MAPPING.items():
        if mapping.get(lane) != expected_track:
            raise GateFail(
                f"FAIL_AUDIO_TRACK_MAPPING: {lane} must resolve to {expected_track}; "
                f"got {mapping.get(lane)!r}"
            )
    return {
        "top5isu_track_mapping_status": "PASS",
        "template_profile": profile,
        "required_tracks": list(expected_tracks),
        "high_impact_indices": list(high_impact_indices),
        "semantic_audio_resolution": dict(EXPECTED_AUDIO_MAPPING),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    args = parser.parse_args()
    try:
        result = validate_top5isu_track_mapping(load_json(Path(args.json_path)))
    except (GateFail, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
