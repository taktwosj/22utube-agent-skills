import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_TEXT = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
OPENAI_YAML = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")


class OneCavemanContractTests(unittest.TestCase):
    def test_frontmatter_is_discoverable(self):
        self.assertRegex(SKILL_TEXT, r"(?m)^name: 1caveman$")
        self.assertRegex(
            SKILL_TEXT,
            r"(?m)^description: Use when Codex performs coding, modification, debugging, refactoring, validation, or code-review work\.$",
        )

    def test_execution_contract_is_complete(self):
        required = (
            "STATE_FIRST",
            "ONE_GOAL",
            "PROVE_FIRST",
            "MINIMAL_DIFF",
            "VERIFY",
            "CONTINUE_WITHIN_SCOPE",
            "REPORT_SHORT",
            "STOP_TWO_FAILURES",
            "WAIT_ROOT_CAUSE",
            "WAIT_SCOPE",
            "RESULT",
            "EVIDENCE",
            "NEXT",
            "The wrapper never replaces a user-required artifact",
            "Workspace rules and domain-specific safety skills remain authoritative.",
            "STOP_FOR_APPROVAL",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, SKILL_TEXT)

    def test_policy_is_independent_and_domain_neutral(self):
        forbidden = (
            "REQUIRED SUB-SKILL",
            "Use caveman",
            "$caveman",
            "CapCut",
            "001short",
            "119-politics",
            "dispatch",
            "PID",
            "receipt",
            "PowerShell",
            "prompt SHA",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, SKILL_TEXT)

    def test_first_free_form_message_has_one_visible_load_canary(self):
        rule = "After loading this skill, start the next free-form user-visible message with `CAVE` on its own line, exactly once."
        self.assertIn(rule, SKILL_TEXT)
        self.assertEqual(SKILL_TEXT.count("`CAVE`"), 1)

    def test_template_debris_is_removed(self):
        self.assertNotIn("TODO", SKILL_TEXT)
        self.assertLessEqual(len(SKILL_TEXT.splitlines()), 120)
        self.assertLessEqual(len(re.findall(r"\S+", SKILL_TEXT)), 200)

    def test_ui_metadata_targets_skill(self):
        self.assertIn('display_name: "1CAVEMAN"', OPENAI_YAML)
        self.assertIn("$1caveman", OPENAI_YAML)
        self.assertIn("every Codex coding task", OPENAI_YAML)

    def test_skill_package_is_ascii_english_only(self):
        paths = (
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents" / "openai.yaml",
            SKILL_ROOT / "tests" / "test_skill_contract.py",
        )
        for path in paths:
            with self.subTest(path=path.name):
                path.read_text(encoding="utf-8").encode("ascii")


if __name__ == "__main__":
    unittest.main()
