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


PASS_VALUES = {"PASS", "DONE", "SCRIPT_LOCK", "SCRIPT_LOCKED", "HARNESS_PASS"}
FAIL_VALUES = {"FAIL", "FAILED", "BLOCK", "BLOCKED", "SCRIPT_REWRITE", "HARNESS_FAILED"}
SCRIPT_LOCK_PACKAGE_FILES = {
    "original_structure_summary": "original_structure_summary.md",
    "urakkai_structure_plan": "urakkai_structure_plan.md",
    "urakkai_structure_delta": "urakkai_structure_delta.json",
    "block_map": "block_map.json",
    "block_role_map": "block_role_map.json",
    "block_voice_switch_map": "block_voice_switch_map.json",
    "tts_copy_text": "tts_copy_text.txt",
}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


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
    if explicit_pass and (pass_count is None or pass_count_ok) and (hard_veto is None or hard_veto_ok):
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


def build_script_handoff_gate(work_dir: Path) -> dict[str, Any]:
    checks = {
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
        "urakkai_structure_delta": json_artifact_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["urakkai_structure_delta"],
            "urakkai structure delta",
        ),
        "block_map": block_map_status(work_dir),
        "block_role_map": json_artifact_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["block_role_map"],
            "block role map",
        ),
        "block_voice_switch_map": json_artifact_status(
            work_dir,
            SCRIPT_LOCK_PACKAGE_FILES["block_voice_switch_map"],
            "block voice switch map",
        ),
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
    if passish(script_handoff_gate) and script_handoff_gate.get("script_status") == "SCRIPT_LOCK_PACKAGE":
        return "CAPCUT_OPENABLE_PROJECT_ALLOWED", "WAIT_CAPCUT_OPENABLE_PROJECT"
    return "WAIT_SCRIPT_HANDOFF_GATE", "WAIT_SCRIPT_HANDOFF_GATE"


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
    script_handoff_gate = build_script_handoff_gate(work_dir)
    capcut_permission, production_status = capcut_permission_status(script_handoff_gate)
    n8n = n8n_status(work_dir, previous_state)

    upstream = {
        "work_order": work_order,
        "execution_spec": execution_spec,
        "implementation_log": implementation_log,
        "persona_mode": personas,
        "script_gate": script_gate,
        "script_handoff_gate": script_handoff_gate,
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
        "status": "SCRIPT_LOCKED" if final_allowed else "NOT_LOCKED",
        "reason": "all required evidence present" if final_allowed else ", ".join(missing) + " missing or failed",
    }
    state = {
        "job_id": job_id,
        "status": "SCRIPT_LOCKED" if final_allowed else "DRAFT",
        "checked_at": validation["checked_at"],
        "work_order": work_order,
        "execution_spec": execution_spec,
        "implementation_log": implementation_log,
        "persona_mode": personas,
        "script_gate": script_gate,
        "script_handoff_gate": script_handoff_gate,
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
    write_json(work_dir / "script_handoff_gate.json", script_handoff_gate)
    write_json(work_dir / "job_state.json", state)
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
