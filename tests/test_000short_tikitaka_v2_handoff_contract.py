from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
STAGE2_VALIDATOR = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_stage2_tikitaka_handoff.py"
)
PRODUCTION_GATE = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_production_gate.py"
)


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def create_valid_tikitaka_v2_package(root: Path) -> dict:
    write_json(
        root / "20_script" / "report1_handoff.json",
        {
            "gate_name": "REPORT1_HANDOFF_GATE",
            "status": "PASS",
            "owner_skill": "00-tikitaka",
            "next_skill": "000short-production-agent",
            "next_gate": "CAPCUT_OPENABLE_PROJECT",
            "required_before_next": [
                "report1_approved=true",
                "voice_audio_route_decided=true",
            ],
            "report1_approved": True,
            "voice_audio_route_decided": True,
        },
    )
    write_json(
        root / "20_script" / "script_handoff_gate.json",
        {
            "gate_name": "SCRIPT_HANDOFF_GATE",
            "status": "PASS",
            "generated_by": "tikitaka_harness_runner",
            "script_status": "SCRIPT_LOCK_PACKAGE",
            "capcut_allowed": True,
            "input_files": ["block_map.json", "block_voice_switch_map.json"],
        },
    )
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
                    "semantic_lane": "narration_tts",
                    "resolved_capcut_track": None,
                    "resolved_by": "000short-production-agent",
                    "caption_type": "tts_narration",
                    "audio_policy": "tts_on_source_off",
                },
                {
                    "edit_id": "E2",
                    "time_start": "00:03",
                    "time_end": "00:08",
                    "track": "audio.speaker_source",
                    "semantic_lane": "speaker_source",
                    "resolved_capcut_track": None,
                    "resolved_by": "000short-production-agent",
                    "caption_type": "speaker_quote",
                    "audio_policy": "source_on_tts_off",
                },
            ],
        },
    )
    write_json(root / "20_script" / "timeline_design_gate.json", {"status": "PASS"})
    write_json(
        root / "20_script" / "humanize_korean_gate.json",
        {
            "status": "PASS",
            "structure_changed": False,
            "protected_fields_changed": False,
        },
    )
    write_json(
        root / "20_script" / "block_map.json",
        {
            "edit_block_sequence": ["E1", "E2"],
            "blocks": [
                {
                    "edit_id": "E1",
                    "source_block_id": "S1",
                    "original_order": 1,
                    "urakkai_order": 1,
                },
                {
                    "edit_id": "E2",
                    "source_block_id": "S2",
                    "original_order": 2,
                    "urakkai_order": 2,
                },
            ],
        },
    )
    write_json(
        root / "20_script" / "block_role_map.json",
        {
            "roles": [
                {"edit_id": "E1", "caption_type": "tts_narration"},
                {"edit_id": "E2", "caption_type": "speaker_quote"},
            ]
        },
    )
    write_json(
        root / "20_script" / "block_voice_switch_map.json",
        {
            "switches": [
                {"edit_id": "E1", "source_audio": "off", "tts": "on"},
                {"edit_id": "E2", "source_audio": "on", "tts": "off"},
            ]
        },
    )
    write(root / "20_script" / "tts_copy_text.txt", "테스트 나레이션")
    write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
    write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})
    reference_path = root / "capcut_refs" / "shrt white"
    reference_path.mkdir(parents=True)
    return {
        "user_request": "capcut project",
        "report1_approved": True,
        "voice_audio_route_decided": True,
        "template_profile": "shrt_white_base_v1",
        "reference_project_name": "shrt white",
        "reference_project_path": str(reference_path),
        "derived_from_reference_project": True,
    }


class TikitakaV2HandoffContractTests(unittest.TestCase):
    def test_valid_tikitaka_v2_handoff_passes_standalone_validator(self):
        module = load_source_module_no_bytecode("stage2_handoff_valid", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)

            result = module.validate_stage2_tikitaka_handoff(root)

            self.assertEqual(result["stage2_tikitaka_handoff_status"], "PASS")
            self.assertEqual(result["stage2_tikitaka_source_of_truth"], "20_script/timeline_design.json")

    def test_timeline_design_missing_blocks_capcut_openable_entry(self):
        module = load_source_module_no_bytecode("production_gate_missing_timeline_design", PRODUCTION_GATE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_valid_tikitaka_v2_package(root)
            (root / "20_script" / "timeline_design.json").unlink()

            with self.assertRaisesRegex(module.GateFail, "WAIT_TIMELINE_DESIGN_REQUIRED"):
                module.validate_capcut_openable_project_entry(contract, root)

    def test_timeline_design_gate_not_pass_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_timeline_gate_fail", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            write_json(root / "20_script" / "timeline_design_gate.json", {"status": "FAIL"})

            with self.assertRaisesRegex(module.GateFail, "WAIT_TIMELINE_DESIGN_REPAIR"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_humanize_gate_not_pass_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_humanize_fail", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            write_json(root / "20_script" / "humanize_korean_gate.json", {"status": "FAIL"})

            with self.assertRaisesRegex(module.GateFail, "WAIT_HUMANIZE_REPAIR"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_report1_wrong_next_skill_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_wrong_next_skill", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            report1_path = root / "20_script" / "report1_handoff.json"
            report1 = json.loads(report1_path.read_text(encoding="utf-8"))
            report1["next_skill"] = "00-tikitaka"
            write_json(report1_path, report1)

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_HANDOFF_GATE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_report1_approval_or_voice_route_missing_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_approval_missing", STAGE2_VALIDATOR)
        for field in ("report1_approved", "voice_audio_route_decided"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                create_valid_tikitaka_v2_package(root)
                report1_path = root / "20_script" / "report1_handoff.json"
                report1 = json.loads(report1_path.read_text(encoding="utf-8"))
                report1[field] = False
                write_json(report1_path, report1)

                with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
                    module.validate_stage2_tikitaka_handoff(root)

    def test_block_role_map_missing_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_block_role_missing", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            (root / "20_script" / "block_role_map.json").unlink()

            with self.assertRaisesRegex(module.GateFail, "WAIT_BLOCK_ROLE_MAP_REQUIRED"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_tts_copy_text_missing_when_tts_narration_exists_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_tts_copy_missing", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            (root / "20_script" / "tts_copy_text.txt").unlink()

            with self.assertRaisesRegex(module.GateFail, "WAIT_TTS_COPY_TEXT_REQUIRED"):
                module.validate_stage2_tikitaka_handoff(root)


if __name__ == "__main__":
    unittest.main()
