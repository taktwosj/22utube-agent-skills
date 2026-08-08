from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterator

from capcut_model import (
    ProjectError,
    capture_structure,
    capture_structure_from_content,
    is_full_content_timeline_mirror,
    iter_materials,
    load_project,
    validate_materials,
    validate_structure,
)
from capcut_io import iter_primary_draft_documents, iter_timeline_json
from clone_and_sync import hash_project_core, template_fingerprint_sha256, validate_id_mirrors
from common import inspect_write_target, manifest_sha256, read_json, result, sha256_file, write_json
from schema_runtime import validate_schema
from validate_design_lock import validate_handoff
from validate_audio_caption import validate_audio_caption
from validate_build_inputs import validate_build_inputs
from track_contract import A10_TEXT_TRACK_BY_COLOR, A12_INDEX, LOGICAL_ROLE_BY_TRACK, STATE_TRACK_BY_EFFECT, TRACK_INDEX, TRACK_LAYOUT


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCHEMA = SKILL_ROOT / "schemas" / "build_contract.schema.json"
SNAPSHOT_SCHEMA = SKILL_ROOT / "schemas" / "structure_snapshot.schema.json"
EVIDENCE_SCHEMA = SKILL_ROOT / "schemas" / "capcut_project_evidence.schema.json"
DESIGN_LOCK_EVIDENCE_SCHEMA = SKILL_ROOT / "schemas" / "design_lock_evidence.schema.json"


def _error(code: str, **detail: Any) -> dict:
    return {"code": code, **detail}


def _segments(model) -> list[dict]:
    rows: list[dict] = []
    for track_index, track in enumerate(model.tracks):
        track_id = track.get("id")
        for segment in track.get("segments", []):
            if isinstance(segment, dict):
                row = dict(segment)
                row["_actual_track_id"] = track_id
                row["_actual_track_index"] = track_index
                rows.append(row)
    return rows


def validate_v2_role_routing(model, contract: dict) -> list[dict]:
    if contract.get("track_layout_version") != TRACK_LAYOUT:
        return [_error("V2_TRACK_LAYOUT_REQUIRED")]
    if len(model.tracks) != len(LOGICAL_ROLE_BY_TRACK):
        return [_error("V2_TRACK_LAYOUT_MISMATCH", observed=len(model.tracks))]
    errors: list[dict] = []
    materials = {
        row.get("id"): row for row in iter_materials(model.materials)
        if isinstance(row.get("id"), str)
    }
    if any(row.get("role") in {"A12", "A12_RESERVED_EMPTY"} for row in materials.values()):
        errors.append(_error("A12_MATERIAL_FORBIDDEN"))
    video_ends = [
        row.get("end")
        for row in contract.get("timeline", [])
        if row.get("role") == "VIDEO" and isinstance(row.get("end"), int)
    ]
    timeline_total = max(video_ends, default=0)
    for role in ("T1", "T2", "SCREEN_WHITE", "SCREEN_EFFECT"):
        index = TRACK_INDEX[role]
        segments = model.tracks[index].get("segments", [])
        timerange = _range(segments[0]) if len(segments) == 1 else None
        if timeline_total <= 0 or timerange is None or timerange[:2] != (0, timeline_total):
            errors.append(_error("FULL_SPAN_ANCHOR_MISMATCH", role=role))
    for segment in _segments(model):
        index = segment["_actual_track_index"]
        expected = LOGICAL_ROLE_BY_TRACK[index]
        if index == A12_INDEX or segment.get("role") != expected:
            errors.append(_error(
                "V2_ROLE_TRACK_MISMATCH", segment_id=segment.get("id"),
                role=segment.get("role"), track_index=index,
            ))
    role_text = contract.get("approved_role_text", {})
    for role in ("T1", "T2"):
        index = TRACK_INDEX[role]
        segments = model.tracks[index].get("segments", [])
        material = materials.get(segments[0].get("material_id")) if len(segments) == 1 else None
        text, valid = _rich_text(material) if isinstance(material, dict) else (None, False)
        if not valid or text != role_text.get(role):
            errors.append(_error("TITLE_TEXT_AUTHORITY_MISMATCH", role=role))
    declared = contract.get("approved_segment_text", {})
    actual_captions = {
        row.get("id"): row for row in _segments(model)
        if row.get("role") in {"A9_TEXT", "A10_TEXT", "STATE"}
    }
    if set(actual_captions) != set(declared):
        errors.append(_error("CAPTION_SEGMENT_AUTHORITY_MISMATCH", detail="segment_set"))
    for segment_id in sorted(set(actual_captions) & set(declared)):
        segment, expected = actual_captions[segment_id], declared[segment_id]
        material = materials.get(segment.get("material_id"))
        text, valid = _rich_text(material) if isinstance(material, dict) else (None, False)
        timerange = _range(segment)
        if (
            not valid or text != expected.get("text")
            or segment.get("role") != expected.get("role")
            or timerange is None
            or (timerange[0], timerange[1]) != (expected.get("start"), expected.get("duration"))
            or (
                expected.get("role") == "A10_TEXT"
                and segment.get("_actual_track_index")
                != A10_TEXT_TRACK_BY_COLOR.get(expected.get("color_role"))
            )
            or (
                expected.get("role") == "STATE"
                and segment.get("_actual_track_index")
                != STATE_TRACK_BY_EFFECT.get(expected.get("state_effect"))
            )
        ):
            errors.append(_error("CAPTION_SEGMENT_AUTHORITY_MISMATCH", segment_id=segment_id))
    return errors


