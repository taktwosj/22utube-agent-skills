from __future__ import annotations

import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_shrt_white_track_mapping.py"
)


def valid_mapping() -> dict:
    return {
        "template_profile": "shrt_white_base_v1",
        "reference_project_name": "shrt white",
        "derived_from_reference_project": True,
        "semantic_audio_resolution": {
            "audio.narration_tts": "A9",
            "audio.speaker_source": "A10",
            "audio.sfx": "A11",
            "audio.bgm": "A12",
        },
    }


class ShrtWhiteTrackMappingTests(unittest.TestCase):
    def test_shrt_white_semantic_audio_mapping_passes(self):
        module = load_source_module_no_bytecode("shrt_white_track_mapping_valid", VALIDATOR)

        result = module.validate_shrt_white_track_mapping(valid_mapping())

        self.assertEqual(result["shrt_white_track_mapping_status"], "PASS")

    def test_a9_a10_reversed_fails(self):
        module = load_source_module_no_bytecode("shrt_white_track_mapping_reversed", VALIDATOR)
        data = valid_mapping()
        data["semantic_audio_resolution"]["audio.narration_tts"] = "A10"
        data["semantic_audio_resolution"]["audio.speaker_source"] = "A9"

        with self.assertRaisesRegex(module.GateFail, "FAIL_AUDIO_TRACK_MAPPING"):
            module.validate_shrt_white_track_mapping(data)

    def test_non_shrt_white_reference_fails(self):
        module = load_source_module_no_bytecode("shrt_white_track_mapping_non_default", VALIDATOR)
        data = valid_mapping()
        data["reference_project_name"] = "260708 short"

        with self.assertRaisesRegex(module.GateFail, "FAIL_SHRT_WHITE_BASE_NOT_CLONED"):
            module.validate_shrt_white_track_mapping(data)


if __name__ == "__main__":
    unittest.main()
