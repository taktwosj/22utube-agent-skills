from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RetiredScriptWriterContractTests(unittest.TestCase):
    def test_retired_skills_are_not_managed_or_routable(self):
        active_files = [
            ROOT / "manifests" / "skill-set.json",
            ROOT / "skills" / "119-politics-longform-capcut" / "SKILL.md",
        ]
        retired_skills = [
            "00-tikitaka",
            "000short-production-agent",
            "001short-production-agent",
            "00script-writer",
            "0shrt-korea-production-agent",
            "josun-historychoon-production-agent",
            "00utube-lm-production-agent",
        ]

        for skill_name in retired_skills:
            self.assertFalse((ROOT / "skills" / skill_name).exists())
            for path in active_files:
                self.assertNotIn(
                    skill_name,
                    path.read_text(encoding="utf-8-sig"),
                    path.as_posix(),
                )

if __name__ == "__main__":
    unittest.main()
