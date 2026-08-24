from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import production_profile
import track_template_matrix as templates
import validate_design_lock


PRESET_ROOT = SKILL_ROOT / "presets" / "politics-ttt-shorts"
PROFILE_PATH = PRESET_ROOT / "profile.json"
EXPECTED_SELECTOR = {
    "schema_version": "001short-production-profile-v1",
    "profile_id": "politics-ttt-shorts",
    "assembly_type": "1",
    "template_profile": "shrt_black_top_v1",
    "production_mode": "URAKKAI",
    "audio_policy": "CAPTION_ONLY_MUTE_SOURCE",
}


class PoliticsTttPresetContractTest(unittest.TestCase):
    def test_profile_is_selector_only_and_resolves_through_the_shared_engine(self):
        self.assertTrue(PROFILE_PATH.is_file(), f"PRESET_PROFILE_MISSING:{PROFILE_PATH}")
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload, EXPECTED_SELECTOR)

        resolved = production_profile.resolve_production_profile(payload)
        self.assertEqual(resolved.selector, EXPECTED_SELECTOR)
        self.assertEqual(resolved.execution_strategy, "caption_only")
        self.assertEqual(resolved.audio_source, "SILENCE")
        self.assertEqual(resolved.track_layout, templates.V3_TRACK_LAYOUT)
        self.assertEqual(set(resolved.required_roles), {"STATE"})
        self.assertEqual(set(resolved.optional_roles), set())

    def test_preset_contains_no_forked_python_engine(self):
        self.assertTrue(PRESET_ROOT.is_dir(), f"PRESET_ROOT_MISSING:{PRESET_ROOT}")
        self.assertEqual(list(PRESET_ROOT.rglob("*.py")), [])

    def test_black_top_profile_reuses_v3_layout_and_supports_source_credit(self):
        profile = templates.track_template_profile("shrt_black_top_v1")
        self.assertEqual(profile.track_layout, templates.V3_TRACK_LAYOUT)
        self.assertTrue(
            templates.profile_supports_role("shrt_black_top_v1", "SOURCE_CREDIT")
        )
        self.assertIn("SOURCE_CREDIT", profile.full_span_roles)
        self.assertNotIn("SOURCE_CREDIT", profile.optional_full_span_roles)

    def test_black_top_requires_one_nonempty_full_span_channel_credit(self):
        duration = 10_000_000
        segments = [
            {"segment_id": "V01", "role": "VIDEO", "start": 0, "duration": duration},
            {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": duration},
            {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": duration},
            {"segment_id": "T2", "role": "T2", "content_type": "TITLE", "text": "정치 쇼츠", "start": 0, "duration": duration},
            {"segment_id": "T1", "role": "T1", "content_type": "TITLE", "text": "핵심 장면", "start": 0, "duration": duration},
        ]
        missing = validate_design_lock.validate_role_contract(
            {"segments": segments},
            duration,
            template_profile=templates.BLACK_TOP_TEMPLATE_PROFILE,
        )
        self.assertIn(
            "FULL_SPAN_ANCHOR_INVALID:SOURCE_CREDIT",
            {f"{row['code']}:{row.get('role')}" for row in missing},
        )

        present = validate_design_lock.validate_role_contract(
            {"segments": [
                *segments,
                {
                    "segment_id": "SOURCE",
                    "role": "SOURCE_CREDIT",
                    "text": "효연의 레벨업",
                    "start": 0,
                    "duration": duration,
                },
            ]},
            duration,
            template_profile=templates.BLACK_TOP_TEMPLATE_PROFILE,
        )
        self.assertEqual(present, [])

        empty = validate_design_lock.validate_role_contract(
            {"segments": [
                *segments,
                {
                    "segment_id": "SOURCE",
                    "role": "SOURCE_CREDIT",
                    "text": "   ",
                    "start": 0,
                    "duration": duration,
                },
            ]},
            duration,
            template_profile=templates.BLACK_TOP_TEMPLATE_PROFILE,
        )
        self.assertIn(
            "SOURCE_CREDIT_TEXT_REQUIRED:SOURCE_CREDIT",
            {f"{row['code']}:{row.get('role')}" for row in empty},
        )


if __name__ == "__main__":
    unittest.main()
