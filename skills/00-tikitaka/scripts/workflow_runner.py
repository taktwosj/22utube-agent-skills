"""00-tikitaka workflow runner.

Reads validator results and enforces cost/ownership policy. Executes only
deterministic local operations:
- ledger append
- state projection rebuild
- compatibility pointer generation
- external packet generation (LOCAL only, never transported)

Never executes:
- external LLM calls
- paid actions
- CapCut GUI operations
- upload

This is a thin lane adapter. The hard policy lives in the shared core.
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
    / "00-tikitaka"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)


class RunnerAbort(Exception):
    """Raised when the runner must STOP per execution policy."""


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tikitaka_runner_core", GENERATED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tikitaka_runner_core"] = mod
    spec.loader.exec_module(mod)
    return mod


# Deterministic operations the runner is allowed to execute automatically.
ALLOWED_DETERMINISTIC_ACTIONS = {
    "PREPARE_G10",
    "PREPARE_G20",
    "PREPARE_OWNER_TRANSFER",
    "BUILD_R1_PACKET",
    "BUILD_R2_PACKET",
    "WRITE_COMPAT_POINTER",
    "REBUILD_STATE_PROJECTION",
    "STOP_AT_G20",
}

# Actions the runner must NEVER execute automatically, regardless of what
# the validator result requests.
FORBIDDEN_AUTO_ACTIONS = {
    "CALL_EXTERNAL_MODEL",
    "TRANSPORT_PACKET",
    "PAID_TTS",
    "OPEN_CAPCUT",
    "UPLOAD",
    "RELEASE",
}


def apply_validator_result(*, validator_result: dict, ledger, cost_guard) -> dict:
    """Decide what (if anything) the runner may execute next.

    Returns a runner decision record. The decision is logged to the ledger
    by the caller.
    """
    if validator_result.get("schema_version") != "gate-result-v1":
        raise RunnerAbort("INVALID_VALIDATOR_RESULT_SHAPE")

    advance_class = validator_result.get("auto_advance_class")
    if advance_class in ("LLM_CALL_ALLOWED", "PAID_ACTION_ALLOWED", "UPLOAD_ALLOWED"):
        raise RunnerAbort(f"FORBIDDEN_ADVANCE_CLASS {advance_class}")

    next_action = validator_result.get("next_action", "NONE")
    if next_action in FORBIDDEN_AUTO_ACTIONS:
        raise RunnerAbort(f"FORBIDDEN_AUTO_ACTION {next_action}")

    if validator_result.get("status") not in ("PASS", "NOT_REQUIRED"):
        return {
            "status": "STOP",
            "reason": f"VALIDATOR_STATUS={validator_result.get('status')}",
            "next_action": "NONE",
        }

    if next_action == "NONE":
        return {"status": "STOP", "reason": "NO_NEXT_ACTION", "next_action": "NONE"}

    if next_action not in ALLOWED_DETERMINISTIC_ACTIONS:
        return {
            "status": "WAIT_USER_INPUT",
            "reason": f"NEXT_ACTION_REQUIRES_USER {next_action}",
            "next_action": next_action,
        }

    # Deterministic local action authorized.
    return {
        "status": "EXECUTE_DETERMINISTIC",
        "next_action": next_action,
        "auto_advance_class": advance_class,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="00-tikitaka workflow runner (policy gate)."
    )
    parser.add_argument("--validator-result", type=Path, required=True)
    args = parser.parse_args(argv)
    result = json.loads(args.validator_result.read_text(encoding="utf-8"))
    core = _import_core()
    decision = apply_validator_result(
        validator_result=result,
        ledger=None,
        cost_guard=None,
    )
    print(json.dumps(decision, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
