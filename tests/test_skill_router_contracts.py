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
        self.assertIn("하나의 lane만 확정", GENERAL_SHORTS)

    def test_general_shorts_is_not_a_cross_skill_handoff_chain(self):
        self.assertIn("다른 영상 제작 스킬의 단계, 템플릿, 상태명, validator, 산출물 계약을 읽거나 합치지 않는다", GENERAL_SHORTS)
        self.assertIn("다른 제작 스킬을 호출하지 않는다", GENERAL_SHORTS)

    def test_politics_capcut_lane_remains_explicit_only(self):
        self.assertIn("Use only when", POLITICS)
        self.assertIn("사용자가 CapCut을 직접 말했을 때만", POLITICS)
        self.assertIn("자동 우회", POLITICS)
        self.assertIn("FORBIDDEN", POLITICS)


if __name__ == "__main__":
    unittest.main()
