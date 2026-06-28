from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_capcut_timeline_order.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("validate_capcut_timeline_order", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def effect(effect_id: str, effect_type: str, value: float) -> dict:
    return {"id": effect_id, "type": effect_type, "value": value}


def source_material(material_id: str) -> dict:
    return {
        "id": material_id,
        "type": "video",
        "path": f"C:/work/{material_id}.mp4",
        "has_audio": True,
        "video_algorithm": {
            "algorithms": [{"type": "QualityEnhance"}],
            "quality_enhance": {"level": 0, "from": "multi_track"},
        },
    }


def source_segment(material_id: str, refs: list[str]) -> dict:
    return {
        "material_id": material_id,
        "extra_material_refs": refs,
        "enable_smart_color_adjust": True,
        "enable_adjust": True,
        "target_timerange": {"start": 0, "duration": 1_000_000},
    }


def valid_draft() -> dict:
    return {
        "materials": {
            "videos": [source_material("v1"), source_material("v2")],
            "effects": [
                effect("smart1", "smart_color_adjust", 0.30),
                effect("clear1", "clear", 0.35),
                effect("sharp1", "sharpen", 0.40),
                effect("part1", "particle", 0.05),
                effect("smart2", "smart_color_adjust", 0.40),
                effect("clear2", "clear", 0.45),
                effect("sharp2", "sharpen", 0.50),
                effect("part2", "particle", 0.30),
            ],
            "loudnesses": [{"enable": True, "target_loudness": -14.0}],
        },
        "tracks": [
            {
                "type": "video",
                "segments": [
                    source_segment("v1", ["smart1", "clear1", "sharp1", "part1"]),
                    source_segment("v2", ["smart2", "clear2", "sharp2", "part2"]),
                ],
            }
        ],
    }


class MandatoryCapCutMediaSettingsTests(unittest.TestCase):
    def test_accepts_complete_settings(self):
        module = load_module()
        result = module.validate_mandatory_capcut_media_settings(valid_draft())
        self.assertEqual(result["mandatory_capcut_media_settings_status"], "PASS")
        self.assertEqual(result["mandatory_capcut_source_video_segment_count"], 2)

    def test_rejects_missing_loudness_normalize(self):
        module = load_module()
        draft = valid_draft()
        draft["materials"]["loudnesses"] = []
        with self.assertRaisesRegex(module.GateFail, "loudness normalize"):
            module.validate_mandatory_capcut_media_settings(draft)

    def test_rejects_adjacent_duplicate_values(self):
        module = load_module()
        draft = valid_draft()
        for item in draft["materials"]["effects"]:
            if item["type"] == "clear":
                item["value"] = 0.35
        with self.assertRaisesRegex(module.GateFail, "adjacent source video segments"):
            module.validate_mandatory_capcut_media_settings(draft)

    def test_rejects_particle_above_30(self):
        module = load_module()
        draft = valid_draft()
        draft["materials"]["effects"][3]["value"] = 0.31
        with self.assertRaisesRegex(module.GateFail, "particle"):
            module.validate_mandatory_capcut_media_settings(draft)

    def test_accepts_capcut_encoded_particle_30(self):
        module = load_module()
        draft = valid_draft()
        draft["materials"]["effects"][3]["value"] = 0.04955
        result = module.validate_mandatory_capcut_media_settings(draft)
        self.assertEqual(result["mandatory_capcut_media_settings_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
