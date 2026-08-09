#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List
from track_contract import CANONICAL_TRACKS, TRACK_LAYOUT

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = SKILL_ROOT / "protocol.json"
ALLOWED_URAKKAI_AUDIO_POLICIES = [
    "A10_RETAINED_SYNC",
    "TTS_ONLY_MUTE_SOURCE",
    "A9_TTS_PLUS_A10_RETAINED",
]
A10_AUDIO_POLICIES = {"A10_RETAINED_SYNC", "A9_TTS_PLUS_A10_RETAINED"}


def _ranges_overlap(left: object, right: object) -> bool:
    return (
        isinstance(left, list) and len(left) == 2
        and isinstance(right, list) and len(right) == 2
        and all(isinstance(value, int) and not isinstance(value, bool) for value in left + right)
        and max(left[0], right[0]) < min(left[1], right[1])
    )


def _range_fully_covered(inner: object, outer: object) -> bool:
    return (
        isinstance(inner, list) and len(inner) == 2
        and isinstance(outer, list) and len(outer) == 2
        and outer[0] <= inner[0] and outer[1] >= inner[1]
    )


def read_json(path: Path) -> Dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def load_protocol(path: Path = DEFAULT_PROTOCOL) -> Dict[str, Any]:
    protocol = read_json(Path(path))
    errors = validate_protocol_document(protocol)
    if errors:
        raise ValueError("PROTOCOL_INVALID:" + ",".join(errors))
    return protocol


