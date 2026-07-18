import json
import re
import unittest
from pathlib import Path


REPO = Path(__file__).parents[1]
SKILL_DIR = REPO / "skills" / "naver-blog-posting"
SKILL_FILE = SKILL_DIR / "SKILL.md"


class NaverBlogPostingContractTests(unittest.TestCase):
    def test_manifest_registers_codex_skill(self):
        manifest = json.loads(
            (REPO / "manifests" / "skill-set.json").read_text(encoding="utf-8")
        )
        entries = {entry["name"]: entry for entry in manifest["skills"]}

        self.assertIn("naver-blog-posting", entries)
        self.assertEqual(entries["naver-blog-posting"]["category"], "naver-blog")
        self.assertEqual(entries["naver-blog-posting"]["targets"], ["codex"])
        self.assertTrue(entries["naver-blog-posting"]["enabled"])

    def test_skill_defines_portable_blog_root_resolution(self):
        skill = SKILL_FILE.read_text(encoding="utf-8")
        required_fragments = (
            "{BLOG_ROOT}",
            "NAVER_BLOG_ROOT",
            "$env:OneDrive",
            "$env:OneDriveConsumer",
            "$env:OneDriveCommercial",
            "HKCU:\\Software\\Microsoft\\OneDrive\\Accounts",
            "scripts/naver_auto_queue.py",
            "assets/naver_images",
            "BLOG_ROOT_NOT_FOUND",
            "BLOG_ROOT_AMBIGUOUS",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, skill)

        self.assertIn(
            "{BLOG_ROOT}/assets/naver_images/임대아파트대출",
            skill,
        )
        self.assertIn("py -3 scripts\\naver_login.py --account <account>", skill)

    def test_skill_does_not_hardcode_a_windows_user_or_machine_onedrive_root(self):
        skill = SKILL_FILE.read_text(encoding="utf-8")

        self.assertIsNone(re.search(r"(?i)[A-Z]:\\Users\\[^<{%$\\]+", skill))
        self.assertNotIn("C:\\ONEtaktwosj", skill)

    def test_private_rental_main_image_uses_the_approved_pastel_card_contract(self):
        skill = SKILL_FILE.read_text(encoding="utf-8")
        required_fragments = (
            "메인 템플릿 시각 계약",
            "파스텔 카드형",
            "굵은 한글 3줄",
            "화면의 약 68~72%",
            "사용 가능 너비의 약 88%",
            "하단 약 18%",
            "1024px 기준 12~14px",
            "ExtraBlack",
            "검정 외곽선",
            "아파트 일러스트",
            "계약서·계산기·열쇠",
            "사송롯데",
            "캐슬민간",
            "호매실민간",
            "임대대출",
            "고정 메인 이미지 프롬프트",
            "빈 배경을 생성한 뒤 글자를 별도 합성하지 않는다",
            "Directly render these exact Korean headline lines",
            "Never omit, paraphrase, crop, or replace them with placeholders",
            "한글이 누락·오탈자·잘림·저대비이면",
            "파란 정보 박스 없음",
            "초록 대표 배지 없음",
            "빈 텍스트 영역 없음",
            "대표 이미지는 본문의 첫 번째 이미지",
        )

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, skill)

        self.assertNotIn("화면의 약 55~65%", skill)
        self.assertNotIn(
            "배경·프레임·아이콘만 생성한 뒤 정확한 한글을 별도 합성한다",
            skill,
        )

    def test_codex_interface_metadata_is_bundled(self):
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn('display_name: "Naver Blog Posting"', metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)


if __name__ == "__main__":
    unittest.main()
