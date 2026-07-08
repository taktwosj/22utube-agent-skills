from __future__ import annotations

import hashlib
import json
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


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_json(path: Path, data: dict) -> None:
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_script_handoff(root: Path, *, inline_voice_map: bool = True) -> None:
    gate = {
        "gate_name": "SCRIPT_HANDOFF_GATE",
        "status": "PASS",
        "generated_by": "tikitaka_harness_runner",
        "script_status": "SCRIPT_LOCK_PACKAGE",
        "capcut_allowed": True,
        "input_files": ["block_map.json"],
    }
    block_map = {
        "edit_block_sequence": ["E1", "E2"],
        "blocks": [
            {
                "edit_id": "E1",
                "source_block_id": "S1",
                "original_order": 1,
                "urakkai_order": 2,
            },
            {
                "edit_id": "E2",
                "source_block_id": "S2",
                "original_order": 2,
                "urakkai_order": 1,
            },
        ],
    }
    voice_map = {
        "switches": [
            {"edit_id": "E1", "source_audio": "off", "tts": "on"},
            {"edit_id": "E2", "source_audio": "on", "tts": "off"},
        ]
    }
    if inline_voice_map:
        block_map["block_voice_switch_map"] = voice_map["switches"]
    else:
        gate["input_files"].append("block_voice_switch_map.json")
        gate["block_voice_switch_map_path"] = "block_voice_switch_map.json"
        write_json(root / "20_script" / "block_voice_switch_map.json", voice_map)

    write_json(root / "20_script" / "script_handoff_gate.json", gate)
    write_json(root / "20_script" / "block_map.json", block_map)


def create_report1_handoff(root: Path, *, status: str = "PASS", next_skill: str = "000short-production-agent") -> None:
    write_json(
        root / "20_script" / "report1_handoff.json",
        {
            "gate_name": "REPORT1_HANDOFF_GATE",
            "status": status,
            "report": "보고서1",
            "owner_skill": "00-tikitaka",
            "next_skill": next_skill,
            "next_stage": "보고서2",
            "next_gate": "CAPCUT_OPENABLE_PROJECT",
            "required_before_next": [
                "report1_approved=true",
                "voice_audio_route_decided=true",
            ],
            "report1_approved": status == "PASS",
            "voice_audio_route_decided": status == "PASS",
        },
    )


def create_shrt_white_reference(root: Path) -> dict:
    reference_path = root / "capcut_refs" / "shrt white"
    reference_path.mkdir(parents=True, exist_ok=True)
    return {
        "template_profile": "shrt_white_base_v1",
        "reference_project_name": "shrt white",
        "reference_project_path": str(reference_path),
        "derived_from_reference_project": True,
    }


def create_shared_fixture(root: Path, script_lock: dict | None = None) -> dict:
    create_script_handoff(root)
    create_report1_handoff(root)
    write(root / "20_script" / "writer_evidence.md")
    write(root / "20_script" / "final_script_ko.md", "최종 대본")
    write_json(root / "10_analysis" / "analysis.json", {"status": "PASS"})
    write_json(root / "10_analysis" / "tikitaka_decision_log.json", {"status": "PASS"})
    write_json(root / "10_analysis" / "watch_direct_frame.json", {"status": "PASS"})
    write_json(root / "90_reports" / "harness_analysis.json", {"status": "PASS"})
    write_json(root / "90_reports" / "harness_assets.json", {"status": "PASS"})
    write_json(root / "90_reports" / "validation_report.json", {"status": "PASS"})
    script_lock = script_lock or {
        "status": "SCRIPT_LOCK",
        "source": "tikitaka_harness_runner",
        "writer_persona_pass_count": 4,
        "hard_veto": False,
    }
    write_json(root / "20_script" / "script_lock_evidence.json", script_lock)

    return {
        "similarity_breaker_harness": "PASS",
        "writer_agent_source": "REAL_AGENT",
        "writer_agent_mode_status": "REAL_RUN",
        "writer_persona_total": 5,
        "writer_persona_pass_count": 4,
        "writer_agent_evidence_files": ["20_script/writer_evidence.md"],
        "hard_veto": False,
        "script_lock_evidence_path": "20_script/script_lock_evidence.json",
        "watch_direct_frame_status": "PASS",
        "watch_direct_frame_report": "10_analysis/watch_direct_frame.json",
        "final_script_ko_path": "20_script/final_script_ko.md",
        "analysis_json_path": "10_analysis/analysis.json",
        "tikitaka_decision_log_path": "10_analysis/tikitaka_decision_log.json",
        "harness_report_analysis": "90_reports/harness_analysis.json",
        "harness_report_assets": "90_reports/harness_assets.json",
        "validation_report_path": "90_reports/validation_report.json",
    }


