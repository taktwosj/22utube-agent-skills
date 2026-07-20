#!/usr/bin/env python3
"""Policy-only runner for the politics lane.

It returns a decision; it does not execute a gate, model call, paid action,
CapCut operation, release, or upload.
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
    / "111-politics-longform"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "politics_runner_core", GENERATED_CORE
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["politics_runner_core"] = module
    spec.loader.exec_module(module)
    return module


ALLOWED = {
    "PREPARE_G10",
    "PREPARE_G20",
    "PREPARE_G30",
    "PREPARE_G40",
    "PREPARE_G50",
    "PREPARE_G60",
    "PREPARE_G70",
    "PREPARE_G80",
    "PREPARE_G90",
    "REBUILD_STATE_PROJECTION",
}
WAIT = {
    "WAIT_EXTERNAL_RETURN",
    "WAIT_USER_EDITORIAL_CONFIRMATION",
    "WAIT_USER_VISUAL_GATE",
    "WAIT_UPLOAD_APPROVAL",
    "WAIT_USER_INPUT",
    "EPISODE_RELEASED",
}
FORBIDDEN_MARKERS = (
    "LLM",
    "MODEL",
    "PAID",
    "COST",
    "UPLOAD",
    "CAPCUT",
    "GUI",
    "RETRY",
    "TRANSPORT",
    "RELEASE",
)


def decide(result: dict) -> dict:
    if result.get("lane") != "politics_longform":
        return {
            "decision": "STOP",
            "status": "STOP",
            "reason": "CROSS_LANE_RESULT",
            "reason_code": "CROSS_LANE_RESULT",
        }
    shared = _import_core().decide_runner_action(
        validator_result=result,
        allowed_deterministic_actions=ALLOWED,
        wait_actions=WAIT,
    )
    decision = dict(shared)
    decision["decision"] = shared["status"]
    decision.setdefault("reason", shared.get("reason_code"))
    return decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validator-result", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.validator_result.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("validator result must be object")
        decision = decide(value)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        decision = {"decision": "STOP", "reason": f"INVALID_INPUT {exc}"}
    print(json.dumps(decision, indent=2, ensure_ascii=False))
    return 0 if decision["decision"] in {"EXECUTE_DETERMINISTIC", "WAIT"} else 1


if __name__ == "__main__":
    sys.exit(main())
