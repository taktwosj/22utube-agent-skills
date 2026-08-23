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
        self.assertIn("IDM_JOBS_ROOT", self.text)
        for required in (
            "E:\정치롱폼\<YYMMDD HH시>\영상\<video_id>",
            "E:\쇼츠\<YYMMDD HH시>",
        ):
            self.assertIn(required, self.text)

    def test_destination_folder_is_a_required_argument(self):
        self.assertIn('ap.add_argument("dest_folder")', self.code)

    def test_youtube_routes_to_ytdlp_and_direct_files_route_to_idm(self):
        self.assertIn("## Routing — IDM is not for YouTube", self.text)
        self.assertIn("class RouteToYtdlp", self.code)
        self.assertIn("PAGE_RE.search(a.url) and not a.try_idm", self.code)
        self.assertIn("DIRECT_FILE_RE", self.code)

    def test_range_measurements_are_recorded(self):
        for required in ("Range 없음", "bytes=0-1048575", "bytes=0-10485759", "403"):
            self.assertIn(required, self.text)

    def test_player_client_defaults_away_from_android_vr(self):
        self.assertIn("player_client", self.text)
        self.assertIn('DEFAULT_CLIENT = "mweb,web_embedded"', self.code)
        self.assertIn("fetch_pot=always", self.code)

    def test_ytdlp_is_resolved_from_path_not_from_sys_executable(self):
        self.assertIn("def ytdlp_cmd", self.code)
        self.assertIn('shutil.which("yt-dlp")', self.code)
        self.assertNotIn('[sys.executable, "-m", "yt_dlp", "--no-warnings"', self.code)

    def test_idm_cannot_hang_on_an_error_dialog(self):
        self.assertIn("START_SEC", self.code)
        self.assertIn("한 바이트도 쓰지 못했다", self.code)

    def test_audio_is_required_only_for_extractor_page_urls(self):
        self.assertIn("def probe(p: Path, need_audio: bool = True):", self.code)
        self.assertIn("need_audio = bool(PAGE_RE.search(a.url))", self.code)

    def test_resolution_floor_is_available_and_blocks_the_move(self):
        self.assertIn("--min-height", self.text)
        self.assertIn('"--min-height"', self.code)
        self.assertIn("if a.min_height and isinstance(h, int) and h < a.min_height:", self.code)

    def test_audio_only_webm_is_named_weba(self):
        self.assertIn(".weba", self.text)
        self.assertIn("audio/webm", self.text)
        self.assertIn('if ext == "webm" and audio_only:', self.code)
        self.assertIn('return "weba"', self.code)

    def test_popup_is_fixed_by_renaming_not_by_clicking(self):
        self.assertIn("팝업을 자동 클릭하지 않는다. 이름을 고친다.", self.text)
        self.assertIn("IDM 을 호출하지 않는다", self.text)

    def test_ffprobe_gate_has_no_fallback(self):
        self.assertIn("ffprobe 게이트에는 폴백이 없다.", self.text)
        self.assertIn("ffprobe FAIL — 최종 폴더로 옮기지 않는다", self.code)

    def test_po_token_prerequisite_is_documented(self):
        self.assertIn("PO Token", self.text)
        self.assertIn("bgutil-ytdlp-pot-provider", self.text)


if __name__ == "__main__":
    unittest.main()
