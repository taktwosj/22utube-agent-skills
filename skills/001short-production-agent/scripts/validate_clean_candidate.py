from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import inspect_write_target, read_json, resolved_declared_path, result, sha256_file, write_json
from schema_runtime import validate_schema
from validate_clean_visual import _portrait_aspect_compatible, _probe_video


SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA = SKILL_ROOT / "schemas" / "source_identity.schema.json"
RECEIPT_SCHEMA = SKILL_ROOT / "schemas" / "clean_candidate_receipt.schema.json"


def validate_clean_candidate(
    source_identity_path: Path,
    candidate_path: Path,
    receipt_path: Path | None = None,
    approved_evidence_root_path: Path | None = None,
) -> dict:
    source_identity_path = Path(source_identity_path).resolve()
    candidate_path = Path(candidate_path).resolve()

    receipt_target: Path | None = None
    if receipt_path is not None:
        if approved_evidence_root_path is None:
            return result([{"code": "CLEAN_CANDIDATE_EVIDENCE_ROOT_REQUIRED"}])
        receipt_target = Path(receipt_path).absolute()
        guard = inspect_write_target(Path(approved_evidence_root_path), receipt_target, require_new=True)
        if guard == "PATH_EXISTS":
            return result([{"code": "CLEAN_CANDIDATE_RECEIPT_PATH_EXISTS"}])
        if guard is not None:
            return result([{"code": "CLEAN_CANDIDATE_RECEIPT_PATH_UNSAFE"}])

    try:
        source = read_json(source_identity_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "CLEAN_CANDIDATE_SOURCE_IDENTITY_INVALID", "detail": str(exc)}])

    schema_errors = validate_schema(source, read_json(SOURCE_SCHEMA))
    if schema_errors:
        return result([{"code": "CLEAN_CANDIDATE_SOURCE_IDENTITY_SCHEMA", "detail": schema_errors}])

    errors: list[dict] = []
    source_media = resolved_declared_path(source_identity_path, source["media_path"])
    if not source_media.is_file() or sha256_file(source_media).lower() != source["media_sha256"].lower():
        errors.append({"code": "CLEAN_CANDIDATE_SOURCE_MEDIA_INVALID"})
    source_ok, source_duration_us, source_width, source_height = _probe_video(source_media)
    if not source_ok:
        errors.append({"code": "CLEAN_CANDIDATE_SOURCE_VIDEO_STREAM_INVALID"})

    candidate_sha = ""
    duration_us = width = height = None
    if not candidate_path.is_file() or candidate_path.stat().st_size <= 0:
        errors.append({"code": "CLEAN_CANDIDATE_FILE_MISSING"})
    else:
        candidate_sha = sha256_file(candidate_path)
        if candidate_sha.lower() == source["media_sha256"].lower():
            errors.append({"code": "CLEAN_CANDIDATE_SAME_AS_SOURCE"})
        candidate_ok, duration_us, width, height = _probe_video(candidate_path)
        if not candidate_ok:
            errors.append({"code": "CLEAN_CANDIDATE_VIDEO_STREAM_INVALID"})
        elif source_ok:
            if abs(duration_us - source_duration_us) > 50_000:
                errors.append({"code": "CLEAN_CANDIDATE_DURATION_MISMATCH"})
            if not _portrait_aspect_compatible(source_width, source_height, width, height):
                errors.append({"code": "CLEAN_CANDIDATE_ASPECT_RATIO_MISMATCH"})
    if errors:
        return result(errors)

    receipt = {
        "schema_version": "001short-clean-candidate-receipt-v1",
        "status": "PASS",
        "episode_id": source["episode_id"],
        "source_identity_path": str(source_identity_path),
        "source_identity_sha256": sha256_file(source_identity_path),
        "source_media_path": str(source_media),
        "source_media_sha256": source["media_sha256"],
        "candidate_path": str(candidate_path),
        "candidate_sha256": candidate_sha,
        "candidate_differs_from_source": True,
        "measured_duration_us": duration_us,
        "width": width,
        "height": height,
        "video_stream_verified": True,
        "ffprobe_verified": True,
        "quality_evaluated": False,
        "user_visual_review_required": True,
        "final_clean_acceptance": "NOT_DECIDED",
    }
    schema_errors = validate_schema(receipt, read_json(RECEIPT_SCHEMA))
    if schema_errors:
        return result([{"code": "CLEAN_CANDIDATE_RECEIPT_SCHEMA", "detail": schema_errors}])
    if receipt_target is not None:
        write_json(receipt_target, receipt)
        receipt["clean_candidate_receipt_path"] = str(receipt_target)
        receipt["clean_candidate_receipt_sha256"] = sha256_file(receipt_target)
    return result([], receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-identity", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-receipt", type=Path, required=True)
    parser.add_argument("--approved-evidence-root", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_clean_candidate(
        args.source_identity, args.candidate, args.candidate_receipt, args.approved_evidence_root
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
