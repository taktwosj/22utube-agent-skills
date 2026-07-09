#!/usr/bin/env python3
"""Validate 00-tikitaka v3 handoff inputs before Stage 2 CapCut work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


REQUIRED_SEGMENT_FIELDS = {
    "edit_id",
    "source_ref",
    "source_order",
    "timeline_order",
    "assembly_role",
    "caption_type",
    "visible_text_role",
    "audio_role",
    "time_start",
    "time_end",
    "track",
    "duration_basis",
    "duration_status",
    "audio_policy",
    "visual_strategy",
}
ALLOWED_ASSEMBLY_ROLES = {
    "intro_narration",
    "context_narration",
    "payoff_narration",
    "ending_narration",
    "verified_speaker_quote",
    "situation_caption",
    "reaction_caption",
    "card_or_comment_caption",
    "source_visual_hold",
    "source_visual_action",
    "transition_or_separator",
    "ranking_item",
}
ALLOWED_DURATION_BASIS = {
    "source_range",
    "estimated_tts_duration",
    "actual_tts_duration",
    "fixed_design_duration",
    "visual_hold",
}
ALLOWED_DURATION_STATUS = {
    "SOURCE_AUDIO_LOCKED",
    "ESTIMATED_ACCEPTED",
    "ACTUAL_AUDIO_LOCKED",
    "FIXED_DESIGN_LOCKED",
    "WAIT_ACTUAL_TTS_AUDIO",
}
NARRATION_AUDIO_TTS_STATUSES = {
    "ESTIMATED_ACCEPTED",
    "ACTUAL_AUDIO_LOCKED",
    "WAIT_ACTUAL_TTS_AUDIO",
}
READY_TTS_TIMING_STATUSES = {
    "ESTIMATED_ACCEPTED",
    "ACTUAL_AUDIO_LOCKED",
}
ALLOWED_RECONCILIATION_ACTIONS = {
    "",
    "none",
    "extend_slot",
    "retime_segment",
    "split_segment",
    "shorten_text",
    "manual_acceptance",
}
SEMANTIC_AUDIO_TRACKS = {
    "audio.narration_tts",
    "audio.speaker_source",
    "audio.sfx",
    "audio.bgm",
}
FORBIDDEN_STAGE1_CAPCUT_AUDIO_TRACKS = {"A9", "A10", "A11", "A12"}


def as_path(root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else root / path


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise GateFail(f"{label} missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise GateFail(f"{label} json parse failed: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GateFail(f"{label} json root must be object: {path}")
    return data


def status_value(data: dict[str, Any]) -> str:
    return str(
        data.get("status")
        or data.get("gate_status")
        or data.get("overall_status")
        or ""
    ).upper()


def truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "approved", "decided"}
    return False


def handoff_or_contract_true(
    data: dict[str, Any],
    contract: dict[str, Any] | None,
    key: str,
) -> bool:
    if key in data:
        return data.get(key) is True
    return truthy((contract or {}).get(key))


def require_status_pass(path: Path, label: str, fail_token: str) -> dict[str, Any]:
    data = load_json(path, label)
    if status_value(data) != "PASS":
        raise GateFail(f"{fail_token}: {label} status must be PASS")
    return data


def require_existing_file(path: Path, label: str, fail_token: str) -> Path:
    if not path.exists():
        raise GateFail(f"{fail_token}: {label} missing: {path}")
    return path


def require_number(value: Any, field: str, fail_token: str) -> None:
    if isinstance(value, bool):
        raise GateFail(f"{fail_token}: {field} must be numeric")
    if isinstance(value, (int, float)) and value >= 0:
        return
    raise GateFail(f"{fail_token}: {field} must be numeric")


def segment_uses_narration_audio(segment: dict[str, Any]) -> bool:
    return (
        segment.get("caption_type") == "tts_narration"
        or segment.get("audio_role") == "audio.narration_tts"
    )


def segment_uses_speaker_quote(segment: dict[str, Any]) -> bool:
    return (
        segment.get("caption_type") == "speaker_quote"
        or segment.get("assembly_role") == "verified_speaker_quote"
    )


def validate_report1_handoff(
    root: Path,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = root / "20_script" / "report1_handoff.json"
    data = load_json(path, "report1_handoff.json")
    if data.get("gate_name") != "REPORT1_HANDOFF_GATE":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: gate_name must be REPORT1_HANDOFF_GATE")
    if status_value(data) != "PASS":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: report1_handoff status must be PASS")
    if data.get("owner_skill") != "00-tikitaka":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: owner_skill must be 00-tikitaka")
    if data.get("next_skill") != "000short-production-agent":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: next_skill must be 000short-production-agent")
    if not handoff_or_contract_true(data, contract, "report1_approved"):
        raise GateFail("WAIT_REPORT1_APPROVAL_TTS_DECISION: report1_approved must be true")
    if not handoff_or_contract_true(data, contract, "voice_audio_route_decided"):
        raise GateFail("WAIT_REPORT1_APPROVAL_TTS_DECISION: voice_audio_route_decided must be true")
    return data


def validate_script_handoff(root: Path) -> dict[str, Any]:
    path = root / "20_script" / "script_handoff_gate.json"
    data = load_json(path, "script_handoff_gate.json")
    if data.get("gate_name") != "SCRIPT_HANDOFF_GATE":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: gate_name must be SCRIPT_HANDOFF_GATE")
    if status_value(data) != "PASS":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: script_handoff_gate status must be PASS")
    if data.get("capcut_allowed") is not True:
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: capcut_allowed must be true")
    return data


def validate_timeline_design(root: Path) -> tuple[dict[str, Any], bool]:
    path = root / "20_script" / "timeline_design.json"
    if not path.exists():
        raise GateFail(f"WAIT_TIMELINE_DESIGN_REQUIRED: timeline_design.json missing: {path}")
    data = load_json(path, "timeline_design.json")
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise GateFail("WAIT_TIMELINE_DESIGN_REQUIRED: timeline_design.segments missing")

    has_narration_audio = False
    seen_edit_ids: set[str] = set()
    seen_timeline_orders: dict[Any, str] = {}
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise GateFail(f"WAIT_TIMELINE_DESIGN_REPAIR: segments[{index}] must be object")
        missing = sorted(key for key in REQUIRED_SEGMENT_FIELDS if segment.get(key) in (None, ""))
        if missing:
            raise GateFail(
                f"WAIT_TIMELINE_DESIGN_REPAIR: segments[{index}] missing {', '.join(missing)}"
            )

        edit_id = str(segment.get("edit_id"))
        if edit_id in seen_edit_ids:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: duplicate edit_id")
        seen_edit_ids.add(edit_id)

        timeline_order = segment.get("timeline_order")
        parallel_group_id = str(segment.get("parallel_group_id") or "")
        existing_parallel_group_id = seen_timeline_orders.get(timeline_order)
        if existing_parallel_group_id is not None:
            if not parallel_group_id or existing_parallel_group_id != parallel_group_id:
                raise GateFail(
                    "WAIT_TIMELINE_DESIGN_REPAIR: duplicate timeline_order without parallel_group_id"
                )
        else:
            seen_timeline_orders[timeline_order] = parallel_group_id

        if segment.get("assembly_role") not in ALLOWED_ASSEMBLY_ROLES:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: unsupported assembly_role")
        if segment.get("duration_basis") not in ALLOWED_DURATION_BASIS:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: unsupported duration_basis")
        if segment.get("duration_status") not in ALLOWED_DURATION_STATUS:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: unsupported duration_status")

        track = str(segment.get("track") or "")
        if track in FORBIDDEN_STAGE1_CAPCUT_AUDIO_TRACKS:
            raise GateFail(
                "WAIT_TIMELINE_DESIGN_REPAIR: timeline_design must use semantic audio track, not "
                f"{track}"
            )
        if track.startswith("audio.") and track not in SEMANTIC_AUDIO_TRACKS:
            raise GateFail(
                "WAIT_TIMELINE_DESIGN_REPAIR: unsupported semantic audio track "
                f"{track}"
            )

        if segment_uses_narration_audio(segment):
            has_narration_audio = True
            for field in ("tts_text_ref", "planned_tts_duration_sec", "tts_duration_status"):
                if segment.get(field) in (None, ""):
                    raise GateFail(f"WAIT_TTS_TIMING_RELOCK: segments[{index}] missing {field}")
            require_number(
                segment.get("planned_tts_duration_sec"),
                f"segments[{index}].planned_tts_duration_sec",
                "WAIT_TTS_TIMING_RELOCK",
            )
            tts_status = str(segment.get("tts_duration_status") or "")
            if tts_status not in NARRATION_AUDIO_TTS_STATUSES:
                raise GateFail("WAIT_TTS_TIMING_RELOCK: unsupported tts_duration_status")
            if tts_status == "ESTIMATED_ACCEPTED":
                if segment.get("estimated_tts_duration_sec") in (None, ""):
                    raise GateFail(
                        f"WAIT_TTS_TIMING_RELOCK: segments[{index}] missing estimated_tts_duration_sec"
                    )
                require_number(
                    segment.get("estimated_tts_duration_sec"),
                    f"segments[{index}].estimated_tts_duration_sec",
                    "WAIT_TTS_TIMING_RELOCK",
                )
            if tts_status == "ACTUAL_AUDIO_LOCKED":
                if segment.get("actual_tts_duration_sec") in (None, ""):
                    raise GateFail(
                        f"WAIT_TTS_TIMING_RELOCK: segments[{index}] missing actual_tts_duration_sec"
                    )
                require_number(
                    segment.get("actual_tts_duration_sec"),
                    f"segments[{index}].actual_tts_duration_sec",
                    "WAIT_TTS_TIMING_RELOCK",
                )

        if segment_uses_speaker_quote(segment):
            for field in ("source_audio_range", "quote_verification_status"):
                if segment.get(field) in (None, ""):
                    raise GateFail(f"WAIT_TIMELINE_DESIGN_REPAIR: segments[{index}] missing {field}")

    return data, has_narration_audio


def validate_tts_timing(root: Path, has_narration_audio: bool) -> None:
    if not has_narration_audio:
        return

    probe_path = root / "20_script" / "tts_duration_probe.json"
    if not probe_path.exists():
        raise GateFail(f"WAIT_TTS_TIMING_RELOCK: tts_duration_probe.json missing: {probe_path}")
    probe = load_json(probe_path, "tts_duration_probe.json")
    probe_status = status_value(probe)
    if probe_status not in {"PASS", "ESTIMATED_ACCEPTED"}:
        raise GateFail(
            f"WAIT_TTS_TIMING_RELOCK: tts_duration_probe status must be PASS or ESTIMATED_ACCEPTED"
        )
    tts_items = probe.get("tts_items", [])
    if tts_items is None:
        tts_items = []
    if not isinstance(tts_items, list):
        raise GateFail("WAIT_TTS_TIMING_RELOCK: tts_duration_probe.tts_items must be list")
    for index, item in enumerate(tts_items):
        if not isinstance(item, dict):
            raise GateFail(f"WAIT_TTS_TIMING_RELOCK: tts_duration_probe.tts_items[{index}] must be object")
        planned = item.get("planned_tts_duration_sec")
        actual = item.get("actual_tts_duration_sec")
        action = str(item.get("reconciliation_action") or "").strip()
        if action not in ALLOWED_RECONCILIATION_ACTIONS:
            raise GateFail("WAIT_TTS_TIMING_RELOCK: unsupported reconciliation action")
        if planned not in (None, ""):
            require_number(
                planned,
                f"tts_duration_probe.tts_items[{index}].planned_tts_duration_sec",
                "WAIT_TTS_TIMING_RELOCK",
            )
        if actual not in (None, ""):
            require_number(
                actual,
                f"tts_duration_probe.tts_items[{index}].actual_tts_duration_sec",
                "WAIT_TTS_TIMING_RELOCK",
            )
            if (
                planned not in (None, "")
                and actual > planned
                and item.get("within_tolerance") is False
                and action in {"", "none"}
            ):
                raise GateFail(
                    "WAIT_TTS_TIMING_RELOCK: actual TTS duration exceeds planned slot without reconciliation action"
                )

    gate_path = root / "20_script" / "tts_timing_reconciliation_gate.json"
    if not gate_path.exists():
        raise GateFail(
            f"WAIT_TTS_TIMING_RELOCK: tts_timing_reconciliation_gate.json missing: {gate_path}"
        )
    gate = load_json(gate_path, "tts_timing_reconciliation_gate.json")
    if status_value(gate) != "PASS":
        raise GateFail("WAIT_TTS_TIMING_RELOCK: tts_timing_reconciliation_gate status must be PASS")
    if str(gate.get("tts_duration_status") or "") not in READY_TTS_TIMING_STATUSES:
        raise GateFail(
            "WAIT_TTS_TIMING_RELOCK: tts_duration_status must be ESTIMATED_ACCEPTED or ACTUAL_AUDIO_LOCKED"
        )
    action = str(gate.get("reconciliation_action") or "").strip()
    if action not in ALLOWED_RECONCILIATION_ACTIONS:
        raise GateFail("WAIT_TTS_TIMING_RELOCK: unsupported reconciliation action")


def validate_humanize_gate(root: Path) -> dict[str, Any]:
    path = root / "20_script" / "humanize_korean_gate.json"
    data = load_json(path, "humanize_korean_gate.json")
    if status_value(data) != "PASS":
        raise GateFail("WAIT_HUMANIZE_REPAIR: humanize_korean_gate status must be PASS")
    if data.get("structure_changed") is True:
        raise GateFail("WAIT_HUMANIZE_REPAIR: structure_changed must be false")
    if data.get("protected_fields_changed") is True:
        raise GateFail("WAIT_HUMANIZE_REPAIR: protected_fields_changed must be false")
    return data


def validate_source_presence(root: Path) -> Path:
    manifest = root / "00_source" / "source_manifest.json"
    if manifest.exists():
        data = load_json(manifest, "source_manifest.json")
        if status_value(data) == "PASS":
            return manifest
        raise GateFail("WAIT_SOURCE_MEDIA_REQUIRED: source_manifest status must be PASS")
    source = root / "00_source" / "source.mp4"
    if source.exists():
        return source
    raise GateFail("WAIT_SOURCE_MEDIA_REQUIRED: source_manifest.json or source.mp4 missing")


def validate_stage2_tikitaka_handoff(
    root: Path,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    report1 = validate_report1_handoff(root, contract)
    validate_script_handoff(root)
    timeline_design, has_narration_audio = validate_timeline_design(root)
    require_status_pass(
        root / "20_script" / "timeline_design_gate.json",
        "timeline_design_gate.json",
        "WAIT_TIMELINE_DESIGN_REPAIR",
    )
    validate_humanize_gate(root)
    require_existing_file(
        root / "20_script" / "block_map.json",
        "block_map.json",
        "WAIT_SCRIPT_HANDOFF_GATE",
    )
    require_existing_file(
        root / "20_script" / "block_role_map.json",
        "block_role_map.json",
        "WAIT_BLOCK_ROLE_MAP_REQUIRED",
    )
    require_existing_file(
        root / "20_script" / "block_voice_switch_map.json",
        "block_voice_switch_map.json",
        "WAIT_SCRIPT_HANDOFF_GATE",
    )
    if has_narration_audio:
        validate_tts_timing(root, has_narration_audio)
        tts_copy = require_existing_file(
            root / "20_script" / "tts_copy_text.txt",
            "tts_copy_text.txt",
            "WAIT_TTS_COPY_TEXT_REQUIRED",
        )
        if not tts_copy.read_text(encoding="utf-8-sig").strip():
            raise GateFail("WAIT_TTS_COPY_TEXT_REQUIRED: tts_copy_text.txt is empty")
    source = validate_source_presence(root)
    return {
        "stage2_tikitaka_handoff_status": "PASS",
        "stage2_tikitaka_source_of_truth": "20_script/timeline_design.json",
        "timeline_design_segment_count": len(timeline_design["segments"]),
        "report1_handoff_next_skill": report1["next_skill"],
        "source_media_or_manifest": str(source),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        result = validate_stage2_tikitaka_handoff(Path(args.root))
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
