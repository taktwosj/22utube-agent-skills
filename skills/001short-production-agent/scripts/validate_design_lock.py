from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import inspect_write_target, read_json, resolved_declared_path, result, sha256_file, write_json
from schema_runtime import validate_schema


SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "design_handoff.schema.json"
SOURCE_SCHEMA = SCHEMA.with_name("source_identity.schema.json")
TIMELINE_SCHEMA = SCHEMA.with_name("approved_timeline.schema.json")
EVIDENCE_SCHEMA = SCHEMA.with_name("design_lock_evidence.schema.json")

LEGAL_ROLES = {
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "T1", "T2", "A9", "A9_TEXT",
    "A10", "A10_TEXT", "STATE", "A11", "A12",
}
UNASSIGNED_SPEAKERS = {"", "UNKNOWN", "UNASSIGNED"}


def validate_role_contract(timeline: dict) -> list[dict]:
    """Fail closed before FINAL_DESIGN_LOCKED when copy roles are ambiguous."""
    errors: list[dict] = []
    rows = timeline.get("segments", []) if isinstance(timeline, dict) else []
    primary_speaker_id = timeline.get("primary_speaker_id")
    title_rows = {role: [row for row in rows if row.get("role") == role] for role in ("T1", "T2")}
    for role, matches in title_rows.items():
        if len(matches) != 1 or not isinstance(matches[0].get("text"), str) or not matches[0]["text"].strip():
            errors.append({"code": "TITLE_TEXT_REQUIRED", "role": role})
    for row in rows:
        role = row.get("role")
        segment_id = row.get("segment_id")
        if role not in LEGAL_ROLES:
            errors.append({"code": "ROLE_ANCHOR_INVALID", "segment_id": segment_id, "role": role})
        text = row.get("text")
        content_type = row.get("content_type")
        if content_type == "SPEAKER" and role != "A10_TEXT":
            errors.append({"code": "SPEAKER_ROLE_MISMATCH", "segment_id": segment_id})
        if content_type in {"SITUATION", "STATE"} and role != "STATE":
            errors.append({"code": "STATE_ROLE_MISMATCH", "segment_id": segment_id})
        if role == "A10_TEXT":
            if content_type != "SPEAKER" or row.get("caption_role") != "A10_TEXT":
                errors.append({"code": "SPEAKER_ROLE_MISMATCH", "segment_id": segment_id})
                continue
            speaker_id = str(row.get("speaker_id", "")).strip()
            if speaker_id.upper() in UNASSIGNED_SPEAKERS:
                errors.append({"code": "SPEAKER_ID_UNASSIGNED", "segment_id": segment_id})
                continue
            if not isinstance(primary_speaker_id, str) or not primary_speaker_id.strip():
                errors.append({"code": "PRIMARY_SPEAKER_ID_REQUIRED", "segment_id": segment_id})
                continue
            expected_color = "WHITE" if speaker_id == primary_speaker_id else "YELLOW"
            if row.get("color_role") != expected_color:
                errors.append({"code": "SPEAKER_COLOR_ROLE_MISMATCH", "segment_id": segment_id, "expected": expected_color})
            if not isinstance(text, str) or not text.strip():
                errors.append({"code": "CAPTION_TEXT_REQUIRED", "segment_id": segment_id})
        if role == "STATE":
            if content_type not in {"SITUATION", "STATE"} or row.get("caption_role") != "STATE":
                errors.append({"code": "STATE_ROLE_MISMATCH", "segment_id": segment_id})
                continue
            if not isinstance(text, str) or not text.strip():
                errors.append({"code": "CAPTION_TEXT_REQUIRED", "segment_id": segment_id})
            elif len("".join(text.split())) > 8:
                errors.append({"code": "STATE_TEXT_TOO_LONG", "segment_id": segment_id})
            if row.get("state_effect") not in {"FLICKER_RAVE", "GLITCH_SHAKE", "LASER_CUT"}:
                errors.append({"code": "STATE_EFFECT_REQUIRED", "segment_id": segment_id})
    return errors


