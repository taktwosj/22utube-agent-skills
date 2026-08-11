from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import read_json, resolved_declared_path, result, sha256_file
from schema_runtime import validate_schema
from validate_audio_caption import _probe_audio


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "schemas" / "vocal_stem_manifest.schema.json"


def validate_vocal_stem(manifest_path: Path) -> dict:
    manifest_path = Path(manifest_path).resolve()
    try:
        manifest = read_json(manifest_path)
    except (OSError, TypeError, ValueError) as exc:
        return result([{"code": "VOCAL_STEM_MANIFEST_INVALID", "detail": str(exc)}])
    errors: list[dict] = []
    if schema_errors := validate_schema(manifest, read_json(SCHEMA)):
        errors.append({"code": "VOCAL_STEM_MANIFEST_SCHEMA", "detail": schema_errors})
        return result(errors)
    source = resolved_declared_path(manifest_path, manifest["source_path"])
    vocals = resolved_declared_path(manifest_path, manifest["vocals_path"])
    allowed = resolved_declared_path(manifest_path, manifest["capcut_allowed_audio_path"])
    if not source.is_file() or sha256_file(source) != manifest["source_sha256"]:
        errors.append({"code": "VOCAL_STEM_SOURCE_INVALID"})
        source_duration_us = None
    else:
        source_duration_us, _ = _probe_audio(source)
        if source_duration_us is None or abs(source_duration_us - manifest["source_duration_us"]) > 100_000:
            errors.append({"code": "VOCAL_STEM_SOURCE_DURATION_MISMATCH"})
    if vocals.name != "vocals.wav" or allowed.name != "vocals.wav":
        errors.append({"code": "VOCAL_STEM_CANONICAL_FILENAME_REQUIRED"})
    if not vocals.is_file() or sha256_file(vocals) != manifest["vocals_sha256"]:
        errors.append({"code": "VOCAL_STEM_VOCALS_FILE_INVALID"})
    elif allowed != vocals:
        errors.append({"code": "VOCAL_STEM_CAPCUT_PATH_NOT_VOCALS"})
    else:
        duration_us, codecs = _probe_audio(vocals)
        if duration_us is None or abs(duration_us - manifest["vocals_duration_us"]) > 100_000:
            errors.append({"code": "VOCAL_STEM_DURATION_MISMATCH"})
        if manifest["vocals_codec"].casefold() not in codecs:
            errors.append({"code": "VOCAL_STEM_CODEC_MISMATCH"})
        if duration_us is not None and source_duration_us is not None and abs(duration_us - source_duration_us) > 100_000:
            errors.append({"code": "VOCAL_STEM_SOURCE_DURATION_MISMATCH"})
    residual_value = manifest.get("residual_reference_path")
    residual_sha = manifest.get("residual_reference_sha256")
    if residual_value or residual_sha:
        residual = resolved_declared_path(manifest_path, str(residual_value or ""))
        if not residual.is_file() or not isinstance(residual_sha, str) or sha256_file(residual) != residual_sha:
            errors.append({"code": "VOCAL_STEM_RESIDUAL_REFERENCE_INVALID"})
    return result(errors, {
        "episode_id": manifest["episode_id"],
        "a10_audio_path": str(vocals),
        "a12_policy": manifest["a12_policy"],
        "human_listen_qc_required": manifest["human_listen_qc_required"],
        "human_listen_qc_status": "NOT_VERIFIED",
        "audio_quality_status": "NOT_VERIFIED",
    })


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a 001short Demucs vocal-stem manifest.")
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_vocal_stem(args.manifest)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