def _range(segment: dict) -> tuple[int, int, int] | None:
    timerange = segment.get("target_timerange")
    if not isinstance(timerange, dict):
        return None
    start = timerange.get("start")
    duration = timerange.get("duration")
    if not isinstance(start, int) or isinstance(start, bool) or not isinstance(duration, int) or isinstance(duration, bool):
        return None
    if start < 0 or duration <= 0:
        return None
    return start, duration, start + duration


def validate_timeline(model, contract: dict) -> list[dict]:
    errors: list[dict] = []
    segments = _segments(model)
    actual_by_id = {row.get("id"): row for row in segments if isinstance(row.get("id"), str)}
    expected_rows = contract.get("timeline", [])
    expected_by_id = {row.get("segment_id"): row for row in expected_rows if isinstance(row, dict)}
    for row in expected_rows:
        if row.get("end") != row.get("start") + row.get("duration", 0):
            errors.append(_error("TIMELINE_RANGE_INVALID", segment_id=row.get("segment_id")))
    observed_order = [
        row.get("id")
        for row in sorted(
            (row for row in segments if _range(row) is not None),
            key=lambda row: (_range(row)[0], str(row.get("id"))),
        )
    ]
    if observed_order != contract.get("approved_actual_order"):
        errors.append(_error("ACTUAL_TIME_ORDER_MISMATCH", observed=observed_order))
    if set(actual_by_id) != set(expected_by_id):
        errors.append(_error("TIMELINE_SEGMENT_SET_MISMATCH"))
    for segment_id in sorted(set(actual_by_id) & set(expected_by_id)):
        actual = actual_by_id[segment_id]
        expected = expected_by_id[segment_id]
        actual_range = _range(actual)
        if actual_range is None:
            errors.append(_error("TIMELINE_RANGE_INVALID", segment_id=segment_id))
            continue
        start, duration, end = actual_range
        if (
            actual.get("role") != expected.get("role")
            or start != expected.get("start")
            or duration != expected.get("duration")
            or end != expected.get("end")
        ):
            errors.append(_error("TIMELINE_RANGE_MISMATCH", segment_id=segment_id))

    primary_roles = set(contract.get("primary_timeline_roles", []))
    primary = sorted(
        (row for row in segments if row.get("role") in primary_roles and _range(row) is not None),
        key=lambda row: (_range(row)[0], str(row.get("id"))),
    )
    allowed_gaps = {tuple(row) for row in contract.get("authorized_gaps", []) if isinstance(row, list) and len(row) == 2}
    allowed_overlaps = {tuple(row) for row in contract.get("authorized_overlaps", []) if isinstance(row, list) and len(row) == 2}
    for previous, current in zip(primary, primary[1:]):
        previous_end = _range(previous)[2]
        current_start = _range(current)[0]
        pair = (previous.get("id"), current.get("id"))
        if current_start > previous_end and pair not in allowed_gaps:
            errors.append(_error("UNAUTHORIZED_GAP", pair=list(pair)))
        if current_start < previous_end and pair not in allowed_overlaps:
            errors.append(_error("UNAUTHORIZED_OVERLAP", pair=list(pair)))

    source_ranges: dict[tuple[str, int, int], list[str]] = {}
    for row in segments:
        source_range = row.get("source_timerange")
        if not isinstance(source_range, dict):
            continue
        key = (
            str(row.get("material_id")),
            source_range.get("start"),
            source_range.get("duration"),
        )
        source_ranges.setdefault(key, []).append(str(row.get("id")))
    for key, ids in source_ranges.items():
        if len(ids) > 1:
            errors.append(_error("DUPLICATE_SOURCE_RANGE", source_range=list(key[1:]), segments=ids))

    expected_roles_by_id = {
        row.get("segment_id"): row.get("role")
        for row in expected_rows
        if isinstance(row, dict)
    }
    for pair in contract.get("parallel_pairs", []):
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        left_id, right_id = pair
        left = actual_by_id.get(left_id)
        right = actual_by_id.get(right_id)
        left_role = expected_roles_by_id.get(left_id)
        right_role = expected_roles_by_id.get(right_id)
        if (
            left is None
            or right is None
            or left.get("role") != left_role
            or right.get("role") != right_role
            or _range(left) != _range(right)
        ):
            errors.append(_error("PARALLEL_PAIR_MISMATCH", pair=pair))
    return errors


