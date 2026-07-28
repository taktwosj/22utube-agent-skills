#!/usr/bin/env python3
"""Validate the fail-closed top5isu build contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


EXPECTED_TRACKS_V1 = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]
EXPECTED_TRACKS_V2 = ["IMAGE_EFFECT_PRESETS", "FRAME", "LOGO", "TTS_TEXT", "SOURCE_TEXT", "T2", "T1"]
HIGH_IMPACT_EFFECTS = ["불꽃 회오리", "불꽃 스와이프", "불꽃 마법"]
REQUIRED_KEYS = {
    "contract_version",
    "template_profile",
    "style_profile",
    "fallback_allowed",
    "clone_required",
    "root_template_mutation",
    "fresh_project_id_required",
    "fresh_timeline_id_required",
    "archive_file",
    "archive_sha256",
    "manifest_sha256",
    "packaged_file_count",
    "required_tracks",
    "image_effect_count_required",
    "image_ui_y",
    "image_json_transform_y",
    "logo_full_duration",
    "sample_media_policy",
    "audio_policy",
    "audio_normalization",
    "portable_manifest_paths",
    "bak_allowed_in_portable_package",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail("FAIL_TOP5ISU_CONTRACT: root must be an object")
    return data


def require(value: bool, code: str, detail: str) -> None:
    if not value:
        raise GateFail(f"{code}: {detail}")


def validate_top5isu_contract(data: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_KEYS - set(data))
    require(not missing, "FAIL_TOP5ISU_CONTRACT", f"missing fields: {missing}")
    template_profile = str(data.get("template_profile") or "")
    expected_pair = {
        "top5isu_v1": "top5isu_build_contract_v1",
        "top5isu_v2_top55": "top5isu_build_contract_v2",
    }
    require(
        template_profile in expected_pair and data.get("contract_version") == expected_pair[template_profile],
        "FAIL_TOP5ISU_CONTRACT",
        "contract_version and template_profile pair is invalid",
    )
    require(
        data.get("fallback_allowed") is False,
        "FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN",
        "fallback_allowed must be false",
    )
    require(data.get("clone_required") is True, "FAIL_TOP5ISU_CONTRACT", "clone_required must be true")
    require(
        data.get("root_template_mutation") is False,
        "FAIL_TOP5ISU_CONTRACT",
        "root_template_mutation must be false",
    )
    for key in ("fresh_project_id_required", "fresh_timeline_id_required"):
        require(data.get(key) is True, "FAIL_TOP5ISU_CONTRACT", f"{key} must be true")

    profile = data.get("style_profile")
    require(profile in {"top5", "gunlimbo"}, "FAIL_TOP5ISU_CONTRACT", "unknown style_profile")
    expected_tracks = EXPECTED_TRACKS_V2 if template_profile == "top5isu_v2_top55" else EXPECTED_TRACKS_V1
    require(data.get("required_tracks") == expected_tracks, "FAIL_TOP5ISU_TRACK_MAPPING", "track order mismatch")
    expected_prototypes = 4 if template_profile == "top5isu_v2_top55" else 7
    require(
        data.get("image_effect_count_required") == expected_prototypes,
        "FAIL_TOP5ISU_TRACK_MAPPING",
        f"{expected_prototypes} root animation prototypes required",
    )
    if template_profile == "top5isu_v2_top55":
        require(
            data.get("image_ui_y") == 0 and data.get("image_json_transform_y") == 0.0,
            "FAIL_TOP5ISU_COORDINATE_LOCK",
            "TOP55 root image transform must remain centered",
        )
        require(data.get("frame_full_duration") is True, "FAIL_TOP5ISU_CONTRACT", "frame must span full duration")
        require(
            data.get("image_transition_animation_required") is True,
            "FAIL_TOP5ISU_IMAGE_TRANSITION_REQUIRED",
            "every image requires an animation",
        )
        require(
            data.get("high_impact_effect_allowed") == HIGH_IMPACT_EFFECTS
            and data.get("high_impact_effect_required_count_min") == 1
            and data.get("high_impact_effect_required_count_max") == 2,
            "FAIL_TOP5ISU_HIGH_IMPACT_EFFECT",
            "one or two approved fire effects are required",
        )
    else:
        require(
            data.get("image_ui_y") == -600 and data.get("image_json_transform_y") == -0.15625,
            "FAIL_TOP5ISU_COORDINATE_LOCK",
            "UI -600 must map to JSON -0.15625",
        )
    require(data.get("logo_full_duration") is True, "FAIL_TOP5ISU_CONTRACT", "logo must span full duration")
    require(data.get("sample_media_policy") == "replace_all", "FAIL_TOP5ISU_CONTRACT", "samples must be replaced")
    require(data.get("portable_manifest_paths") is True, "FAIL_TOP5ISU_CONTRACT", "relative manifests required")
    require(
        data.get("bak_allowed_in_portable_package") is False,
        "FAIL_TOP5ISU_CONTRACT",
        ".bak must be forbidden",
    )

    archive_file = str(data.get("archive_file") or "")
    require(
        bool(archive_file) and Path(archive_file).name == archive_file and ".." not in archive_file,
        "FAIL_TOP5ISU_CONTRACT",
        "archive_file must be relative basename",
    )
    for key in ("archive_sha256", "manifest_sha256"):
        require(
            bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(data.get(key) or ""))),
            "FAIL_TOP5ISU_CONTRACT",
            f"{key} must be SHA256",
        )
    require(
        isinstance(data.get("packaged_file_count"), int) and data["packaged_file_count"] > 0,
        "FAIL_TOP5ISU_CONTRACT",
        "packaged_file_count must be positive",
    )

    normalization = data.get("audio_normalization")
    require(isinstance(normalization, dict), "FAIL_AUDIO_NORMALIZATION_CONTRACT", "audio_normalization missing")
    expected_normalization = {
        "method": "ffmpeg_loudnorm",
        "target_integrated_lufs": -14,
        "preimport_measurement_required": True,
        "final_export_remeasure_required": True,
    }
    require(
        all(normalization.get(k) == v for k, v in expected_normalization.items()),
        "FAIL_AUDIO_NORMALIZATION_CONTRACT",
        "ffmpeg loudnorm and final remeasurement are required",
    )

    audio_policy = data.get("audio_policy")
    require(isinstance(audio_policy, dict), "FAIL_SPEAKER_AUDIO_POLICY", "audio_policy missing")
    if profile == "gunlimbo":
        require(
            audio_policy.get("speaker_segments_preserved") is True
            and audio_policy.get("speaker_mute_forbidden") is True,
            "FAIL_SPEAKER_AUDIO_POLICY",
            "gunlimbo must preserve and unmute approved speaker segments",
        )

    return {
        "top5isu_contract_status": "PASS",
        "template_profile": template_profile,
        "style_profile": profile,
        "required_tracks": list(expected_tracks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract_json")
    args = parser.parse_args()
    try:
        result = validate_top5isu_contract(load_json(Path(args.contract_json)))
    except (GateFail, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
