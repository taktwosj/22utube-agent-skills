from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from common import inspect_write_target, read_json, resolved_declared_path, result, sha256_file, write_json
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA = SKILL_ROOT / "schemas" / "clean_visual_manifest.schema.json"
SOURCE_SCHEMA = SKILL_ROOT / "schemas" / "source_identity.schema.json"
DESIGN_SCHEMA = SKILL_ROOT / "schemas" / "design_lock_evidence.schema.json"
RECEIPT_SCHEMA = SKILL_ROOT / "schemas" / "clean_visual_receipt.schema.json"


def _probe_video(path: Path) -> tuple[bool, int | None, int | None, int | None]:
    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                "stream=codec_type,width,height:format=duration", "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return False, None, None, None
        payload = json.loads(completed.stdout)
        streams = [row for row in payload.get("streams", []) if row.get("codec_type") == "video"]
        if not streams:
            return False, None, None, None
        stream = streams[0]
        duration_us = round(float(payload["format"]["duration"]) * 1_000_000)
        return duration_us > 0, duration_us, int(stream["width"]), int(stream["height"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False, None, None, None


def validate_clean_visual(
    manifest_path: Path,
    source_identity_path: Path,
    design_lock_evidence_path: Path,
    evidence_path: Path | None = None,
    approved_evidence_root_path: Path | None = None,
) -> dict:
    manifest_path = Path(manifest_path).resolve()
    source_identity_path = Path(source_identity_path).resolve()
    design_lock_evidence_path = Path(design_lock_evidence_path).resolve()

    evidence_target: Path | None = None
    if evidence_path is not None:
        if approved_evidence_root_path is None:
            return result([{"code": "CLEAN_VISUAL_EVIDENCE_ROOT_REQUIRED"}])
        evidence_target = Path(evidence_path).absolute()
        guard = inspect_write_target(Path(approved_evidence_root_path), evidence_target, require_new=True)
        if guard == "PATH_EXISTS":
            return result([{"code": "CLEAN_VISUAL_EVIDENCE_PATH_EXISTS"}])
        if guard is not None:
            return result([{"code": "CLEAN_VISUAL_EVIDENCE_PATH_UNSAFE"}])

    try:
        manifest = read_json(manifest_path)
        source = read_json(source_identity_path)
        design = read_json(design_lock_evidence_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "CLEAN_VISUAL_INPUT_INVALID", "detail": str(exc)}])

    errors: list[dict] = []
    for payload, schema_path, code in (
        (manifest, MANIFEST_SCHEMA, "CLEAN_VISUAL_MANIFEST_SCHEMA"),
        (source, SOURCE_SCHEMA, "CLEAN_VISUAL_SOURCE_IDENTITY_SCHEMA"),
        (design, DESIGN_SCHEMA, "CLEAN_VISUAL_DESIGN_LOCK_SCHEMA"),
    ):
        schema_errors = validate_schema(payload, read_json(schema_path))
        if schema_errors:
            errors.append({"code": code, "detail": schema_errors})
    if errors:
        return result(errors)

    actual_source_sha = sha256_file(source_identity_path)
    actual_design_sha = sha256_file(design_lock_evidence_path)
    if resolved_declared_path(manifest_path, manifest["source_identity_path"]) != source_identity_path:
        errors.append({"code": "CLEAN_VISUAL_SOURCE_IDENTITY_PATH_MISMATCH"})
    if manifest["source_identity_sha256"].lower() != actual_source_sha.lower():
        errors.append({"code": "CLEAN_VISUAL_SOURCE_IDENTITY_SHA_MISMATCH"})
    if resolved_declared_path(manifest_path, manifest["design_lock_evidence_path"]) != design_lock_evidence_path:
        errors.append({"code": "CLEAN_VISUAL_DESIGN_LOCK_PATH_MISMATCH"})
    if manifest["design_lock_evidence_sha256"].lower() != actual_design_sha.lower():
        errors.append({"code": "CLEAN_VISUAL_DESIGN_LOCK_SHA_MISMATCH"})

    if len({manifest["episode_id"], source["episode_id"], design["episode_id"]}) != 1:
        errors.append({"code": "CLEAN_VISUAL_EPISODE_ID_MISMATCH"})
    if (
        resolved_declared_path(design_lock_evidence_path, design["source_identity_path"])
        != source_identity_path
        or design["source_identity_sha256"].lower() != actual_source_sha.lower()
    ):
        errors.append({"code": "CLEAN_VISUAL_DESIGN_SOURCE_IDENTITY_MISMATCH"})
    if design["source_fingerprint"] != source["source_fingerprint"]:
        errors.append({"code": "CLEAN_VISUAL_SOURCE_FINGERPRINT_MISMATCH"})

    source_media = resolved_declared_path(source_identity_path, source["media_path"])
    if not source_media.is_file() or sha256_file(source_media).lower() != source["media_sha256"].lower():
        errors.append({"code": "CLEAN_VISUAL_SOURCE_MEDIA_INVALID"})

    clean_source = resolved_declared_path(manifest_path, manifest["clean_source_path"])
    clean_sha = ""
    duration_us = width = height = None
    if not clean_source.is_file() or clean_source.stat().st_size <= 0:
        errors.append({"code": "CLEAN_VISUAL_FILE_MISSING"})
    else:
        clean_sha = sha256_file(clean_source)
        if clean_sha.lower() != manifest["clean_source_sha256"].lower():
            errors.append({"code": "CLEAN_VISUAL_FILE_SHA_MISMATCH"})
        if clean_sha.lower() == source["media_sha256"].lower():
            errors.append({"code": "CLEAN_VISUAL_SAME_AS_SOURCE"})
        valid_video, duration_us, width, height = _probe_video(clean_source)
        if not valid_video:
            errors.append({"code": "CLEAN_VISUAL_VIDEO_STREAM_INVALID"})
        else:
            if abs(duration_us - manifest["expected_duration_us"]) > 50_000:
                errors.append({"code": "CLEAN_VISUAL_DURATION_MISMATCH"})
            if (width, height) != (manifest["expected_width"], manifest["expected_height"]):
                errors.append({"code": "CLEAN_VISUAL_RESOLUTION_MISMATCH"})
    if errors:
        return result(errors)

    receipt = {
        "schema_version": "001short-clean-visual-receipt-v1",
        "status": "PASS",
        "episode_id": manifest["episode_id"],
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "source_identity_path": str(source_identity_path),
        "source_identity_sha256": actual_source_sha,
        "design_lock_evidence_path": str(design_lock_evidence_path),
        "design_lock_evidence_sha256": actual_design_sha,
        "clean_source_path": str(clean_source),
        "clean_source_sha256": clean_sha,
        "source_fingerprint": source["source_fingerprint"],
        "measured_duration_us": duration_us,
        "width": width,
        "height": height,
        "video_stream_verified": True,
        "ffprobe_verified": True,
    }
    schema_errors = validate_schema(receipt, read_json(RECEIPT_SCHEMA))
    if schema_errors:
        return result([{"code": "CLEAN_VISUAL_RECEIPT_SCHEMA", "detail": schema_errors}])
    if evidence_target is not None:
        write_json(evidence_target, receipt)
        receipt["clean_visual_receipt_path"] = str(evidence_target)
        receipt["clean_visual_receipt_sha256"] = sha256_file(evidence_target)
    return result([], receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-identity", type=Path, required=True)
    parser.add_argument("--design-lock-evidence", type=Path, required=True)
    parser.add_argument("--clean-visual-evidence", type=Path, required=True)
    parser.add_argument("--approved-evidence-root", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_clean_visual(
        args.manifest,
        args.source_identity,
        args.design_lock_evidence,
        args.clean_visual_evidence,
        args.approved_evidence_root,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
