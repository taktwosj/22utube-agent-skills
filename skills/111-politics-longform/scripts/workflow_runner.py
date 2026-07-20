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
    if result.get("schema_version") != "gate-result-v1":
        return {"decision": "STOP", "reason": "INVALID_VALIDATOR_RESULT"}
    if result.get("lane") != "politics_longform":
        return {"decision": "STOP", "reason": "CROSS_LANE_RESULT"}
    advance_class = result.get("auto_advance_class")
    if advance_class not in ("NONE", "DETERMINISTIC_ONLY"):
        return {"decision": "STOP", "reason": "FORBIDDEN_ADVANCE_CLASS"}
    action = str(result.get("next_action", "NONE"))
    if action in WAIT:
        return {"decision": "WAIT", "reason": action, "next_action": action}
    if any(marker in action.upper() for marker in FORBIDDEN_MARKERS):
        return {"decision": "STOP", "reason": f"FORBIDDEN_ACTION {action}"}
    if result.get("status") != "PASS":
        return {"decision": "STOP", "reason": f"VALIDATOR_STATUS={result.get('status')}"}
    if action not in ALLOWED:
        return {"decision": "STOP", "reason": f"UNLISTED_ACTION {action}"}
    if result.get("auto_advance_allowed") is not True:
        return {"decision": "STOP", "reason": "AUTO_ADVANCE_NOT_ALLOWED"}
    return {
        "decision": "EXECUTE_DETERMINISTIC",
        "next_action": action,
        "max_auto_retries": 0,
    }


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
