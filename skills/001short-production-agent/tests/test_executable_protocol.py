import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PROTOCOL = SKILL / "protocol.json"
SCHEMA = SKILL / "schemas" / "executable_protocol.schema.json"
PLAN_SCHEMA = SKILL / "schemas" / "executable_production_plan.schema.json"
COMPLETION_SCHEMA = SKILL / "schemas" / "completion_report.schema.json"
VALIDATOR = SKILL / "scripts" / "validate_executable_protocol.py"


def load_validator():
    if not VALIDATOR.is_file():
        return None
    spec = importlib.util.spec_from_file_location("validate_executable_protocol", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExecutableProtocolContractTest(unittest.TestCase):
    def test_skill_and_workflow_mandate_executable_protocol(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))
        self.assertIn("## Executable Protocol (Mandatory)", skill_text)
        self.assertIn("Load `protocol.json` before mode routing", skill_text)
        self.assertIn("STOP_PROTOCOL_CONFLICT", skill_text)
        self.assertIn("UPLOAD_METADATA_MISSING", skill_text)
        self.assertIn("protocol.json", workflow["common"])
        self.assertEqual(workflow["executable_protocol"]["path"], "protocol.json")
        self.assertEqual(
            workflow["executable_protocol"]["validator"],
            "scripts/validate_executable_protocol.py",
        )
        self.assertEqual(
            workflow["runtime"]["completion_report_path"],
            "{episode_root}/90_reports/completion_report.json",
        )
        self.assertEqual(
            workflow["validation"]["checks"]["05"]["protocol_validator"],
            "python3 scripts/validate_executable_protocol.py --plan {episode_root}/20_script/production_plan.json",
        )
        self.assertEqual(
            workflow["validation"]["checks"]["09"]["completion_validator"],
            "python3 scripts/validate_executable_protocol.py --completion-report {episode_root}/90_reports/completion_report.json",
        )
        self.assertEqual(
            workflow["completion_gate"]["validator"],
            "python3 scripts/validate_executable_protocol.py --completion-report {episode_root}/90_reports/completion_report.json",
        )
        self.assertTrue(workflow["completion_gate"]["validator_pass_required"])
        self.assertIn("upload_title", workflow["completion_gate"]["required_fields"])
        self.assertIn("upload_description", workflow["completion_gate"]["required_fields"])
        self.assertIn("sources", workflow["completion_gate"]["required_fields"])
        self.assertIn("executable_protocol", tools)
        self.assertEqual(tools["executable_protocol"]["file"], "protocol.json")
        self.assertEqual(
            tools["executable_protocol"]["validator"],
            "scripts/validate_executable_protocol.py",
        )
        self.assertEqual(
            tools["executable_protocol"]["completion_report"],
            "{episode_root}/90_reports/completion_report.json",
        )

    def test_protocol_declares_modes_nine_stages_and_completion_gate(self):
        self.assertTrue(PROTOCOL.is_file(), "protocol.json must exist")
        self.assertTrue(SCHEMA.is_file(), "executable protocol schema must exist")
        self.assertTrue(PLAN_SCHEMA.is_file(), "production plan schema must exist")
        self.assertTrue(COMPLETION_SCHEMA.is_file(), "completion report schema must exist")
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        self.assertIn("schemas", protocol)
        self.assertEqual(protocol["schemas"]["production_plan"], "schemas/executable_production_plan.schema.json")
        self.assertEqual(protocol["schemas"]["completion_report"], "schemas/completion_report.schema.json")
        plan_schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("timeline", plan_schema["required"])
        self.assertIn("order_signature", plan_schema["required"])
        self.assertNotIn("tracks", plan_schema["required"])
        self.assertEqual(protocol["schema_version"], "001short-executable-protocol-v1")
        self.assertEqual([stage["id"] for stage in protocol["stages"]], [f"{n:02d}" for n in range(1, 10)])
        self.assertEqual(
            set(protocol["production_modes"]),
            {"URAKKAI", "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY"},
        )
        self.assertEqual(
            protocol["completion_report"]["cloud_row_required_fields"],
            ["name", "size", "duration", "type", "modified_time"],
        )
        self.assertEqual(
            protocol["completion_report"]["required_fields"],
            [
                "episode_id",
                "capcut_project_name",
                "production_mode",
                "T1",
                "T2",
                "validation_status",
                "capcut_cloud_destination",
                "capcut_cloud_row",
                "upload_title",
                "upload_description",
                "sources",
                "public_upload_status",
            ],
        )

    def test_cross_file_self_check_catches_missing_schema(self):
        module = load_validator()
        self.assertIsNotNone(module, "validate_executable_protocol.py must exist")
        self.assertTrue(hasattr(module, "validate_skill_contract"), "cross-file self-check must exist")
        protocol = module.load_protocol(PROTOCOL)
        self.assertEqual(module.validate_skill_contract(SKILL, protocol), [])
        broken = json.loads(json.dumps(protocol, ensure_ascii=False))
        broken["schemas"]["completion_report"] = "schemas/not-present.schema.json"
        self.assertIn(
            "PROTOCOL_REQUIRED_FILE_MISSING:schemas/not-present.schema.json",
            module.validate_skill_contract(SKILL, broken),
        )

    def test_clean_only_plan_requires_single_video_audio_and_empty_tracks(self):
        module = load_validator()
        self.assertIsNotNone(module, "validate_executable_protocol.py must exist")
        protocol = module.load_protocol(PROTOCOL)
        valid = json.loads((SKILL / "tests" / "fixtures" / "clean_only_plan.pass.json").read_text(encoding="utf-8"))
        self.assertEqual(module.validate_production_plan(valid, protocol), [])
        invalid = json.loads(json.dumps(valid, ensure_ascii=False))
        invalid["timeline"][0]["placements"].append({
            "anchor": "A11",
            "operation": "clone_template_segment",
            "asset_key": "impact_sfx",
            "target_range_us": [0, 8_000_000],
        })
        errors = module.validate_production_plan(invalid, protocol)
        self.assertIn("CLEAN_ONLY_FORBIDDEN_TRACK_NOT_EMPTY:A11", errors)

    def test_urakkai_rejects_unchanged_order(self):
        module = load_validator()
        self.assertIsNotNone(module, "validate_executable_protocol.py must exist")
        protocol = module.load_protocol(PROTOCOL)
        unchanged_path = SKILL / "tests" / "fixtures" / "urakkai_same_order.fail.json"
        reordered_path = SKILL / "tests" / "fixtures" / "urakkai_reordered.pass.json"
        self.assertTrue(unchanged_path.is_file(), "unchanged urakkai fixture must exist")
        self.assertTrue(reordered_path.is_file(), "reordered urakkai fixture must exist")
        unchanged = json.loads(unchanged_path.read_text(encoding="utf-8"))
        reordered = json.loads(reordered_path.read_text(encoding="utf-8"))
        errors = module.validate_production_plan(unchanged, protocol)
        self.assertIn("URAKKAI_STRUCTURE_UNCHANGED", errors)
        self.assertEqual(module.validate_production_plan(reordered, protocol), [])

    def test_completion_report_rejects_missing_upload_metadata(self):
        module = load_validator()
        self.assertIsNotNone(module, "validate_executable_protocol.py must exist")
        protocol = module.load_protocol(PROTOCOL)
        report = {
            "episode_id": "SH_TEST",
            "capcut_project_name": "SH_TEST_Hermes",
            "production_mode": "URAKKAI",
            "T1": "제목1",
            "T2": "제목2",
            "validation_status": "PASS",
            "capcut_cloud_destination": "User3160027826975의 공간/MAC",
            "capcut_cloud_row": {
                "name": "SH_TEST_Hermes",
                "size": "9.1MB",
                "duration": "00:09",
                "type": "프로젝트",
                "modified_time": "오늘 02:51",
            },
            "public_upload_status": "WAIT_APPROVAL"
        }
        errors = module.validate_completion_report(report, protocol)
        self.assertEqual(
            errors,
            [
                "UPLOAD_METADATA_MISSING:upload_title",
                "UPLOAD_METADATA_MISSING:upload_description",
                "UPLOAD_METADATA_MISSING:sources",
            ],
        )

    def test_completion_report_accepts_complete_metadata_and_blocks_unapproved_public_upload(self):
        module = load_validator()
        self.assertIsNotNone(module, "validate_executable_protocol.py must exist")
        protocol = module.load_protocol(PROTOCOL)
        report = {
            "episode_id": "SH_TEST",
            "capcut_project_name": "SH_TEST_Hermes",
            "production_mode": "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY",
            "T1": "제목1",
            "T2": "제목2",
            "validation_status": "PASS",
            "capcut_cloud_destination": "User3160027826975의 공간/MAC",
            "capcut_cloud_row": {
                "name": "SH_TEST_Hermes",
                "size": "9.1MB",
                "duration": "00:09",
                "type": "프로젝트",
                "modified_time": "오늘 02:51",
            },
            "upload_title": "업로드 제목",
            "upload_description": "업로드 설명",
            "sources": [{"channel": "원본 채널", "url": "https://example.com/source"}],
            "public_upload_status": "WAIT_APPROVAL"
        }
        self.assertEqual(module.validate_completion_report(report, protocol), [])
        incomplete_cloud_row = json.loads(json.dumps(report, ensure_ascii=False))
        del incomplete_cloud_row["capcut_cloud_row"]["size"]
        self.assertIn(
            "CAPCUT_CLOUD_ROW_MISSING:size",
            module.validate_completion_report(incomplete_cloud_row, protocol),
        )
        report["public_upload_status"] = "UPLOADED"
        report["public_upload_approval"] = False
        self.assertIn(
            "PUBLIC_UPLOAD_NOT_APPROVED",
            module.validate_completion_report(report, protocol),
        )


if __name__ == "__main__":
    unittest.main()