def validate_protocol_document(protocol: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if protocol.get("schema_version") != "001short-executable-protocol-v1":
        errors.append("PROTOCOL_SCHEMA_VERSION")
    if protocol.get("owner_skill") != "001short-production-agent":
        errors.append("PROTOCOL_OWNER_SKILL")
    if protocol.get("lane") != "general_shorts_production":
        errors.append("PROTOCOL_LANE")
    expected_tracks = list(CANONICAL_TRACKS)
    if protocol.get("track_layout") != TRACK_LAYOUT:
        errors.append("PROTOCOL_TRACK_LAYOUT")
    if protocol.get("canonical_tracks") != expected_tracks:
        errors.append("PROTOCOL_CANONICAL_TRACKS")
    if protocol.get("visual_asset_modes") != ["CLEAN_VISUAL_READY", "SOURCE_VIDEO_PROVISIONAL"]:
        errors.append("PROTOCOL_VISUAL_ASSET_MODES")
    if protocol.get("stage07_outputs") != ["audio_lock.json", "caption_lock.json", "final.srt"]:
        errors.append("PROTOCOL_STAGE07_OUTPUTS")
    if protocol.get("a12_policy") != "EMPTY":
        errors.append("PROTOCOL_A12_POLICY")
    if protocol.get("anchors", {}).get("A10") != "validated Demucs source vocal stem only":
        errors.append("PROTOCOL_A10_AUTHORITY")
    expected_manual_finalization = {
        "automation_terminal_state": "WAIT_USER_CAPCUT_CHECK",
        "clean_source_policy": {
            "primary": "AGENT_PRIMARY_CLEAN_SOURCE",
            "fallback": "USER_FALLBACK_CLEAN_SOURCE",
            "fallback_reasons": [
                "VMAKE_CURRENT_WORK_WINDOW_INCOMPLETE",
                "VMAKE_ACQUISITION_ISSUE",
                "VMAKE_VERIFICATION_ISSUE",
            ],
            "sequence": [
                "VMAKE_SUBMIT_FIRST",
                "SOURCE_VIDEO_PROVISIONAL_BUILD_NONBLOCKING",
                "VALIDATE_CLEAN_SOURCE_THEN_VIDEO_ONLY_SWAP_OR_REASSEMBLY",
            ],
        },
        "stage08_clean_swap_route": "scripts/build_episode_capcut.py --swap-provisional-video-only",
        "user_only_actions": [
            "capcut_visual_review_and_refinement",
            "render",
            "upload",
        ],
        "source_video_provisional_next_action": "CLEAN_SOURCE_SWAP_NONBLOCKING",
    }
    if protocol.get("manual_finalization") != expected_manual_finalization:
        errors.append("PROTOCOL_MANUAL_FINALIZATION_POLICY")

    session_handoff = protocol.get("session_handoff")
    expected_session_handoff = {
        "schema_version": "001short-session-handoff-v1",
        "owner_skill": "001short-production-agent",
        "lane": "general_shorts_production",
        "schema": "schemas/conversation_handoff.schema.json",
        "validator": "scripts/validate_conversation_handoff.py",
        "template": "templates/conversation-handoff.json",
        "env_file": "$HOME/.hermes/.env",
        "env_load": "SOURCE_ONCE_WITHOUT_OUTPUT",
        "resume_requires_episode_id_and_explicit_request": True,
        "old_episode_access_without_resume": "FORBIDDEN",
        "secret_material": "FORBIDDEN",
    }
    if not isinstance(session_handoff, dict):
        errors.append("PROTOCOL_SESSION_HANDOFF")
    else:
        for key, value in expected_session_handoff.items():
            if session_handoff.get(key) != value:
                errors.append(f"PROTOCOL_SESSION_HANDOFF_GATE:{key}")

    modes = protocol.get("production_modes")
    expected_modes = {"URAKKAI", "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY"}
    if not isinstance(modes, dict) or set(modes) != expected_modes:
        errors.append("PROTOCOL_MODES")
    else:
        urakkai = modes["URAKKAI"]
        clean_only = modes["SOURCE_ORDER_UNCHANGED_CLEAN_ONLY"]
        for key in ("meaningful_reorder_required", "fake_split_forbidden", "approved_final_order_required"):
            if urakkai.get(key) is not True:
                errors.append(f"PROTOCOL_URAKKAI_GATE_FALSE:{key}")
        if urakkai.get("allowed_audio_policies") != ALLOWED_URAKKAI_AUDIO_POLICIES:
            errors.append("PROTOCOL_URAKKAI_AUDIO_POLICIES_INVALID")
        if urakkai.get("minimum_video_segments", 0) < 2:
            errors.append("PROTOCOL_URAKKAI_MINIMUM_CUTS")
        expected_clean = {
            "explicit_exception_to_multi_cut_gate": True,
            "video_segments": 1,
            "original_audio_segments": 1,
            "video_duration": "FULL_LENGTH",
            "original_audio_duration": "FULL_LENGTH",
            "source_order_change": "FORBIDDEN",
        }
        for key, value in expected_clean.items():
            if clean_only.get(key) != value:
                errors.append(f"PROTOCOL_CLEAN_ONLY_GATE:{key}")

    review = protocol.get("urakkai_review_loop")
    if not isinstance(review, dict):
        errors.append("PROTOCOL_URAKKAI_REVIEW_LOOP")
    else:
        expected_review = {
            "enabled_for": ["URAKKAI"],
            "preferred_provider": "claude_cli",
            "preferred_model": "Claude Opus 5",
            "effort": "low",
            "reviews_per_loop": 1,
            "review_runner": "current_local_runtime",
            "approval_authority": "user",
            "fallback_provider": "codex_cli",
            "fallback_model": "gpt-5.6-sol",
            "fallback_effort": "low",
            "fallback_on_claude_failure": True,
            "evidence_path": "20_script/external-review.json",
        }
        if review.get("review_loop_count") != 1:
            errors.append("PROTOCOL_URAKKAI_REVIEW_LOOP_COUNT")
        for key, value in expected_review.items():
            if review.get(key) != value:
                errors.append(f"PROTOCOL_URAKKAI_REVIEW_GATE:{key}")

    stages = protocol.get("stages")
    expected_stages = [f"{number:02d}" for number in range(1, 10)]
    observed_stages = [stage.get("id") for stage in stages] if isinstance(stages, list) else []
    if observed_stages != expected_stages:
        errors.append("PROTOCOL_STAGE_ORDER")
    elif stages[6].get("requires_state") != "FINAL_DESIGN_LOCKED_OR_CLEAN_VISUAL_READY":
        errors.append("PROTOCOL_SOURCE_PROVISIONAL_AUDIO_GATE")
    elif stages[6].get("produces") != [
        "30_audio_srt/audio_lock.json", "30_audio_srt/caption_lock.json", "30_audio_srt/final.srt"
    ]:
        errors.append("PROTOCOL_STAGE07_OUTPUTS")
    elif stages[7].get("requires_state") != "AUDIO_CAPTION_VALIDATED_WITH_CLEAN_OR_SOURCE_VIDEO_PROVISIONAL":
        errors.append("PROTOCOL_SOURCE_PROVISIONAL_CAPCUT_GATE")
    elif stages[8].get("produces") != [] or "validators" in stages[8]:
        errors.append("PROTOCOL_STAGE09_MANUAL_TERMINAL")

    completion = protocol.get("completion_report")
    required_completion = [
        "episode_id",
        "capcut_project_name",
        "production_mode",
        "T1",
        "T2",
        "validation_status",
        "source_file_evidence",
        "vmake_final_download",
        "capcut_visual_confirmation",
        "completion_claim",
        "upload_title",
        "upload_description",
        "sources",
        "public_upload_status",
    ]
    if not isinstance(completion, dict) or completion.get("required_fields") != required_completion:
        errors.append("PROTOCOL_COMPLETION_FIELDS")
    expected_cloud_row_fields = ["name", "size", "duration", "type", "modified_time"]
    expected_cloud_sync = {
        "default_status": "NOT_REQUESTED",
        "requires_explicit_user_request": True,
        "destination_must_be_explicit": True,
        "forbid_preemptive_sync": True,
        "synced_status": "SYNCED",
    }
    if (
        not isinstance(completion, dict)
        or completion.get("cloud_sync_row_required_fields") != expected_cloud_row_fields
        or completion.get("capcut_cloud_sync") != expected_cloud_sync
    ):
        errors.append("PROTOCOL_CLOUD_SYNC_POLICY")

    invariants = protocol.get("invariants")
    required_invariants = (
        "session_handoff_secret_material_forbidden",
        "session_handoff_owner_must_remain_001",
        "old_episode_access_requires_explicit_resume",
        "state_advance_after_validator_pass_only",
        "vmake_dom_first",
        "vmake_submit_after_source_identity",
        "vmake_candidate_integrity_only",
        "vmake_visual_quality_authority_user",
        "vmake_nonblocking_source_provisional_allowed",
        "source_provisional_report_required",
        "vmake_full_download_required",
        "vmake_direct_insert_required",
        "urakkai_final_duration_independent_from_source",
        "clean_visual_duration_matches_source_before_edit",
        "clean_only_full_source_duration_required",
        "source_file_evidence_required",
        "vmake_final_download_evidence_required",
        "vmake_substitute_file_forbidden",
        "capcut_visual_confirmation_required_before_completion",
        "source_audio_vocal_stem_required_when_retained",
        "capcut_vocal_retain_metadata_not_audio_separation",
        "capcut_root_immutable",
        "capcut_project_media_internal",
        "capcut_cloud_sync_explicit_request_required",
        "capcut_cloud_destination_explicit_request_required",
        "capcut_cloud_row_readback_required_when_requested",
        "capcut_cloud_reopen_playback_required_when_requested",
        "public_upload_requires_explicit_approval",
        "completion_report_requires_upload_metadata",
    )
    if not isinstance(invariants, dict):
        errors.append("PROTOCOL_INVARIANTS")
    else:
        for key in required_invariants:
            if invariants.get(key) is not True:
                errors.append(f"PROTOCOL_INVARIANT_FALSE:{key}")
        if invariants.get("vmake_direct_insert_asset") != "40_assets_used/clean_source.mp4":
            errors.append("PROTOCOL_VMAKE_DIRECT_INSERT_ASSET")
        if invariants.get("vmake_direct_insert_asset_key") != "clean_video":
            errors.append("PROTOCOL_VMAKE_DIRECT_INSERT_ASSET_KEY")
        if invariants.get("source_provisional_video_asset_key") != "source_video":
            errors.append("PROTOCOL_SOURCE_PROVISIONAL_ASSET_KEY")
    return errors


def validate_skill_contract(skill_root: Path, protocol: Dict[str, Any]) -> List[str]:
    root = Path(skill_root)
    errors: List[str] = []
    authority = protocol.get("authority", {})
    schemas = protocol.get("schemas", {})
    session_handoff = protocol.get("session_handoff", {})
    required_paths = [
        authority.get("policy"),
        authority.get("machine_contract"),
        authority.get("state_machine"),
        authority.get("enforcement"),
        schemas.get("protocol"),
        schemas.get("production_plan"),
        schemas.get("completion_report"),
        schemas.get("session_handoff"),
        schemas.get("vocal_stem_manifest"),
        schemas.get("source_intake_receipt"),
        session_handoff.get("validator"),
        session_handoff.get("template"),
        "scripts/validate_source_intake.py",
        "references/production-orchestrator.md",
        "tools.json",
    ]
    for relative in required_paths:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            errors.append(f"PROTOCOL_PATH_INVALID:{relative}")
            continue
        path = root / relative
        if not path.is_file():
            errors.append(f"PROTOCOL_REQUIRED_FILE_MISSING:{relative}")

    for relative in [
        authority.get("machine_contract"),
        authority.get("state_machine"),
        schemas.get("protocol"),
        schemas.get("production_plan"),
        schemas.get("completion_report"),
        schemas.get("session_handoff"),
        schemas.get("vocal_stem_manifest"),
        schemas.get("source_intake_receipt"),
        "tools.json",
    ]:
        if isinstance(relative, str) and (root / relative).is_file():
            try:
                json.loads((root / relative).read_text(encoding="utf-8"))
            except Exception:
                errors.append(f"PROTOCOL_JSON_INVALID:{relative}")

    skill_path = root / str(authority.get("policy", "SKILL.md"))
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8")
        for token in [
            "references/production-orchestrator.md",
            "STOP_PROTOCOL_CONFLICT",
            "## New Session Handoff Bootstrap",
            "scripts/validate_conversation_handoff.py",
            "HANDOFF_SECRET_MATERIAL_FORBIDDEN",
        ]:
            if token not in skill_text:
                errors.append(f"PROTOCOL_SKILL_TOKEN_MISSING:{token}")

    orchestrator_path = root / "references/production-orchestrator.md"
    if orchestrator_path.is_file():
        orchestrator_text = orchestrator_path.read_text(encoding="utf-8")
        for token in [
            "0000shrt",
            "scripts/validate_source_intake.py",
            "GOOGLE_DRIVE",
            "URL",
            "DESKTOP",
            "A11=SFX",
            "A12=EMPTY",
        ]:
            if token not in orchestrator_text:
                errors.append(f"PROTOCOL_ORCHESTRATOR_TOKEN_MISSING:{token}")

    workflow_path = root / str(authority.get("state_machine", "workflow.json"))
    if workflow_path.is_file():
        try:
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
            executable = workflow.get("executable_protocol", {})
            if executable.get("path") != authority.get("machine_contract"):
                errors.append("PROTOCOL_WORKFLOW_PATH_MISMATCH")
            if executable.get("validator") != authority.get("enforcement"):
                errors.append("PROTOCOL_WORKFLOW_VALIDATOR_MISMATCH")
            if authority.get("machine_contract") not in workflow.get("common", []):
                errors.append("PROTOCOL_WORKFLOW_COMMON_MISSING")
            if workflow.get("completion_gate", {}).get("required_fields") != protocol.get("completion_report", {}).get("required_fields"):
                errors.append("PROTOCOL_WORKFLOW_COMPLETION_FIELDS_MISMATCH")
            if workflow.get("completion_gate", {}).get("validator_pass_required") is not True:
                errors.append("PROTOCOL_WORKFLOW_COMPLETION_GATE_DISABLED")
            if workflow.get("manual_finalization") != protocol.get("manual_finalization"):
                errors.append("PROTOCOL_WORKFLOW_MANUAL_FINALIZATION_MISMATCH")
            stage09 = workflow.get("parallel_execution", {}).get("stage09", {})
            if stage09.get("sequence") != ["WAIT_USER_CAPCUT_CHECK"]:
                errors.append("PROTOCOL_WORKFLOW_STAGE09_AUTOMATION_NOT_STOPPED")
            stages = {row.get("id"): row for row in workflow.get("production_stages", []) if isinstance(row, dict)}
            if stages.get("09", {}).get("pass") != "WAIT_USER_CAPCUT_CHECK":
                errors.append("PROTOCOL_WORKFLOW_STAGE09_MANUAL_WAIT_MISSING")
            if workflow.get("validation", {}).get("checks", {}).get("09") != {
                "reference": "references/checks/render.md", "manual_only": True,
            }:
                errors.append("PROTOCOL_WORKFLOW_STAGE09_MANUAL_ROUTER_MISSING")
            bootstrap = workflow.get("session_bootstrap", {})
            if bootstrap.get("env_file") != session_handoff.get("env_file"):
                errors.append("PROTOCOL_WORKFLOW_HANDOFF_ENV_MISMATCH")
            if bootstrap.get("validator") != session_handoff.get("validator"):
                errors.append("PROTOCOL_WORKFLOW_HANDOFF_VALIDATOR_MISMATCH")
            if bootstrap.get("resume_requires_episode_id_and_explicit_request") is not True:
                errors.append("PROTOCOL_WORKFLOW_HANDOFF_RESUME_GATE_DISABLED")
            if workflow.get("blueprint_frontend", {}).get("assembly", {}).get("a10_authority") != "validated_demucs_source_vocal_stem":
                errors.append("PROTOCOL_WORKFLOW_A10_AUTHORITY_MISMATCH")
            interim = workflow.get("interim_capcut", {})
            if interim.get("a10_anchor") != "A10_VALIDATED_DEMUCS_VOCAL_STEM":
                errors.append("PROTOCOL_WORKFLOW_A10_ANCHOR_MISMATCH")
        except Exception:
            pass

    tools_path = root / "tools.json"
    if tools_path.is_file():
        try:
            tools = json.loads(tools_path.read_text(encoding="utf-8"))
            executable = tools.get("executable_protocol", {})
            if executable.get("file") != authority.get("machine_contract"):
                errors.append("PROTOCOL_TOOLS_PATH_MISMATCH")
            if executable.get("validator") != authority.get("enforcement"):
                errors.append("PROTOCOL_TOOLS_VALIDATOR_MISMATCH")
            if executable.get("completion_report") != "{episode_root}/90_reports/completion_report.json":
                errors.append("PROTOCOL_TOOLS_COMPLETION_PATH_MISMATCH")
            handoff_tool = tools.get("session_handoff", {})
            if handoff_tool.get("schema") != session_handoff.get("schema"):
                errors.append("PROTOCOL_TOOLS_HANDOFF_SCHEMA_MISMATCH")
            if handoff_tool.get("validator") != session_handoff.get("validator"):
                errors.append("PROTOCOL_TOOLS_HANDOFF_VALIDATOR_MISMATCH")
            if handoff_tool.get("env_file") != session_handoff.get("env_file"):
                errors.append("PROTOCOL_TOOLS_HANDOFF_ENV_MISMATCH")
            mapping = tools.get("capcut_preflight", {}).get("track_mapping", {})
            if mapping.get("profile") != TRACK_LAYOUT:
                errors.append("PROTOCOL_TOOLS_TRACK_LAYOUT_MISMATCH")
            if mapping.get("required") != list(CANONICAL_TRACKS):
                errors.append("PROTOCOL_TOOLS_TRACKS_MISMATCH")
            production_ids = [row.get("id") for row in tools.get("production_tools", []) if isinstance(row, dict)]
            if production_ids != list(CANONICAL_TRACKS):
                errors.append("PROTOCOL_TOOLS_PRODUCTION_TRACKS_MISMATCH")
            if tools.get("root_profiles") != ["home_windows", "macmini"]:
                errors.append("PROTOCOL_TOOLS_ROOT_PROFILES_MISMATCH")
            if tools.get("template_profile") != "shrt_white_base_v2":
                errors.append("PROTOCOL_TOOLS_TEMPLATE_PROFILE_MISMATCH")
        except Exception:
            pass
    return errors


def _segments(tracks: Any, role: str) -> List[Dict[str, Any]]:
    if not isinstance(tracks, dict):
        return []
    value = tracks.get(role, [])
    return value if isinstance(value, list) else []


def _full_range(segment: Dict[str, Any], duration: int) -> bool:
    expected = [0, duration]
    return segment.get("source_range_us") == expected and segment.get("target_range_us") == expected


def _effective_video_groups(video: List[Dict[str, Any]]) -> int:
    ordered = sorted(video, key=lambda row: (row.get("target_range_us") or [0, 0])[0])
    groups = 0
    previous: Dict[str, Any] | None = None
    for segment in ordered:
        if previous is None:
            groups += 1
        else:
            previous_source = previous.get("source_range_us")
            current_source = segment.get("source_range_us")
            previous_target = previous.get("target_range_us")
            current_target = segment.get("target_range_us")
            source_contiguous = (
                isinstance(previous_source, list) and len(previous_source) == 2
                and isinstance(current_source, list) and len(current_source) == 2
                and previous_source[1] == current_source[0]
            )
            target_contiguous = (
                isinstance(previous_target, list) and len(previous_target) == 2
                and isinstance(current_target, list) and len(current_target) == 2
                and previous_target[1] == current_target[0]
            )
            same_asset = previous.get("asset_key") == segment.get("asset_key")
            same_speed = previous.get("speed", 1) == segment.get("speed", 1)
            if not (source_contiguous and target_contiguous and same_asset and same_speed):
                groups += 1
        previous = segment
    return groups


def _normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    direct_tracks = plan.get("tracks")
    if isinstance(direct_tracks, dict):
        return {
            "layout": "tracks",
            "tracks": direct_tracks,
            "original_order": plan.get("original_order"),
            "final_order": plan.get("final_order"),
            "declared_empty": {role for role, segments in direct_tracks.items() if isinstance(segments, list) and not segments},
            "errors": [],
        }

    timeline = plan.get("timeline")
    errors: List[str] = []
    if not isinstance(timeline, list) or not timeline:
        return {
            "layout": "invalid",
            "tracks": {},
            "original_order": plan.get("original_order"),
            "final_order": plan.get("final_order"),
            "declared_empty": set(),
            "errors": ["PRODUCTION_PLAN_LAYOUT_INVALID"],
        }

    tracks: Dict[str, List[Dict[str, Any]]] = {}
    observed_order: List[Any] = []
    for row_index, row in enumerate(timeline):
        if not isinstance(row, dict):
            errors.append(f"TIMELINE_ROW_INVALID:{row_index}")
            continue
        observed_order.append(row.get("segment_key"))
        row_range = row.get("target_range_us")
        placements = row.get("placements")
        if not isinstance(placements, list):
            errors.append(f"TIMELINE_PLACEMENTS_INVALID:{row_index}")
            continue
        for placement_index, placement in enumerate(placements):
            if not isinstance(placement, dict):
                errors.append(f"TIMELINE_PLACEMENT_INVALID:{row_index}:{placement_index}")
                continue
            anchor = placement.get("anchor")
            if not isinstance(anchor, str) or not anchor:
                errors.append(f"TIMELINE_ANCHOR_MISSING:{row_index}:{placement_index}")
                continue
            if row_range is not None and placement.get("target_range_us") != row_range:
                errors.append(f"TIMELINE_TARGET_RANGE_MISMATCH:{row_index}:{anchor}")
            tracks.setdefault(anchor, []).append(placement)

    signature = plan.get("order_signature")
    final_order = signature if isinstance(signature, list) and signature else observed_order
    if isinstance(signature, list) and signature != observed_order:
        errors.append("TIMELINE_ORDER_SIGNATURE_MISMATCH")
    original_order = plan.get("original_order")
    locks = plan.get("locks")
    if (
        plan.get("production_mode") == "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY"
        and (not isinstance(original_order, list) or not original_order)
        and isinstance(locks, dict)
        and locks.get("source_order_unchanged") is True
    ):
        original_order = list(final_order)

    cleared = plan.get("cleared_anchors")
    declared_empty = set(cleared) if isinstance(cleared, list) else set()
    for role in declared_empty:
        tracks.setdefault(role, [])
    return {
        "layout": "timeline",
        "tracks": tracks,
        "original_order": original_order,
        "final_order": final_order,
        "declared_empty": declared_empty,
        "errors": errors,
    }


def validate_production_plan(plan: Dict[str, Any], protocol: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(plan, dict):
        return ["PRODUCTION_PLAN_OBJECT_REQUIRED"]

    mode = plan.get("production_mode")
    modes = protocol.get("production_modes", {})
    if mode not in modes:
        return ["PRODUCTION_MODE_INVALID"]

    duration = plan.get("total_duration_us")
    if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
        errors.append("PRODUCTION_DURATION_INVALID")
        duration = 0

    view = _normalize_plan(plan)
    errors.extend(view["errors"])
    tracks = view["tracks"]
    original_order = view["original_order"]
    final_order = view["final_order"]
    if not isinstance(original_order, list) or not original_order:
        errors.append("ORIGINAL_ORDER_MISSING")
    if not isinstance(final_order, list) or not final_order:
        errors.append("FINAL_ORDER_MISSING")

    video = _segments(tracks, "VIDEO")
    audio = _segments(tracks, "A10")
    tts = _segments(tracks, "A9")
    if _segments(tracks, "A12"):
        errors.append("A12_RESERVED_EMPTY")

    invariants = protocol.get("invariants", {})
    if isinstance(invariants, dict) and invariants.get("vmake_direct_insert_required") is True:
        visual_mode = plan.get("visual_asset_mode", "CLEAN_VISUAL_READY")
        if visual_mode == "SOURCE_VIDEO_PROVISIONAL":
            expected_asset_key = invariants.get("source_provisional_video_asset_key", "source_video")
            error_prefix = "SOURCE_PROVISIONAL_ASSET_INVALID"
        elif visual_mode == "CLEAN_VISUAL_READY":
            expected_asset_key = invariants.get("vmake_direct_insert_asset_key", "clean_video")
            error_prefix = "VMAKE_DIRECT_INSERT_ASSET_INVALID"
        else:
            errors.append(f"VISUAL_ASSET_MODE_INVALID:{visual_mode}")
            expected_asset_key = None
            error_prefix = "VMAKE_DIRECT_INSERT_ASSET_INVALID"
        for segment in video:
            if expected_asset_key is not None and segment.get("asset_key") != expected_asset_key:
                errors.append(f"{error_prefix}:{segment.get('asset_key')}")
                break

    if mode == "URAKKAI":
        config = modes[mode]
        if isinstance(original_order, list) and original_order == final_order:
            errors.append(config.get("unchanged_error", "URAKKAI_STRUCTURE_UNCHANGED"))
        minimum = config.get("minimum_video_segments", 2)
        if len(video) < minimum:
            errors.append("URAKKAI_VIDEO_SEGMENT_COUNT")
        if config.get("fake_split_forbidden") and _effective_video_groups(video) < minimum:
            errors.append("URAKKAI_FAKE_SPLIT")
        audio_policy = plan.get("audio_policy", "A10_RETAINED_SYNC")
        if audio_policy not in config.get("allowed_audio_policies", []):
            errors.append("URAKKAI_AUDIO_POLICY_INVALID")
            return errors
        if audio_policy in A10_AUDIO_POLICIES:
            if config.get("video_audio_mapping_must_match") and len(video) != len(audio):
                errors.append("URAKKAI_VIDEO_AUDIO_COUNT_MISMATCH")
            audio_by_target: Dict[tuple, List[Dict[str, Any]]] = {}
            for segment in audio:
                target = segment.get("target_range_us")
                if isinstance(target, list) and len(target) == 2:
                    audio_by_target.setdefault(tuple(target), []).append(segment)
            for segment in video:
                target = segment.get("target_range_us")
                matches = audio_by_target.get(tuple(target), []) if isinstance(target, list) else []
                if len(matches) != 1 or matches[0].get("source_range_us") != segment.get("source_range_us"):
                    errors.append("URAKKAI_AUDIO_VIDEO_MAPPING_MISMATCH")
                    break
            if audio_policy == "A9_TTS_PLUS_A10_RETAINED" and not tts:
                errors.append("URAKKAI_MIXED_A9_REQUIRED")
            if audio_policy == "A9_TTS_PLUS_A10_RETAINED":
                if _segments(tracks, "A11"):
                    errors.append("URAKKAI_MIXED_A11_FORBIDDEN")
                for retained in audio:
                    overlapping_tts = [
                        narration for narration in tts
                        if _ranges_overlap(
                            retained.get("target_range_us"),
                            narration.get("target_range_us"),
                        )
                    ]
                    if any(
                        not _range_fully_covered(
                            retained.get("target_range_us"),
                            narration.get("target_range_us"),
                        )
                        for narration in overlapping_tts
                    ):
                        errors.append("URAKKAI_MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED")
                        break
                    if overlapping_tts and retained.get("volume") != 0:
                        errors.append("URAKKAI_MIXED_A10_NOT_MUTED_UNDER_A9")
                        break
                    if not overlapping_tts and retained.get("volume") != 1:
                        errors.append("URAKKAI_MIXED_A10_NOT_RESTORED_OUTSIDE_A9")
                        break
        else:
            if audio:
                errors.append("URAKKAI_TTS_ONLY_A10_FORBIDDEN")
            if any(segment.get("volume") != 0 for segment in video):
                errors.append("URAKKAI_TTS_ONLY_VIDEO_NOT_MUTED")
            if not tts:
                errors.append("URAKKAI_TTS_ONLY_A9_REQUIRED")
            if _segments(tracks, "A11") or _segments(tracks, "A12"):
                errors.append("URAKKAI_TTS_ONLY_FORBIDDEN_AUDIO_PRESENT")
            cleared = set(plan.get("cleared_anchors", []))
            if not {"A10", "A11", "A12"}.issubset(cleared):
                errors.append("URAKKAI_TTS_ONLY_CLEAR_ANCHOR_MISSING")
        return errors

    config = modes[mode]
    if isinstance(original_order, list) and isinstance(final_order, list) and original_order != final_order:
        errors.append("CLEAN_ONLY_SOURCE_ORDER_CHANGED")
    if len(video) != config.get("video_segments", 1):
        errors.append("CLEAN_ONLY_VIDEO_COUNT")
    if len(audio) != config.get("original_audio_segments", 1):
        errors.append("CLEAN_ONLY_AUDIO_COUNT")

    if len(video) == 1:
        if not _full_range(video[0], duration):
            errors.append("CLEAN_ONLY_VIDEO_RANGE")
        if video[0].get("volume") != config.get("video_volume", 0):
            errors.append("CLEAN_ONLY_VIDEO_VOLUME")
    if len(audio) == 1:
        if not _full_range(audio[0], duration):
            errors.append("CLEAN_ONLY_AUDIO_RANGE")
        if audio[0].get("volume") != config.get("original_audio_volume", 1):
            errors.append("CLEAN_ONLY_AUDIO_VOLUME")

    for title_role in config.get("required_title_tracks", []):
        title_segments = _segments(tracks, title_role)
        if len(title_segments) != 1 or not str(title_segments[0].get("text", "")).strip():
            errors.append(f"CLEAN_ONLY_TITLE_INVALID:{title_role}")

    for role in config.get("must_clear_tracks", []):
        if role not in tracks:
            errors.append(f"CLEAN_ONLY_TRACK_MISSING:{role}")
        elif _segments(tracks, role):
            errors.append(f"CLEAN_ONLY_FORBIDDEN_TRACK_NOT_EMPTY:{role}")
    return errors


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_evidence_path(raw: Any, report_path: Path | None) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute() and report_path is not None:
        path = report_path.resolve().parent / path
    return path.resolve()


def _probe_duration_seconds(path: Path) -> float | None:
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        value = float(completed.stdout.strip())
        return value if value > 0 else None
    except (OSError, ValueError):
        return None


def _file_evidence_matches(
    evidence: Any,
    *,
    path_field: str,
    sha_field: str,
    report_path: Path | None,
    size_field: str | None = None,
    duration_field: str | None = None,
) -> tuple[bool, Path | None, float | None]:
    if not isinstance(evidence, dict):
        return False, None, None
    path = _resolve_evidence_path(evidence.get(path_field), report_path)
    if path is None or not path.is_file() or path.is_symlink():
        return False, path, None
    declared_sha = evidence.get(sha_field)
    if not isinstance(declared_sha, str) or _sha256_file(path).lower() != declared_sha.lower():
        return False, path, None
    if size_field is not None and evidence.get(size_field) != path.stat().st_size:
        return False, path, None
    measured_duration = None
    if duration_field is not None:
        declared_duration = evidence.get(duration_field)
        measured_duration = _probe_duration_seconds(path)
        if (
            not isinstance(declared_duration, (int, float))
            or isinstance(declared_duration, bool)
            or declared_duration <= 0
            or measured_duration is None
            or abs(float(declared_duration) - measured_duration) > 0.1
        ):
            return False, path, measured_duration
    return True, path, measured_duration


def validate_completion_report(
    report: Dict[str, Any], protocol: Dict[str, Any], report_path: Path | None = None
) -> List[str]:
    if not isinstance(report, dict):
        return ["COMPLETION_REPORT_OBJECT_REQUIRED"]
    config = protocol["completion_report"]
    prefix = config.get("missing_error_prefix", "UPLOAD_METADATA_MISSING")
    errors: List[str] = []
    evidence_missing = {
        "source_file_evidence": "SOURCE_FILE_EVIDENCE_MISSING",
        "vmake_final_download": "VMAKE_FINAL_DOWNLOAD_EVIDENCE_MISSING",
        "capcut_visual_confirmation": "CAPCUT_VISUAL_CONFIRMATION_MISSING",
    }
    for field in config["required_fields"]:
        if _missing(report.get(field)):
            errors.append(evidence_missing.get(field, f"{prefix}:{field}"))

    sources = report.get("sources")
    if isinstance(sources, list) and sources:
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"SOURCE_CREDIT_INVALID:{index}")
                continue
            for field in config.get("source_required_fields", []):
                if _missing(source.get(field)):
                    errors.append(f"SOURCE_CREDIT_MISSING:{index}:{field}")

    cloud_row = report.get("capcut_cloud_row")
    if isinstance(cloud_row, dict):
        for field in config.get("cloud_row_required_fields", []):
            if _missing(cloud_row.get(field)):
                errors.append(f"CAPCUT_CLOUD_ROW_MISSING:{field}")

    source_evidence = report.get("source_file_evidence")
    if isinstance(source_evidence, dict):
        required = config.get("source_file_evidence_required_fields", [])
        valid, _, measured = _file_evidence_matches(
            source_evidence, path_field="local_path", sha_field="sha256",
            report_path=report_path, duration_field="duration",
        )
        ranges = source_evidence.get("approved_source_time_ranges")
        range_limit = round(measured * 1_000_000) + 100_000 if measured is not None else 0
        ranges_valid = isinstance(ranges, list) and bool(ranges)
        if ranges_valid:
            for item in ranges:
                if (
                    not isinstance(item, list) or len(item) != 2
                    or any(not isinstance(value, int) or isinstance(value, bool) for value in item)
                    or item[0] < 0 or item[1] <= item[0] or item[1] > range_limit
                ):
                    ranges_valid = False
                    break
        if any(_missing(source_evidence.get(field)) for field in required) or not valid or not ranges_valid:
            errors.append("SOURCE_FILE_EVIDENCE_INVALID")

    vmake = report.get("vmake_final_download")
    if isinstance(vmake, dict):
        required = config.get("vmake_final_download_required_fields", [])
        valid, _, _ = _file_evidence_matches(
            vmake, path_field="downloaded_file_path", sha_field="sha256",
            report_path=report_path, size_field="size_bytes", duration_field="duration",
        )
        if (
            any(_missing(vmake.get(field)) for field in required)
            or vmake.get("is_actual_vmake_final_download") is not True
            or not valid
            or (
                isinstance(source_evidence, dict)
                and isinstance(source_evidence.get("sha256"), str)
                and str(vmake.get("sha256", "")).lower() == source_evidence["sha256"].lower()
            )
        ):
            errors.append("VMAKE_FINAL_DOWNLOAD_EVIDENCE_INVALID")

    visual = report.get("capcut_visual_confirmation")
    if isinstance(visual, dict):
        required = config.get("capcut_visual_confirmation_required_fields", [])
        screen_ok, _, _ = _file_evidence_matches(
            visual, path_field="screen_evidence_path", sha_field="screen_evidence_sha256",
            report_path=report_path,
        )
        draft = visual.get("draft_readback")
        draft_ok, _, _ = _file_evidence_matches(
            draft, path_field="local_path", sha_field="sha256", report_path=report_path,
        )
        if (
            any(_missing(visual.get(field)) for field in required)
            or visual.get("actual_project_name") != report.get("capcut_project_name")
            or visual.get("screen_confirmation_status") != "PASS"
            or not screen_ok or not draft_ok
            or not isinstance(draft, dict)
            or visual.get("final_project_hash", "").lower() != str(draft.get("sha256", "")).lower()
        ):
            errors.append("CAPCUT_VISUAL_CONFIRMATION_INVALID")

    claim = report.get("completion_claim")
    if claim in config.get("render_claim_values", []):
        render = report.get("render_evidence")
        if not isinstance(render, dict):
            errors.append("RENDER_EVIDENCE_MISSING")
        else:
            valid, _, _ = _file_evidence_matches(
                render, path_field="mp4_path", sha_field="mp4_sha256",
                report_path=report_path, size_field="size_bytes", duration_field="duration",
            )
            if any(_missing(render.get(field)) for field in config.get("render_evidence_required_fields", [])) or not valid:
                errors.append("RENDER_EVIDENCE_INVALID")

    sync = config.get("capcut_cloud_sync", {})
    sync_status = report.get("capcut_cloud_sync_status", sync.get("default_status", "NOT_REQUESTED"))
    if sync_status not in {sync.get("default_status"), sync.get("synced_status")}:
        errors.append("CAPCUT_CLOUD_SYNC_STATUS_INVALID")
    elif sync_status == sync.get("synced_status"):
        if report.get("capcut_cloud_sync_requested") is not True:
            errors.append("CAPCUT_CLOUD_SYNC_EXPLICIT_REQUEST_REQUIRED")
        if _missing(report.get("capcut_cloud_destination")):
            errors.append("CAPCUT_CLOUD_DESTINATION_MISSING")
        row = report.get("capcut_cloud_row")
        if not isinstance(row, dict) or any(_missing(row.get(field)) for field in config.get("cloud_sync_row_required_fields", [])):
            errors.append("CAPCUT_CLOUD_ROW_MISSING")
    elif "capcut_cloud_sync_requested" in report:
        errors.append("CAPCUT_CLOUD_SYNC_UNREQUESTED")

    status = report.get("public_upload_status")
    if status in config.get("public_upload_done_values", []):
        approval_field = config.get("public_upload_approval_field", "public_upload_approval")
        if report.get(approval_field) is not True:
            errors.append("PUBLIC_UPLOAD_NOT_APPROVED")
    return errors


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the 001short executable protocol, episode plan, and completion report.")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--completion-report", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    try:
        raw_protocol = read_json(args.protocol)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "errors": [f"PROTOCOL_READ:{exc}"]}, ensure_ascii=False, indent=2))
        return 1

    errors = validate_protocol_document(raw_protocol)
    errors.extend(validate_skill_contract(args.protocol.resolve().parent, raw_protocol))
    checked = ["protocol", "skill_contract"]
    if args.plan:
        checked.append("production_plan")
        try:
            errors.extend(validate_production_plan(read_json(args.plan), raw_protocol))
        except Exception as exc:
            errors.append(f"PRODUCTION_PLAN_READ:{exc}")
    if args.completion_report:
        checked.append("completion_report")
        try:
            errors.extend(validate_completion_report(read_json(args.completion_report), raw_protocol, args.completion_report))
        except Exception as exc:
            errors.append(f"COMPLETION_REPORT_READ:{exc}")
    if not (args.self_check or args.plan or args.completion_report):
        errors.append("VALIDATION_TARGET_REQUIRED")

    result = {"status": "PASS" if not errors else "FAIL", "checked": checked, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
