import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TokenLoadingMapContractTest(unittest.TestCase):
    def test_required_token_loading_map_is_shipped_with_the_skill(self):
        token_map = ROOT / "TOKEN_LOADING_MAP.md"
        self.assertTrue(token_map.is_file())
        text = token_map.read_text(encoding="utf-8")
        self.assertIn("| 01 |", text)
        self.assertIn("| 09 |", text)

    def test_stage05_route_keeps_a12_reserved_empty(self):
        token_map = (ROOT / "TOKEN_LOADING_MAP.md").read_text(encoding="utf-8")
        contract = (ROOT / "references" / "root-contract-production-plan.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("references/root-contract-production-plan.md", token_map)
        self.assertIn("A12_RESERVED_EMPTY", token_map)
        self.assertIn("A12_RESERVED_EMPTY", contract)
        self.assertIn("Legacy v1 12-track note", contract)
        self.assertNotIn("A9, A11, or A12 template segments", contract)
        self.assertNotIn("including A9/A11/A12", contract)
        self.assertNotIn("A11, and A12 placements", contract)

    def test_stage08_routes_to_official_builder_and_manual_relink_contract(self):
        stage08 = (ROOT / "steps" / "08-capcut-assembly.md").read_text(encoding="utf-8")

        required = (
            "scripts/build_episode_capcut.py",
            "SOURCE_VIDEO_PROVISIONAL",
            "30_audio_srt/audio_lock.json",
            "30_audio_srt/caption_lock.json",
            "30_audio_srt/final.srt",
            "shrt_white_base_v2_15",
            "A12_RESERVED_EMPTY",
            "CapCut built-in vocal separation",
            "references/urakkai-artifact-contract.md",
            "project_path",
            "media_source_path",
            "references/interim-capcut-project-sync.md",
            "explicit sync",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, stage08)


if __name__ == "__main__":
    unittest.main()