def validate_handoff(
    handoff_path: Path,
    source_identity_path: Path,
    timeline_path: Path,
    evidence_path: Path | None = None,
) -> dict:
    handoff_path = Path(handoff_path).resolve()
    source_identity_path = Path(source_identity_path).resolve()
    timeline_path = Path(timeline_path).resolve()
    errors: list[dict] = []
    try:
        handoff = read_json(handoff_path)
        source = read_json(source_identity_path)
        timeline = read_json(timeline_path)
        schema = read_json(SCHEMA)
        source_schema = read_json(SOURCE_SCHEMA)
        timeline_schema = read_json(TIMELINE_SCHEMA)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "DESIGN_LOCK_SCHEMA", "detail": str(exc)}])

    schema_errors = validate_schema(handoff, schema)
    source_schema_errors = validate_schema(source, source_schema)
    timeline_schema_errors = validate_schema(timeline, timeline_schema)
    if schema_errors:
        errors.append({"code": "DESIGN_LOCK_SCHEMA", "detail": schema_errors})
        return result(errors)
    if source_schema_errors:
        errors.append({"code": "DESIGN_LOCK_SOURCE_SCHEMA", "detail": source_schema_errors})
    if timeline_schema_errors:
        errors.append({"code": "DESIGN_LOCK_TIMELINE_SCHEMA", "detail": timeline_schema_errors})
    if errors:
        return result(errors)

    errors.extend(validate_role_contract(timeline))
    if errors:
        return result(errors)

    if resolved_declared_path(handoff_path, handoff["source_identity_path"]) != source_identity_path:
        errors.append({"code": "SOURCE_IDENTITY_PATH_MISMATCH"})
    actual_source_sha = sha256_file(source_identity_path)
    if actual_source_sha.lower() != handoff["source_identity_sha256"].lower():
        errors.append({"code": "SOURCE_IDENTITY_SHA_MISMATCH"})
    if resolved_declared_path(handoff_path, handoff["timeline_path"]) != timeline_path:
        errors.append({"code": "TIMELINE_PATH_MISMATCH"})
    actual_timeline_sha = sha256_file(timeline_path)
    if actual_timeline_sha.lower() != handoff["timeline_sha256"].lower():
        errors.append({"code": "TIMELINE_SHA_MISMATCH"})

    identity_values = {
        handoff["episode_id"],
        source.get("episode_id"),
        timeline.get("episode_id"),
    }
    fingerprints = {
        handoff["source_fingerprint"],
        source.get("source_fingerprint"),
        timeline.get("source_fingerprint"),
    }
    if len(identity_values) != 1 or len(fingerprints) != 1:
        errors.append({"code": "SOURCE_IDENTITY_MISMATCH"})

    source_media_path = resolved_declared_path(source_identity_path, source["media_path"])
    if not source_media_path.is_file():
        errors.append({"code": "SOURCE_MEDIA_MISSING"})
        actual_media_sha = None
    else:
        actual_media_sha = sha256_file(source_media_path)
        if actual_media_sha.lower() != source["media_sha256"].lower():
            errors.append({"code": "SOURCE_MEDIA_SHA_MISMATCH"})
    if any(row.get("source_ref") != source.get("source_id") for row in timeline["segments"]):
        errors.append({"code": "TIMELINE_SOURCE_REF_MISMATCH"})

    ordered = sorted(
        (row for row in timeline["segments"] if isinstance(row, dict)),
        key=lambda row: row.get("timeline_order", float("inf")),
    )
    observed_order = [row.get("segment_id") for row in ordered]
    if observed_order != handoff["approved_timeline_order"]:
        errors.append({"code": "TIMELINE_ORDER_MISMATCH"})
    for row in ordered:
        start = row.get("start")
        duration = row.get("duration")
        if not isinstance(start, int) or isinstance(start, bool) or start < 0:
            errors.append({"code": "DESIGN_LOCK_TIMELINE_RANGE_INVALID", "segment_id": row.get("segment_id"), "field": "start"})
        if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            errors.append({"code": "DESIGN_LOCK_TIMELINE_RANGE_INVALID", "segment_id": row.get("segment_id"), "field": "duration"})

    evidence = {
        "schema_version": "001short-design-lock-evidence-v1",
        "status": "PASS",
        "episode_id": handoff["episode_id"],
        "handoff_path": str(handoff_path),
        "handoff_sha256": sha256_file(handoff_path),
        "source_identity_path": str(source_identity_path),
        "source_identity_sha256": actual_source_sha,
        "source_media_path": str(source_media_path),
        "source_media_sha256": actual_media_sha or "",
        "timeline_path": str(timeline_path),
        "timeline_sha256": actual_timeline_sha,
        "source_fingerprint": handoff["source_fingerprint"],
    }
    if errors:
        return result(errors)
    evidence_schema_errors = validate_schema(evidence, read_json(EVIDENCE_SCHEMA))
    if evidence_schema_errors:
        return result([{"code": "DESIGN_LOCK_EVIDENCE_SCHEMA", "detail": evidence_schema_errors}])
    if evidence_path is not None:
        evidence_path = Path(evidence_path).absolute()
        guard = inspect_write_target(handoff_path.parent, evidence_path, require_new=True)
        if guard is not None:
            code = "DESIGN_LOCK_EVIDENCE_EXISTS" if guard == "PATH_EXISTS" else "DESIGN_LOCK_EVIDENCE_PATH_UNSAFE"
            return result([{"code": code}])
        write_json(evidence_path, evidence)
        evidence["design_lock_evidence_path"] = str(evidence_path)
        evidence["design_lock_evidence_sha256"] = sha256_file(evidence_path)
    return result([], evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--source-identity", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_handoff(args.handoff, args.source_identity, args.timeline, args.evidence)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
