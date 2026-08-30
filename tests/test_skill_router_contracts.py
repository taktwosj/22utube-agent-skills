from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERAL_SHORTS = (
    ROOT / "skills" / "001short-production-agent" / "SKILL.md"
).read_text(encoding="utf-8")
POLITICS = (
    ROOT / "skills" / "119-politics-longform-capcut" / "SKILL.md"
).read_text(encoding="utf-8")


class SkillRouterContractTests(unittest.TestCase):
    def test_general_shorts_has_one_current_owner_and_lane(self):
        self.assertIn("owner_skill=001short-production-agent", GENERAL_SHORTS)
        self.assertIn("lane=general_shorts_production", GENERAL_SHORTS)
        self.assertIn("never chain another production skill", GENERAL_SHORTS)

    def test_general_shorts_is_not_a_cross_skill_handoff_chain(self):
        self.assertIn("Lane Isolation", GENERAL_SHORTS)
        self.assertNotIn("top5isu-shorts", GENERAL_SHORTS)
        self.assertIn("never chain another production skill", GENERAL_SHORTS)

    def test_politics_capcut_lane_remains_explicit_only(self):
        self.assertIn("Use only when", POLITICS)
        self.assertIn("사용자가 CapCut, 캡컷, 119, 119정치롱폼을 명시했을 때", POLITICS)
        self.assertIn("명시 호출이 없으면 119로 자동 우회하지 않는다", POLITICS)


if __name__ == "__main__":
    unittest.main()
