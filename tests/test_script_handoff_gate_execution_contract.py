from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
TIKITAKA_HARNESS = ROOT / "skills" / "00-tikitaka" / "scripts" / "tikitaka_harness_runner.py"
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


def write_json(path: Path, text: str) -> None:
    write(path, text.strip() + "\n")


def create_tikitaka_base_evidence(work_dir: Path) -> None:
    write(work_dir / "work_order.md")
    write(work_dir / "execution_spec.md")
    write(work_dir / "implementation_log.md")
    persona_dir = work_dir / "persona_outputs"
    persona_dir.mkdir(parents=True)
    for index in range(5):
        write(persona_dir / f"persona_{index}.md")
    write_json(
        work_dir / "script_gate_report.json",
        """
        {
          "status": "SCRIPT_LOCK",
          "writer_persona_pass_count": 4,
          "writer_persona_hard_veto": false
        }
        """,
    )
    write(work_dir / "n8n_execution_id.txt", "n8n-ok")


def create_script_lock_package_artifacts(work_dir: Path) -> None:
    write(work_dir / "original_structure_summary.md")
    write(work_dir / "urakkai_structure_plan.md")
    write_json(work_dir / "urakkai_structure_delta.json", '{"status":"PASS"}')
    write_json(
        work_dir / "block_map.json",
        """
        {
          "edit_block_sequence": ["E1"],
          "blocks": [
            {
              "edit_id": "E1",
              "source_block_id": "S1",
              "original_order": 1,
              "urakkai_order": 1,
              "caption_type": "tts_narration"
            }
          ]
        }
        """,
    )
    write_json(
        work_dir / "block_role_map.json",
        """
        {
          "roles": [
            {"edit_id": "E1", "caption_type": "tts_narration"}
          ]
        }
        """,
    )
    write_json(
        work_dir / "block_voice_switch_map.json",
        """
        {
          "switches": [
            {"edit_id": "E1", "source_audio": "off", "tts": "on"}
          ]
        }
        """,
    )
    write(work_dir / "tts_copy_text.txt", "테스트 나레이션")


class ScriptHandoffGateExecutionContractTests(unittest.TestCase):
    def test_tikitaka_harness_generates_script_handoff_gate_from_lock_package(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_exec", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)

            state = module.audit(work_dir, "job-test")

            gate_path = work_dir / "script_handoff_gate.json"
            self.assertTrue(gate_path.is_file())
            gate = module.read_json(gate_path)
            self.assertEqual(gate["gate_name"], "SCRIPT_HANDOFF_GATE")
            self.assertEqual(gate["status"], "PASS")
            self.assertEqual(gate["generated_by"], "tikitaka_harness_runner")
            self.assertEqual(gate["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertIs(gate["capcut_allowed"], True)
            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")

    def test_tikitaka_harness_fails_script_handoff_gate_when_voice_switch_map_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_fail", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            (work_dir / "block_voice_switch_map.json").unlink()

            state = module.audit(work_dir, "job-test")

            gate = module.read_json(work_dir / "script_handoff_gate.json")
            self.assertEqual(gate["status"], "FAIL")
            self.assertIs(gate["capcut_allowed"], False)
            self.assertIn("block_voice_switch_map", gate["missing_or_failed"])
            self.assertFalse(state["final_report_allowed"])

    def test_tikitaka_handoff_pass_allows_capcut_openable_even_when_final_lock_evidence_missing(self):
        module = load_source_module_no_bytecode("tikitaka_harness_runner_openable", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_script_lock_package_artifacts(work_dir)

            state = module.audit(work_dir, "job-test")

            self.assertEqual(state["script_handoff_gate"]["status"], "PASS")
            self.assertEqual(state["script_handoff_gate"]["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertIs(state["script_handoff_gate"]["capcut_allowed"], True)
            self.assertEqual(state["capcut_permission"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")
            self.assertEqual(state["production_status"], "WAIT_CAPCUT_OPENABLE_PROJECT")
            self.assertFalse(state["final_report_allowed"])
            self.assertEqual(state["script_lock"]["status"], "NOT_LOCKED")

    def test_production_shared_requirements_fail_without_script_handoff_gate(self):
        module = load_source_module_no_bytecode("production_gate_missing_handoff", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(module.GateFail, "WAIT_SCRIPT_HANDOFF_GATE"):
                module.validate_shared_requirements({}, Path(tmp))

    def test_production_accepts_validator_generated_script_handoff_gate(self):
        module = load_source_module_no_bytecode("production_gate_handoff_pass", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "20_script" / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "generated_by": "tikitaka_harness_runner",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": true,
                  "input_files": ["20_script/block_map.json"]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_map.json",
                """
                {
                  "edit_block_sequence": ["E1"],
                  "blocks": [
                    {
                      "edit_id": "E1",
                      "source_block_id": "S1",
                      "original_order": 1,
                      "urakkai_order": 1
                    }
                  ],
                  "block_voice_switch_map": [
                    {"edit_id": "E1", "source_audio": "off", "tts": "on"}
                  ]
                }
                """,
            )

            result = module.validate_script_handoff_gate({}, root)

            self.assertEqual(result["script_handoff_gate_status"], "PASS")
            self.assertEqual(result["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertEqual(result["capcut_permission"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")

    def test_production_accepts_harness_input_files_relative_to_gate_directory(self):
        module = load_source_module_no_bytecode("production_gate_handoff_relative_inputs", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "20_script" / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "generated_by": "tikitaka_harness_runner",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": true,
                  "input_files": ["block_map.json"]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_map.json",
                """
                {
                  "edit_block_sequence": ["E1"],
                  "blocks": [
                    {
                      "edit_id": "E1",
                      "source_block_id": "S1",
                      "original_order": 1,
                      "urakkai_order": 1
                    }
                  ],
                  "block_voice_switch_map": [
                    {"edit_id": "E1", "source_audio": "off", "tts": "off"}
                  ]
                }
                """,
            )

            result = module.validate_script_handoff_gate({}, root)

            self.assertEqual(result["script_handoff_gate_status"], "PASS")

    def test_production_capcut_openable_entry_does_not_require_final_lock_fields(self):
        module = load_source_module_no_bytecode("production_gate_openable_entry", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "20_script" / "script_handoff_gate.json",
                """
                {
                  "gate_name": "SCRIPT_HANDOFF_GATE",
                  "status": "PASS",
                  "generated_by": "tikitaka_harness_runner",
                  "script_status": "SCRIPT_LOCK_PACKAGE",
                  "capcut_allowed": true,
                  "input_files": ["20_script/block_map.json"]
                }
                """,
            )
            write_json(
                root / "20_script" / "block_map.json",
                """
                {
                  "edit_block_sequence": ["E1"],
                  "blocks": [
                    {
                      "edit_id": "E1",
                      "source_block_id": "S1",
                      "original_order": 1,
                      "urakkai_order": 1
                    }
                  ],
                  "block_voice_switch_map": [
                    {"edit_id": "E1", "source_audio": "off", "tts": "off"}
                  ]
                }
                """,
            )
            write(root / "00_source" / "source_manifest.json", '{"status":"PASS"}')

            result = module.validate_capcut_openable_project_entry({}, root)

            self.assertEqual(result["status"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")
            self.assertEqual(result["script_status"], "SCRIPT_LOCK_PACKAGE")
            self.assertEqual(result["next_gate"], "ASSET_PREP_GATE")
            self.assertNotIn("writer_persona_total", result)


if __name__ == "__main__":
    unittest.main()
