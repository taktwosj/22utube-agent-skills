from __future__ import annotations

import argparse
import json
from pathlib import Path

from audio_policy_matrix import TTS_POLICIES
from common import inspect_write_target, meaningful_text_length, read_json, resolved_declared_path, result, sha256_file, write_json
from schema_runtime import validate_schema


SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "design_handoff.schema.json"
SOURCE_SCHEMA = SCHEMA.with_name("source_identity.schema.json")
TIMELINE_SCHEMA = SCHEMA.with_name("approved_timeline.schema.json")
EVIDENCE_SCHEMA = SCHEMA.with_name("design_lock_evidence.schema.json")

LEGAL_ROLES = {
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "T1", "T2", "A9", "A9_TEXT",
    "A10", "A10_TEXT", "STATE", "A11", "A12", "SOURCE_CREDIT",
}

# shrt_white_base_v2/v3 seeds are placeholders with no width or wrap settings, and
# the builder swaps text without touching font size, so CapCut neither shrinks
# nor wraps.  These are the measured per-line budgets before text leaves frame.
# SOURCE_CREDIT is not measured: it is scaled from T2's 12 characters at font
# size 16 down to the credit lane's size 12.0, which is the more conservative of
# the two title ratios.  Measure it against a real render before raising it.
MAX_LINE_LENGTH_BY_ROLE = {
    "T1": 12, "T2": 12, "A10_TEXT": 15, "A9_TEXT": 10, "STATE": 15,
    "SOURCE_CREDIT": 16,
}
MAX_LINE_COUNT_BY_ROLE = {"A9_TEXT": 2, "STATE": 2, "SOURCE_CREDIT": 1}
FULL_SPAN_ROLES = ("T1", "T2", "SCREEN_WHITE", "SCREEN_EFFECT")
# The credit lane is v3-only and optional, so it cannot be required outright:
# a v2 episode declares no SOURCE_CREDIT and track 3 stays empty.  When a plan
# does declare it, it spans the whole timeline exactly like T1/T2.
OPTIONAL_FULL_SPAN_ROLES = ("SOURCE_CREDIT",)


def _overlong_line(text: str, limit: int) -> str | None:
    for line in str(text).splitlines():
        if meaningful_text_length(line) > limit:
            return line
    return None


