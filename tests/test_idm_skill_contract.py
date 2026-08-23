import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "idm" / "SKILL.md"
SCRIPT = ROOT / "skills" / "idm" / "scripts" / "idm_download.py"


class IdmSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")
        cls.code = SCRIPT.read_text(encoding="utf-8")

    def test_skill_ships_its_own_downloader(self):
        self.assertTrue(SCRIPT.is_file())
        ast.parse(self.code)

    def test_save_path_is_chosen_per_purpose_and_never_on_desktop_or_c_drive(self):
        self.assertIn("## Save path — set it per purpose", self.text)
        self.assertIn("The script never decides where the file lands.", self.text)
        self.assertIn("Do not save to the Desktop or the C drive.", self.text)
        for required in (
            "E:\정치롱폼\<YYMMDD HH시>\영상\<video_id>",
            "E:\쇼츠\<YYMMDD HH시>",
        ):
            self.assertIn(required, self.text)

    def test_destination_folder_is_a_required_argument(self):
        self.assertIn('ap.add_argument("dest_folder")', self.code)

    def test_page_url_is_never_handed_to_idm(self):
        self.assertIn("Never point IDM at a page URL.", self.text)
        self.assertIn("def direct_streams", self.code)

    def test_resolution_floor_is_available_and_blocks_the_move(self):
        self.assertIn("--min-height", self.text)
        self.assertIn('"--min-height"', self.code)
        self.assertIn("if a.min_height and isinstance(h, int) and h < a.min_height:", self.code)

    def test_audio_only_webm_is_named_weba(self):
        self.assertIn(".weba", self.text)
        self.assertIn('if ext == "webm" and audio_only:', self.code)
        self.assertIn('return "weba"', self.code)

    def test_popup_is_fixed_by_renaming_not_by_clicking(self):
        self.assertIn("Never fix a popup by clicking it.", self.text)
        self.assertIn("Do not automate the popup. Fix the name.", self.text)

    def test_ffprobe_gate_has_no_fallback(self):
        self.assertIn("The ffprobe gate is not", self.text)
        self.assertIn("optional and has no fallback.", self.text)
        self.assertIn("ffprobe FAIL — 최종 폴더로 옮기지 않는다", self.code)

    def test_po_token_prerequisite_is_documented(self):
        self.assertIn("PO Token provider", self.text)
        self.assertIn("bgutil-ytdlp-pot-provider", self.text)


if __name__ == "__main__":
    unittest.main()
