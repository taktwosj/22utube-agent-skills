from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLITICS = (
    ROOT / "skills" / "119-politics-longform-capcut" / "SKILL.md"
).read_text(encoding="utf-8")


class SkillRouterContractTests(unittest.TestCase):
    def test_politics_capcut_lane_remains_explicit_only(self):
        self.assertIn("Use only when", POLITICS)
        self.assertIn("사용자가 CapCut을 직접 말했을 때만", POLITICS)
        self.assertIn("자동 우회", POLITICS)
        self.assertIn("FORBIDDEN", POLITICS)


if __name__ == "__main__":
    unittest.main()
