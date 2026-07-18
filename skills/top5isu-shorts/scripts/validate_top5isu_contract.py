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


EXPECTED_TRACKS = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]
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
    require(
        data.get("contract_version") == "top5isu_build_contract_v1",
        "FAIL_TOP5ISU_CONTRACT",
        "contract_version must be top5isu_build_contract_v1",
    )
    require(
        data.get("template_profile") == "top5isu_v1",
        "FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN",
        "template_profile must be top5isu_v1",
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
    require(data.get("required_tracks") == EXPECTED_TRACKS, "FAIL_TOP5ISU_TRACK_MAPPING", "track order mismatch")
    require(data.get("image_effect_count_required") == 7, "FAIL_TOP5ISU_TRACK_MAPPING", "seven effects required")
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
        "template_profile": "top5isu_v1",
        "style_profile": profile,
        "required_tracks": list(EXPECTED_TRACKS),
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
