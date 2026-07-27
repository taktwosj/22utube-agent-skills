import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "1caveman" / "SKILL.md"


class OneCavemanSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_skill_is_explicitly_standalone(self):
        self.assertIn("This skill is standalone.", self.text)
        self.assertIn("no other skill required", self.text)
        self.assertNotIn("REQUIRED SUB-SKILL", self.text)
        self.assertNotIn("Use caveman", self.text)

    def test_compact_reporting_rules_are_embedded(self):
        for required in (
            "## Compact Reporting Style",
            "Remove filler",
            "State each fact once.",
            "Never invent abbreviations",
            "Quote only the shortest decisive error.",
            "Keep code blocks unchanged.",
        ):
            self.assertIn(required, self.text)


if __name__ == "__main__":
    unittest.main()