FORBIDDEN_VISIBLE = re.compile(
    r"(?i)(?:\b(?:work_id|slot_id|source_id|todo|placeholder)\b|"
    r"(?:[a-z]:[\\/]|/users/|/" r"home/)|\.(?:mp4|mov|wav|mp3|json)\b|"
    r"\[\d{2}:\d{2}(?:[.:]\d+)?\]|\b(?:seg|mat|track|timeline|draft|project)-[\w-]+)"
)


def _rich_text(material: dict) -> tuple[str | None, bool]:
    content = material.get("content")
    if not isinstance(content, str) or not content.strip():
        value = material.get("text")
        return (value.strip(), False) if isinstance(value, str) and value.strip() else (None, False)
    try:
        rich = json.loads(content)
    except json.JSONDecodeError:
        return content.strip(), False
    text = rich.get("text")
    styles = rich.get("styles")
    valid = (
        isinstance(text, str)
        and isinstance(styles, list)
        and bool(styles)
        and all(
            isinstance(style, dict) and style.get("range") == [0, len(text)]
            for style in styles
        )
    )
    return (text.strip() if isinstance(text, str) and text.strip() else None, valid)


def _visible_text(model) -> Iterator[tuple[str, str, bool]]:
    for material in iter_materials(model.materials):
        if material.get("type") == "text":
            text, rich_valid = _rich_text(material)
            if text:
                yield f"material:{material.get('id')}:content", text, rich_valid
    for segment in _segments(model):
        for field in ("content", "text"):
            value = segment.get(field)
            if isinstance(value, str) and value.strip():
                yield f"segment:{segment.get('id')}:{field}", value.strip(), True


def validate_visible_text(model, contract: dict) -> list[dict]:
    approved = set(contract.get("approved_text", []))
    errors: list[dict] = []
    for location, text, rich_valid in _visible_text(model):
        if location.startswith("material:") and not rich_valid:
            errors.append(_error("CAPCUT_RICH_TEXT_INVALID", location=location))
        elif FORBIDDEN_VISIBLE.search(text):
            errors.append(_error("FORBIDDEN_VISIBLE_TEXT", location=location))
        elif text not in approved:
            errors.append(_error("UNAPPROVED_VISIBLE_TEXT", location=location))
    return errors


def validate_subtitle_binding(model, contract: dict) -> list[dict]:
    """Bind declared CapCut caption roles/segments to final locked SRT cues."""
    caption_lock_path = Path(contract["caption_lock_path"]).resolve()
    try:
        caption = read_json(caption_lock_path)
    except (OSError, ValueError, TypeError):
        return [_error("AUDIO_CAPTION_PREREQUISITE_INVALID")]
    cues = caption.get("cues", []) if isinstance(caption.get("cues"), list) else []
    locked_texts = {
        cue.get("text")
        for cue in cues
        if isinstance(cue, dict) and isinstance(cue.get("text"), str)
    }
    locked_timings = {
        (cue.get("start_us"), cue.get("end_us"))
        for cue in cues
        if isinstance(cue, dict)
        and isinstance(cue.get("start_us"), int)
        and isinstance(cue.get("end_us"), int)
    }
    materials = {
        row.get("id"): row
        for row in iter_materials(model.materials)
        if isinstance(row.get("id"), str)
    }
    segments = {
        row.get("id"): row
        for row in _segments(model)
        if isinstance(row.get("id"), str)
    }
    cues_by_id = {
        str(cue.get("cue_id")): cue
        for cue in cues
        if isinstance(cue, dict) and cue.get("cue_id") is not None
    }
    declared_bindings = contract.get("caption_bindings")
    binding_by_segment: dict[str, dict] = {}
    if declared_bindings is not None:
        if not isinstance(declared_bindings, list):
            return [_error("SUBTITLE_BINDING_INVALID")]
        used_cue_ids: set[str] = set()
        for binding in declared_bindings:
            if (
                not isinstance(binding, dict)
                or not isinstance(binding.get("segment_id"), str)
                or binding.get("cue_id") is None
                or binding.get("role") not in {"STATE", "A10_TEXT", "A9_TEXT"}
                or str(binding.get("cue_id")) in used_cue_ids
                or binding["segment_id"] in binding_by_segment
            ):
                return [_error("SUBTITLE_BINDING_INVALID")]
            used_cue_ids.add(str(binding["cue_id"]))
            binding_by_segment[binding["segment_id"]] = binding
    declared_roles = contract.get("subtitle_roles")
    if declared_roles is None:
        subtitle_roles = set()
    elif not isinstance(declared_roles, list) or not all(
        isinstance(role, str) and role for role in declared_roles
    ):
        return [_error("SUBTITLE_BINDING_INVALID")]
    else:
        subtitle_roles = set(declared_roles)

    errors: list[dict] = []
    for segment_id in binding_by_segment:
        if segment_id not in segments:
            errors.append(_error("SUBTITLE_BINDING_SEGMENT_MISSING", segment_id=segment_id))
    for segment in segments.values():
        role = segment.get("role")
        binding = binding_by_segment.get(segment.get("id"))
        if binding is None and role not in subtitle_roles:
            continue
        if binding is None:
            errors.append(_error("SUBTITLE_BINDING_CUE_MISSING", segment_id=segment.get("id")))
            continue
        material = materials.get(segment.get("material_id"))
        if not isinstance(material, dict):
            errors.append(_error("SUBTITLE_BINDING_MATERIAL_MISSING", segment_id=segment.get("id")))
            continue
        text, rich_valid = _rich_text(material)
        target_range = _range(segment)
        cue = cues_by_id.get(str(binding["cue_id"]))
        if cue is None:
            errors.append(_error("SUBTITLE_BINDING_CUE_MISSING", segment_id=segment.get("id")))
            continue
        if binding.get("role") != role or cue.get("layer") != role:
            errors.append(_error(
                "SUBTITLE_BINDING_LAYER_MISMATCH", segment_id=segment.get("id"),
                segment_role=role, cue_layer=cue.get("layer"),
            ))
        expected_text = cue.get("text")
        expected_timing = (cue.get("start_us"), cue.get("end_us"))
        if (
            not rich_valid
            or not isinstance(text, str)
            or not text.strip()
            or (expected_text is not None and text.strip() != expected_text)
            or (expected_text is None and text.strip() not in locked_texts)
        ):
            errors.append(
                _error("SUBTITLE_TEXT_NOT_IN_LOCKED_SRT", segment_id=segment.get("id"))
            )
        observed_timing = (target_range[0], target_range[2]) if target_range is not None else None
        if (
            observed_timing is None
            or (expected_timing is not None and observed_timing != expected_timing)
            or (expected_timing is None and observed_timing not in locked_timings)
        ):
            errors.append(
                _error("SUBTITLE_TIMING_DRIFT", segment_id=segment.get("id"))
            )
    return errors


