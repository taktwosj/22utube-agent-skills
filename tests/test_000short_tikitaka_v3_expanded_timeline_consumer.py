from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode
from test_000short_tikitaka_v2_handoff_contract import create_valid_tikitaka_v2_package, write_json


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "000short-production-agent" / "SKILL.md"
PIPELINE_RULES = ROOT / "skills" / "000short-production-agent" / "02_PIPELINE_RULES.md"
LAYOUT_CONTRACT = ROOT / "skills" / "000short-production-agent" / "03_CAPCUT_LAYOUT_CONTRACT.md"
HARNESS_REQUIREMENTS = ROOT / "skills" / "000short-production-agent" / "04_HARNESS_REQUIREMENTS.md"
DRAFT_FAST_CONTRACT = ROOT / "skills" / "000short-production-agent" / "07_DRAFT_FAST_REPORT_CONTRACT.md"
TIMELINE_SCHEMA = ROOT / "skills" / "000short-production-agent" / "schemas" / "timeline_design.schema.json"
LAYOUT_SCHEMA = ROOT / "skills" / "000short-production-agent" / "schemas" / "capcut_layout_plan.schema.json"
TIMELINE_MANIFEST_SCHEMA = (
    ROOT / "skills" / "000short-production-agent" / "schemas" / "capcut_timeline_manifest.schema.json"
)
PRODUCTION_GATE = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_production_gate.py"
)


V3_REQUIRED_SEGMENT_FIELDS = {
    "edit_id",
    "source_ref",
    "source_order",
    "timeline_order",
    "assembly_role",
    "caption_type",
    "visible_text_role",
    "audio_role",
    "time_start",
    "time_end",
    "track",
    "duration_basis",
    "duration_status",
    "audio_policy",
    "visual_strategy",
}


class TikitakaV3ExpandedTimelineConsumerTests(unittest.TestCase):
    def test_timeline_design_schema_requires_v3_expanded_fields(self):
        schema = json.loads(TIMELINE_SCHEMA.read_text(encoding="utf-8"))
        item_schema = schema["properties"]["segments"]["items"]

        self.assertIn("source_fingerprint_sha256", schema["required"])
        self.assertEqual(
            schema["properties"]["source_fingerprint_sha256"]["pattern"],
            "^[A-Fa-f0-9]{64}$",
        )
        self.assertLessEqual(V3_REQUIRED_SEGMENT_FIELDS, set(item_schema["required"]))
        self.assertIn("assembly_role", item_schema["properties"])
        self.assertIn("duration_basis", item_schema["properties"])
        self.assertIn("duration_status", item_schema["properties"])
        self.assertIn("tts_duration_status", item_schema["properties"])
        self.assertEqual(item_schema["properties"]["track"]["not"]["enum"], ["A9", "A10", "A11", "A12"])

    def test_capcut_layout_plan_schema_preserves_expanded_timeline_contract(self):
        schema = json.loads(LAYOUT_SCHEMA.read_text(encoding="utf-8"))

        for key in [
            "assembly_role_sequence_preserved",
            "timeline_order_preserved",
            "source_order_preserved",
            "duration_basis_preserved",
            "duration_status_preserved",
        ]:
            self.assertIn(key, schema["required"])
            self.assertEqual(schema["properties"][key]["const"], True)

        timeline_item = schema["properties"]["timeline_segments"]["items"]
        self.assertLessEqual(V3_REQUIRED_SEGMENT_FIELDS, set(timeline_item["required"]))

    def test_capcut_timeline_manifest_schema_proves_v3_preservation(self):
        schema = json.loads(TIMELINE_MANIFEST_SCHEMA.read_text(encoding="utf-8"))

        for key in [
            "implemented_timeline_segment_count",
            "protected_fields_preserved",
            "assembly_role_sequence_preserved",
            "timeline_order_preserved",
            "source_order_preserved",
            "duration_basis_preserved",
            "duration_status_preserved",
            "semantic_audio_resolution",
            "implemented_segments",
        ]:
            self.assertIn(key, schema["required"])

        implemented_item = schema["properties"]["implemented_segments"]["items"]
        self.assertLessEqual(V3_REQUIRED_SEGMENT_FIELDS, set(implemented_item["required"]))
        for key in [
            "resolved_capcut_text_track",
            "resolved_capcut_audio_track",
            "resolved_video_track",
            "material_id",
        ]:
            self.assertIn(key, implemented_item["properties"])

    def test_docs_define_v3_consumer_lock_and_tts_caption_exception(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                SKILL,
                PIPELINE_RULES,
                LAYOUT_CONTRACT,
                HARNESS_REQUIREMENTS,
                DRAFT_FAST_CONTRACT,
            ]
        )

        for token in [
            "Stage 2 Tikitaka v3 Expanded Timeline Source of Truth",
            "source_order is source provenance",
            "timeline_order is playback/edit order",
            "WAIT_TIKITAKA_DESIGN_REPAIR",
            "tts_caption/audio_role=none",
            "must not trigger TTS generation",
            "tts_narration/audio_role=audio.narration_tts",
            "Do not derive timeline_order from source_order",
            "DRAFT_FAST does not waive expanded timeline requirements",
            "FAIL_ACTIVE_GATE_ACCEPTS_OLD_TIMELINE_DESIGN",
        ]:
            self.assertIn(token, combined)

    def test_active_production_gate_rejects_old_six_field_timeline_design(self):
        module = load_source_module_no_bytecode("production_gate_old_timeline_design", PRODUCTION_GATE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_valid_tikitaka_v2_package(root)
            write_json(
                root / "20_script" / "timeline_design.json",
                {
                    "project_duration_sec": 8,
                    "segments": [
                        {
                            "edit_id": "E1",
                            "time_start": "00:00",
                            "time_end": "00:03",
                            "track": "audio.narration_tts",
                            "caption_type": "tts_narration",
                            "audio_policy": "tts_on_source_off",
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(module.GateFail, "WAIT_TIMELINE_DESIGN_REPAIR"):
                module.validate_capcut_openable_project_entry(contract, root)


if __name__ == "__main__":
    unittest.main()
