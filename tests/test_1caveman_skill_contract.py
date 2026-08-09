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

    def test_local_shared_skill_update_contract_is_embedded(self):
        frontmatter = self.text.split("---", 2)[1]
        self.assertIn("## Local Shared Skill Update", self.text)
        section = self.text.split("## Local Shared Skill Update", 1)[1].split("\n## ", 1)[0]

        for trigger in ("스킬 업데이트", "스킬 최신화", "스킬 적용", "skill update"):
            self.assertIn(trigger, frontmatter)

        for required in (
            "current computer Codex, Claude, and Hermes only",
            "Never deploy to another PC.",
            "clean confirmed source commit",
            "WAIT_COMMIT_CONFIRMATION",
            "source `HEAD`",
            "local runtime `active.json.release_id`",
            "python -B scripts/skill_release.py verify --target all --self-check",
            "SKIP_SAME_VERSION",
            "Do not publish, activate, back up, or relink.",
            "python -B scripts/skill_release.py publish",
            "python -B scripts/skill_release.py activate --target all",
            "Never use `update.ps1`, `install.ps1`, direct copies, or the save watcher",
            "runtime-deployment authorization for this current computer",
            "source commit, push, or merge retains its separate explicit user approval gate",
        ):
            self.assertIn(required, section)

        authorization_rule = section.split("Treat an explicit user", 1)[1]
        for trigger in ("스킬 업데이트", "스킬 최신화", "스킬 적용", "skill update"):
            self.assertIn(trigger, authorization_rule)


if __name__ == "__main__":
    unittest.main()
