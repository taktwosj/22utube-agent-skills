"""P10 thin-router and token-regression contract tests (RED first)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "tests" / "fixtures" / "shared_gates" / "token_baselines.json"
MIGRATION = (
    ROOT / "docs" / "migrations" / "shared-gates-separated-lanes-v2" / "token-regression.json"
)
VERIFY_PS1 = ROOT / "scripts" / "verify.ps1"

SKILLS = {
    "00-tikitaka": ["G00", "G10", "G20"],
    "000short-production-agent": ["G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"],
    "111-politics-longform": [
        "G00", "G10", "G20", "G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"
    ],
}


def _estimated_tokens(path: Path) -> int:
    return len(path.read_text(encoding="utf-8")) // 4


class ThinRouterContractTests(unittest.TestCase):
    def test_skill_md_routes_to_current_gate_reference(self):
        for skill, gates in SKILLS.items():
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("workflow.yaml", text)
                self.assertIn("Load exactly one current-gate reference", text)
                for gate in gates:
                    self.assertIn(f"references/gates/{gate.split('.')[0]}", text)

    def test_future_gate_reference_not_loaded(self):
        for skill in SKILLS:
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("Do not load future-gate references", text)

    def test_previous_gate_instruction_not_reloaded(self):
        for skill in SKILLS:
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("Do not reload previous-gate instructions", text)

    def test_full_srt_not_injected_by_default(self):
        for skill in SKILLS:
            text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn("Do not inject a full SRT by default", text)


class TokenRegressionBudgetTests(unittest.TestCase):
    def test_token_regression_budget(self):
        baseline = json.loads(BASELINES.read_text(encoding="utf-8"))
        self.assertEqual(baseline["estimator_version"], "chars_div_4_v1")
        before = [baseline["skills"][skill]["input_tokens"] for skill in SKILLS]
        after = [_estimated_tokens(ROOT / "skills" / skill / "SKILL.md") for skill in SKILLS]
        before_median = sorted(before)[len(before) // 2]
        after_median = sorted(after)[len(after) // 2]
        reduction_percent = (before_median - after_median) * 100 / before_median

        self.assertLessEqual(
            after_median,
            int(before_median * 1.10),
            "FAIL_TOKEN_REGRESSION: median input tokens increased by more than 10%",
        )
        self.assertGreaterEqual(reduction_percent, 30.0)

        report = json.loads(MIGRATION.read_text(encoding="utf-8"))
        self.assertEqual(report["baseline_median_input_tokens"], before_median)
        self.assertEqual(report["new_median_input_tokens"], after_median)
        self.assertEqual(report["reduction_percent"], round(reduction_percent, 2))
        self.assertEqual(report["target_status"], "TARGET_MET")


class VerifyFilenameRegressionTests(unittest.TestCase):
    def test_known_token_policy_files_are_explicitly_allowed_without_weakening_secret_pattern(self):
        text = VERIFY_PS1.read_text(encoding="utf-8")
        for path in (
            "tests/test_shared_gate_context_token_policy.py",
            "tests/test_shared_gate_token_regression.py",
            "tests/fixtures/shared_gates/token_baselines.json",
            "docs/migrations/shared-gates-separated-lanes-v2/token-regression.json",
        ):
            with self.subTest(path=path):
                self.assertIn(path, text)
        self.assertRegex(text, re.compile(r"secretPattern.*(env\|key\|token\|cookie\|session\|secret\|credential)", re.DOTALL))


if __name__ == "__main__":
    unittest.main()