def _probe_duration_us(path: Path) -> int | None:
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
        duration = float(payload["format"]["duration"])
        return round(duration * 1_000_000) if duration > 0 else None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _probe(path: Path) -> bool:
    return _probe_duration_us(path) is not None


def _probe_stream_types(path: Path) -> set[str]:
    """Return the set of codec_type values (e.g. ``audio``, ``video``) decoded
    from the real media file. Any decode failure or ffprobe absence returns an
    empty set, which downstream callers treat as a fail-closed mismatch."""
    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "stream=codec_type", "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if completed.returncode != 0:
        return set()
    try:
        payload = json.loads(completed.stdout)
    except (ValueError, json.JSONDecodeError):
        return set()
    streams = payload.get("streams")
    if not isinstance(streams, list):
        return set()
    return {
        stream.get("codec_type")
        for stream in streams
        if isinstance(stream, dict) and isinstance(stream.get("codec_type"), str)
    }


def _resolve_required_asset(project: Path, raw_path: str) -> Path | None:
    normalized = raw_path.replace("\\", "/")
    match = re.match(r"^##_draftpath_placeholder_[^#]+_##/(Resources/.+)$", normalized)
    if match:
        candidate = project / Path(match.group(1))
    else:
        candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = project / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(project)
    except ValueError:
        return None
    return candidate


def _referenced_media_paths(model, project: Path) -> set[str]:
    referenced: set[str] = set()
    referenced_ids = {
        segment.get("material_id")
        for segment in _segments(model)
        if isinstance(segment.get("material_id"), str)
    }
    for material in iter_materials(model.materials):
        if material.get("id") not in referenced_ids:
            continue
        if material.get("type") not in {"video", "audio", "music", "extract_music"}:
            continue
        raw_path = material.get("path") or material.get("media_path")
        if not isinstance(raw_path, str) or not raw_path:
            continue
        candidate = _resolve_required_asset(project, raw_path)
        if candidate is not None:
            referenced.add(candidate.relative_to(project).as_posix())
    return referenced