def create_proof_fixture(root: Path) -> None:
    write_json(
        root / "cut_manifest.json",
        {
            "source_segments": [{"id": "S1"}, {"id": "S2"}],
            "timeline_order": ["S2", "S1"],
        },
    )
    write_bytes(root / "proof" / "contact_sheet.jpg", b"\xff\xd8\xff\xe0JFIF\x00\xff\xd9")
    write(root / "proof" / "clip_durations.csv", "clip,status\nS1,PASS\nS2,PASS\n")
    write(root / "proof" / "timeline_order.txt", "S2\nS1\n")
    write_json(
        root / "proof" / "capcut_assembly_report.json",
        {
            "status": "PASS",
            "timeline_order_verified": True,
            "visible_trim_verified": True,
            "handle_extendable": True,
            "independent_clips_verified": True,
            "proof_files_verified": True,
        },
    )


def create_full_contract(root: Path) -> dict:
    write_json(root / "render_plan.json", {"actual_render_order": ["B", "A"]})
    write_json(root / "90_reports" / "source_dialogue.json", {"status": "NO_DIALOGUE"})
    write_json(root / "30_audio_srt" / "tts_manifest.json", {"status": "PASS"})
    write(root / "input" / "source.txt", "source-v1")
    contract = {
        "source_url": "https://example.test/watch?v=abc",
        "render_plan_path": "render_plan.json",
        "edit_assembly_mode": "order_remix",
        "original_beat_order": ["A", "B"],
        "remix_candidates": [["B", "A"], ["A", "B"], ["B", "A"]],
        "selected_remix_order": ["B", "A"],
        "youtube_restriction_guideline_gate_complete": True,
        "youtube_restriction_policy_risk_tier": "LOW",
        "youtube_restriction_platform_verdict": "PASS",
        "youtube_restriction_hard_blocks": [],
        "youtube_restriction_rewrite_required": [],
        "generated_tts_authorized": True,
        "user_srt_audio_required": False,
        "source_dialogue_analysis_status": "NO_DIALOGUE",
        "source_dialogue_analysis_provider": "whisper",
        "source_dialogue_analysis_path": "90_reports/source_dialogue.json",
        "tts_manifest_path": "30_audio_srt/tts_manifest.json",
        "input_files": [
            {
                "path": "input/source.txt",
                "sha256": sha256(root / "input" / "source.txt"),
            }
        ],
        "report1_approved": True,
        "voice_audio_route_decided": True,
        "tts_route": "Codex/API TTS 생성",
        "user_upload_approval": True,
        "rights_risk_acknowledged": True,
        "user_request": "capcut project",
    }
    contract.update(create_shared_fixture(root))
    return contract


def trusted_stage2_job_state() -> dict:
    stage_scope_gate = {"status": "PASS", "decision": "stage_2_full"}
    return {
        "user_stage_decision": "stage_2_full",
        "stage_scope_gate": stage_scope_gate,
        "script_lock": {
            "status": "SCRIPT_LOCK",
            "source": "tikitaka_harness_runner",
            "generated_by": "tikitaka_harness_runner",
            "stage_scope_gate": stage_scope_gate,
        },
        "validation": {"status": "PASS"},
        "evidence_pack": {"status": "PASS"},
        "harness_trace": {"status": "PASS"},
        "report1_approved": True,
        "voice_audio_route_decided": True,
        "tts_route": "Codex/API TTS 생성",
    }


