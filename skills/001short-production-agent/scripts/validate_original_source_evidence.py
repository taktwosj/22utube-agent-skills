from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common import resolve_episode_artifact, sha256_file
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SKILL_ROOT / "schemas" / "original_source_evidence.schema.json"
CONTRACT_VERSION = "001short-original-source-transcript-v1"
INTAKE_V2 = "001short-source-intake-receipt-v2"


def _error(code: str, **details: Any) -> dict:
    return {"code": code, "table": "original", **details}


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def _checked_file(episode_root: Path, declared: object, expected_sha: object) -> Path:
    if not isinstance(declared, str) or not declared.strip() or not isinstance(expected_sha, str):
        raise ValueError("PATH_OR_SHA_REQUIRED")
    path = resolve_episode_artifact(episode_root, declared)
    if not path.is_file() or sha256_file(path).lower() != expected_sha.lower():
        raise ValueError("PATH_OR_SHA_MISMATCH")
    return path


def resolve_contract_context(original_path: Path, state_path: Path | None = None) -> dict:
    original = Path(original_path).resolve()
    episode_root = original.parent.parent
    canonical_state = episode_root / "90_workflow" / "state.json"
    intake_path = episode_root / "00_input" / "source_intake_receipt.json"
    errors: list[dict] = []

    if state_path is not None and Path(state_path).resolve() != canonical_state.resolve():
        return {
            "required": True,
            "errors": [_error("ORIGINAL_ANALYSIS_STATE_PATH_MISMATCH")],
            "segments": {},
        }
    try:
        state = _read_json(canonical_state) if canonical_state.is_file() else {}
        intake = _read_json(intake_path) if intake_path.is_file() else {}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "required": True,
            "errors": [_error("ORIGINAL_ANALYSIS_CONTRACT_READ", detail=str(exc))],
            "segments": {},
        }

    state_version = state.get("original_analysis_contract_version")
    intake_version = intake.get("original_analysis_contract_version")
    versioned = bool(state_version or intake_version or intake.get("schema_version") == INTAKE_V2)
    if not versioned:
        return {"required": False, "errors": [], "segments": {}}
    if state_version != CONTRACT_VERSION or intake_version != CONTRACT_VERSION:
        errors.append(_error(
            "ORIGINAL_ANALYSIS_CONTRACT_VERSION_MISMATCH",
            state_version=state_version,
            intake_version=intake_version,
        ))
    if intake.get("schema_version") != INTAKE_V2:
        errors.append(_error("ORIGINAL_ANALYSIS_INTAKE_V2_REQUIRED"))
    if state.get("episode_id") != intake.get("episode_id"):
        errors.append(_error("ORIGINAL_ANALYSIS_EPISODE_ID_MISMATCH"))

    evidence_declared = state.get("original_source_evidence_path")
    evidence_sha = state.get("original_source_evidence_sha256")
    if not isinstance(evidence_declared, str) or not isinstance(evidence_sha, str):
        errors.append(_error("ORIGINAL_SOURCE_EVIDENCE_REQUIRED"))
        return {"required": True, "errors": errors, "segments": {}}
    try:
        evidence_path = _checked_file(episode_root, evidence_declared, evidence_sha)
        evidence = _read_json(evidence_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(_error("ORIGINAL_SOURCE_EVIDENCE_INVALID", detail=str(exc)))
        return {"required": True, "errors": errors, "segments": {}}

    schema_errors = validate_schema(evidence, _read_json(SCHEMA))
    if schema_errors:
        errors.append(_error("ORIGINAL_SOURCE_EVIDENCE_SCHEMA_INVALID", detail=schema_errors[0]))
        return {"required": True, "errors": errors, "segments": {}}
    if evidence.get("episode_id") != state.get("episode_id"):
        errors.append(_error("ORIGINAL_SOURCE_EVIDENCE_EPISODE_MISMATCH"))

    try:
        identity_path = _checked_file(
            episode_root, evidence["source_identity_path"], evidence["source_identity_sha256"]
        )
        source_path = _checked_file(
            episode_root, evidence["source_media_path"], evidence["source_media_sha256"]
        )
        identity = _read_json(identity_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(_error("ORIGINAL_SOURCE_BINDING_INVALID", detail=str(exc)))
        return {"required": True, "errors": errors, "segments": {}}
    if identity.get("media_sha256", "").lower() != evidence["source_media_sha256"].lower():
        errors.append(_error("ORIGINAL_SOURCE_MEDIA_IDENTITY_MISMATCH"))
    if identity.get("episode_id") != state.get("episode_id"):
        errors.append(_error("ORIGINAL_SOURCE_IDENTITY_EPISODE_MISMATCH"))
    identity_media = (identity_path.parent / str(identity.get("media_path", ""))).resolve()
    try:
        identity_media.relative_to(episode_root.resolve())
    except ValueError:
        errors.append(_error("ORIGINAL_SOURCE_IDENTITY_MEDIA_PATH_INVALID"))
    else:
        if identity_media != source_path:
            errors.append(_error("ORIGINAL_SOURCE_IDENTITY_MEDIA_PATH_MISMATCH"))
    if intake.get("source_identity_sha256", "").lower() != evidence["source_identity_sha256"].lower():
        errors.append(_error("ORIGINAL_SOURCE_INTAKE_IDENTITY_MISMATCH"))
    if intake.get("local_media_sha256", "").lower() != evidence["source_media_sha256"].lower():
        errors.append(_error("ORIGINAL_SOURCE_INTAKE_MEDIA_MISMATCH"))

    segments: dict[str, dict] = {}
    for row in evidence["segments"]:
        segment_id = row["segment_id"]
        if segment_id in segments:
            errors.append(_error("ORIGINAL_SOURCE_EVIDENCE_SEGMENT_DUPLICATE", segment=segment_id))
            continue
        start, end = row["source_range_us"][:2]
        if len(row["source_range_us"]) != 2 or start >= end:
            errors.append(_error("ORIGINAL_SOURCE_EVIDENCE_RANGE_INVALID", segment=segment_id))
        ocr_values = set()
        for frame in row["keyframes"]:
            try:
                _checked_file(episode_root, frame["path"], frame["sha256"])
            except (OSError, ValueError) as exc:
                errors.append(_error(
                    "ORIGINAL_SOURCE_KEYFRAME_INVALID", segment=segment_id, detail=str(exc)
                ))
            if not start <= frame["timestamp_us"] < end:
                errors.append(_error("ORIGINAL_SOURCE_KEYFRAME_TIME_INVALID", segment=segment_id))
            ocr_values.add(frame["literal_ocr"])
        for prefix in ("transcript_evidence", "audio_evidence"):
            try:
                _checked_file(episode_root, row[f"{prefix}_path"], row[f"{prefix}_sha256"])
            except (OSError, ValueError) as exc:
                errors.append(_error(
                    "ORIGINAL_SOURCE_AUDIO_TEXT_EVIDENCE_INVALID",
                    segment=segment_id,
                    evidence=prefix,
                    detail=str(exc),
                ))
        fields = row["classified_fields"]
        situation_ocr = fields["situation_description"].partition("화면 OCR:")[2].strip()
        if ocr_values != {situation_ocr}:
            errors.append(_error("ORIGINAL_SOURCE_OCR_EVIDENCE_MISMATCH", segment=segment_id))
        segments[segment_id] = row
    return {
        "required": True,
        "errors": errors,
        "segments": segments,
        "contract_version": CONTRACT_VERSION,
        "evidence_path": str(evidence_path),
        "source_path": str(source_path),
    }