def validate_role_contract(timeline: dict, expected_duration: int | None = None) -> list[dict]:
    errors: list[dict] = []
    rows = timeline.get("segments", []) if isinstance(timeline, dict) else []
    video_ends = [
        row["start"] + row["duration"]
        for row in rows
        if row.get("role") == "VIDEO"
        and isinstance(row.get("start"), int) and not isinstance(row.get("start"), bool)
        and isinstance(row.get("duration"), int) and not isinstance(row.get("duration"), bool)
        and row["start"] >= 0 and row["duration"] > 0
    ]
    timeline_total = max(video_ends, default=0)
    if expected_duration is not None and timeline_total != expected_duration:
        errors.append({
            "code": "FULL_SPAN_ANCHOR_INVALID", "role": "VIDEO",
            "expected_duration": expected_duration, "observed_duration": timeline_total,
        })
    for role in FULL_SPAN_ROLES:
        matches = [row for row in rows if row.get("role") == role]
        if (
            timeline_total <= 0 or len(matches) != 1
            or matches[0].get("start") != 0
            or matches[0].get("duration") != timeline_total
        ):
            errors.append({
                "code": "FULL_SPAN_ANCHOR_INVALID", "role": role,
                "expected_start": 0, "expected_duration": timeline_total,
                "observed_count": len(matches),
            })
    for role in OPTIONAL_FULL_SPAN_ROLES:
        matches = [row for row in rows if row.get("role") == role]
        if not matches:
            continue
        if (
            timeline_total <= 0 or len(matches) != 1
            or matches[0].get("start") != 0
            or matches[0].get("duration") != timeline_total
        ):
            errors.append({
                "code": "FULL_SPAN_ANCHOR_INVALID", "role": role,
                "expected_start": 0, "expected_duration": timeline_total,
                "observed_count": len(matches),
            })
        elif not isinstance(matches[0].get("text"), str) or not matches[0]["text"].strip():
            errors.append({"code": "TITLE_TEXT_REQUIRED", "role": role})
    for role in ("T1", "T2"):
        matches = [row for row in rows if row.get("role") == role]
        if len(matches) != 1 or not isinstance(matches[0].get("text"), str) or not matches[0]["text"].strip():
            errors.append({"code": "TITLE_TEXT_REQUIRED", "role": role})
        elif matches[0].get("content_type") != "TITLE":
            errors.append({"code": "TITLE_CONTENT_TYPE_INVALID", "role": role})

    primary = timeline.get("primary_speaker_id")
    for row in rows:
        role, content_type = row.get("role"), row.get("content_type")
        segment_id = row.get("segment_id")
        limit = MAX_LINE_LENGTH_BY_ROLE.get(role)
        if limit is not None and isinstance(row.get("text"), str):
            overlong = _overlong_line(row["text"], limit)
            if overlong is not None:
                errors.append({
                    "code": "CAPTION_LINE_TOO_LONG", "segment_id": segment_id, "role": role,
                    "limit": limit, "line": overlong,
                })
        line_limit = MAX_LINE_COUNT_BY_ROLE.get(role)
        if (
            line_limit is not None
            and isinstance(row.get("text"), str)
            and len(row["text"].splitlines()) > line_limit
        ):
            errors.append({
                "code": "CAPTION_TOO_MANY_LINES", "segment_id": segment_id, "role": role,
                "limit": line_limit,
            })
        if role not in LEGAL_ROLES:
            errors.append({"code": "ROLE_ANCHOR_INVALID", "segment_id": segment_id})
        if role == "A12":
            errors.append({"code": "A12_RESERVED_EMPTY", "segment_id": segment_id})
        if content_type == "SPEAKER" and role != "A10_TEXT":
            errors.append({"code": "SPEAKER_ROLE_MISMATCH", "segment_id": segment_id})
        if content_type in {"SITUATION", "STATE"} and role != "STATE":
            errors.append({"code": "STATE_ROLE_MISMATCH", "segment_id": segment_id})
        if role == "A10_TEXT":
            speaker = str(row.get("speaker_id", "")).strip()
            if content_type != "SPEAKER" or row.get("caption_role") != "A10_TEXT":
                errors.append({"code": "SPEAKER_ROLE_MISMATCH", "segment_id": segment_id})
            elif speaker.upper() in {"", "UNKNOWN", "UNASSIGNED"}:
                errors.append({"code": "SPEAKER_ID_UNASSIGNED", "segment_id": segment_id})
            elif not isinstance(primary, str) or not primary.strip():
                errors.append({"code": "PRIMARY_SPEAKER_ID_REQUIRED", "segment_id": segment_id})
            else:
                expected = "WHITE" if speaker == primary else "YELLOW"
                if row.get("color_role") != expected:
                    errors.append({"code": "SPEAKER_COLOR_ROLE_MISMATCH", "segment_id": segment_id})
        if role == "STATE":
            if content_type not in {"SITUATION", "STATE"} or row.get("caption_role") != "STATE":
                errors.append({"code": "STATE_ROLE_MISMATCH", "segment_id": segment_id})
            text = row.get("text")
            if not isinstance(text, str) or not text.strip():
                errors.append({"code": "CAPTION_TEXT_REQUIRED", "segment_id": segment_id})
            elif _overlong_line(text, 15) is not None:
                errors.append({"code": "STATE_TEXT_TOO_LONG", "segment_id": segment_id})
            if row.get("state_effect") != "LASER_CUT":
                errors.append({"code": "STATE_EFFECT_LASER_ONLY", "segment_id": segment_id})

    a9_rows = [row for row in rows if row.get("role") == "A9"]
    a9_text_rows = [row for row in rows if row.get("role") == "A9_TEXT"]
    for role, paired in (("A9", a9_rows), ("A9_TEXT", a9_text_rows)):
        cue_ids = [row.get("cue_id") for row in paired]
        duplicates = {cue_id for cue_id in cue_ids if cue_id is not None and cue_ids.count(cue_id) > 1}
        for cue_id in sorted(duplicates, key=str):
            errors.append({"code": "A9_TEXT_CUE_DUPLICATE", "role": role, "cue_id": cue_id})
    a9 = {row.get("cue_id"): row for row in a9_rows}
    a9_text = {row.get("cue_id"): row for row in a9_text_rows}
    if set(a9) != set(a9_text) or None in a9 or None in a9_text:
        errors.append({"code": "A9_TEXT_PAIRING_MISMATCH"})
    for cue_id in sorted(set(a9) & set(a9_text), key=str):
        sound, text = a9[cue_id], a9_text[cue_id]
        if (
            sound.get("content_type") != "TTS"
            or text.get("content_type") != "TTS"
            or text.get("caption_role") != "A9_TEXT"
            or (sound.get("start"), sound.get("duration")) != (text.get("start"), text.get("duration"))
            or sound.get("text") != text.get("text")
        ):
            errors.append({"code": "A9_TEXT_PAIRING_MISMATCH", "cue_id": cue_id})
    if timeline.get("audio_policy") in TTS_POLICIES and not a9:
        errors.append({"code": "A9_REQUIRED_FOR_TTS_POLICY"})
    return errors


def validate_handoff(
    handoff_path: Path,
    source_identity_path: Path,
    timeline_path: Path,
    evidence_path: Path | None = None,
    allow_relock: bool = False,
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
        # Re-locking after an approved design edit is a normal path; it just has
        # to be asked for, so an accidental overwrite still fails closed.
        guard = inspect_write_target(
            handoff_path.parent, evidence_path, require_new=not allow_relock
        )
        if guard is not None:
            code = "DESIGN_LOCK_EVIDENCE_EXISTS" if guard == "PATH_EXISTS" else "DESIGN_LOCK_EVIDENCE_PATH_UNSAFE"
            detail = "pass --relock to overwrite the existing evidence" if guard == "PATH_EXISTS" else None
            return result([{"code": code, **({"detail": detail} if detail else {})}])
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
    parser.add_argument("--relock", action="store_true", help="overwrite existing design lock evidence")
    args = parser.parse_args()
    payload = validate_handoff(
        args.handoff, args.source_identity, args.timeline, args.evidence, allow_relock=args.relock
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
