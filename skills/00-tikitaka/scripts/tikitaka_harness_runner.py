#!/usr/bin/env python3
"""Fail-closed evidence auditor for 00-tikitaka SCRIPT_LOCK reports.

The runner does not trust model text. It reads evidence files from a work
directory, writes a visible gate report, and exits nonzero unless every required
piece of evidence is present and passing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


PASS_VALUES = {"PASS", "DONE", "SCRIPT_LOCK", "HARNESS_PASS"}
FAIL_VALUES = {"FAIL", "FAILED", "BLOCK", "BLOCKED", "SCRIPT_REWRITE", "HARNESS_FAILED"}
ALLOWED_STAGE1_AUDIO_TRACKS = {
    "audio.narration_tts": "narration_tts",
    "audio.speaker_source": "speaker_source",
    "audio.sfx": "sfx",
    "audio.bgm": "bgm",
}
FORBIDDEN_STAGE1_CAPCUT_AUDIO_TRACKS = {"A9", "A10", "A11", "A12"}
SCRIPT_LOCK_PACKAGE_FILES = {
    "original_structure_summary": "original_structure_summary.md",
    "urakkai_structure_plan": "urakkai_structure_plan.md",
    "urakkai_structure_delta": "urakkai_structure_delta.json",
    "timeline_design": "timeline_design.json",
    "timeline_design_gate": "timeline_design_gate.json",
    "humanize_korean_gate": "humanize_korean_gate.json",
    "block_map": "block_map.json",
    "block_role_map": "block_role_map.json",
    "block_voice_switch_map": "block_voice_switch_map.json",
    "tts_copy_text": "tts_copy_text.txt",
}
SCRIPT_BODY_CANDIDATES = (
    "final_script_ko.md",
    "final_script_ko.txt",
    "tikitaka_script.md",
    "tikitaka_script.txt",
    "script_body.md",
    "script_body.txt",
    "20_script/final_script_ko.md",
    "20_script/final_script_ko.txt",
    "20_script/tikitaka_script.md",
    "20_script/tikitaka_script.txt",
)
TTS_COPY_TEXT_CANDIDATES = (
    "tts_copy_text.txt",
    "20_script/tts_copy_text.txt",
)
STAGE2_DECISION_VALUES = {
    "STAGE_2_FULL",
    "STAGE2_FULL",
    "STAGE_2",
    "AUTO_FULL",
    "AUTO_FULL_CAPCUT_PROJECT",
    "FINAL_LOCK",
    "FULL",
    "PRODUCTION",
    "자동모드",
    "최종",
}
STAGE2_DECISION_VALUES.update(
    {
        "자동모드",
        "자동으로 다",
        "끝까지",
        "최종",
        "다음단계",
        "캣컵프로젝트파일까지",
        "캣컵 프로젝트 파일까지",
        "캐컷프로젝트파일까지",
        "CAPCUT PROJECT",
    }
)
STAGE1_DECISION_VALUES = {
    "STAGE_1_SCRIPT",
    "STAGE1_SCRIPT",
    "STAGE_1_ONLY",
    "SCRIPT_ONLY",
    "DRAFT_SCRIPT",
    "TIKITAKA_ONLY",
    "대본까지",
    "대본만",
    "초벌",
    "티키타카",
    "초안만",
    "검토용",
    "스크립트만",
}
STAGE1_REQUEST_TOKENS = (
    "대본까지",
    "대본만",
    "초벌",
    "티키타카",
    "초안만",
    "검토용",
    "스크립트만",
)
STAGE2_REQUEST_TOKENS = (
    "자동모드",
    "자동으로 다",
    "끝까지",
    "최종",
    "다음단계",
    "업로드까지",
    "슈퍼톤",
    "supertone",
    "tts 만들",
    "tts 생성",
    "tts mp3",
    "캣컵프로젝트파일까지",
    "캣컵 프로젝트 파일까지",
    "캐컷프로젝트파일까지",
    "capcut project",
)
REQUEST_TEXT_KEYS = (
    "user_request",
    "request_text",
    "prompt",
    "expected_output",
    "requested_output",
    "work_order",
)
REQUEST_TEXT_FILES = (
    "user_request.txt",
    "request_text.txt",
    "prompt.txt",
    "handoff_request.md",
    "work_order.md",
)
USER_TTS_OR_SRT_PATH_KEYS = (
    "user_tts_audio_path",
    "user_tts_path",
    "tts_audio_path",
    "user_audio_path",
    "user_mp3_path",
    "provided_tts_audio_path",
    "provided_mp3_path",
    "user_srt_path",
    "user_srt_audio_package_path",
)
REPORT1_APPROVAL_KEYS = (
    "report1_approved",
    "report_1_approved",
    "script_approved_by_user",
    "user_script_ok",
    "user_ok_after_report1",
    "report1_user_ok",
)
VOICE_AUDIO_ROUTE_DECISION_KEYS = (
    "voice_audio_route_decided",
    "tts_route_decided",
    "audio_route_decided",
    "tts_user_decision_done",
    "no_tts_source_bgm_route_approved",
)
VOICE_AUDIO_ROUTE_VALUE_KEYS = (
    "voice_audio_route",
    "tts_route",
    "audio_route",
    "source_audio_route",
    "selected_voice_audio_route",
)
CAPCUT_DRAFT_CONTENT_CANDIDATES = (
    "50_capcut_project/draft_content.json",
    "50_capcut_project/draft_content_snapshot.json",
    "draft_content.json",
)
SCRIPT_HANDOFF_GATE_CANDIDATES = (
    "script_handoff_gate.json",
    "20_script/script_handoff_gate.json",
)
BLOCK_MAP_CANDIDATES = (
    "block_map.json",
    "20_script/block_map.json",
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def nonempty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def read_json(path: Path) -> dict[str, Any]:
    if not nonempty(path):
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"_parse_error": True}
    return data if isinstance(data, dict) else {"_non_object": True}


def status_block(status: str, evidence: str | None, reason: str = "") -> dict[str, Any]:
    return {"status": status, "evidence": evidence, "reason": reason}


def file_status(work_dir: Path, name: str, label: str | None = None) -> dict[str, Any]:
    path = work_dir / name
    if nonempty(path):
        return status_block("PASS", name)
    return status_block("MISSING", None, f"{label or name} missing")


def persona_status(work_dir: Path) -> dict[str, Any]:
    persona_dir = work_dir / "persona_outputs"
    if not persona_dir.exists() or not persona_dir.is_dir():
        return status_block("NOT_RUN", None, "persona_outputs/ missing")
    outputs = sorted(p for p in persona_dir.glob("*.md") if nonempty(p))
    if len(outputs) < 5:
        return status_block("NOT_RUN", "persona_outputs/", f"only {len(outputs)} persona outputs found")
    return {
        "status": "PASS",
        "evidence": "persona_outputs/",
        "count": len(outputs),
        "files": [p.name for p in outputs],
    }


def script_gate_status(work_dir: Path) -> dict[str, Any]:
    path = work_dir / "script_gate_report.json"
    data = read_json(path)
    if not data:
        return status_block("NOT_RUN", None, "script_gate_report.json missing")
    if data.get("_parse_error"):
        return status_block("FAILED", "script_gate_report.json", "script_gate_report.json parse failed")

    raw_status = str(data.get("status") or data.get("script_lock_status") or "").upper()
    pass_count = data.get("writer_persona_pass_count")
    hard_veto = data.get("writer_persona_hard_veto")
    hard_veto_personas = data.get("hard_veto_personas") or []

    pass_count_ok = isinstance(pass_count, int) and pass_count >= 4
    hard_veto_ok = hard_veto is False and not hard_veto_personas
    explicit_pass = raw_status in PASS_VALUES
    explicit_fail = raw_status in FAIL_VALUES

    if explicit_fail:
        return status_block("FAILED", "script_gate_report.json", f"script gate status={raw_status}")
    if explicit_pass and pass_count_ok and hard_veto_ok:
        return {
            "status": "PASS",
            "evidence": "script_gate_report.json",
            "writer_persona_pass_count": pass_count,
            "writer_persona_hard_veto": hard_veto,
        }
    return status_block("FAILED", "script_gate_report.json", "script gate lacks pass_count>=4 or hard-veto=false")


def n8n_status(work_dir: Path, previous_state: dict[str, Any]) -> dict[str, Any]:
    previous = previous_state.get("n8n") if isinstance(previous_state.get("n8n"), dict) else {}
    previous_status = str(previous.get("status") or "").upper()
    previous_execution = previous.get("execution_id")
    previous_evidence = previous.get("evidence")
    if previous_status == "DONE" and (previous_execution or previous_evidence):
        return {
            "status": "DONE",
            "execution_id": previous_execution,
            "evidence": previous_evidence,
            "reason": "carried from existing job_state.json",
        }

    candidates = [
        "n8n_execution_id.txt",
        "n8n_callback.log",
        "n8n_webhook_response.log",
        "n8n_webhook_response.json",
        "n8n_output_artifact.json",
        "n8n_output_artifact.md",
    ]
    for name in candidates:
        if nonempty(work_dir / name):
            execution_id = None
            if name == "n8n_execution_id.txt":
                execution_id = (work_dir / name).read_text(encoding="utf-8-sig").strip()
            return {"status": "DONE", "execution_id": execution_id, "evidence": name, "reason": ""}

    return status_block("NOT_RUN", None, "no n8n execution id, callback, webhook response, or output artifact")


def append_trace(work_dir: Path, job_id: str) -> dict[str, Any]:
    trace = work_dir / "harness_trace.log"
    with trace.open("a", encoding="utf-8") as fh:
        fh.write(f"{utc_now()} job_id={job_id} audit=tikitaka_harness_runner\n")
    return status_block("PASS", "harness_trace.log")


def passish(block: dict[str, Any]) -> bool:
    return str(block.get("status") or "").upper() in PASS_VALUES


def legacy_stage_scope_status(previous_state: dict[str, Any]) -> dict[str, Any]:
    value = str(
        previous_state.get("user_stage_decision")
        or previous_state.get("stage_scope")
        or previous_state.get("requested_stage")
        or ""
    ).strip()
    if value.upper() in STAGE2_DECISION_VALUES:
        return {
            "status": "PASS",
            "decision": "stage_2_full",
            "evidence": "job_state.json",
            "reason": "user authorized stage 2",
        }
    if value:
        return {
            "status": "WAIT",
            "decision": value,
            "evidence": "job_state.json",
            "reason": "stage 2 not authorized",
        }
    return {
        "status": "WAIT",
        "decision": "WAIT_USER_STAGE_DECISION",
        "evidence": "job_state.json",
        "reason": "ask user '어디까지 만들까?' before CapCut stage",
    }


def contains_token(text: str, tokens: tuple[str, ...] | set[str]) -> bool:
    folded = text.casefold()
    return any(token.casefold() in folded for token in tokens)


def truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "pass",
            "passed",
            "yes",
            "y",
            "ok",
            "okay",
            "complete",
            "completed",
            "예",
            "승인",
            "완료",
        }
    return False


def collect_request_text(work_dir: Path | None, previous_state: dict[str, Any]) -> tuple[str, str]:
    parts: list[str] = []
    evidence: list[str] = []
    for key in REQUEST_TEXT_KEYS:
        value = previous_state.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value)
            evidence.append(f"job_state.json:{key}")
    if work_dir is not None:
        for name in REQUEST_TEXT_FILES:
            path = work_dir / name
            if nonempty(path):
                parts.append(path.read_text(encoding="utf-8-sig"))
                evidence.append(name)
    return "\n".join(parts), ", ".join(evidence) if evidence else "job_state.json"


def has_user_tts_or_srt_path(previous_state: dict[str, Any]) -> bool:
    return any(
        isinstance(previous_state.get(key), str) and str(previous_state.get(key)).strip()
        for key in USER_TTS_OR_SRT_PATH_KEYS
    )


def has_report1_approval(previous_state: dict[str, Any]) -> bool:
    return any(truthy(previous_state.get(key)) for key in REPORT1_APPROVAL_KEYS)


def has_voice_audio_route_decision(previous_state: dict[str, Any]) -> bool:
    return any(truthy(previous_state.get(key)) for key in VOICE_AUDIO_ROUTE_DECISION_KEYS)


def report1_transition_ready(previous_state: dict[str, Any]) -> bool:
    return has_report1_approval(previous_state) and has_voice_audio_route_decision(previous_state)


def stage2_wait_block(evidence: str, reason_prefix: str) -> dict[str, Any]:
    return {
        "status": "WAIT",
        "decision": "stage_2_full",
        "evidence": evidence,
        "blocker": "WAIT_REPORT1_APPROVAL_TTS_DECISION",
        "reason": f"{reason_prefix}; wait for report1_approved and voice_audio_route_decided",
    }


def classify_stage_scope_text(text: str) -> str:
    value = text.strip()
    if not value:
        return ""
    if value.upper() in STAGE2_DECISION_VALUES or contains_token(value, STAGE2_REQUEST_TOKENS):
        return "stage_2_full"
    if value.upper() in STAGE1_DECISION_VALUES or contains_token(value, STAGE1_REQUEST_TOKENS):
        return "stage_1_script"
    return ""


def stage_scope_status(previous_state: dict[str, Any], work_dir: Path | None = None) -> dict[str, Any]:
    explicit_value = str(
        previous_state.get("user_stage_decision")
        or previous_state.get("stage_scope")
        or previous_state.get("requested_stage")
        or ""
    ).strip()
    explicit_decision = classify_stage_scope_text(explicit_value)
    if explicit_decision == "stage_2_full":
        if report1_transition_ready(previous_state):
            return {
                "status": "PASS",
                "decision": "stage_2_full",
                "evidence": "job_state.json",
                "reason": "user authorized stage 2 after 보고서1 approval and voice/audio route decision",
            }
        return stage2_wait_block("job_state.json", "stage 2 intent found")
    if has_user_tts_or_srt_path(previous_state):
        if report1_transition_ready(previous_state):
            return {
                "status": "PASS",
                "decision": "stage_2_full",
                "evidence": "job_state.json",
                "reason": "user supplied voice/audio path after 보고서1 approval and explicit route decision",
            }
        return stage2_wait_block("job_state.json", "voice/audio route found")
    if explicit_decision == "stage_1_script":
        return {
            "status": "WAIT",
            "decision": "stage_1_script",
            "evidence": "job_state.json",
            "reason": "stage 1 script-only request; stop after 보고서1",
        }
    if explicit_value:
        return {
            "status": "WAIT",
            "decision": explicit_value,
            "evidence": "job_state.json",
            "reason": "stage 2 not authorized",
        }

    request_text, evidence = collect_request_text(work_dir, previous_state)
    request_decision = classify_stage_scope_text(request_text)
    if request_decision == "stage_2_full":
        return stage2_wait_block(evidence, "stage 2 request text found")
    if request_decision == "stage_1_script":
        return {
            "status": "WAIT",
            "decision": "stage_1_script",
            "evidence": evidence,
            "reason": "stage 1 script-only request; stop after 보고서1",
        }
    return {
        "status": "WAIT",
        "decision": "WAIT_USER_STAGE_DECISION",
        "evidence": evidence,
        "reason": "ask user '어디까지 만들까?' before CapCut stage",
    }


def find_reentry_script_handoff(work_dir: Path) -> dict[str, Any]:
    for candidate in SCRIPT_HANDOFF_GATE_CANDIDATES:
        gate = read_json(work_dir / candidate)
        if not gate:
            continue
        if gate.get("_parse_error") or gate.get("_non_object"):
            return {
                "status": "FAIL",
                "evidence": candidate,
                "blocker": "WAIT_SCRIPT_HANDOFF_GATE_REPAIR",
                "report": "Existing script_handoff_gate is invalid; repair stage 1 before CapCut rework.",
            }
        raw_status = str(gate.get("status") or gate.get("gate_status") or "").upper()
        if raw_status not in PASS_VALUES:
            return {
                "status": "WAIT",
                "evidence": candidate,
                "blocker": "WAIT_SCRIPT_HANDOFF_GATE_REPAIR",
                "report": "Existing script_handoff_gate is not PASS; repair stage 1 before CapCut rework.",
            }
        if gate.get("script_status") != "SCRIPT_LOCK_PACKAGE":
            return {
                "status": "WAIT",
                "evidence": candidate,
                "blocker": "WAIT_SCRIPT_HANDOFF_GATE_REPAIR",
                "report": "Existing script_handoff_gate PASS lacks SCRIPT_LOCK_PACKAGE; repair stage 1 before CapCut rework.",
            }
        return {
            "status": "PASS",
            "evidence": candidate,
            "blocker": "",
            "report": "Existing script_handoff_gate PASS found.",
        }
    return {
        "status": "WAIT",
        "evidence": "",
        "blocker": "WAIT_SCRIPT_HANDOFF_GATE",
        "report": "script_handoff_gate PASS missing.",
    }


def find_reentry_block_map(work_dir: Path) -> dict[str, Any]:
    for candidate in BLOCK_MAP_CANDIDATES:
        data = read_json(work_dir / candidate)
        if not data:
            continue
        if data.get("_parse_error") or data.get("_non_object"):
            return {
                "status": "FAIL",
                "evidence": candidate,
                "blocker": "WAIT_BLOCK_MAP_REPAIR",
                "report": "Existing block_map is invalid; repair stage 1 before CapCut rework.",
            }
        sequence = data.get("edit_block_sequence")
        blocks = data.get("blocks") or data.get("edit_blocks")
        if isinstance(sequence, list) and sequence and isinstance(blocks, list) and blocks:
            return {
                "status": "PASS",
                "evidence": candidate,
                "blocker": "",
                "report": "Existing block_map found.",
            }
        return {
            "status": "WAIT",
            "evidence": candidate,
            "blocker": "WAIT_BLOCK_MAP_REPAIR",
            "report": "Existing block_map lacks edit_block_sequence or blocks; repair stage 1 before CapCut rework.",
        }
    return {
        "status": "WAIT",
        "evidence": "",
        "blocker": "WAIT_BLOCK_MAP_REPAIR",
        "report": "block_map missing.",
    }


def reentry_stage_status(work_dir: Path, previous_state: dict[str, Any] | None = None) -> dict[str, Any]:
    previous_state = previous_state or {}
    report1_and_voice_ready = report1_transition_ready(previous_state)
    for candidate in CAPCUT_DRAFT_CONTENT_CANDIDATES:
        path = work_dir / candidate
        if nonempty(path):
            data = read_json(path)
            if data.get("_parse_error") or data.get("_non_object"):
                return {
                    "status": "FAIL",
                    "resume_stage": "capcut_rework",
                    "evidence": candidate,
                    "blocker": "FAIL_CAPCUT_DRAFT_CONTENT_INVALID",
                    "report": "Existing CapCut draft_content is present but invalid; repair CapCut package before continuing.",
                }
            handoff = find_reentry_script_handoff(work_dir)
            if handoff["status"] != "PASS":
                return {
                    "status": "WAIT",
                    "resume_stage": "stage_1_repair",
                    "evidence": candidate,
                    "blocker": handoff["blocker"],
                    "report": f"Existing CapCut draft_content found, but {handoff['report']}",
                }
            block_map = find_reentry_block_map(work_dir)
            if block_map["status"] != "PASS":
                return {
                    "status": "WAIT",
                    "resume_stage": "stage_1_repair",
                    "evidence": candidate,
                    "blocker": block_map["blocker"],
                    "report": f"Existing CapCut draft_content found, but {block_map['report']}",
                }
            if not report1_and_voice_ready:
                return {
                    "status": "WAIT",
                    "resume_stage": "capcut_rework",
                    "evidence": f"{candidate}; {handoff['evidence']}; {block_map['evidence']}",
                    "blocker": "WAIT_REPORT1_APPROVAL_TTS_DECISION",
                    "report": (
                        "Existing CapCut draft_content, script_handoff_gate PASS, and block_map found. "
                        "Report the resume point first, then wait for report1_approved and "
                        "voice_audio_route_decided before CapCut rework."
                    ),
                }
            return {
                "status": "PASS",
                "resume_stage": "capcut_rework",
                "evidence": f"{candidate}; {handoff['evidence']}; {block_map['evidence']}",
                "blocker": "",
                "report": "Existing CapCut draft_content, script_handoff_gate PASS, and block_map found. This package reached CapCut stage; resume at CapCut rework after reporting the state.",
            }

    handoff = find_reentry_script_handoff(work_dir)
    if handoff["evidence"] and handoff["status"] != "PASS":
        return {
            "status": "WAIT",
            "resume_stage": "stage_1_repair",
            "evidence": handoff["evidence"],
            "blocker": handoff["blocker"],
            "report": handoff["report"],
        }
    if handoff["status"] == "PASS":
        if not report1_and_voice_ready:
            return {
                "status": "WAIT",
                "resume_stage": "stage_2_resume",
                "evidence": handoff["evidence"],
                "blocker": "WAIT_REPORT1_APPROVAL_TTS_DECISION",
                "report": (
                    "Existing script_handoff_gate PASS found. This package completed stage 1; "
                    "wait for report1_approved and voice_audio_route_decided before stage 2."
                ),
            }
        return {
            "status": "PASS",
            "resume_stage": "stage_2_resume",
            "evidence": handoff["evidence"],
            "blocker": "",
            "report": "Existing script_handoff_gate PASS found. This package completed stage 1; resume at stage 2 only after user decision.",
        }

    return {
        "status": "WAIT",
        "resume_stage": "g0_restart",
        "evidence": "",
        "blocker": "WAIT_USER_STAGE_DECISION",
        "report": "No script handoff or CapCut draft package found. Restart from G0 and ask the user where to stop.",
    }


def json_artifact_status(work_dir: Path, name: str, label: str) -> dict[str, Any]:
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, f"{label} missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, f"{label} parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, f"{label} json root must be an object")

    raw_status = str(data.get("status") or data.get("gate_status") or "").upper()
    if raw_status in FAIL_VALUES:
        return status_block("FAILED", name, f"{label} status={raw_status}")
    if raw_status and raw_status not in PASS_VALUES:
        return status_block("FAILED", name, f"{label} status is not PASS: {raw_status}")
    return status_block("PASS", name)


def json_status_pass_artifact_status(work_dir: Path, name: str, label: str) -> dict[str, Any]:
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, f"{label} missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, f"{label} parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, f"{label} json root must be an object")

    raw_status = str(data.get("status") or data.get("gate_status") or "").upper()
    if raw_status not in PASS_VALUES:
        return status_block("FAILED", name, f"{label} status must be PASS")
    return status_block("PASS", name)


def visible_script_body_status(work_dir: Path) -> dict[str, Any]:
    _, source = first_nonempty_text(work_dir, SCRIPT_BODY_CANDIDATES)
    if source:
        return status_block("PASS", source)
    return status_block("MISSING", None, "visible script body missing")


def humanize_korean_gate_status(work_dir: Path) -> dict[str, Any]:
    name = SCRIPT_LOCK_PACKAGE_FILES["humanize_korean_gate"]
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, "humanize_korean_gate missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, "humanize_korean_gate parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, "humanize_korean_gate json root must be an object")

    raw_status = str(data.get("status") or data.get("gate_status") or "").upper()
    if raw_status not in PASS_VALUES:
        return status_block("FAILED", name, "humanize_korean_gate status must be PASS")
    if data.get("structure_changed") is True:
        return status_block("FAILED", name, "humanize_korean_gate must not change timeline structure")
    if data.get("protected_fields_changed") is True:
        return status_block("FAILED", name, "humanize_korean_gate must not change protected fields")
    return status_block("PASS", name)


def timeline_design_status(work_dir: Path) -> dict[str, Any]:
    name = SCRIPT_LOCK_PACKAGE_FILES["timeline_design"]
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, "timeline_design missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, "timeline_design parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, "timeline_design json root must be an object")

    segments = data.get("segments") or data.get("timeline_segments")
    if not isinstance(segments, list) or not segments:
        return status_block("FAILED", name, "timeline_design.segments missing")
    required = {"edit_id", "time_start", "time_end", "track", "caption_type", "audio_policy"}
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            return status_block("FAILED", name, f"timeline_design.segments[{index}] must be object")
        missing = sorted(key for key in required if segment.get(key) in (None, ""))
        if missing:
            return status_block(
                "FAILED",
                name,
                f"timeline_design.segments[{index}] missing {', '.join(missing)}",
            )
        track = str(segment.get("track") or "")
        if track in FORBIDDEN_STAGE1_CAPCUT_AUDIO_TRACKS:
            return status_block(
                "FAILED",
                name,
                f"timeline_design.segments[{index}] must use semantic audio track, not {track}",
            )
        if track.startswith("audio."):
            expected_lane = ALLOWED_STAGE1_AUDIO_TRACKS.get(track)
            if expected_lane is None:
                return status_block(
                    "FAILED",
                    name,
                    f"timeline_design.segments[{index}] unsupported semantic audio track {track}",
                )
            if segment.get("semantic_lane") != expected_lane:
                return status_block(
                    "FAILED",
                    name,
                    f"timeline_design.segments[{index}] semantic_lane must be {expected_lane}",
                )
            if segment.get("resolved_capcut_track") is not None:
                return status_block(
                    "FAILED",
                    name,
                    f"timeline_design.segments[{index}] resolved_capcut_track must be null in stage 1",
                )
            if segment.get("resolved_by") != "000short-production-agent":
                return status_block(
                    "FAILED",
                    name,
                    f"timeline_design.segments[{index}] resolved_by must be 000short-production-agent",
                )
    return status_block("PASS", name)


def block_map_status(work_dir: Path) -> dict[str, Any]:
    name = SCRIPT_LOCK_PACKAGE_FILES["block_map"]
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, "block_map missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, "block_map parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, "block_map json root must be an object")

    sequence = data.get("edit_block_sequence")
    blocks = data.get("blocks") or data.get("edit_blocks")
    if not isinstance(sequence, list) or not sequence:
        return status_block("FAILED", name, "block_map.edit_block_sequence missing")
    if not isinstance(blocks, list) or not blocks:
        return status_block("FAILED", name, "block_map.blocks missing")

    required = {"edit_id", "source_block_id", "original_order", "urakkai_order"}
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            return status_block("FAILED", name, f"block_map.blocks[{index}] must be object")
        missing = sorted(key for key in required if block.get(key) in (None, ""))
        if missing:
            return status_block(
                "FAILED",
                name,
                f"block_map.blocks[{index}] missing {', '.join(missing)}",
            )
    return status_block("PASS", name)


def block_role_map_status(work_dir: Path) -> dict[str, Any]:
    name = SCRIPT_LOCK_PACKAGE_FILES["block_role_map"]
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, "block_role_map missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, "block_role_map parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, "block_role_map json root must be an object")

    roles = data.get("roles") or data.get("block_roles")
    if not isinstance(roles, list) or not roles:
        return status_block("FAILED", name, "block_role_map.roles missing")
    required = {"edit_id", "caption_type"}
    for index, role in enumerate(roles):
        if not isinstance(role, dict):
            return status_block("FAILED", name, f"block_role_map.roles[{index}] must be object")
        missing = sorted(key for key in required if role.get(key) in (None, ""))
        if missing:
            return status_block(
                "FAILED",
                name,
                f"block_role_map.roles[{index}] missing {', '.join(missing)}",
            )
    return status_block("PASS", name)


def block_voice_switch_map_status(work_dir: Path) -> dict[str, Any]:
    name = SCRIPT_LOCK_PACKAGE_FILES["block_voice_switch_map"]
    data = read_json(work_dir / name)
    if not data:
        return status_block("MISSING", None, "block_voice_switch_map missing")
    if data.get("_parse_error"):
        return status_block("FAILED", name, "block_voice_switch_map parse failed")
    if data.get("_non_object"):
        return status_block("FAILED", name, "block_voice_switch_map json root must be an object")

    switches = data.get("switches") or data.get("voice_switches") or data.get("block_voice_switch_map")
    if not isinstance(switches, list) or not switches:
        return status_block("FAILED", name, "block_voice_switch_map.switches missing")
    required = {"edit_id", "source_audio", "tts"}
    for index, switch in enumerate(switches):
        if not isinstance(switch, dict):
            return status_block("FAILED", name, f"block_voice_switch_map.switches[{index}] must be object")
        missing = sorted(key for key in required if switch.get(key) in (None, ""))
        if missing:
            return status_block(
                "FAILED",
                name,
                f"block_voice_switch_map.switches[{index}] missing {', '.join(missing)}",
            )
    return status_block("PASS", name)


def build_script_handoff_gate(work_dir: Path) -> dict[str, Any]:
    checks = {
        "visible_script_body": visible_script_body_status(work_dir),
        "original_structure_summary": file_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["original_structure_summary"],
            "original structure summary",
        ),
        "urakkai_structure_plan": file_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["urakkai_structure_plan"],
            "urakkai structure plan",
        ),
        "urakkai_structure_delta": json_status_pass_artifact_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["urakkai_structure_delta"],
            "urakkai structure delta",
        ),
        "timeline_design": timeline_design_status(work_dir),
        "timeline_design_gate": json_status_pass_artifact_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["timeline_design_gate"],
            "timeline design gate",
        ),
        "humanize_korean_gate": humanize_korean_gate_status(work_dir),
        "block_map": block_map_status(work_dir),
        "block_role_map": block_role_map_status(work_dir),
        "block_voice_switch_map": block_voice_switch_map_status(work_dir),
        "tts_copy_text": file_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["tts_copy_text"],
            "TTS copy text",
        ),
    }
    missing = [name for name, block in checks.items() if not passish(block)]
    status = "PASS" if not missing else "FAIL"
    return {
        "gate_name": "SCRIPT_HANDOFF_GATE",
        "status": status,
        "generated_by": "tikitaka_harness_runner",
        "checked_at": utc_now(),
        "script_status": "SCRIPT_LOCK_PACKAGE" if status == "PASS" else "WAIT_SCRIPT_HANDOFF_GATE",
        "capcut_allowed": status == "PASS",
        "input_files": list(SCRIPT_LOCK_PACKAGE_FILES.values()),
        "checks": checks,
        "missing_or_failed": missing,
    }


def capcut_permission_status(script_handoff_gate: dict[str, Any]) -> tuple[str, str]:
    if (
        passish(script_handoff_gate)
        and script_handoff_gate.get("script_status") == "SCRIPT_LOCK_PACKAGE"
        and script_handoff_gate.get("capcut_allowed") is True
    ):
        return "CAPCUT_OPENABLE_PROJECT_ALLOWED", "WAIT_CAPCUT_OPENABLE_PROJECT"
    capcut_blocker = script_handoff_gate.get("capcut_blocker")
    if capcut_blocker:
        return str(capcut_blocker), str(capcut_blocker)
    return "WAIT_SCRIPT_HANDOFF_GATE", "WAIT_SCRIPT_HANDOFF_GATE"


def build_report1_handoff_gate(
    previous_state: dict[str, Any],
    stage_scope_gate: dict[str, Any],
    script_handoff_gate: dict[str, Any],
    capcut_permission: str,
) -> dict[str, Any]:
    ready = (
        passish(script_handoff_gate)
        and capcut_permission == "CAPCUT_OPENABLE_PROJECT_ALLOWED"
        and report1_transition_ready(previous_state)
    )
    blocker = "" if ready else "WAIT_REPORT1_APPROVAL_TTS_DECISION"
    if not passish(script_handoff_gate):
        blocker = "WAIT_SCRIPT_HANDOFF_GATE"

    return {
        "gate_name": "REPORT1_HANDOFF_GATE",
        "status": "PASS" if ready else "WAIT",
        "blocker": blocker,
        "report": "보고서1",
        "owner_skill": "00-tikitaka",
        "next_skill": "000short-production-agent",
        "next_stage": "보고서2",
        "next_gate": "CAPCUT_OPENABLE_PROJECT",
        "required_before_next": [
            "report1_approved=true",
            "voice_audio_route_decided=true",
        ],
        "report1_approved": has_report1_approval(previous_state),
        "voice_audio_route_decided": has_voice_audio_route_decision(previous_state),
        "forbidden_next": [
            "00-tikitaka writes 보고서2",
            "CapCut before report1 approval",
            "TTS before voice/audio route decision",
        ],
        "copy_to_next_chat": (
            "Use $000short-production-agent. 보고서1 승인 + TTS/오디오 방식 결정 후 "
            "보고서2 / CAPCUT_OPENABLE_PROJECT 단계로 진행."
        ),
    }


def checked(flag: bool) -> str:
    return "[x]" if flag else "[ ]"


def build_stage_gate_todo(job_state: dict[str, Any]) -> str:
    decision = job_state["stage_scope_gate"].get("decision") or "WAIT_USER_STAGE_DECISION"
    handoff_pass = passish(job_state["script_handoff_gate"])
    stage2_pass = passish(job_state["stage_scope_gate"])
    capcut_allowed = job_state["capcut_permission"] == "CAPCUT_OPENABLE_PROJECT_ALLOWED"
    final_allowed = job_state["final_report_allowed"] is True
    return "\n".join(
        [
            "# 11short Stage Gate TODO",
            "",
            f"{checked(decision != 'WAIT_USER_STAGE_DECISION')} G0: {decision} - user stage decision or request token",
            f"{checked(handoff_pass)} G1: stage 1 artifacts - timeline_design + humanize + block maps + tts_copy + script_handoff_gate",
            f"{checked(handoff_pass)} G2: stage 1 STOP - 보고서1",
            f"{checked(stage2_pass and capcut_allowed)} G3: stage 2 entry - user_stage_decision=stage_2_full",
            f"{checked(final_allowed)} G4: final production report is production-agent owned",
            "",
        ]
    )


def first_nonempty_text(work_dir: Path, candidates: tuple[str, ...]) -> tuple[str, str]:
    for candidate in candidates:
        path = work_dir / candidate
        if nonempty(path):
            return path.read_text(encoding="utf-8-sig").strip(), candidate
    return "", ""


def build_stage_scope_report(job_state: dict[str, Any], work_dir: Path) -> str:
    decision = job_state["stage_scope_gate"].get("decision") or "WAIT_USER_STAGE_DECISION"
    reentry = job_state.get("reentry_stage") or {}
    waits_for_report1 = (
        job_state["stage_scope_gate"].get("blocker") == "WAIT_REPORT1_APPROVAL_TTS_DECISION"
        or job_state.get("capcut_permission") == "WAIT_REPORT1_APPROVAL_TTS_DECISION"
    )
    stage2_report = decision == "stage_2_full" and not waits_for_report1
    if stage2_report:
        header = "# 2단계 인계 보고"
        status = "PASS" if job_state["capcut_permission"] == "CAPCUT_OPENABLE_PROJECT_ALLOWED" else "WAIT"
        mode = "stage_2_full"
        blocker = job_state["capcut_permission"] if status == "WAIT" else "WAIT_CAPCUT_BUILD"
    else:
        header = "# 보고서1"
        status = "WAIT_REPORT1_APPROVAL_TTS_DECISION" if waits_for_report1 else "WAIT_USER_STAGE_DECISION"
        mode = "stage_1_script"
        blocker = "WAIT_REPORT1_APPROVAL_TTS_DECISION" if waits_for_report1 else "WAIT_USER_STAGE_DECISION"
    script_body, script_source = first_nonempty_text(work_dir, SCRIPT_BODY_CANDIDATES)
    tts_copy_text, tts_source = first_nonempty_text(work_dir, TTS_COPY_TEXT_CANDIDATES)
    report1_blockers: list[str] = []
    if not script_body:
        report1_blockers.append("FAIL_REPORT1_VISIBLE_SCRIPT_BODY_MISSING")
    if not tts_copy_text:
        report1_blockers.append("FAIL_REPORT1_TTS_COPY_TEXT_MISSING")

    report1_blocked = bool(report1_blockers) and not stage2_report
    if report1_blocked:
        header = "# 보고서1 BLOCKED"
        status = "FAIL_REPORT1_BODY_MISSING"
        blocker = ", ".join(report1_blockers)

    visible_script_body = script_body or "(누락: visible script body)"
    visible_script_source = script_source or "N/A"
    visible_tts_copy_text = tts_copy_text or "(누락: tts_copy_text.txt)"
    visible_tts_source = tts_source or "N/A"
    return "\n".join(
        [
            header,
            "",
            (
                "대본 승인용: 아니오"
                if report1_blocked
                else ("대본 승인용: 예" if not stage2_report else "대본 승인용: 완료/확인 필요")
            ),
            "CapCut 생성: 아니오" if not stage2_report else "CapCut 생성: 다음 단계",
            "TTS 생성: 아니오" if not stage2_report else "TTS 생성: 다음 단계",
            "업로드 준비: 아니오",
            "",
            f"상태: {status}",
            f"모드: {mode}",
            "CapCut draft: NOT_CREATED",
            "draft path: N/A",
            f"source: {job_state['stage_scope_gate'].get('evidence') or 'N/A'}",
            f"reason: {job_state['stage_scope_gate'].get('reason') or 'N/A'}",
            "",
            f"대본 본문 source: {visible_script_source}",
            "대본 본문:",
            visible_script_body,
            "",
            f"중단 TTS 글자만 복사 source: {visible_tts_source}",
            "중단 TTS 글자만 복사:",
            visible_tts_copy_text,
            "",
            "대본 산출물:",
            "- 1차설계서 / timeline_design.json / timeline_design_gate.json",
            "- 상단/중단/구간오디오정책표",
            "- 중단 TTS 글자만 복사",
            "- humanize_korean_gate.json",
            "- block_map.json / block_role_map.json / block_voice_switch_map.json",
            "- tts_copy_text.txt",
            "",
            "handoff:",
            "- 다음 스킬: 000short-production-agent",
            "- 다음 단계: 보고서2 / CAPCUT_OPENABLE_PROJECT",
            "- 다음 채팅에 붙일 지시: Use $000short-production-agent",
            "- 필요 조건: 보고서1 승인 + TTS/오디오 방식 결정",
            "- 00-tikitaka는 보고서2를 작성하지 않는다",
            "",
            "RE-ENTRY:",
            f"- resume_stage: {reentry.get('resume_stage', 'g0_restart')}",
            f"- report: {reentry.get('report', '')}",
            "",
            "BLOCKERS:",
            f"- {blocker}",
            *[f"- {item}" for item in report1_blockers],
            "",
            "NEXT:",
            "- 사용자 선택: 수정 / 2단계 CapCut 프로젝트 / TTS MP3 제공 / Supertone 자동",
            "",
            build_stage_gate_todo(job_state).rstrip(),
            "",
        ]
    )


def build_visual_gate(job_state: dict[str, Any]) -> str:
    def line(label: str, block: dict[str, Any]) -> str:
        evidence = block.get("evidence") or "없음"
        status = block.get("status") or "MISSING"
        return f"{label}: {status} / evidence={evidence}"

    return "\n".join(
        [
            "[VISUAL HARNESS BOARD]",
            f"작업 ID: {job_state['job_id']}",
            line("요청 원문 보존", job_state["work_order"]),
            line("Work Order", job_state["work_order"]),
            line("Execution Spec", job_state["execution_spec"]),
            line("5작가 모드", job_state["persona_mode"]),
            line("Script Gate", job_state["script_gate"]),
            line("Script Handoff Gate", job_state["script_handoff_gate"]),
            line("Stage Scope Gate", job_state["stage_scope_gate"]),
            line("Re-entry Stage", job_state["reentry_stage"]),
            f"CapCut openable permission: {job_state['capcut_permission']}",
            f"Production status: {job_state['production_status']}",
            line("n8n", job_state["n8n"]),
            line("Validation Report", job_state["validation"]),
            line("Evidence Pack", job_state["evidence_pack"]),
            f"SCRIPT_LOCK: {job_state['script_lock']['status']} / reason={job_state['script_lock']['reason']}",
            f"최종 상태: {job_state['status']}",
            f"완료 보고 가능 여부: {'YES' if job_state['final_report_allowed'] else 'NO'}",
            "",
        ]
    )


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit(work_dir: Path, job_id: str) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    previous_state = read_json(work_dir / "job_state.json")

    trace = append_trace(work_dir, job_id)
    work_order = file_status(work_dir, "work_order.md", "work order")
    execution_spec = file_status(work_dir, "execution_spec.md", "execution spec")
    implementation_log = file_status(work_dir, "implementation_log.md", "implementation log")
    personas = persona_status(work_dir)
    script_gate = script_gate_status(work_dir)
    reentry_stage = reentry_stage_status(work_dir, previous_state)
    script_handoff_gate = build_script_handoff_gate(work_dir)
    stage_scope_gate = stage_scope_status(previous_state, work_dir)
    if passish(script_handoff_gate) and not passish(stage_scope_gate):
        script_handoff_gate = dict(script_handoff_gate)
        script_handoff_gate["capcut_allowed"] = False
        script_handoff_gate["capcut_blocker"] = stage_scope_gate.get("blocker") or "WAIT_USER_STAGE_DECISION"
        script_handoff_gate["stage_scope_gate"] = stage_scope_gate
    capcut_permission, production_status = capcut_permission_status(script_handoff_gate)
    report1_handoff_gate = build_report1_handoff_gate(
        previous_state,
        stage_scope_gate,
        script_handoff_gate,
        capcut_permission,
    )
    n8n = n8n_status(work_dir, previous_state)

    upstream = {
        "work_order": work_order,
        "execution_spec": execution_spec,
        "implementation_log": implementation_log,
        "persona_mode": personas,
        "script_gate": script_gate,
        "script_handoff_gate": script_handoff_gate,
        "stage_scope_gate": stage_scope_gate,
        "n8n": n8n,
        "harness_trace": trace,
    }
    missing = [name for name, block in upstream.items() if not passish(block) and block.get("status") != "DONE"]
    validation_status = "PASS" if not missing else "FAILED"
    validation = {
        "status": validation_status,
        "evidence": "validation_report.json",
        "missing_or_failed": missing,
        "checked_at": utc_now(),
        "rule": "fail_closed",
    }
    evidence_pack = {
        "status": "PASS" if validation_status == "PASS" else "FAILED",
        "evidence": "evidence_pack.json",
        "items": upstream,
        "checked_at": validation["checked_at"],
    }

    final_allowed = validation_status == "PASS" and evidence_pack["status"] == "PASS"
    script_lock = {
        "status": "SCRIPT_LOCK" if final_allowed else "NOT_LOCKED",
        "reason": "all required evidence present" if final_allowed else ", ".join(missing) + " missing or failed",
        "source": "tikitaka_harness_runner",
        "generated_by": "tikitaka_harness_runner",
        "writer_persona_pass_count": personas.get("count", 0),
        "hard_veto": script_gate.get("writer_persona_hard_veto", True),
        "script_handoff_gate_status": script_handoff_gate["status"],
        "capcut_allowed": capcut_permission == "CAPCUT_OPENABLE_PROJECT_ALLOWED",
        "capcut_blocker": (
            "" if capcut_permission == "CAPCUT_OPENABLE_PROJECT_ALLOWED" else capcut_permission
        ),
        "stage_scope_gate": stage_scope_gate,
    }
    state = {
        "job_id": job_id,
        "status": "SCRIPT_LOCK" if final_allowed else "DRAFT",
        "checked_at": validation["checked_at"],
        "user_stage_decision": stage_scope_gate["decision"],
        "work_order": work_order,
        "execution_spec": execution_spec,
        "implementation_log": implementation_log,
        "persona_mode": personas,
        "script_gate": script_gate,
        "script_handoff_gate": script_handoff_gate,
        "report1_handoff_gate": report1_handoff_gate,
        "stage_scope_gate": stage_scope_gate,
        "reentry_stage": reentry_stage,
        "capcut_permission": capcut_permission,
        "production_status": production_status,
        "n8n": n8n,
        "validation": validation,
        "evidence_pack": evidence_pack,
        "harness_trace": trace,
        "script_lock": script_lock,
        "final_report_allowed": final_allowed,
    }

    write_json(work_dir / "validation_report.json", validation)
    write_json(work_dir / "evidence_pack.json", evidence_pack)
    write_json(work_dir / "script_lock_evidence.json", script_lock)
    write_json(work_dir / "script_handoff_gate.json", script_handoff_gate)
    write_json(work_dir / "report1_handoff.json", report1_handoff_gate)
    write_json(work_dir / "job_state.json", state)
    (work_dir / "stage_gate_todo.md").write_text(build_stage_gate_todo(state), encoding="utf-8")
    (work_dir / "stage_scope_report.md").write_text(build_stage_scope_report(state, work_dir), encoding="utf-8")
    (work_dir / "visual_gate.md").write_text(build_visual_gate(state), encoding="utf-8")
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Tikitaka SCRIPT_LOCK evidence and fail closed.")
    parser.add_argument("work_dir", help="Tikitaka work directory containing evidence files")
    parser.add_argument("--job-id", default="", help="Stable job id for reporting")
    parser.add_argument("--allow-draft-exit-zero", action="store_true", help="Return 0 even when locked=false")
    args = parser.parse_args()

    job_id = args.job_id or dt.datetime.now().strftime("%Y-%m%d-%H%M%S")
    state = audit(Path(args.work_dir).resolve(), job_id)
    print(build_visual_gate(state), end="")

    if state["final_report_allowed"] or args.allow_draft_exit_zero:
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
