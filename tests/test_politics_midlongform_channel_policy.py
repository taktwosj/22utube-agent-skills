import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "111-politics-longform" / "SKILL.md"
POLICY = (
    ROOT
    / "skills"
    / "111-politics-longform"
    / "references"
    / "midlongform-channel-policy.md"
)


class PoliticsMidlongformChannelPolicyTests(unittest.TestCase):
    def test_skill_routes_midlongform_source_selection_to_pinned_policy(self):
        skill_text = SKILL.read_text(encoding="utf-8-sig")
        for token in (
            "references/midlongform-channel-policy.md",
            "WAIT_CHANNEL_NOT_ALLOWLISTED",
            "MBC 라디오 시사",
            "블랙리스트가 허용 목록보다 우선",
        ):
            self.assertIn(token, skill_text)

    def test_policy_pins_24_allowed_channels_and_one_blacklisted_channel(self):
        policy_text = POLICY.read_text(encoding="utf-8-sig")
        allowed = re.findall(r"^\| ALLOW \|", policy_text, flags=re.MULTILINE)
        blocked = re.findall(r"^\| BLOCK \|", policy_text, flags=re.MULTILINE)
        self.assertEqual(len(allowed), 24)
        self.assertEqual(len(blocked), 1)

        for token in (
            "KTV 국민방송",
            "이재명",
            "김어준의 겸손은힘들다 뉴스공장",
            "최욱의 매불쇼",
            "뉴스타파 Newstapa",
            "델리민주 [더민주당]",
            "MBCNEWS",
            "Channel A News",
            "UCIMOytYIzaUpoAM2bpT4JZQ",
            "UCfq4V1DAuaojnr2ryvWNysw",
            "@mbcradio_sisa",
        ):
            self.assertIn(token, policy_text)

    def test_policy_separates_channel_eligibility_from_rights_clearance(self):
        policy_text = POLICY.read_text(encoding="utf-8-sig")
        self.assertIn("rights/fair-use PASS를 뜻하지 않는다", policy_text)
        self.assertIn("채널 ID를 이름보다 우선", policy_text)


if __name__ == "__main__":
    unittest.main()
