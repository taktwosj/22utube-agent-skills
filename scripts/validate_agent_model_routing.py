#!/usr/bin/env python3
"""Validate the central agent model-routing and cost-control policy."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


class PolicyError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PolicyError(message)


def at(root: dict[str, Any], *keys: str) -> Any:
    value: Any = root
    for key in keys:
        require(isinstance(value, dict) and key in value, f"missing: {'.'.join(keys)}")
        value = value[key]
    return value


def validate(policy: dict[str, Any]) -> None:
    require(policy.get("schema_version") == "agent_model_routing_v1", "invalid schema_version")

    ultra = at(policy, "cost_control", "ultra")
    require(ultra.get("enabled_by_default") is False, "Ultra must default OFF")
    require(ultra.get("automatic_call") is False, "Ultra automatic calls must be OFF")
    require(ultra.get("normal_production") == "forbidden", "Ultra must be forbidden in normal production")
    require(ultra.get("max_runs_per_incident") == 1, "Ultra incident limit must be 1")

    escalation = at(policy, "cost_control", "escalation_order")
    require(escalation == [
        "luna_medium", "terra_medium", "terra_high", "sol_high", "sol_extra_high", "sol_max"
    ], "unexpected escalation order")
    require(at(policy, "cost_control", "skip_escalation_steps") is False, "escalation steps cannot be skipped")
    require(at(policy, "cost_control", "extra_high_auto_repeat") is False, "Extra High auto-repeat must be OFF")

    hermes = at(policy, "hermes", "default")
    require(hermes == {"model": "terra", "effort": "medium"}, "Hermes default must be Terra/Medium")

    validator = at(policy, "workers", "deterministic_validator")
    require(validator.get("executor") == "main_runtime", "validator must run in main runtime")
    require(validator.get("model") == "none", "deterministic validator must not call a model")

    skills = at(policy, "skills")
    required_skills = {
        "001short-production-agent",
        "110-politics-longform-script",
        "111-politics-longform-voice-srt",
        "112-politics-longform-hyperframes",
    }
    require(required_skills.issubset(skills), "one or more required skill routes are missing")

    s2r = at(policy, "skills", "110-politics-longform-script", "stages", "s2r_full_rewrite")
    require(s2r.get("model") == "sol" and s2r.get("effort") == "extra_high", "110 S2R must use Sol/Extra High")
    require(s2r.get("max_runs_per_episode") == 1, "110 S2R must be limited to one run per episode")
    require(s2r.get("repeat_same_source_packet") is False, "110 S2R same-packet repeat must be disabled")

    v4 = at(policy, "skills", "112-politics-longform-hyperframes", "stages", "p5_v4_complex_design")
    require(v4.get("max_runs") == 1, "112 V4 Extra High must be limited to one run")

    review = at(policy, "external_review_policy")
    require(review.get("mode") == "user_manual", "external review must be USER_MANUAL")
    require(review.get("automatic_call") is False, "external review automatic calls must be OFF")
    require(review.get("external_pass_is_final") is False, "external PASS cannot be final authority")

    receipt = at(policy, "cost_control", "execution_receipt", "required")
    require(set(receipt) == {"actual_model", "actual_effort", "ultra_used"}, "execution receipt fields are incomplete")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "policy",
        nargs="?",
        default="config/agent-model-routing-v1.yaml",
        type=Path,
    )
    args = parser.parse_args()

    try:
        data = yaml.safe_load(args.policy.read_text(encoding="utf-8"))
        require(isinstance(data, dict), "policy root must be a mapping")
        validate(data)
    except (OSError, yaml.YAMLError, PolicyError) as exc:
        print(f"FAIL_AGENT_MODEL_ROUTING: {exc}", file=sys.stderr)
        return 1

    print("PASS_AGENT_MODEL_ROUTING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
