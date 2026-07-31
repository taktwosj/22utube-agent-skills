from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_agent_model_routing.py"
POLICY = ROOT / "config" / "agent-model-routing-v1.yaml"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_agent_model_routing", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_policy():
    return yaml.safe_load(POLICY.read_text(encoding="utf-8"))


def test_canonical_policy_passes():
    load_validator().validate(load_policy())


def test_ultra_default_on_fails():
    validator = load_validator()
    policy = load_policy()
    policy["cost_control"]["ultra"]["enabled_by_default"] = True
    try:
        validator.validate(policy)
    except validator.PolicyError as exc:
        assert "Ultra must default OFF" in str(exc)
    else:
        raise AssertionError("Ultra default ON must fail")


def test_s2r_repeat_limit_is_enforced():
    validator = load_validator()
    policy = load_policy()
    route = policy["skills"]["110-politics-longform-script"]["stages"]["s2r_full_rewrite"]
    route["max_runs_per_episode"] = 2
    try:
        validator.validate(policy)
    except validator.PolicyError as exc:
        assert "limited to one run" in str(exc)
    else:
        raise AssertionError("S2R repeat limit drift must fail")


def test_deterministic_validator_cannot_call_model():
    validator = load_validator()
    policy = load_policy()
    policy["workers"]["deterministic_validator"]["model"] = "luna"
    try:
        validator.validate(policy)
    except validator.PolicyError as exc:
        assert "must not call a model" in str(exc)
    else:
        raise AssertionError("deterministic validator model call must fail")