def validate_segment_material_types_and_durations(
    model, project: Path, contract: dict | None = None
) -> list[dict]:
    materials = {
        row.get("id"): row
        for row in iter_materials(model.materials)
        if isinstance(row.get("id"), str)
    }
    expected_rows = {
        row.get("segment_id"): row
        for row in (contract or {}).get("timeline", [])
        if isinstance(row, dict) and isinstance(row.get("segment_id"), str)
    }
    errors: list[dict] = []
    for segment in _segments(model):
        role = segment.get("role")
        expected_row = expected_rows.get(segment.get("id"), {})
        expected_type = expected_row.get("material_type")
        if not isinstance(expected_type, str) or not expected_type:
            errors.append(
                _error(
                    "MATERIAL_TYPE_DECLARATION_MISSING",
                    segment_id=segment.get("id"),
                    role=role,
                )
            )
            continue
        material = materials.get(segment.get("material_id"))
        if (
            material is None
            or material.get("type") != expected_type
            or material.get("role") != role
        ):
            errors.append(
                _error(
                    "MATERIAL_TYPE_ROLE_MISMATCH",
                    segment_id=segment.get("id"),
                    role=role,
                )
            )
            continue
        stream_type = "audio" if expected_type in {"audio", "music", "extract_music"} else expected_type
        if stream_type not in {"audio", "video"}:
            continue
        raw_path = material.get("path") or material.get("media_path")
        if not isinstance(raw_path, str):
            continue
        media_path = _resolve_required_asset(project, raw_path)
        if media_path is None or not media_path.is_file():
            continue
        stream_types = _probe_stream_types(media_path)
        if stream_type not in stream_types:
            errors.append(
                _error(
                    "MEDIA_STREAM_TYPE_MISMATCH",
                    segment_id=segment.get("id"),
                    role=role,
                    expected_stream=stream_type,
                )
            )
            continue
        actual_duration = _probe_duration_us(media_path)
        target_range = _range(segment)
        if actual_duration is None or target_range is None:
            continue
        exact_duration = expected_row.get("duration_mode") == "exact"
        if not exact_duration:
            source_range = segment.get("source_timerange")
            if isinstance(source_range, dict):
                source_start = source_range.get("start")
                source_duration = source_range.get("duration")
                if (
                    isinstance(source_start, int)
                    and isinstance(source_duration, int)
                    and source_start + source_duration > actual_duration + 50_000
                ):
                    errors.append(
                        _error(
                            "SOURCE_RANGE_EXCEEDS_MEDIA",
                            segment_id=segment.get("id"),
                            source_end_us=source_start + source_duration,
                            media_duration_us=actual_duration,
                        )
                    )
                    continue
        if exact_duration:
            mismatch = abs(actual_duration - target_range[1]) > 50_000
        else:
            source_range = segment.get("source_timerange")
            required_duration = (
                source_range.get("duration")
                if isinstance(source_range, dict)
                and isinstance(source_range.get("duration"), int)
                else target_range[1]
            )
            mismatch = actual_duration + 50_000 < required_duration
        if mismatch:
            errors.append(
                _error(
                    "MEDIA_DURATION_MISMATCH",
                    segment_id=segment.get("id"),
                    actual_duration_us=actual_duration,
                )
            )
    return errors


def validate_design_lock_authority(contract: dict) -> tuple[list[dict], dict | None]:
    design_lock_path = Path(contract["design_lock_evidence_path"]).resolve()
    try:
        evidence = read_json(design_lock_path)
        if validate_schema(evidence, read_json(DESIGN_LOCK_EVIDENCE_SCHEMA)):
            return [_error("DESIGN_LOCK_EVIDENCE_INVALID")], None
        handoff_path = Path(evidence["handoff_path"]).resolve()
        source_identity_path = Path(evidence["source_identity_path"]).resolve()
        timeline_path = Path(evidence["timeline_path"]).resolve()
        verified = validate_handoff(handoff_path, source_identity_path, timeline_path)
    except (OSError, ValueError, TypeError, KeyError):
        return [_error("DESIGN_LOCK_EVIDENCE_INVALID")], None
    if verified.get("status") != "PASS":
        return [_error("DESIGN_LOCK_EVIDENCE_INVALID")], None
    verified_evidence = verified.get("evidence", {})
    for field in (
        "handoff_path",
        "handoff_sha256",
        "source_identity_path",
        "source_identity_sha256",
        "source_media_path",
        "source_media_sha256",
        "timeline_path",
        "timeline_sha256",
        "source_fingerprint",
    ):
        if str(verified_evidence.get(field)) != str(evidence.get(field)):
            return [_error("DESIGN_LOCK_EVIDENCE_INVALID", field=field)], None
    if evidence.get("episode_id") != contract.get("episode_id"):
        return [_error("DESIGN_LOCK_EVIDENCE_INVALID", field="episode_id")], None
    approved_timeline = read_json(timeline_path)
    approved_rows = sorted(
        approved_timeline.get("segments", []), key=lambda row: (row.get("start", 0), row.get("segment_id", ""))
    )
    contract_rows = contract.get("timeline", [])
    if (
        [row.get("segment_id") for row in approved_rows]
        != contract.get("approved_actual_order")
        or len(approved_rows) != len(contract_rows)
        or any(
            any(approved.get(field) != planned.get(field) for field in ("segment_id", "role", "start", "duration"))
            for approved, planned in zip(approved_rows, sorted(contract_rows, key=lambda row: (row.get("start", 0), row.get("segment_id", ""))))
        )
    ):
        return [_error("DESIGN_LOCK_TIMELINE_AUTHORITY_MISMATCH")], approved_timeline
    return [], approved_timeline


