"""000short-production-agent deterministic gate validator (G30-G90).

Validates only the current gate. Never:
- calls an external model
- opens CapCut
- performs paid TTS without authorization
- uploads
- silently advances authority

Enforces:
- entry owner-transfer receipt + matching design_handoff SHA
- G30 measured audio precedes G40 SRT lock (NORM-002)
- status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS (NORM-003)
- G70 release_allowed=false
- G90 release requires FINAL_QC_PASS + UPLOAD_APPROVED (RW-P03-02)
- production cannot rewrite hook or urakkai order

Thin lane adapter over the shared generated core.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_CORE = (
    REPO_ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)


class GateFail(Exception):
    pass


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "short_prod_workflow_harness_core", GENERATED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["short_prod_workflow_harness_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in value)


def _resolve_artifact_path(root: Path | None, value: object) -> Path | None:
    if root is None or not isinstance(value, str) or not value.strip():
        return None
    root = root.resolve()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _read_json_file(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _probe_media(path: Path) -> dict | None:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
        duration = float(payload.get("format", {}).get("duration", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    stream_types = {
        stream.get("codec_type")
        for stream in payload.get("streams", [])
        if isinstance(stream, dict)
    }
    return {
        "duration_us": round(duration * 1_000_000),
        "has_audio": "audio" in stream_types,
        "has_video": "video" in stream_types,
    }


def _missing_fields(payload: dict, fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if field not in payload]


def validate_entry(
    *,
    owner_transfer_receipt: dict | None,
    design_handoff: dict | None,
    design_handoff_path: Path | None = None,
    artifact_root: Path | None = None,
) -> list[dict]:
    """G30 entry contract: reject without valid owner-transfer receipt and
    matching canonical handoff SHA."""
    errors: list[dict] = []
    if not owner_transfer_receipt:
        errors.append({"code": "FAIL_ENTRY_NO_OWNER_TRANSFER_RECEIPT"})
    if not design_handoff:
        errors.append({"code": "FAIL_ENTRY_NO_DESIGN_HANDOFF"})
    if errors:
        return errors
    assert owner_transfer_receipt is not None
    assert design_handoff is not None
    receipt_required = (
        "schema_version",
        "from_lane",
        "from_skill",
        "to_lane",
        "to_skill",
        "source_fingerprint",
        "canonical_handoff_path",
        "canonical_handoff_sha256",
        "requested_target",
        "transfer_status",
    )
    if _missing_fields(owner_transfer_receipt, receipt_required):
        errors.append({"code": "FAIL_ENTRY_RECEIPT_SCHEMA"})
    if owner_transfer_receipt.get("schema_version") != "owner-transfer-v1":
        errors.append({"code": "FAIL_ENTRY_RECEIPT_SCHEMA"})
    if (
        owner_transfer_receipt.get("from_lane") != "general_shorts_design"
        or owner_transfer_receipt.get("from_skill") != "00-tikitaka"
        or owner_transfer_receipt.get("to_lane") != "general_shorts_production"
        or owner_transfer_receipt.get("to_skill") != "000short-production-agent"
    ):
        errors.append({"code": "FAIL_ENTRY_RECEIPT_ROUTE"})
    if owner_transfer_receipt.get("transfer_status") != "PASS":
        errors.append({"code": "FAIL_ENTRY_RECEIPT_NOT_PASS"})
    handoff_required = (
        "schema_version",
        "episode_id",
        "lane",
        "content_profile",
        "production_mode",
        "requested_target",
        "source_fingerprint",
        "design_blueprint_sha256",
        "timeline_sha256",
        "external_review_receipt_sha256",
        "status",
    )
    if (
        _missing_fields(design_handoff, handoff_required)
        or design_handoff.get("schema_version") != "shorts-design-handoff-v1"
    ):
        errors.append({"code": "FAIL_ENTRY_HANDOFF_SCHEMA"})
    expected_sha = owner_transfer_receipt.get("canonical_handoff_sha256")
    actual_sha = None
    if design_handoff_path is not None and design_handoff_path.is_file():
        actual_sha = _sha256_file(design_handoff_path)
    else:
        actual_sha = design_handoff.get("design_handoff_sha256") or design_handoff.get(
            "canonical_handoff_sha256"
        )
    if not _is_sha256(expected_sha) or not _is_sha256(actual_sha):
        errors.append({"code": "FAIL_ENTRY_HANDOFF_SHA_MISSING"})
    elif expected_sha != actual_sha:
        errors.append(
            {
                "code": "FAIL_ENTRY_HANDOFF_SHA_MISMATCH",
                "expected": expected_sha,
                "actual": actual_sha,
            }
        )
    if artifact_root is not None:
        declared_handoff = _resolve_artifact_path(
            artifact_root,
            owner_transfer_receipt.get("canonical_handoff_path"),
        )
        if (
            declared_handoff is None
            or design_handoff_path is None
            or declared_handoff != design_handoff_path.resolve()
        ):
            errors.append({"code": "FAIL_ENTRY_HANDOFF_PATH_MISMATCH"})
        for path_field, sha_field, code in (
            (
                "design_blueprint_path",
                "design_blueprint_sha256",
                "FAIL_ENTRY_DESIGN_BLUEPRINT_SHA",
            ),
            ("timeline_path", "timeline_sha256", "FAIL_ENTRY_TIMELINE_SHA"),
            (
                "external_review_receipt_path",
                "external_review_receipt_sha256",
                "FAIL_ENTRY_EXTERNAL_REVIEW_SHA",
            ),
        ):
            referenced = _resolve_artifact_path(artifact_root, design_handoff.get(path_field))
            expected = design_handoff.get(sha_field)
            if (
                referenced is None
                or not referenced.is_file()
                or not _is_sha256(expected)
                or _sha256_file(referenced) != expected
            ):
                errors.append({"code": code})
    for field in (
        "source_fingerprint",
        "design_blueprint_sha256",
        "timeline_sha256",
        "external_review_receipt_sha256",
        "requested_target",
    ):
        receipt_value = owner_transfer_receipt.get(field)
        handoff_value = design_handoff.get(field)
        if receipt_value is not None and receipt_value != handoff_value:
            errors.append({"code": "FAIL_ENTRY_AUTHORITY_MISMATCH", "field": field})
    if design_handoff.get("status") != "PASS":
        errors.append({"code": "FAIL_ENTRY_HANDOFF_NOT_PASS"})
    return errors


def validate_g30(
    *,
    audio_lock: dict,
    owner_transfer_receipt: dict | None = None,
    design_handoff: dict | None = None,
    design_handoff_path: Path | None = None,
    artifact_root: Path | None = None,
) -> dict:
    core = _import_core()
    errors: list[dict] = []

    errors.extend(
        validate_entry(
            owner_transfer_receipt=owner_transfer_receipt,
            design_handoff=design_handoff,
            design_handoff_path=design_handoff_path,
            artifact_root=artifact_root,
        )
    )
    required_audio_fields = (
        "schema_version",
        "episode_id",
        "status",
        "audio_source",
        "audio_path",
        "audio_sha256",
        "measured_duration_us",
        "measured_duration_evidence_path",
        "measured_duration_evidence_sha256",
        "ffprobe_verified",
    )
    if (
        audio_lock.get("schema_version") != "shorts-audio-lock-v1"
        or _missing_fields(audio_lock, required_audio_fields)
    ):
        errors.append({"code": "FAIL_G30_AUDIO_LOCK_SCHEMA"})

    # NORM-003: NOT_REQUIRED_NO_GENERATED_TTS is forbidden.
    raw_status = audio_lock.get("status")
    if raw_status == "NOT_REQUIRED_NO_GENERATED_TTS":
        errors.append({"code": "FAIL_FORBIDDEN_NOT_REQUIRED_NO_GENERATED_TTS"})
    if raw_status == "NOT_REQUIRED":
        if audio_lock.get("reason_code") != "NO_GENERATED_TTS":
            errors.append({"code": "FAIL_NO_GENERATED_TTS_REASON_CODE_MISSING"})

    # PASS and source-led NOT_REQUIRED both require measured duration evidence.
    if raw_status in ("PASS", "NOT_REQUIRED"):
        if not _is_sha256(audio_lock.get("measured_duration_evidence_sha256")):
            errors.append({"code": "FAIL_G30_NO_MEASURED_DURATION"})
        if not isinstance(audio_lock.get("measured_duration_us"), int) or audio_lock.get(
            "measured_duration_us", 0
        ) <= 0:
            errors.append({"code": "FAIL_G30_INVALID_MEASURED_DURATION"})
        if audio_lock.get("audio_source") not in ("GENERATED_TTS", "SOURCE_CLIP"):
            errors.append({"code": "FAIL_G30_AUDIO_SOURCE_REQUIRED"})
        audio_path = _resolve_artifact_path(artifact_root, audio_lock.get("audio_path"))
        evidence_path = _resolve_artifact_path(
            artifact_root,
            audio_lock.get("measured_duration_evidence_path"),
        )
        if audio_path is None or not audio_path.is_file():
            errors.append({"code": "FAIL_G30_AUDIO_FILE_MISSING"})
        elif (
            not _is_sha256(audio_lock.get("audio_sha256"))
            or _sha256_file(audio_path) != audio_lock.get("audio_sha256")
        ):
            errors.append({"code": "FAIL_G30_AUDIO_SHA_MISMATCH"})
        if evidence_path is None or not evidence_path.is_file():
            errors.append({"code": "FAIL_G30_MEASUREMENT_EVIDENCE_MISSING"})
            evidence = None
        elif _sha256_file(evidence_path) != audio_lock.get(
            "measured_duration_evidence_sha256"
        ):
            errors.append({"code": "FAIL_G30_MEASUREMENT_EVIDENCE_SHA_MISMATCH"})
            evidence = None
        else:
            evidence = _read_json_file(evidence_path)
            if evidence is None:
                errors.append({"code": "FAIL_G30_MEASUREMENT_EVIDENCE_INVALID"})
        if audio_path is not None and audio_path.is_file():
            probe = _probe_media(audio_path)
            measured = audio_lock.get("measured_duration_us")
            if (
                probe is None
                or not probe["has_audio"]
                or not audio_lock.get("ffprobe_verified") is True
            ):
                errors.append({"code": "FAIL_G30_FFPROBE"})
            elif not isinstance(measured, int) or abs(probe["duration_us"] - measured) > 50_000:
                errors.append(
                    {
                        "code": "FAIL_G30_DURATION_MISMATCH",
                        "actual": probe["duration_us"],
                        "locked": measured,
                    }
                )
            if evidence is not None:
                for field in ("audio_sha256", "measured_duration_us", "ffprobe_verified"):
                    if evidence.get(field) != audio_lock.get(field):
                        errors.append(
                            {
                                "code": "FAIL_G30_MEASUREMENT_EVIDENCE_MISMATCH",
                                "field": field,
                            }
                        )
    if raw_status == "PASS":
        if audio_lock.get("audio_source") == "GENERATED_TTS":
            if not audio_lock.get("paid_tts_cost_event_id"):
                errors.append({"code": "FAIL_G30_PAID_TTS_NO_COST_EVENT"})

    reason_code = audio_lock.get("reason_code") if raw_status == "NOT_REQUIRED" else None
    return core.validate_gate(
        lane="general_shorts_production",
        gate="G30",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G40" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status=(
            "PASS"
            if not errors and raw_status == "PASS"
            else (raw_status if not errors and raw_status else None)
        ),
        reason_code=reason_code,
    )


def validate_g40(
    *,
    caption_lock: dict,
    g30_audio_lock: dict | None,
    g30_audio_lock_path: Path | None = None,
    artifact_root: Path | None = None,
) -> dict:
    core = _import_core()
    errors: list[dict] = []

    required_caption_fields = (
        "schema_version",
        "episode_id",
        "status",
        "g30_audio_lock_sha256",
        "final_cue_count",
        "final_srt_sha256",
    )
    if (
        caption_lock.get("schema_version") != "shorts-caption-lock-v1"
        or any(field not in caption_lock for field in required_caption_fields)
    ):
        errors.append({"code": "FAIL_G40_CAPTION_LOCK_SCHEMA"})

    # NORM-002: SRT lock requires measured audio (G30 PASS or NOT_REQUIRED
    # with NO_GENERATED_TTS and measured source duration).
    if g30_audio_lock is None:
        errors.append({"code": "FAIL_G40_NO_G30_AUDIO_LOCK"})
    else:
        g30_status = g30_audio_lock.get("status")
        if g30_status not in ("PASS", "NOT_REQUIRED"):
            errors.append({"code": "FAIL_G40_G30_NOT_LOCKED"})
        if (
            g30_status == "NOT_REQUIRED"
            and g30_audio_lock.get("reason_code") != "NO_GENERATED_TTS"
        ):
            errors.append({"code": "FAIL_G40_G30_NO_TTS_REASON"})
        if not g30_audio_lock.get("measured_duration_evidence_sha256"):
            errors.append({"code": "FAIL_G40_G30_NO_MEASURED_DURATION"})

    if not _is_sha256(caption_lock.get("g30_audio_lock_sha256")):
        errors.append({"code": "FAIL_G40_G30_SHA_MISSING"})
    elif (
        g30_audio_lock_path is None
        or not g30_audio_lock_path.is_file()
        or _sha256_file(g30_audio_lock_path)
        != caption_lock.get("g30_audio_lock_sha256")
    ):
        errors.append({"code": "FAIL_G40_G30_SHA_MISMATCH"})
    if g30_audio_lock is not None:
        if caption_lock.get("episode_id") != g30_audio_lock.get("episode_id"):
            errors.append({"code": "FAIL_G40_EPISODE_MISMATCH"})
        audio_path = _resolve_artifact_path(
            artifact_root,
            g30_audio_lock.get("audio_path"),
        )
        if (
            audio_path is None
            or not audio_path.is_file()
            or _sha256_file(audio_path) != g30_audio_lock.get("audio_sha256")
        ):
            errors.append({"code": "FAIL_G40_G30_AUDIO_UNVERIFIED"})
        else:
            probe = _probe_media(audio_path)
            locked_duration = g30_audio_lock.get("measured_duration_us")
            if (
                probe is None
                or not probe["has_audio"]
                or not isinstance(locked_duration, int)
                or abs(probe["duration_us"] - locked_duration) > 50_000
            ):
                errors.append({"code": "FAIL_G40_G30_DURATION_UNVERIFIED"})
    if caption_lock.get("status") != "PASS":
        errors.append({"code": "FAIL_G40_CAPTION_LOCK_NOT_PASS"})
    final_srt_path = _resolve_artifact_path(
        artifact_root,
        caption_lock.get("final_srt_path"),
    )
    if (
        final_srt_path is None
        or not final_srt_path.is_file()
        or not _is_sha256(caption_lock.get("final_srt_sha256"))
        or _sha256_file(final_srt_path) != caption_lock.get("final_srt_sha256")
    ):
        errors.append({"code": "FAIL_G40_FINAL_SRT_SHA_MISMATCH"})
    cues = caption_lock.get("cues")
    if (
        not isinstance(cues, list)
        or caption_lock.get("final_cue_count") != len(cues)
    ):
        errors.append({"code": "FAIL_G40_CUE_COUNT"})
        cues = []
    measured_duration = (
        g30_audio_lock.get("measured_duration_us", -1)
        if g30_audio_lock is not None
        else -1
    )
    previous_end = -1
    for cue in cues:
        if not isinstance(cue, dict):
            errors.append({"code": "FAIL_G40_CUE_SCHEMA"})
            continue
        start = cue.get("start_us")
        end = cue.get("end_us")
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or end > measured_duration
        ):
            errors.append({"code": "FAIL_G40_CUE_OUTSIDE_MEASURED_AUDIO"})
        if isinstance(start, int) and start < previous_end:
            errors.append({"code": "FAIL_G40_CUE_OVERLAP"})
        if isinstance(end, int):
            previous_end = end
    if caption_lock.get("all_cues_within_measured_audio") is not True:
        errors.append({"code": "FAIL_G40_CUE_OUTSIDE_MEASURED_AUDIO"})
    if caption_lock.get("no_overlap_verified") is not True:
        errors.append({"code": "FAIL_G40_CUE_OVERLAP"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G40",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G50" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g50(
    *,
    track_plan: dict,
    g40_caption_lock: dict | None,
    g40_caption_lock_path: Path | None = None,
    design_handoff: dict | None = None,
    design_handoff_path: Path | None = None,
    artifact_root: Path | None = None,
) -> dict:
    core = _import_core()
    errors: list[dict] = []

    required_track_fields = (
        "schema_version",
        "episode_id",
        "status",
        "g40_caption_lock_sha256",
        "design_handoff_sha256",
        "segments",
        "timeline_order_matches_design_handoff",
    )
    if (
        track_plan.get("schema_version") != "shorts-track-plan-v1"
        or _missing_fields(track_plan, required_track_fields)
    ):
        errors.append({"code": "FAIL_G50_TRACK_PLAN_SCHEMA"})
    if track_plan.get("status") != "PASS":
        errors.append({"code": "FAIL_G50_TRACK_PLAN_NOT_PASS"})
    if g40_caption_lock is None:
        errors.append({"code": "FAIL_G50_NO_G40_CAPTION_LOCK"})
    elif g40_caption_lock.get("status") != "PASS":
        errors.append({"code": "FAIL_G50_G40_NOT_PASS"})
    if not _is_sha256(track_plan.get("g40_caption_lock_sha256")):
        errors.append({"code": "FAIL_G50_G40_SHA_MISSING"})
    elif (
        g40_caption_lock_path is None
        or not g40_caption_lock_path.is_file()
        or _sha256_file(g40_caption_lock_path)
        != track_plan.get("g40_caption_lock_sha256")
    ):
        errors.append({"code": "FAIL_G50_G40_SHA_MISMATCH"})
    if not track_plan.get("segments"):
        errors.append({"code": "FAIL_G50_NO_SEGMENTS"})
    if track_plan.get("timeline_order_matches_design_handoff") is not True:
        errors.append({"code": "FAIL_G50_CREATIVE_REORDER_FORBIDDEN"})
    protected_creative_fields = {
        "hook",
        "hook_text",
        "urakkai_order",
        "production_profile",
        "editorial_authority",
    }
    for segment in track_plan.get("segments", []):
        if protected_creative_fields.intersection(segment):
            errors.append(
                {
                    "code": "FAIL_G50_CREATIVE_LOCK_MISMATCH",
                    "slot_id": segment.get("slot_id"),
                }
            )
    if not _is_sha256(track_plan.get("design_handoff_sha256")):
        errors.append({"code": "FAIL_G50_DESIGN_HANDOFF_SHA_MISSING"})
    elif (
        design_handoff_path is None
        or not design_handoff_path.is_file()
        or _sha256_file(design_handoff_path)
        != track_plan.get("design_handoff_sha256")
    ):
        errors.append({"code": "FAIL_G50_DESIGN_HANDOFF_SHA_MISMATCH"})
    if not design_handoff:
        errors.append({"code": "FAIL_G50_DESIGN_HANDOFF_MISSING"})
        timeline = None
    else:
        timeline_path = _resolve_artifact_path(
            artifact_root,
            design_handoff.get("timeline_path"),
        )
        if (
            timeline_path is None
            or not timeline_path.is_file()
            or _sha256_file(timeline_path) != design_handoff.get("timeline_sha256")
        ):
            errors.append({"code": "FAIL_G50_TIMELINE_SHA_MISMATCH"})
            timeline = None
        else:
            timeline = _read_json_file(timeline_path)
            if timeline is None:
                errors.append({"code": "FAIL_G50_TIMELINE_SCHEMA"})
    if timeline is not None:
        timeline_rows = {
            row.get("edit_id"): row
            for row in timeline.get("segments", [])
            if isinstance(row, dict) and row.get("edit_id")
        }
        plan_rows = {
            row.get("slot_id"): row
            for row in track_plan.get("segments", [])
            if isinstance(row, dict) and row.get("slot_id")
        }
        if set(timeline_rows) != set(plan_rows):
            errors.append({"code": "FAIL_G50_CREATIVE_LOCK_MISMATCH"})
        cue_rows = {}
        if g40_caption_lock is not None:
            cue_rows = {
                cue.get("cue_id"): cue
                for cue in g40_caption_lock.get("cues", [])
                if isinstance(cue, dict) and cue.get("cue_id")
            }
        for slot_id in sorted(set(timeline_rows) & set(plan_rows)):
            timeline_row = timeline_rows[slot_id]
            plan_row = plan_rows[slot_id]
            comparisons = (
                ("assembly_role", "assembly_role"),
                ("source_order", "source_order"),
                ("timeline_order", "timeline_order"),
                ("caption_role", "caption_type"),
            )
            if any(
                plan_row.get(plan_field) != timeline_row.get(timeline_field)
                for plan_field, timeline_field in comparisons
            ):
                errors.append(
                    {
                        "code": "FAIL_G50_CREATIVE_LOCK_MISMATCH",
                        "slot_id": slot_id,
                    }
                )
            cue = cue_rows.get(slot_id)
            if cue is not None and (
                plan_row.get("clip_start_us") != cue.get("start_us")
                or plan_row.get("clip_end_us") != cue.get("end_us")
            ):
                errors.append(
                    {
                        "code": "FAIL_G50_G40_TIMING_MISMATCH",
                        "slot_id": slot_id,
                    }
                )

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G50",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G60" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def _ledger_validation_errors(core, ledger_events: list[dict] | None) -> list[dict]:
    errors: list[dict] = []
    if not isinstance(ledger_events, list) or not ledger_events:
        return [{"code": "FAIL_LEDGER_REQUIRED"}]
    genesis_episode_id = (
        ledger_events[0].get("episode_id")
        if isinstance(ledger_events[0], dict)
        else None
    )
    required = (
        "event_id",
        "timestamp",
        "episode_id",
        "lane",
        "gate",
        "event_type",
        "actor",
        "previous_event_id",
    )
    for index, event in enumerate(ledger_events):
        if not isinstance(event, dict) or _missing_fields(event, required):
            errors.append({"code": "FAIL_LEDGER_EVENT_SCHEMA", "index": index})
            continue
        if event.get("lane") != "general_shorts_production":
            errors.append({"code": "FAIL_LEDGER_LANE", "index": index})
        if (
            genesis_episode_id is not None
            and event.get("episode_id") != genesis_episode_id
        ):
            errors.append({"code": "FAIL_LEDGER_EPISODE", "index": index})
    if errors:
        return errors
    try:
        store = core.LedgerStore()
        store.extend(ledger_events)
    except Exception as exc:
        errors.append({"code": "FAIL_LEDGER_CHAIN", "message": str(exc)})
    return errors


def _has_user_visual_pass(ledger_events: list[dict]) -> bool:
    return any(
        isinstance(event, dict)
        and event.get("event_type") == "USER_VISUAL_PASS"
        and event.get("gate") == "G60.USER"
        and event.get("actor") == "USER"
        for event in ledger_events
    )


def validate_g60(
    *,
    assembly_result: dict,
    g50_track_plan: dict | None = None,
    g50_track_plan_path: Path | None = None,
    template_contract: dict | None = None,
    template_contract_path: Path | None = None,
    template_contract_sha256: str | None = None,
) -> dict:
    core = _import_core()
    errors: list[dict] = []

    required_assembly_fields = (
        "schema_version",
        "episode_id",
        "status",
        "capcut_root",
        "g50_track_plan_sha256",
        "template_contract_sha256",
        "required_internal_asset",
        "cache_online_material_referenced",
        "capcut_gui_opened",
        "slots",
        "hard_fails",
    )
    if (
        assembly_result.get("schema_version") != "shorts-assembly-result-v1"
        or _missing_fields(assembly_result, required_assembly_fields)
        or not isinstance(assembly_result.get("slots"), list)
        or not isinstance(assembly_result.get("hard_fails"), list)
    ):
        errors.append({"code": "FAIL_G60_ASSEMBLY_SCHEMA"})
    if assembly_result.get("status") != "PASS":
        errors.append({"code": "FAIL_G60_ASSEMBLY_NOT_PASS"})
    if assembly_result.get("capcut_root") != "shrt white":
        errors.append({"code": "FAIL_G60_WRONG_CAPCUT_ROOT"})
    if (
        g50_track_plan is None
        or g50_track_plan.get("status") != "PASS"
        or g50_track_plan_path is None
        or not g50_track_plan_path.is_file()
        or _sha256_file(g50_track_plan_path)
        != assembly_result.get("g50_track_plan_sha256")
    ):
        errors.append({"code": "FAIL_G60_G50_SHA_MISMATCH"})
    expected_template_sha = (
        _sha256_file(template_contract_path)
        if template_contract_path is not None and template_contract_path.is_file()
        else None
    )
    if (
        template_contract is None
        or template_contract.get("capcut_root_project_name") != "shrt white"
        or not _is_sha256(expected_template_sha)
        or assembly_result.get("template_contract_sha256") != expected_template_sha
    ):
        errors.append({"code": "FAIL_G60_TEMPLATE_CONTRACT_SHA_MISMATCH"})
    if (
        assembly_result.get("required_internal_asset")
        != "Resources/media/transparent_center_white_1080x1920.png"
    ):
        errors.append({"code": "FAIL_STALE_TEMPLATE_IMAGE"})
    if assembly_result.get("cache_online_material_referenced") is not False:
        errors.append({"code": "FAIL_UNAPPROVED_TEMPLATE_MATERIAL"})
    if assembly_result.get("capcut_gui_opened") is not False:
        errors.append({"code": "FAIL_G60_CAPCUT_GUI_OPERATION"})
    hard_fails = (
        assembly_result.get("hard_fails", [])
        if isinstance(assembly_result.get("hard_fails"), list)
        else []
    )
    for hf in hard_fails:
        errors.append({"code": hf})
    if template_contract is not None:
        expected_slots = {
            slot.get("slot_id"): slot
            for slot in template_contract.get("slots", [])
            if isinstance(slot, dict) and slot.get("slot_id")
        }
        actual_slots = {
            slot.get("slot_id"): slot
            for slot in (
                assembly_result.get("slots", [])
                if isinstance(assembly_result.get("slots"), list)
                else []
            )
            if isinstance(slot, dict) and slot.get("slot_id")
        }
        if set(expected_slots) != set(actual_slots):
            errors.append({"code": "FAIL_TEMPLATE_SLOT_COVERAGE"})
        text_box_fields = {
            "line_max_width",
            "background_width",
            "background_height",
            "background_round_radius",
        }
        code_by_field = {
            "transform_x": "FAIL_TEMPLATE_X_CHANGED",
            "transform_y": "FAIL_TEMPLATE_Y_CHANGED",
            "scale_x": "FAIL_TEMPLATE_SCALE_CHANGED",
            "scale_y": "FAIL_TEMPLATE_SCALE_CHANGED",
            "rotation": "FAIL_TEMPLATE_ROTATION_CHANGED",
            "font_resource_id": "FAIL_TEMPLATE_FONT_CHANGED",
            "font_size": "FAIL_TEMPLATE_FONT_SIZE_CHANGED",
            "initial_scale": "FAIL_TEMPLATE_SCALE_CHANGED",
            "alignment": "FAIL_TEMPLATE_ALIGNMENT_CHANGED",
            "global_alpha": "FAIL_TEMPLATE_OPACITY_CHANGED",
            "layer_index": "FAIL_LAYER_ORDER_CHANGED",
            "track_order": "FAIL_TRACK_ORDER_CHANGED",
        }
        for slot_id in sorted(set(expected_slots) & set(actual_slots)):
            expected_slot = expected_slots[slot_id]
            actual_slot = actual_slots[slot_id]
            fields = set(expected_slot.get("locked_fields", []))
            fields.update(
                field
                for field in (
                    "transform_x",
                    "transform_y",
                    "scale_x",
                    "scale_y",
                    "rotation",
                    "alpha",
                )
                if field in expected_slot
            )
            if expected_slot.get("material_role") == "TEXT":
                fields.update(
                    field for field in text_box_fields if field in expected_slot
                )
            for field in sorted(fields):
                if actual_slot.get(field) == expected_slot.get(field):
                    continue
                errors.append(
                    {
                        "code": (
                            "FAIL_TEMPLATE_TEXTBOX_CHANGED"
                            if field in text_box_fields
                            else code_by_field.get(
                                field,
                                "FAIL_TEMPLATE_LOCK_CHANGED",
                            )
                        ),
                        "slot_id": slot_id,
                        "field": field,
                    }
                )
    # Static PASS transitions to WAIT_USER_VISUAL_GATE.
    status = "PASS" if not errors else "FAIL"
    next_action = "WAIT_USER_VISUAL_GATE" if not errors else "NONE"

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G60",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action=next_action,
        auto_advance_allowed=False,  # WAIT_USER_VISUAL_GATE is a user gate
        auto_advance_class="NONE",
        status=status,
    )


def validate_g60_user(*, ledger_events: list[dict] | None) -> dict:
    core = _import_core()
    errors = _ledger_validation_errors(core, ledger_events)
    if errors and errors == [{"code": "FAIL_LEDGER_REQUIRED"}]:
        errors = []
    has_pass = bool(ledger_events) and _has_user_visual_pass(ledger_events)
    if not errors and not has_pass:
        return core.validate_gate(
            lane="general_shorts_production",
            gate="G60.USER",
            subgate=None,
            validated_inputs=[],
            evidence=[],
            errors=[],
            warnings=[],
            next_action="WAIT_USER_VISUAL_GATE",
            auto_advance_allowed=False,
            auto_advance_class="NONE",
            status="WAIT_USER_VISUAL_GATE",
        )
    return core.validate_gate(
        lane="general_shorts_production",
        gate="G60.USER",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G70" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g70(
    *,
    upload_package: dict,
    ledger_events: list[dict] | None = None,
    artifact_root: Path | None = None,
) -> dict:
    core = _import_core()
    errors = _ledger_validation_errors(core, ledger_events)

    if upload_package.get("release_allowed") is not False:
        errors.append({"code": "FAIL_G70_RELEASE_MUST_BE_FALSE"})
    required = (
        "schema_version",
        "episode_id",
        "status",
        "release_allowed",
        "thumbnail_path",
        "thumbnail_sha256",
        "metadata_path",
        "metadata_sha256",
        "uploaded_marker_present",
    )
    if (
        upload_package.get("schema_version") != "shorts-upload-package-v1"
        or _missing_fields(upload_package, required)
    ):
        errors.append({"code": "FAIL_G70_UPLOAD_PACKAGE_SCHEMA"})
    if upload_package.get("status") != "PASS":
        errors.append({"code": "FAIL_G70_UPLOAD_PACKAGE_NOT_PASS"})
    if not ledger_events or not _has_user_visual_pass(ledger_events):
        errors.append({"code": "FAIL_G70_NO_USER_VISUAL_PASS"})
    for path_field, sha_field, code in (
        ("thumbnail_path", "thumbnail_sha256", "FAIL_G70_THUMBNAIL_SHA"),
        ("metadata_path", "metadata_sha256", "FAIL_G70_METADATA_SHA"),
    ):
        path = _resolve_artifact_path(artifact_root, upload_package.get(path_field))
        if (
            path is None
            or not path.is_file()
            or path.stat().st_size <= 0
            or not _is_sha256(upload_package.get(sha_field))
            or _sha256_file(path) != upload_package.get(sha_field)
        ):
            errors.append({"code": code})
    if upload_package.get("uploaded_marker_present") is not False:
        errors.append({"code": "FAIL_G70_UPLOAD_ALREADY_OCCURRED"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G70",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G80" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g80(
    *,
    render_evidence: dict,
    g70_upload_package: dict | None = None,
    g70_upload_package_path: Path | None = None,
    artifact_root: Path | None = None,
) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if (
        g70_upload_package is None
        or g70_upload_package.get("status") != "PASS"
        or g70_upload_package.get("release_allowed") is not False
    ):
        errors.append({"code": "FAIL_G80_G70_NOT_PASS"})
    if (
        g70_upload_package_path is None
        or not g70_upload_package_path.is_file()
        or _sha256_file(g70_upload_package_path)
        != render_evidence.get("g70_upload_package_sha256")
    ):
        errors.append({"code": "FAIL_G80_G70_SHA_MISMATCH"})
    required = (
        "schema_version",
        "episode_id",
        "status",
        "g70_upload_package_sha256",
        "rendered_mp4_path",
        "rendered_mp4_sha256",
        "rendered_size_bytes",
        "duration_us",
        "duration_tolerance_us",
        "ffprobe_verified",
        "video_stream_present",
        "audio_stream_present",
    )
    if (
        render_evidence.get("schema_version") != "shorts-render-evidence-v1"
        or _missing_fields(render_evidence, required)
    ):
        errors.append({"code": "FAIL_G80_RENDER_EVIDENCE_SCHEMA"})
    if render_evidence.get("status") != "PASS":
        errors.append({"code": "FAIL_G80_RENDER_EVIDENCE_NOT_PASS"})
    if not render_evidence.get("ffprobe_verified"):
        errors.append({"code": "FAIL_G80_FFPROBE"})
    if not _is_sha256(render_evidence.get("rendered_mp4_sha256")):
        errors.append({"code": "FAIL_G80_NO_RENDERED_MP4"})
    render_path = _resolve_artifact_path(
        artifact_root,
        render_evidence.get("rendered_mp4_path"),
    )
    if render_path is None or not render_path.is_file():
        errors.append({"code": "FAIL_G80_RENDER_FILE_MISSING"})
    else:
        if (
            render_path.stat().st_size <= 0
            or render_path.stat().st_size != render_evidence.get("rendered_size_bytes")
            or _sha256_file(render_path) != render_evidence.get("rendered_mp4_sha256")
        ):
            errors.append({"code": "FAIL_G80_RENDER_FILE_INTEGRITY"})
        probe = _probe_media(render_path)
        if probe is None:
            errors.append({"code": "FAIL_G80_FFPROBE"})
        else:
            if not probe["has_video"] or render_evidence.get(
                "video_stream_present"
            ) is not True:
                errors.append({"code": "FAIL_G80_VIDEO_STREAM"})
            if not probe["has_audio"] or render_evidence.get(
                "audio_stream_present"
            ) is not True:
                errors.append({"code": "FAIL_G80_AUDIO_STREAM"})
            duration = render_evidence.get("duration_us")
            tolerance = render_evidence.get("duration_tolerance_us")
            if (
                not isinstance(duration, int)
                or not isinstance(tolerance, int)
                or tolerance < 0
                or abs(probe["duration_us"] - duration) > tolerance
            ):
                errors.append({"code": "FAIL_G80_RENDER_DURATION_MISMATCH"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G80",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G90" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g90(
    *,
    final_qc: dict,
    ledger_events: list[dict] | None = None,
    render_evidence: dict | None = None,
) -> dict:
    core = _import_core()
    errors = _ledger_validation_errors(core, ledger_events)
    if errors and errors[0].get("code") == "FAIL_LEDGER_REQUIRED":
        errors[0]["code"] = "FAIL_G90_LEDGER_REQUIRED"
    if (
        final_qc.get("schema_version") != "shorts-final-qc-v1"
        or not final_qc.get("episode_id")
    ):
        errors.append({"code": "FAIL_G90_FINAL_QC_SCHEMA"})
    if render_evidence is None or render_evidence.get("status") != "PASS":
        errors.append({"code": "FAIL_G90_G80_RENDER_EVIDENCE"})
    events = [
        event
        for event in (ledger_events or [])
        if isinstance(event, dict)
    ]
    has_g80_pass = any(
        event.get("event_type") == "GATE_PASSED"
        and event.get("gate") == "G80"
        and event.get("actor") == "VALIDATOR"
        for event in events
    )
    if not has_g80_pass:
        errors.append({"code": "FAIL_G90_G80_NOT_PASS"})
    has_final_qc_pass = any(
        event.get("event_type") == "FINAL_QC_PASS"
        and event.get("gate") == "G90"
        and event.get("actor") == "VALIDATOR"
        for event in events
    )
    has_upload_approved = any(
        event.get("event_type") == "UPLOAD_APPROVED"
        and event.get("gate") == "G90"
        and event.get("actor") == "USER"
        for event in events
    )
    if any(
        (
            event.get("event_type") == "FINAL_QC_PASS"
            and (
                event.get("gate") != "G90"
                or event.get("actor") != "VALIDATOR"
            )
        )
        or (
            event.get("event_type") == "UPLOAD_APPROVED"
            and (
                event.get("gate") != "G90"
                or event.get("actor") != "USER"
            )
        )
        for event in events
    ):
        errors.append({"code": "FAIL_G90_EVENT_AUTHORITY"})
    release_allowed = False
    if not errors:
        state = core.rebuild_state(events)
        release_allowed = state.get("release_allowed") is True
        if has_upload_approved and not release_allowed:
            errors.append({"code": "FAIL_G90_UPLOAD_BEFORE_FINAL_QC"})
    if not has_final_qc_pass and has_upload_approved:
        errors.append({"code": "FAIL_G90_UPLOAD_BEFORE_FINAL_QC"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G90",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action=(
            "EPISODE_RELEASED"
            if not errors and release_allowed
            else (
                "WAIT_UPLOAD_APPROVAL"
                if not errors and has_final_qc_pass
                else ("WAIT_USER_INPUT" if not errors else "NONE")
            )
        ),
        auto_advance_allowed=False,  # upload requires explicit user approval
        auto_advance_class="NONE",
        status=(
            "PASS"
            if not errors and release_allowed
            else (
                "WAIT_UPLOAD_APPROVAL"
                if not errors and has_final_qc_pass
                else ("WAIT_USER_INPUT" if not errors else None)
            )
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a 000short-production-agent gate (G30-G90)."
    )
    parser.add_argument(
        "--gate",
        required=True,
        choices=["G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"],
    )
    parser.add_argument("--audio-lock", type=Path)
    parser.add_argument("--caption-lock", type=Path)
    parser.add_argument("--track-plan", type=Path)
    parser.add_argument("--assembly-result", type=Path)
    parser.add_argument("--upload-package", type=Path)
    parser.add_argument("--render-evidence", type=Path)
    parser.add_argument("--final-qc", type=Path)
    parser.add_argument("--g30-audio-lock", type=Path, help="G40 input: G30 lock")
    parser.add_argument("--g40-caption-lock", type=Path, help="G50 input: G40 lock")
    parser.add_argument("--g50-track-plan", type=Path, help="G60 input: G50 plan")
    parser.add_argument("--g70-upload-package", type=Path, help="G80 input: G70 package")
    parser.add_argument("--owner-transfer-receipt", type=Path)
    parser.add_argument("--design-handoff", type=Path)
    parser.add_argument("--template-contract", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--episode-root", type=Path)
    args = parser.parse_args(argv)

    def _load(p: Path | None) -> dict:
        if p is None or not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def _load_ledger(p: Path | None) -> list[dict]:
        if p is None or not p.exists():
            return []
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".jsonl":
            return [
                json.loads(line)
                for line in text.splitlines()
                if line.strip()
            ]
        value = json.loads(text)
        return value if isinstance(value, list) else []

    artifact_root = args.episode_root.resolve() if args.episode_root else None
    ledger_events = _load_ledger(args.ledger)
    if args.gate == "G30":
        result = validate_g30(
            audio_lock=_load(args.audio_lock),
            owner_transfer_receipt=_load(args.owner_transfer_receipt) or None,
            design_handoff=_load(args.design_handoff) or None,
            design_handoff_path=args.design_handoff,
            artifact_root=artifact_root,
        )
    elif args.gate == "G40":
        result = validate_g40(
            caption_lock=_load(args.caption_lock),
            g30_audio_lock=_load(args.g30_audio_lock) or None,
            g30_audio_lock_path=args.g30_audio_lock,
            artifact_root=artifact_root,
        )
    elif args.gate == "G50":
        result = validate_g50(
            track_plan=_load(args.track_plan),
            g40_caption_lock=_load(args.g40_caption_lock) or None,
            g40_caption_lock_path=args.g40_caption_lock,
            design_handoff=_load(args.design_handoff) or None,
            design_handoff_path=args.design_handoff,
            artifact_root=artifact_root,
        )
    elif args.gate == "G60":
        template_path = args.template_contract or (
            REPO_ROOT
            / "manifests"
            / "capcut-template-contracts"
            / "shrt_white_base_v1.json"
        )
        result = validate_g60(
            assembly_result=_load(args.assembly_result),
            g50_track_plan=_load(args.g50_track_plan) or None,
            g50_track_plan_path=args.g50_track_plan,
            template_contract=_load(template_path) or None,
            template_contract_path=template_path,
        )
    elif args.gate == "G60.USER":
        result = validate_g60_user(ledger_events=ledger_events)
    elif args.gate == "G70":
        result = validate_g70(
            upload_package=_load(args.upload_package),
            ledger_events=ledger_events,
            artifact_root=artifact_root,
        )
    elif args.gate == "G80":
        result = validate_g80(
            render_evidence=_load(args.render_evidence),
            g70_upload_package=_load(args.g70_upload_package) or None,
            g70_upload_package_path=args.g70_upload_package,
            artifact_root=artifact_root,
        )
    elif args.gate == "G90":
        result = validate_g90(
            final_qc=_load(args.final_qc),
            ledger_events=ledger_events,
            render_evidence=_load(args.render_evidence) or None,
        )
    else:
        result = {"status": "FAIL", "errors": [{"code": "UNKNOWN_GATE"}]}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return (
        0
        if result["status"]
        in (
            "PASS",
            "NOT_REQUIRED",
            "WAIT_UPLOAD_APPROVAL",
            "WAIT_USER_VISUAL_GATE",
        )
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
