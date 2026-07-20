"""000short-production-agent workflow runner.

Reads validator results and enforces cost/ownership policy. Executes only
deterministic local operations. Never executes external LLM calls, paid
actions without COST_AUTHORIZED, CapCut GUI operations, or upload.

Thin lane adapter. The hard policy lives in the shared generated core.
"""

from __future__ import annotations

import argparse
import json
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


class RunnerAbort(Exception):
    pass


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "short_prod_runner_core", GENERATED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["short_prod_runner_core"] = mod
    spec.loader.exec_module(mod)
    return mod


ALLOWED_DETERMINISTIC_ACTIONS = {
    "PREPARE_G40",
    "PREPARE_G50",
    "PREPARE_G60",
    "PREPARE_G80",
    "PREPARE_G90",
    "REBUILD_STATE_PROJECTION",
    "WRITE_COMPAT_POINTER",
}

# WAIT_* actions are allowed as next_action but they STOP the runner —
# they never execute automatically.
WAIT_ACTIONS = {
    "WAIT_USER_VISUAL_GATE",
    "WAIT_UPLOAD_APPROVAL",
    "WAIT_PAID_ACTION_APPROVAL",
    "WAIT_TIKITAKA_DESIGN_REPAIR",
    "WAIT_USER_INPUT",
    "EPISODE_RELEASED",
}

FORBIDDEN_AUTO_ACTIONS = {
    "CALL_EXTERNAL_MODEL",
    "TRANSPORT_PACKET",
    "PAID_TTS_WITHOUT_COST_EVENT",
    "OPEN_CAPCUT",
    "UPLOAD",
    "RELEASE_WITHOUT_APPROVAL",
}


def apply_validator_result(*, validator_result: dict) -> dict:
    if validator_result.get("schema_version") != "gate-result-v1":
        raise RunnerAbort("INVALID_VALIDATOR_RESULT_SHAPE")

    advance_class = validator_result.get("auto_advance_class")
    if advance_class in ("LLM_CALL_ALLOWED", "PAID_ACTION_ALLOWED", "UPLOAD_ALLOWED"):
        raise RunnerAbort(f"FORBIDDEN_ADVANCE_CLASS {advance_class}")

    next_action = validator_result.get("next_action", "NONE")
    if next_action in FORBIDDEN_AUTO_ACTIONS:
        raise RunnerAbort(f"FORBIDDEN_AUTO_ACTION {next_action}")

    status = validator_result.get("status")
    if status not in ("PASS", "NOT_REQUIRED", "WAIT_UPLOAD_APPROVAL"):
        return {
            "status": "STOP",
            "reason": f"VALIDATOR_STATUS={status}",
            "next_action": "NONE",
        }

    if next_action in WAIT_ACTIONS:
        return {
            "status": "WAIT",
            "reason": next_action,
            "next_action": next_action,
        }

    if next_action == "NONE":
        return {"status": "STOP", "reason": "NO_NEXT_ACTION", "next_action": "NONE"}

    if next_action not in ALLOWED_DETERMINISTIC_ACTIONS:
        return {
            "status": "WAIT_USER_INPUT",
            "reason": f"NEXT_ACTION_REQUIRES_USER {next_action}",
            "next_action": next_action,
        }

    return {
        "status": "EXECUTE_DETERMINISTIC",
        "next_action": next_action,
        "auto_advance_class": advance_class,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="000short-production-agent workflow runner (policy gate)."
    )
    parser.add_argument("--validator-result", type=Path, required=True)
    args = parser.parse_args(argv)
    result = json.loads(args.validator_result.read_text(encoding="utf-8"))
    decision = apply_validator_result(validator_result=result)
    print(json.dumps(decision, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