def validate_build_inputs_authority(
    contract: dict, build_contract_path: Path
) -> list[dict]:
    audio_lock_path = Path(contract["audio_lock_path"]).resolve()
    caption_lock_path = Path(contract["caption_lock_path"]).resolve()
    srt_path = Path(contract["final_srt_path"]).resolve()
    timeline_path = Path(contract["approved_timeline_path"]).resolve()
    receipt_path = Path(contract["build_inputs_receipt_path"]).resolve()
    linked_files = (
        (audio_lock_path, "audio_lock_sha256"),
        (caption_lock_path, "caption_lock_sha256"),
        (srt_path, "final_srt_sha256"),
        (timeline_path, "approved_timeline_sha256"),
    )
    if any(
        not path.is_file() or sha256_file(path) != contract[sha_field]
        for path, sha_field in linked_files
    ):
        return [_error("AUDIO_CAPTION_PREREQUISITE_INVALID")]
    audio_caption_result = validate_audio_caption(audio_lock_path, caption_lock_path)
    if audio_caption_result.get("status") != "PASS":
        return [
            _error(
                "AUDIO_CAPTION_PREREQUISITE_INVALID",
                prerequisite_errors=audio_caption_result.get("errors", []),
            )
        ]
    if (
        not receipt_path.is_file()
        or sha256_file(receipt_path) != contract["build_inputs_receipt_sha256"]
    ):
        return [_error("BUILD_INPUTS_RECEIPT_MISMATCH")]
    fresh_build_inputs = validate_build_inputs(
        caption_lock_path, srt_path, build_contract_path, timeline_path
    )
    if fresh_build_inputs.get("status") != "PASS":
        return [
            _error(
                "BUILD_INPUTS_PREREQUISITE_INVALID",
                prerequisite_errors=fresh_build_inputs.get("errors", []),
            )
        ]
    try:
        receipt = read_json(receipt_path)
    except (OSError, ValueError, TypeError):
        return [_error("BUILD_INPUTS_RECEIPT_MISMATCH")]
    if not isinstance(receipt, dict):
        return [_error("BUILD_INPUTS_RECEIPT_MISMATCH")]
    if (
        receipt.get("status") != "PASS"
        or receipt.get("errors") != []
        or receipt.get("evidence") != fresh_build_inputs.get("evidence")
    ):
        return [_error("BUILD_INPUTS_RECEIPT_MISMATCH")]
    return []


