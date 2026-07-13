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

    def test_codex_interface_metadata_is_bundled(self):
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn('display_name: "Naver Blog Posting"', metadata)
        self.assertIn("allow_implicit_invocation: true", metadata)


if __name__ == "__main__":
    unittest.main()
