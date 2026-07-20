"""P08 shared deterministic runner and episode cost-guard tests (RED first)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "shared" / "workflow-harness" / "core"
RUNNER_POLICY = CORE / "runner_policy.py"
COST_GUARD = CORE / "cost_guard.py"
GATE_VALIDATION = CORE / "gate_validation.py"
LEDGER_SCHEMA = (
    ROOT
    / "shared"
    / "workflow-harness"
    / "schemas"
    / "gate_ledger_event.schema.json"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SharedRunnerCostGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = _load("p08_runner_policy", RUNNER_POLICY)
        cls.cost = _load("p08_cost_guard", COST_GUARD)
        cls.validator = _load("p08_gate_validation", GATE_VALIDATION)

    def _result(self, action: str, *, advance_class: str = "DETERMINISTIC_ONLY"):
        return {
            "schema_version": "gate-result-v1",
            "status": "PASS",
            "lane": "politics_longform",
            "gate": "G20",
            "next_action": action,
            "auto_advance_allowed": True,
            "auto_advance_class": advance_class,
        }

    def test_validator_never_executes_next_stage(self):
        called = []
        result = self.validator.validate_gate(
            lane="politics_longform",
            gate="G20",
            subgate=None,
            validated_inputs=[],
            evidence=[],
            errors=[],
            warnings=[],
            next_action="PREPARE_G30",
            auto_advance_allowed=True,
            auto_advance_class="DETERMINISTIC_ONLY",
        )
        self.assertEqual(result["next_action"], "PREPARE_G30")
        self.assertEqual(called, [])

    def test_runner_rejects_llm_auto_action(self):
        decision = self.runner.decide_runner_action(
            validator_result=self._result("CALL_EXTERNAL_MODEL"),
            allowed_deterministic_actions={"PREPARE_G30"},
            wait_actions=set(),
        )
        self.assertEqual(decision["status"], "STOP")
        self.assertEqual(decision["reason_code"], "FORBIDDEN_AUTO_ACTION")

    def test_runner_rejects_unapproved_paid_action(self):
        decision = self.runner.decide_runner_action(
            validator_result=self._result("PAID_TTS"),
            allowed_deterministic_actions=set(),
            wait_actions=set(),
            episode_id="EP-01",
            paid_action={
                "action_id": "tts",
                "cost_usd": 1.25,
                "chars": 500,
            },
            cost_guard=self.cost.CostGuard(
                episode_budget_usd=10,
                max_model_input_tokens_per_gate=1000,
                max_model_output_tokens_per_gate=1000,
                max_paid_tts_chars=1000,
                paid_tts_authorization={
                    "status": "AUTHORIZED_FOR_EPISODE",
                    "scope": "tts_only",
                    "max_chars": 1000,
                },
            ),
            ledger_events=[],
        )
        self.assertEqual(decision["status"], "STOP")
        self.assertEqual(decision["reason_code"], "COST_AUTHORIZED_EVENT_REQUIRED")

    def test_max_auto_retries_is_zero(self):
        decision = self.runner.decide_runner_action(
            validator_result=self._result("PREPARE_G30"),
            allowed_deterministic_actions={"PREPARE_G30"},
            wait_actions=set(),
        )
        self.assertEqual(decision["status"], "EXECUTE_DETERMINISTIC")
        self.assertEqual(decision["max_auto_retries"], 0)

    def test_unknown_cost_stops(self):
        guard = self.cost.CostGuard(
            episode_budget_usd=10,
            max_model_input_tokens_per_gate=None,
            max_model_output_tokens_per_gate=None,
            max_paid_tts_chars=1000,
            paid_tts_authorization={
                "status": "AUTHORIZED_FOR_EPISODE",
                "scope": "tts_only",
                "max_chars": 1000,
            },
        )
        decision = guard.authorize_paid_action(
            episode_id="EP-01",
            action_id="tts",
            cost_usd=None,
            chars=100,
            ledger_events=[],
        )
        self.assertEqual(decision["status"], "STOP")
        self.assertEqual(decision["reason_code"], "UNKNOWN_COST")

    def test_cost_budget_overrun_stops(self):
        guard = self.cost.CostGuard(
            episode_budget_usd=1.0,
            max_model_input_tokens_per_gate=None,
            max_model_output_tokens_per_gate=None,
            max_paid_tts_chars=1000,
            paid_tts_authorization={
                "status": "AUTHORIZED_FOR_EPISODE",
                "scope": "tts_only",
                "max_chars": 1000,
            },
        )
        decision = guard.authorize_paid_action(
            episode_id="EP-01",
            action_id="tts",
            cost_usd=1.01,
            chars=100,
            ledger_events=[
                {
                    "event_type": "COST_AUTHORIZED",
                    "episode_id": "EP-01",
                    "action_id": "tts",
                    "max_cost_usd": 2.0,
                    "actor": "USER",
                }
            ],
        )
        self.assertEqual(decision["status"], "STOP")
        self.assertEqual(decision["reason_code"], "BUDGET_OVERRUN")

    def test_cost_authorization_must_match_episode_and_limit(self):
        guard = self.cost.CostGuard(
            episode_budget_usd=10.0,
            max_model_input_tokens_per_gate=None,
            max_model_output_tokens_per_gate=None,
            max_paid_tts_chars=1000,
            paid_tts_authorization={
                "status": "AUTHORIZED_FOR_EPISODE",
                "scope": "tts_only",
                "max_chars": 1000,
            },
        )
        wrong_episode = guard.authorize_paid_action(
            episode_id="EP-01",
            action_id="tts",
            cost_usd=1.0,
            chars=100,
            ledger_events=[
                {
                    "event_type": "COST_AUTHORIZED",
                    "episode_id": "EP-02",
                    "action_id": "tts",
                    "max_cost_usd": 2.0,
                    "actor": "USER",
                }
            ],
        )
        self.assertEqual(wrong_episode["status"], "STOP")

    def test_authorized_paid_action_still_waits_and_accepts_ledger_store(self):
        class LedgerStore:
            events = [
                {
                    "event_type": "COST_AUTHORIZED",
                    "episode_id": "EP-01",
                    "action_id": "tts",
                    "max_cost_usd": 2.0,
                    "actor": "USER",
                }
            ]

        decision = self.runner.decide_runner_action(
            validator_result=self._result("PAID_TTS"),
            allowed_deterministic_actions=set(),
            wait_actions=set(),
            episode_id="EP-01",
            paid_action={"action_id": "tts", "cost_usd": 1.0, "chars": 100},
            cost_guard=self.cost.CostGuard(
                episode_budget_usd=10.0,
                max_model_input_tokens_per_gate=None,
                max_model_output_tokens_per_gate=None,
                max_paid_tts_chars=1000,
                paid_tts_authorization={
                    "status": "AUTHORIZED_FOR_EPISODE",
                    "scope": "tts_only",
                    "max_chars": 1000,
                },
            ),
            ledger_events=LedgerStore(),
        )
        self.assertEqual(decision["status"], "WAIT")
        self.assertEqual(decision["max_auto_retries"], 0)

    def test_failed_validator_blocks_even_authorized_paid_action(self):
        result = self._result("PAID_TTS")
        result["status"] = "FAIL"
        decision = self.runner.decide_runner_action(
            validator_result=result,
            allowed_deterministic_actions=set(),
            wait_actions=set(),
            episode_id="EP-01",
            paid_action={"action_id": "tts", "cost_usd": 1.0, "chars": 100},
            cost_guard=self.cost.CostGuard(
                episode_budget_usd=10.0,
                max_model_input_tokens_per_gate=None,
                max_model_output_tokens_per_gate=None,
                max_paid_tts_chars=1000,
                paid_tts_authorization={
                    "status": "AUTHORIZED_FOR_EPISODE",
                    "scope": "tts_only",
                    "max_chars": 1000,
                },
            ),
            ledger_events=[
                {
                    "event_type": "COST_AUTHORIZED",
                    "episode_id": "EP-01",
                    "action_id": "tts",
                    "max_cost_usd": 2.0,
                    "actor": "USER",
                }
            ],
        )
        self.assertEqual(decision["status"], "STOP")
        self.assertEqual(decision["reason_code"], "VALIDATOR_NOT_PASS")

    def test_cost_authorized_event_schema_requires_exact_action_limit(self):
        import json

        schema = json.loads(LEDGER_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("action_id", schema["properties"])
        self.assertIn("max_cost_usd", schema["properties"])
        conditional_text = json.dumps(schema.get("allOf", []), sort_keys=True)
        self.assertIn("COST_AUTHORIZED", conditional_text)
        self.assertIn("action_id", conditional_text)
        self.assertIn("max_cost_usd", conditional_text)


if __name__ == "__main__":
    unittest.main()