class ProductionGateBehavioralContractTests(unittest.TestCase):
    def test_tikitaka_harness_writes_canonical_script_lock_evidence(self):
        module = load_source_module_no_bytecode("tikitaka_harness_script_lock_evidence", TIKITAKA_HARNESS)

        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            from test_script_handoff_gate_execution_contract import (
                create_script_lock_package_artifacts,
                create_tikitaka_base_evidence,
                write_stage2_decision,
            )

            create_tikitaka_base_evidence(work_dir)
            create_script_lock_package_artifacts(work_dir)
            write_stage2_decision(work_dir)

            module.audit(work_dir, "job-test")
            evidence = module.read_json(work_dir / "script_lock_evidence.json")

            self.assertEqual(evidence["status"], "SCRIPT_LOCK")
            self.assertEqual(evidence["source"], "tikitaka_harness_runner")
            self.assertGreaterEqual(evidence["writer_persona_pass_count"], 4)
            self.assertIs(evidence["hard_veto"], False)

    def test_validate_shared_requirements_rejects_phantom_script_lock_source(self):
        module = load_source_module_no_bytecode("production_gate_phantom_lock_source", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_shared_fixture(
                root,
                {
                    "status": "SCRIPT_LOCK",
                    "source": "validate_writer_agent",
                    "writer_persona_pass_count": 4,
                    "hard_veto": False,
                },
            )

            with self.assertRaisesRegex(module.GateFail, "SCRIPT_LOCK must be generated"):
                module.validate_shared_requirements(contract, root)

    def test_validate_shared_requirements_rejects_script_locked_token(self):
        module = load_source_module_no_bytecode("production_gate_script_locked_token", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_shared_fixture(
                root,
                {
                    "status": "SCRIPT_LOCKED",
                    "source": "tikitaka_harness_runner",
                    "writer_persona_pass_count": 4,
                    "hard_veto": False,
                },
            )

            with self.assertRaisesRegex(module.GateFail, "status must be SCRIPT_LOCK"):
                module.validate_shared_requirements(contract, root)

    def test_bare_pass_true_report_is_not_pass_authority(self):
        module = load_source_module_no_bytecode("production_gate_bare_pass", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "reports" / "stub.json", {"pass": True})

            with self.assertRaisesRegex(module.GateFail, "status must be PASS"):
                module.require_json_status_pass(root, "reports/stub.json", "stub_report")

    def test_validate_script_handoff_gate_accepts_separate_voice_switch_map(self):
        module = load_source_module_no_bytecode("production_gate_separate_voice_map", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root, inline_voice_map=False)

            result = module.validate_script_handoff_gate({}, root)

            self.assertEqual(result["script_handoff_gate_status"], "PASS")

    def test_validate_script_handoff_gate_fails_voice_switch_coverage_gap(self):
        module = load_source_module_no_bytecode("production_gate_voice_gap", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            block_map_path = root / "20_script" / "block_map.json"
            block_map = json.loads(block_map_path.read_text(encoding="utf-8"))
            block_map["block_voice_switch_map"] = [
                {"edit_id": "E1", "source_audio": "off", "tts": "on"}
            ]
            write_json(block_map_path, block_map)

            with self.assertRaisesRegex(module.GateFail, "voice switch coverage"):
                module.validate_script_handoff_gate({}, root)

    def test_capcut_openable_requires_draft_content_artifact(self):
        module = load_source_module_no_bytecode("production_gate_openable_draft_required", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})

            with self.assertRaisesRegex(module.GateFail, "draft_content"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        **create_shrt_white_reference(root),
                    },
                    root,
                )

    def test_capcut_openable_requires_report1_handoff_gate_file(self):
        module = load_source_module_no_bytecode("production_gate_openable_report1_handoff_required", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_HANDOFF_GATE"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        **create_shrt_white_reference(root),
                    },
                    root,
                )

    def test_capcut_openable_rejects_wait_report1_handoff_gate(self):
        module = load_source_module_no_bytecode("production_gate_openable_report1_handoff_wait", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root, status="WAIT")
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_HANDOFF_GATE"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        **create_shrt_white_reference(root),
                    },
                    root,
                )

    def test_capcut_openable_rejects_report1_handoff_wrong_next_skill(self):
        module = load_source_module_no_bytecode("production_gate_openable_report1_handoff_wrong_skill", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root, next_skill="00-tikitaka")
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_HANDOFF_GATE"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                    },
                    root,
                )

    def test_capcut_openable_template_requires_reference_project_resolution(self):
        module = load_source_module_no_bytecode("production_gate_template_reference_required", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        "user_explicit_template_override": True,
                        "template_profile": "character-comments",
                    },
                    root,
                )

    def test_capcut_openable_template_reports_root_reference_project_used(self):
        module = load_source_module_no_bytecode("production_gate_template_reference_pass", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root_reference_name = "character-comments-root-template-v1"
            reference_path = root / "capcut_refs" / root_reference_name
            reference_path.mkdir(parents=True)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(
                root / "00_source" / "source_manifest.json",
                {
                    "status": "PASS",
                    "upload_title": "test title",
                    "upload_description": "test body",
                    "source_url": "https://example.com/source",
                },
            )
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            result = module.validate_capcut_openable_project_entry(
                {
                    "user_request": "capcut project",
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                    "user_explicit_template_override": True,
                    "template_profile": "character-comments",
                    "reference_project_name": root_reference_name,
                    "reference_project_path": str(reference_path),
                    "derived_from_reference_project": True,
                    "capcut_project_name": "SH_20260708_t_fdf0wfjg_character_comments_base_v2",
                },
                root,
            )

            self.assertEqual(result["template_reference_resolution_gate"], "PASS")
            self.assertEqual(result["reference_project_name"], root_reference_name)
            self.assertIn(root_reference_name, result["report2"])

    def test_character_comments_blocks_known_derived_project_as_root_reference(self):
        module = load_source_module_no_bytecode("production_gate_template_reference_derived_fail", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference_path = root / "capcut_refs" / module.CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT
            reference_path.mkdir(parents=True)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "FAIL_TEMPLATE_ROOT_NOT_RESOLVED"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        "user_explicit_template_override": True,
                        "template_profile": "character-comments",
                        "reference_project_name": module.CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT,
                        "reference_project_path": str(reference_path),
                        "derived_from_reference_project": True,
                    },
                    root,
                )

    def test_capcut_openable_blocks_without_user_stage_decision(self):
        module = load_source_module_no_bytecode("production_gate_openable_stage_decision", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
                module.validate_capcut_openable_project_entry({}, root)

    def test_capcut_openable_rejects_status_file_stage2_decision_without_gate_pass(self):
        module = load_source_module_no_bytecode("production_gate_openable_status_injection", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})
            write_json(root / "status.json", {"stage_scope_gate": {"decision": "stage_2_full"}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "유튜브 URL과 Gemini 분석본으로 진행해줘",
                        "status_json_path": "status.json",
                    },
                    root,
                )

    def test_capcut_openable_rejects_self_attested_status_file_stage2_decision(self):
        module = load_source_module_no_bytecode("production_gate_openable_status_self_attested", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})
            write_json(
                root / "status.json",
                {
                    "user_stage_decision": "stage_2_full",
                    "stage_scope_gate": {"status": "PASS", "decision": "stage_2_full"},
                },
            )

            with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "progress from URL and Gemini",
                        "status_json_path": "status.json",
                    },
                    root,
                )

    def test_capcut_openable_accepts_trusted_status_file_stage2_decision(self):
        module = load_source_module_no_bytecode("production_gate_openable_status_gate_pass", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})
            write_json(
                root / "status.json",
                trusted_stage2_job_state(),
            )

            result = module.validate_capcut_openable_project_entry(
                {
                    "user_request": "유튜브 URL과 Gemini 분석본으로 진행해줘",
                    "status_json_path": "status.json",
                    "upload_title": "테스트 쇼츠 제목",
                    "upload_description": "테스트 쇼츠 설명\n출처: https://example.com/source\n#shorts",
                    "source_url": "https://example.com/source",
                    **create_shrt_white_reference(root),
                },
                root,
            )

            self.assertEqual(result["status"], "CAPCUT_OPENABLE_PROJECT_ALLOWED")
            self.assertIn("# 보고서2", result["report2"])
            self.assertIn("보고서2 시작: 예", result["report2"])
            self.assertIn("최종보고서: 예", result["report2"])
            self.assertIn("상태: REPORT2_FINAL", result["report2"])
            self.assertIn("제목: 테스트 쇼츠 제목", result["report2"])
            self.assertIn("내용(출처 태그 포함):", result["report2"])
            self.assertIn("출처: https://example.com/source", result["report2"])
            self.assertIn("대본 반영: 예", result["report2"])
            self.assertIn("TTS/오디오 반영: 아니오", result["report2"])
            self.assertIn("자막 반영: 아니오", result["report2"])
            self.assertIn("원본 영상 반영: 아니오", result["report2"])
            self.assertIn("임시파일 정리: 아니오", result["report2"])
            self.assertIn("업로드 준비 완료: 아니오", result["report2"])
            self.assertIn("남은 일:", result["report2"])

    def test_capcut_openable_requires_shrt_white_as_default_base(self):
        module = load_source_module_no_bytecode("production_gate_default_shrt_white_required", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_SHRT_WHITE_BASE_REQUIRED"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                    },
                    root,
                )

    def test_capcut_openable_rejects_prior_derived_project_as_default_base(self):
        module = load_source_module_no_bytecode("production_gate_prior_derived_default_base", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference_path = root / "capcut_refs" / module.CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT
            reference_path.mkdir(parents=True)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "FAIL_DEFAULT_SHRT_WHITE_BASE_REQUIRED"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        "template_profile": "character-comments",
                        "reference_project_name": module.CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT,
                        "reference_project_path": str(reference_path),
                        "derived_from_reference_project": True,
                    },
                    root,
                )

    def test_capcut_openable_blocks_stale_builder_reference_name(self):
        module = load_source_module_no_bytecode("production_gate_stale_builder_reference_name", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})
            write(
                root / "90_reports" / "build_character_comments_base_v2.py",
                f'REFERENCE_NAME = "{module.CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT}"\n',
            )

            with self.assertRaisesRegex(module.GateFail, "FAIL_STALE_DERIVED_REFERENCE_BUILDER"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        **create_shrt_white_reference(root),
                    },
                    root,
                )

    def test_capcut_openable_rejects_untrusted_status_file_report1_voice_override(self):
        module = load_source_module_no_bytecode("production_gate_openable_status_approval_injection", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})
            write_json(
                root / "status.json",
                {
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                },
            )

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": False,
                        "voice_audio_route_decided": False,
                        "status_json_path": "status.json",
                    },
                    root,
                )

    def test_capcut_openable_rejects_stale_reentry_source_manifest(self):
        module = load_source_module_no_bytecode("production_gate_openable_stale_source", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            create_report1_handoff(root)
            write_json(
                root / "00_source" / "source_manifest.json",
                {
                    "status": "WAIT_SOURCE_DOWNLOAD",
                    "local_source_path": "00_source/missing.mp4",
                },
            )
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "source_manifest status must be PASS"):
                module.validate_capcut_openable_project_entry(
                    {
                        "user_request": "capcut project",
                        "report1_approved": True,
                        "voice_audio_route_decided": True,
                        **create_shrt_white_reference(root),
                    },
                    root,
                )

    def test_validate_gate_requires_hard_fail_proof_files(self):
        module = load_source_module_no_bytecode("production_gate_requires_proof", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)

            with self.assertRaisesRegex(module.GateFail, "cut_manifest"):
                module.validate_gate(contract, root)

    def test_validate_gate_blocks_without_user_stage_decision_before_proof(self):
        module = load_source_module_no_bytecode("production_gate_stage_decision_before_proof", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            contract.pop("user_request", None)

            with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
                module.validate_gate(contract, root)

    def test_validate_gate_rejects_edited_input_hash(self):
        module = load_source_module_no_bytecode("production_gate_input_hash", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            create_proof_fixture(root)
            write(root / "input" / "source.txt", "source-edited")

            with self.assertRaisesRegex(module.GateFail, "sha256 mismatch"):
                module.validate_gate(contract, root)

    def test_validate_gate_rejects_string_form_input_files_without_hash(self):
        module = load_source_module_no_bytecode("production_gate_string_input_hash", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            contract["input_files"] = ["input/source.txt"]
            create_proof_fixture(root)

            with self.assertRaisesRegex(module.GateFail, "sha256 required"):
                module.validate_gate(contract, root)

    def test_validate_gate_requires_at_least_one_hashed_input_file(self):
        module = load_source_module_no_bytecode("production_gate_min_input_hash", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            contract["input_files"] = []
            create_proof_fixture(root)

            with self.assertRaisesRegex(module.GateFail, "input_files must include"):
                module.validate_gate(contract, root)

    def test_validate_gate_rejects_invalid_contact_sheet_contents(self):
        module = load_source_module_no_bytecode("production_gate_contact_sheet", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            create_proof_fixture(root)
            write(root / "proof" / "contact_sheet.jpg", "not an image")

            with self.assertRaisesRegex(module.GateFail, "contact_sheet"):
                module.validate_gate(contract, root)

    def test_validate_gate_rejects_clip_duration_rows_that_are_not_pass(self):
        module = load_source_module_no_bytecode("production_gate_clip_duration_rows", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            create_proof_fixture(root)
            write(root / "proof" / "clip_durations.csv", "clip,status\nS1,FAIL\nS2,PASS\n")

            with self.assertRaisesRegex(module.GateFail, "clip_durations"):
                module.validate_gate(contract, root)

    def test_validate_gate_rejects_timeline_order_text_mismatch(self):
        module = load_source_module_no_bytecode("production_gate_timeline_text", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            create_proof_fixture(root)
            write(root / "proof" / "timeline_order.txt", "S1\nS2\n")

            with self.assertRaisesRegex(module.GateFail, "timeline_order"):
                module.validate_gate(contract, root)

    def test_complete_production_gate_fixture_passes_with_real_proof_and_hashes(self):
        module = load_source_module_no_bytecode("production_gate_complete_fixture", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_full_contract(root)
            create_proof_fixture(root)

            result = module.validate_gate(contract, root)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["project_file_request_mode"], "AUTO_FULL_CAPCUT_PROJECT")
            self.assertIs(result["upload_ready_allowed"], True)

    def test_project_file_request_mode_blocks_stage1_request_before_stage2(self):
        module = load_source_module_no_bytecode("production_gate_project_mode", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
            module.project_file_request_mode({"user_request": "유튜브 URL과 Gemini 분석본으로 대본까지만 해줘"})

    def test_project_file_request_mode_blocks_silent_default_before_stage2(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_silent", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
            module.project_file_request_mode({"source_url": "https://youtube.test/watch?v=abc"})

    def test_project_file_request_mode_blocks_url_gemini_generic_progress_without_stage_decision(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_url_gemini_generic", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
            module.project_file_request_mode(
                {
                    "source_url": "https://youtube.test/watch?v=abc",
                    "analysis_hint_raw": "Gemini raw intake",
                    "user_request": "유튜브 URL과 Gemini 분석본으로 진행해줘",
                }
            )

    def test_project_file_request_mode_stage2_token_opens_auto_full(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_stage2", PRODUCTION_GATE)

        for request in [
            "유튜브 URL로 캣컵프로젝트파일까지 진행해줘",
            "유튜브 URL로 캐컷프로젝트파일까지 진행해줘",
            "TTS mp3까지 받아서 진행해줘",
            "capcut project까지 진행해줘",
        ]:
            with self.subTest(request=request):
                self.assertEqual(
                    module.project_file_request_mode(
                        {
                            "user_request": request,
                            "report1_approved": True,
                            "voice_audio_route_decided": True,
                        }
                    ),
                    "AUTO_FULL_CAPCUT_PROJECT",
                )

    def test_project_file_request_mode_blocks_stage2_token_before_report1_approval(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_report1_wait", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
            module.project_file_request_mode(
                {
                    "user_request": "유튜브 URL로 캣컵프로젝트파일까지 진행해줘",
                    "voice_audio_route_decided": True,
                }
            )

    def test_project_file_request_mode_blocks_stage2_token_before_tts_decision(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_tts_wait", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
            module.project_file_request_mode(
                {
                    "user_request": "유튜브 URL로 캣컵프로젝트파일까지 진행해줘",
                    "report1_approved": True,
                }
            )

    def test_project_file_request_mode_generated_tts_authorized_is_not_voice_route_decision(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_generated_tts_not_route", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
            module.project_file_request_mode(
                {
                    "user_request": "자동모드로 끝까지",
                    "report1_approved": True,
                    "generated_tts_authorized": True,
                }
            )

    def test_stage2_request_tokens_do_not_include_generic_progress_words(self):
        module = load_source_module_no_bytecode("production_gate_stage2_generic_tokens", PRODUCTION_GATE)

        for token in ["진행", "해줘", "쭉"]:
            with self.subTest(token=token):
                self.assertNotIn(token, module.STAGE2_REQUEST_TOKENS)

    def test_project_file_request_mode_tts_path_without_voice_route_decision_blocks_auto_full(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_tts_path", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
            module.project_file_request_mode(
                {
                    "user_tts_audio_path": "D:/Downloads/hook.mp3",
                    "report1_approved": True,
                }
            )

    def test_project_file_request_mode_tts_path_with_voice_route_decision_opens_auto_full(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_tts_path_ready", PRODUCTION_GATE)

        self.assertEqual(
            module.project_file_request_mode(
                {
                    "user_tts_audio_path": "D:/Downloads/hook.mp3",
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                }
            ),
            "AUTO_FULL_CAPCUT_PROJECT",
        )

    def test_project_file_request_mode_auto_mode_token_opens_auto_full(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_auto_mode", PRODUCTION_GATE)

        self.assertEqual(
            module.project_file_request_mode(
                {
                    "user_request": "자동모드로 끝까지",
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                }
            ),
            "AUTO_FULL_CAPCUT_PROJECT",
        )

    def test_project_file_request_mode_fast_draft_tokens_match_skill_contract(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_draft_fast_tokens", PRODUCTION_GATE)

        for request in ["DRAFT_FAST", "검토용 draft만", "검토용 드래프트만", "빠른 초안", "기술 초안"]:
            with self.subTest(request=request):
                self.assertEqual(
                    module.project_file_request_mode(
                        {
                            "production_mode": "DRAFT_FAST",
                            "user_request": request,
                            "report1_approved": True,
                            "voice_audio_route_decided": True,
                        }
                    ),
                    "DRAFT_FAST",
                )

    def test_project_file_request_mode_draft_fast_blocks_before_report1_approval(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_draft_fast_report1_wait", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
            module.project_file_request_mode(
                {
                    "production_mode": "DRAFT_FAST",
                    "user_request": "DRAFT_FAST",
                    "voice_audio_route_decided": True,
                }
            )

    def test_project_file_request_mode_draft_fast_blocks_before_voice_route_decision(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_draft_fast_voice_wait", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
            module.project_file_request_mode(
                {
                    "production_mode": "DRAFT_FAST",
                    "user_request": "검토용 draft만",
                    "report1_approved": True,
                }
            )

    def test_project_file_request_mode_draft_fast_requires_literal_fast_token(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_draft_fast_literal_token", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_DRAFT_FAST_EXPLICIT_TOKEN"):
            module.project_file_request_mode(
                {
                    "production_mode": "DRAFT_FAST",
                    "user_request": "capcut project",
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                }
            )

    def test_capcut_openable_draft_fast_blocks_without_report1_and_voice_route(self):
        module = load_source_module_no_bytecode("production_gate_openable_draft_fast_wait", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_script_handoff(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})
            write_json(root / "50_capcut_project" / "draft_content.json", {"materials": {}})

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
                module.validate_capcut_openable_project_entry(
                    {
                        "production_mode": "DRAFT_FAST",
                        "user_request": "DRAFT_FAST",
                    },
                    root,
                )

    def test_project_file_request_mode_rejects_unverified_user_stage_decision(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_decision", PRODUCTION_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_USER_STAGE_DECISION"):
            module.project_file_request_mode({"user_stage_decision": "stage_2_full"})

    def test_merged_request_scope_strips_untrusted_stage_scope_verified_flag(self):
        module = load_source_module_no_bytecode("production_gate_stage_scope_verified_flag", PRODUCTION_GATE)

        with tempfile.TemporaryDirectory() as tmp:
            merged = module.merged_request_scope_contract(
                {
                    "user_stage_decision": "stage_2_full",
                    "_stage_scope_gate_verified": True,
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                },
                Path(tmp),
            )

        self.assertNotIn("_stage_scope_gate_verified", merged)
        self.assertNotIn("user_stage_decision", merged)

    def test_project_file_request_mode_verified_stage_scope_opens_auto_full(self):
        module = load_source_module_no_bytecode("production_gate_project_mode_verified_decision", PRODUCTION_GATE)

        self.assertEqual(
            module.project_file_request_mode(
                {
                    "user_stage_decision": "stage_2_full",
                    "_stage_scope_gate_verified": True,
                    "report1_approved": True,
                    "voice_audio_route_decided": True,
                }
            ),
            "AUTO_FULL_CAPCUT_PROJECT",
        )


if __name__ == "__main__":
    unittest.main()
