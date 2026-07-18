from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "chatgpt_review_workflow.py"
)
SOURCE_FINGERPRINT = "a" * 64


def load_workflow():
    assert WORKFLOW_PATH.is_file(), "chatgpt_review_workflow.py is missing"
    spec = importlib.util.spec_from_file_location(
        "tikitaka_chatgpt_review_workflow",
        WORKFLOW_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load ChatGPT review workflow")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: object) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def create_round1_fixture(work_dir: Path) -> None:
    write_json(
        work_dir / "timeline_design.json",
        {
            "source_fingerprint_sha256": SOURCE_FINGERPRINT,
            "segments": [
                {
                    "edit_id": "E1",
                    "source_ref": "source-1",
                    "source_order": 1,
                    "timeline_order": 1,
                    "assembly_role": "intro_narration",
                    "caption_type": "tts_caption",
                    "visible_text_role": "timed_middle",
                    "audio_role": "none",
                    "time_start": 0,
                    "time_end": 2,
                    "track": "TTS",
                    "duration_basis": "fixed_design_duration",
                    "duration_status": "FIXED_DESIGN_LOCKED",
                    "audio_policy": {
                        "source_audio": "off",
                        "tts": "off",
                        "bgm": "optional",
                    },
                    "visual_strategy": "source_visual_hold",
                }
            ],
        },
    )
    write_json(
        work_dir / "timeline_design_gate.json",
        {"status": "PASS", "source_fingerprint_sha256": SOURCE_FINGERPRINT},
    )
    write_json(
        work_dir / "caption_beat_map.json",
        {
            "status": "PASS",
            "source_fingerprint_sha256": SOURCE_FINGERPRINT,
            "beats": [{"beat_id": "B1", "edit_id": "E1", "text": "첫 장면"}],
        },
    )
    write_text(
        work_dir / "design_blueprint.md",
        "# 설계도\n\n## 기본 정보\n\nfixture\n",
    )
    write_json(
        work_dir / "source_identity_lock.json",
        {
            "canonical_url": "https://www.youtube.com/shorts/fixture",
            "sha256": SOURCE_FINGERPRINT,
        },
    )


def require_function(testcase: unittest.TestCase, module, name: str):
    testcase.assertTrue(hasattr(module, name), f"{name} is not implemented")
    return getattr(module, name)


def valid_response_for(result: dict[str, object], *, recommendation: str = "") -> str:
    recommendation_block = (
        f"## 4. EXTERNAL_RECOMMENDATION\n{recommendation}\n\n"
        if recommendation
        else ""
    )
    return (
        "ROUTE=SHORTS\n"
        f"review_round: {result['review_round']}\n"
        f"review_cycle_id: {result['review_cycle_id']}\n"
        f"packet_id: {result['packet_id']}\n"
        f"sent_packet_sha256: {result['sent_packet_sha256']}\n\n"
        "## 1. REVIEW\n검수 결과\n\n"
        f"{recommendation_block}"
        "external_review_status: PENDING_CODEX_REVIEW\n"
    )


def complete_round1(work_dir: Path, workflow) -> dict[str, object]:
    round1 = workflow.build_round1(work_dir, review_cycle_id="cycle-fixture")
    write_text(
        work_dir / "chatgpt_review" / "round1_chatgpt_raw.md",
        valid_response_for(round1),
    )
    write_json(
        work_dir / "chatgpt_review" / "round1_codex_decisions.json",
        {
            "status": "PASS",
            "all_suggestions_dispositioned": True,
            "decisions": [],
        },
    )
    write_json(
        work_dir / "humanize_korean_gate.json",
        {
            "status": "PASS",
            "structure_changed": False,
            "protected_fields_changed": False,
        },
    )
    write_json(
        work_dir / "block_map.json",
        {"status": "PASS", "blocks": [{"edit_id": "E1"}]},
    )
    write_json(
        work_dir / "block_role_map.json",
        {"status": "PASS", "blocks": [{"edit_id": "E1"}]},
    )
    write_json(
        work_dir / "block_voice_switch_map.json",
        {"status": "PASS", "blocks": [{"edit_id": "E1"}]},
    )
    write_text(work_dir / "tts_copy_text.txt", "첫 장면\n")
    return round1


class TikitakaChatGPTReviewWorkflowTests(unittest.TestCase):
    def test_canonical_hash_removes_only_current_top_level_hash_line(self):
        workflow = load_workflow()
        text = (
            "content_type: shorts\r\n"
            "sent_packet_sha256: placeholder\r\n"
            "embedded: |\r\n"
            "  sent_packet_sha256: keep-me\r\n"
        )
        expected = (
            "content_type: shorts\n"
            "embedded: |\n"
            "  sent_packet_sha256: keep-me\n"
        )

        self.assertEqual(
            workflow.canonical_packet_sha256(text),
            hashlib.sha256(expected.encode("utf-8")).hexdigest(),
        )

    def test_build_round1_writes_required_metadata_and_artifacts(self):
        workflow = load_workflow()
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)

            result = workflow.build_round1(
                work_dir,
                review_cycle_id="cycle-fixture",
            )

            packet_path = work_dir / "chatgpt_review" / "round1_review_packet.md"
            self.assertEqual(result["review_round"], 1)
            self.assertEqual(Path(result["packet_path"]), packet_path)
            self.assertTrue(packet_path.is_file())
            packet = packet_path.read_text(encoding="utf-8")
            self.assertIn("content_type: shorts\n", packet)
            self.assertIn("review_round: 1\n", packet)
            self.assertIn("review_cycle_id: cycle-fixture\n", packet)
            self.assertIn(f"source_fingerprint_sha256: {SOURCE_FINGERPRINT}\n", packet)
            self.assertIn("## design_blueprint.md\n", packet)
            self.assertIn("## timeline_design.json\n", packet)
            self.assertIn("## caption_beat_map.json\n", packet)
            self.assertEqual(
                result["sent_packet_sha256"],
                workflow.canonical_packet_sha256(packet),
            )

    def test_build_round1_reads_source_lock_from_episode_analysis_directory(self):
        workflow = load_workflow()
        with tempfile.TemporaryDirectory() as tmp:
            episode_dir = Path(tmp) / "episode-fixture"
            work_dir = episode_dir / "20_script"
            create_round1_fixture(work_dir)
            (episode_dir / "10_analysis").mkdir(parents=True, exist_ok=True)
            (work_dir / "source_identity_lock.json").replace(
                episode_dir / "10_analysis" / "source_identity_lock.json"
            )

            result = workflow.build_round1(
                work_dir,
                review_cycle_id="cycle-fixture",
            )

            packet = Path(result["packet_path"]).read_text(encoding="utf-8")
            self.assertIn("## 10_analysis/source_identity_lock.json\n", packet)
            self.assertEqual(
                result["source_fingerprint_sha256"],
                SOURCE_FINGERPRINT,
            )

    def test_cli_build_round1_runs_after_all_functions_are_defined(self):
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(WORKFLOW_PATH),
                    "build-round1",
                    "--work-dir",
                    str(work_dir),
                    "--review-cycle-id",
                    "cycle-cli",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["review_cycle_id"], "cycle-cli")
            self.assertTrue(Path(payload["packet_path"]).is_file())

    def test_validate_round1_response_requires_exact_packet_echo(self):
        workflow = load_workflow()
        validate_response = require_function(self, workflow, "validate_response")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            result = workflow.build_round1(work_dir, review_cycle_id="cycle-fixture")
            response_path = work_dir / "round1-response.md"
            write_text(response_path, valid_response_for(result))

            parsed = validate_response(
                Path(result["packet_path"]),
                response_path,
                1,
            )

            self.assertEqual(parsed["review_round"], 1)
            self.assertEqual(parsed["review_cycle_id"], "cycle-fixture")
            self.assertEqual(parsed["packet_id"], "cycle-fixture-round1")
            self.assertEqual(parsed["recommendation"], None)

    def test_validate_response_rejects_tampered_sent_hash(self):
        workflow = load_workflow()
        validate_response = require_function(self, workflow, "validate_response")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            result = workflow.build_round1(work_dir, review_cycle_id="cycle-fixture")
            response_path = work_dir / "round1-response.md"
            response = valid_response_for(result).replace(
                str(result["sent_packet_sha256"]),
                "b" * 64,
                1,
            )
            write_text(response_path, response)

            with self.assertRaisesRegex(
                workflow.ReviewWorkflowError,
                "sent_packet_sha256 mismatch",
            ):
                validate_response(Path(result["packet_path"]), response_path, 1)

    def test_validate_response_requires_route_first_and_final_status_last(self):
        workflow = load_workflow()
        validate_response = require_function(self, workflow, "validate_response")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            result = workflow.build_round1(work_dir, review_cycle_id="cycle-fixture")
            response_path = work_dir / "round1-response.md"
            write_text(
                response_path,
                valid_response_for(result).replace(
                    "ROUTE=SHORTS",
                    "검수 시작\nROUTE=SHORTS",
                    1,
                ),
            )
            with self.assertRaisesRegex(
                workflow.ReviewWorkflowError,
                "first line",
            ):
                validate_response(Path(result["packet_path"]), response_path, 1)

            write_text(
                response_path,
                valid_response_for(result) + "extra trailing text\n",
            )
            with self.assertRaisesRegex(
                workflow.ReviewWorkflowError,
                "final line",
            ):
                validate_response(Path(result["packet_path"]), response_path, 1)

    def test_validate_round2_response_reads_recommendation_from_raw_text(self):
        workflow = load_workflow()
        validate_response = require_function(self, workflow, "validate_response")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            packet_path = work_dir / "round2-packet.md"
            packet_template = (
                "content_type: shorts\n"
                "review_round: 2\n"
                "review_cycle_id: cycle-fixture\n"
                "packet_id: cycle-fixture-round2\n"
                "sent_packet_sha256: __PENDING__\n"
                f"source_fingerprint_sha256: {SOURCE_FINGERPRINT}\n"
            )
            sent_hash = workflow.canonical_packet_sha256(packet_template)
            packet = packet_template.replace("__PENDING__", sent_hash, 1)
            write_text(packet_path, packet)
            result = {
                "review_round": 2,
                "review_cycle_id": "cycle-fixture",
                "packet_id": "cycle-fixture-round2",
                "sent_packet_sha256": sent_hash,
            }
            response_path = work_dir / "round2-response.md"
            write_text(
                response_path,
                valid_response_for(result, recommendation="PASS_RECOMMENDED"),
            )

            parsed = validate_response(packet_path, response_path, 2)

            self.assertEqual(parsed["recommendation"], "PASS_RECOMMENDED")

    def test_record_response_preserves_valid_raw_text_at_canonical_path(self):
        workflow = load_workflow()
        record_response = require_function(self, workflow, "record_response")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            round1 = workflow.build_round1(
                work_dir,
                review_cycle_id="cycle-fixture",
            )
            incoming = work_dir / "incoming-round1.md"
            raw = valid_response_for(round1)
            write_text(incoming, raw)

            result = record_response(work_dir, 1, incoming)

            canonical = (
                work_dir / "chatgpt_review" / "round1_chatgpt_raw.md"
            )
            self.assertEqual(Path(result["response_path"]), canonical)
            self.assertEqual(canonical.read_text(encoding="utf-8"), raw)
            self.assertEqual(result["status"], "VALID")

    def test_cli_parser_exposes_all_review_workflow_commands(self):
        workflow = load_workflow()
        build_parser = require_function(self, workflow, "build_parser")
        parser = build_parser()

        for command in [
            "build-round1",
            "record-response",
            "build-round2",
            "finalize-gate",
        ]:
            with self.subTest(command=command):
                if command in {"build-round1", "build-round2"}:
                    args = parser.parse_args(
                        [
                            command,
                            "--work-dir",
                            "fixture",
                            "--review-cycle-id",
                            "cycle-1",
                        ]
                    )
                elif command == "record-response":
                    args = parser.parse_args(
                        [
                            command,
                            "--work-dir",
                            "fixture",
                            "--round",
                            "1",
                            "--input",
                            "response.md",
                        ]
                    )
                else:
                    args = parser.parse_args(
                        [command, "--work-dir", "fixture"]
                    )
                self.assertEqual(args.command, command)

    def test_validate_codex_decisions_rejects_pending_evidence(self):
        workflow = load_workflow()
        validate_decisions = require_function(
            self,
            workflow,
            "validate_codex_decisions",
        )
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            response_path = work_dir / "round1.md"
            decisions_path = work_dir / "decisions.json"
            write_text(
                response_path,
                "ROUTE=SHORTS\nsuggestion_id: S1\n"
                "external_review_status: PENDING_CODEX_REVIEW\n",
            )
            write_json(
                decisions_path,
                {
                    "status": "PASS",
                    "all_suggestions_dispositioned": True,
                    "decisions": [
                        {
                            "suggestion_id": "S1",
                            "disposition": "PENDING_EVIDENCE",
                        }
                    ],
                },
            )

            with self.assertRaisesRegex(
                workflow.ReviewWorkflowError,
                "PENDING_EVIDENCE",
            ):
                validate_decisions(decisions_path, response_path)

    def test_build_round2_embeds_round1_and_locks_protected_fields(self):
        workflow = load_workflow()
        build_round2 = require_function(self, workflow, "build_round2")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            complete_round1(work_dir, workflow)

            result = build_round2(work_dir, review_cycle_id="cycle-fixture")

            packet_path = work_dir / "chatgpt_review" / "round2_audit_packet.md"
            self.assertEqual(result["review_round"], 2)
            self.assertTrue(packet_path.is_file())
            packet = packet_path.read_text(encoding="utf-8")
            self.assertIn("review_round: 2\n", packet)
            self.assertIn("## round1_chatgpt_raw.md\n", packet)
            self.assertIn("## round1_codex_decisions.json\n", packet)
            self.assertIn("## revised timeline_design.json\n", packet)
            self.assertRegex(
                packet,
                r"protected_fields_sha256: [a-f0-9]{64}\n",
            )
            self.assertEqual(
                result["sent_packet_sha256"],
                workflow.canonical_packet_sha256(packet),
            )

    def test_finalize_gate_rejects_nonpassing_raw_round2_recommendation(self):
        workflow = load_workflow()
        build_round2 = require_function(self, workflow, "build_round2")
        finalize_gate = require_function(self, workflow, "finalize_gate")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            complete_round1(work_dir, workflow)
            round2 = build_round2(work_dir, review_cycle_id="cycle-fixture")
            write_text(
                work_dir / "chatgpt_review" / "round2_chatgpt_raw.md",
                valid_response_for(round2, recommendation="REVISE_REQUIRED"),
            )

            with self.assertRaisesRegex(
                workflow.ReviewWorkflowError,
                "REVISE_REQUIRED",
            ):
                finalize_gate(work_dir)
            self.assertFalse((work_dir / "chatgpt_review_gate.json").exists())

    def test_finalize_gate_writes_pass_from_valid_raw_artifacts(self):
        workflow = load_workflow()
        build_round2 = require_function(self, workflow, "build_round2")
        finalize_gate = require_function(self, workflow, "finalize_gate")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            complete_round1(work_dir, workflow)
            round2 = build_round2(work_dir, review_cycle_id="cycle-fixture")
            write_text(
                work_dir / "chatgpt_review" / "round2_chatgpt_raw.md",
                valid_response_for(round2, recommendation="PASS_RECOMMENDED"),
            )

            gate = finalize_gate(work_dir)

            gate_path = work_dir / "chatgpt_review_gate.json"
            self.assertTrue(gate_path.is_file())
            self.assertEqual(gate["status"], "PASS")
            self.assertEqual(
                gate["gate_name"],
                "CHATGPT_PROJECT_TWO_PASS_REVIEW_GATE",
            )
            self.assertEqual(gate["round2"]["recommendation"], "PASS_RECOMMENDED")
            self.assertIs(gate["protected_fields_changed_after_round2"], False)
            self.assertEqual(gate["final_decision_owner"], "Codex")

    def test_finalize_gate_rejects_protected_field_change_after_round2(self):
        workflow = load_workflow()
        build_round2 = require_function(self, workflow, "build_round2")
        finalize_gate = require_function(self, workflow, "finalize_gate")
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            create_round1_fixture(work_dir)
            complete_round1(work_dir, workflow)
            round2 = build_round2(work_dir, review_cycle_id="cycle-fixture")
            write_text(
                work_dir / "chatgpt_review" / "round2_chatgpt_raw.md",
                valid_response_for(round2, recommendation="PASS_RECOMMENDED"),
            )
            timeline_path = work_dir / "timeline_design.json"
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            timeline["segments"][0]["time_end"] = 3
            write_json(timeline_path, timeline)

            with self.assertRaisesRegex(
                workflow.ReviewWorkflowError,
                "protected fields changed",
            ):
                finalize_gate(work_dir)


if __name__ == "__main__":
    unittest.main()