def validate_capcut_project(
    project_path: Path,
    structure_snapshot_path: Path,
    build_contract_path: Path,
    evidence_path: Path | None = None,
    approved_evidence_root_path: Path | None = None,
) -> dict:
    project_path = Path(project_path).resolve()
    structure_snapshot_path = Path(structure_snapshot_path).resolve()
    build_contract_path = Path(build_contract_path).resolve()
    if not project_path.is_dir():
        return {**result([_error("PROJECT_PATH_MISSING")]), "next_action": "NONE"}
    if not structure_snapshot_path.is_file():
        return {**result([_error("STRUCTURE_SNAPSHOT_MISSING")]), "next_action": "NONE"}
    if not build_contract_path.is_file():
        return {**result([_error("BUILD_CONTRACT_MISSING")]), "next_action": "NONE"}
    try:
        contract = read_json(build_contract_path)
        snapshot = read_json(structure_snapshot_path)
        build_schema = read_json(BUILD_SCHEMA)
        snapshot_schema = read_json(SNAPSHOT_SCHEMA)
    except (OSError, ValueError, TypeError) as exc:
        return {**result([_error("BUILD_CONTRACT_SCHEMA", detail=str(exc))]), "next_action": "NONE"}
    contract_schema_errors = validate_schema(contract, build_schema)
    if isinstance(contract.get("root_contract_path"), str) and Path(contract["root_contract_path"]).is_absolute():
        contract_schema_errors.append("$.root_contract_path: workspace-relative path required")
    if contract_schema_errors or not contract.get("source_core_sha256"):
        return {
            **result([_error("BUILD_CONTRACT_SCHEMA", detail=contract_schema_errors)]),
            "next_action": "NONE",
        }
    visual_tuple = (
        contract.get("visual_asset_mode"), contract.get("video_asset_key"),
        contract.get("upload_ready"),
    )
    if visual_tuple not in {
        ("SOURCE_VIDEO_PROVISIONAL", "source_video", False),
        ("CLEAN_VISUAL_READY", "clean_video", True),
    }:
        return {
            **result([_error("BUILD_CONTRACT_VISUAL_MODE_MISMATCH")]),
            "next_action": "NONE",
        }
    snapshot_schema_errors = validate_schema(snapshot, snapshot_schema)
    if snapshot_schema_errors:
        return {
            **result([_error("STRUCTURE_SNAPSHOT_SCHEMA", detail=snapshot_schema_errors)]),
            "next_action": "NONE",
        }
    if sha256_file(structure_snapshot_path).lower() != contract["structure_snapshot_sha256"].lower():
        return {**result([_error("STRUCTURE_SNAPSHOT_SHA_MISMATCH")]), "next_action": "NONE"}

    prerequisite_errors = validate_build_inputs_authority(contract, build_contract_path)
    if prerequisite_errors:
        return {**result(prerequisite_errors), "next_action": "NONE"}

    source_path = Path(contract["source_project_path"]).resolve()
    declared_working = Path(contract["working_project_path"]).resolve()
    if evidence_path is not None:
        if approved_evidence_root_path is None:
            return {**result([_error("EVIDENCE_ROOT_REQUIRED")]), "next_action": "NONE"}
        approved_evidence_root = Path(approved_evidence_root_path).absolute()
        declared_evidence_root = Path(contract["evidence_root_path"]).absolute()
        if declared_evidence_root.resolve(strict=False) != approved_evidence_root.resolve(strict=False):
            return {**result([_error("EVIDENCE_ROOT_MISMATCH")]), "next_action": "NONE"}
        unresolved_evidence = Path(evidence_path).absolute()
        resolved_evidence = unresolved_evidence.resolve(strict=False)
        try:
            resolved_evidence.relative_to(source_path)
            return {**result([_error("SOURCE_WRITE_FORBIDDEN")]), "next_action": "NONE"}
        except ValueError:
            pass
        try:
            resolved_evidence.relative_to(project_path)
            return {**result([_error("EVIDENCE_WRITE_CONFLICT")]), "next_action": "NONE"}
        except ValueError:
            pass
        evidence_guard = inspect_write_target(
            approved_evidence_root, unresolved_evidence, require_new=True
        )
        if evidence_guard == "PATH_EXISTS":
            return {**result([_error("EVIDENCE_PATH_EXISTS")]), "next_action": "NONE"}
        if evidence_guard is not None:
            return {**result([_error("EVIDENCE_PATH_UNSAFE")]), "next_action": "NONE"}
    try:
        project_path.relative_to(source_path)
        overlaps = True
    except ValueError:
        try:
            source_path.relative_to(project_path)
            overlaps = True
        except ValueError:
            overlaps = False
    errors: list[dict] = []
    if declared_working != project_path or source_path == project_path or overlaps:
        errors.append(_error("SOURCE_WORKING_CONFLICT"))
    try:
        actual_source_core = hash_project_core(source_path)
        if actual_source_core != contract["source_core_sha256"]:
            errors.append(_error("SOURCE_SHA_CHANGED"))
    except (OSError, ValueError):
        actual_source_core = {}
        errors.append(_error("SOURCE_SHA_CHANGED"))
    actual_source_root = manifest_sha256(actual_source_core) if actual_source_core else None
    if actual_source_root != contract.get("source_root_sha256"):
        errors.append(_error("SOURCE_ROOT_SHA_MISMATCH"))
    try:
        actual_template_sha256 = template_fingerprint_sha256(source_path)
    except OSError:
        actual_template_sha256 = None
    if actual_template_sha256 != contract.get("template_sha256"):
        errors.append(_error("TEMPLATE_SHA_MISMATCH"))
    design_lock_evidence_path = Path(contract["design_lock_evidence_path"]).resolve()
    if (
        not design_lock_evidence_path.is_file()
        or sha256_file(design_lock_evidence_path) != contract.get("design_lock_evidence_sha256")
    ):
        errors.append(_error("DESIGN_LOCK_EVIDENCE_SHA_MISMATCH"))
    design_lock_errors, _ = validate_design_lock_authority(contract)
    errors.extend(design_lock_errors)
    authority = snapshot.get("authority", {})
    expected_authority = {
        "captured_from": "source",
        "source_project_path": str(source_path),
        "source_root_sha256": contract.get("source_root_sha256"),
        "template_sha256": contract.get("template_sha256"),
        "design_lock_evidence_sha256": contract.get("design_lock_evidence_sha256"),
    }
    if authority != expected_authority:
        errors.append(_error("STRUCTURE_SNAPSHOT_AUTHORITY_MISMATCH"))
    try:
        source_structure = capture_structure(load_project(source_path))
        snapshot_structure = {
            key: snapshot.get(key) for key in ("schema_version", "track_order", "tracks")
        }
        if source_structure != snapshot_structure:
            errors.append(_error("STRUCTURE_SNAPSHOT_AUTHORITY_MISMATCH"))
    except ProjectError:
        errors.append(_error("STRUCTURE_SNAPSHOT_AUTHORITY_MISMATCH"))
    try:
        model = load_project(project_path)
    except ProjectError as exc:
        return {**result(errors + [_error(exc.code, detail=exc.detail)]), "next_action": "NONE"}

    mirror_result = validate_id_mirrors(project_path)
    errors.extend(mirror_result.get("errors", []))
    observed_ids = mirror_result.get("evidence", {})
    if any(
        observed_ids.get(key) != contract.get(key)
        for key in ("project_id", "draft_id", "main_timeline_id")
    ):
        errors.append(_error("PROJECT_ID_MISMATCH"))
    errors.extend(validate_structure(model, snapshot))
    snapshot_track_surface = {
        "schema_version": snapshot.get("schema_version"),
        "track_order": snapshot.get("track_order"),
        "tracks": snapshot.get("tracks"),
    }
    for mirror_file, mirror_content in iter_primary_draft_documents(project_path):
        if mirror_file == project_path / "draft_content.json":
            continue
        if not is_full_content_timeline_mirror(mirror_content, mirror_file):
            continue
        mirror_structure = capture_structure_from_content(mirror_content)
        mirror_surface = {
            "schema_version": mirror_structure["schema_version"],
            "track_order": mirror_structure["track_order"],
            "tracks": mirror_structure["tracks"],
        }
        if mirror_surface != snapshot_track_surface:
            errors.append(_error("STRUCTURE_SNAPSHOT_AUTHORITY_MISMATCH"))
            break
    errors.extend(validate_materials(model, project_path))
    errors.extend(validate_segment_material_types_and_durations(model, project_path, contract))
    declared_assets = {
        candidate.relative_to(project_path).as_posix()
        for raw_path in contract["required_asset_paths"]
        if (candidate := _resolve_required_asset(project_path, raw_path)) is not None
    }
    for relative in sorted(_referenced_media_paths(model, project_path) - declared_assets):
        errors.append(_error("MATERIAL_ASSET_NOT_REQUIRED", path=relative))
    errors.extend(validate_timeline(model, contract))
    errors.extend(validate_v2_role_routing(model, contract))
    errors.extend(validate_visible_text(model, contract))
    errors.extend(validate_subtitle_binding(model, contract))

    validated_files: dict[str, str] = {}
    timeline_json_paths = [path for path, _ in iter_timeline_json(project_path)]
    required_json_paths = [
        project_path / "draft_content.json",
        project_path / "draft_meta_info.json",
        *timeline_json_paths,
    ]
    for path in required_json_paths:
        if path.is_file():
            validated_files[path.relative_to(project_path).as_posix()] = sha256_file(path)
    for raw_path in contract["required_asset_paths"]:
        asset = _resolve_required_asset(project_path, raw_path)
        if asset is None or not asset.is_file():
            errors.append(_error("REQUIRED_ASSET_MISSING", path=raw_path))
            continue
        if not _probe(asset):
            errors.append(_error("MEDIA_DECODE_FAILED", path=raw_path))
            continue
        validated_files[asset.relative_to(project_path).as_posix()] = sha256_file(asset)

    if errors:
        return {**result(errors), "next_action": "NONE"}
    if evidence_path is None:
        return {**result([_error("CAPCUT_PROJECT_EVIDENCE_PATH_MISSING")]), "next_action": "NONE"}
    evidence_path = Path(evidence_path).absolute()
    evidence = {
        "schema_version": "001short-capcut-project-evidence-v1",
        "status": "PASS",
        "episode_id": contract["episode_id"],
        "actual_project_path": str(project_path),
        "build_contract_path": str(build_contract_path),
        "build_contract_sha256": sha256_file(build_contract_path),
        "structure_snapshot_path": str(structure_snapshot_path),
        "structure_snapshot_sha256": sha256_file(structure_snapshot_path),
        "source_project_path": str(source_path),
        "source_core_sha256": contract["source_core_sha256"],
        "source_root_sha256": contract["source_root_sha256"],
        "template_sha256": contract["template_sha256"],
        "design_lock_evidence_path": str(design_lock_evidence_path),
        "design_lock_evidence_sha256": contract["design_lock_evidence_sha256"],
        "project_id": contract["project_id"],
        "draft_id": contract["draft_id"],
        "main_timeline_id": contract["main_timeline_id"],
        "timeline_json_files": sorted(
            path.relative_to(project_path).as_posix() for path in timeline_json_paths
        ),
        "validated_files": validated_files,
    }
    evidence_errors = validate_schema(evidence, read_json(EVIDENCE_SCHEMA))
    if evidence_errors:
        return {
            **result([_error("CAPCUT_PROJECT_EVIDENCE_SCHEMA", detail=evidence_errors)]),
            "next_action": "NONE",
        }
    write_json(evidence_path, evidence)
    return {
        **result([], {"evidence_path": str(evidence_path), "evidence_sha256": sha256_file(evidence_path)}),
        "next_action": "WAIT_USER_VISUAL_GATE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--build-contract", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_capcut_project(
        args.project,
        args.snapshot,
        args.build_contract,
        args.evidence,
        approved_evidence_root_path=args.evidence_root,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
