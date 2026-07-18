from __future__ import annotations

import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "skills" / "000short-production-agent"
VALIDATOR = PRODUCTION / "scripts" / "validate_top5isu_track_mapping.py"


def valid_mapping() -> dict:
    return {
        "template_profile": "top5isu_v1",
        "reference_project_name": "top5isu",
        "derived_from_reference_project": True,
        "fallback_allowed": False,
        "required_tracks": ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"],
        "image_effect_segments": 7,
        "image_ui_y": -600,
        "image_json_transform_y": -0.15625,
        "semantic_audio_resolution": {
            "audio.narration_tts": "A_TTS",
            "audio.speaker_source": "A_SOURCE",
            "audio.sfx": "A_SFX",
            "audio.bgm": "A_BGM",
        },
    }


class Top5IsuTrackMappingTests(unittest.TestCase):
    def test_valid_mapping_passes(self):
        module = load_source_module_no_bytecode("top5isu_mapping_valid", VALIDATOR)
        result = module.validate_top5isu_track_mapping(valid_mapping())
        self.assertEqual(result["top5isu_track_mapping_status"], "PASS")

    def test_shrt_white_fallback_is_rejected(self):
        module = load_source_module_no_bytecode("top5isu_mapping_fallback", VALIDATOR)
        data = valid_mapping()
        data["template_profile"] = "shrt_white_base_v1"
        data["reference_project_name"] = "shrt white"
        with self.assertRaisesRegex(module.GateFail, "FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN"):
            module.validate_top5isu_track_mapping(data)

    def test_wrong_track_order_or_coordinate_is_rejected(self):
        module = load_source_module_no_bytecode("top5isu_mapping_track", VALIDATOR)
        data = valid_mapping()
        data["required_tracks"][1:3] = ["T2", "TTS"]
        with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_TRACK_MAPPING"):
            module.validate_top5isu_track_mapping(data)

        data = valid_mapping()
        data["image_json_transform_y"] = -600
        with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_COORDINATE_LOCK"):
            module.validate_top5isu_track_mapping(data)

    def test_audio_lanes_are_semantic_unique_and_not_shrt_white_rows(self):
        module = load_source_module_no_bytecode("top5isu_mapping_audio", VALIDATOR)
        data = valid_mapping()
        data["semantic_audio_resolution"]["audio.speaker_source"] = "A_TTS"
        with self.assertRaisesRegex(module.GateFail, "FAIL_AUDIO_TRACK_MAPPING"):
            module.validate_top5isu_track_mapping(data)

        data = valid_mapping()
        data["semantic_audio_resolution"]["audio.narration_tts"] = "A9"
        with self.assertRaisesRegex(module.GateFail, "FAIL_AUDIO_TRACK_MAPPING"):
            module.validate_top5isu_track_mapping(data)

    def test_adapter_and_contract_are_documented_without_replacing_default(self):
        adapter = (PRODUCTION / "adapters" / "top5isu_v1.md").read_text(encoding="utf-8")
        layout = (PRODUCTION / "03_CAPCUT_LAYOUT_CONTRACT.md").read_text(encoding="utf-8")
        skill = (PRODUCTION / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("template_profile=top5isu_v1", adapter)
        self.assertIn("FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN", adapter)
        self.assertIn("image_json_transform_y=-0.15625", adapter)
        self.assertIn("ffmpeg loudnorm", adapter)
        self.assertIn("## top5isu_v1 Explicit Adapter", layout)
        self.assertIn("top5isu_v1", skill)
        self.assertIn("The default remains `shrt white`", skill)


if __name__ == "__main__":
    unittest.main()
