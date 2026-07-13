import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "111-politics-longform" / "SKILL.md"
SKILL_DIR = SKILL.parent


class PoliticsLongformEmbeddedContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL.read_text(encoding="utf-8-sig")

    def test_skill_embeds_common_longform_boundaries(self):
        for token in (
            "## 정치 롱폼 공통 제작 계약",
            "22factory_20260628",
            "Stage 1",
            "Stage 2",
            "1280x720",
            "speech_boundary_lock.json",
            "roughcut_edl_locked.json",
            "source_labels_locked.json",
            "harness",
            "ffprobe",
            "frame QA",
        ):
            self.assertIn(token, self.skill_text)

    def test_skill_does_not_depend_on_retired_common_skill(self):
        self.assertNotIn("22utube-production-agent", self.skill_text)

    def test_skill_uses_portable_workspace_roots(self):
        self.assertIn(r"${env:WORKSPACE_ROOT}\22factory_20260628", self.skill_text)
        self.assertIn(r"${env:UTUBE_ROOT}", self.skill_text)
        self.assertIn(r"docs\YOUTUBE_PRODUCTION_WORK_ORDER.md", self.skill_text)
        self.assertNotIn(r"C:\Users\arajun", self.skill_text)

    def test_new_source_evidence_prefers_factory_lane_and_legacy_is_read_only(self):
        self.assertIn(r"02_politics_longform\episodes\{episode_id}", self.skill_text)
        self.assertIn("legacy read-only fallback", self.skill_text)
        self.assertNotIn(
            "For source evidence, prefer the episode folder under `22utube\\11utube\\yellow\\episodes\\...`.",
            self.skill_text,
        )

    def test_capcut_backups_stay_outside_active_draft_and_cleanup_is_fail_closed(self):
        self.assertIn("outside the active CapCut draft tree", self.skill_text)
        self.assertIn("WAIT_PROJECT_CLEANUP", self.skill_text)
        self.assertIn("FAIL_PROJECT_CLEANUP", self.skill_text)

    def test_skill_folder_does_not_ship_stale_duplicate_contract(self):
        duplicates = [path.name for path in SKILL_DIR.glob("SKILL*.md") if path.name != "SKILL.md"]
        self.assertEqual(duplicates, [])


if __name__ == "__main__":
    unittest.main()
