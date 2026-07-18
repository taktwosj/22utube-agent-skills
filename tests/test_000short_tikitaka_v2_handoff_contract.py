from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from _support import (
    load_source_module_no_bytecode,
    write_source_voice_separation_fixture,
    write_valid_source_mp4,
)


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
                    "source_ref": "S3",
                    "source_order": 3,
                    "timeline_order": 1,
                    "assembly_role": "intro_narration",
                    "time_start": "00:00",
                    "time_end": "00:03",
                    "track": "audio.narration_tts",
                    "semantic_lane": "narration_tts",
                    "resolved_capcut_track": None,
                    "resolved_by": "000short-production-agent",
                    "caption_type": "tts_narration",
                    "visible_text_role": "tts_caption",
                    "audio_role": "audio.narration_tts",
                    "duration_basis": "estimated_tts_duration",
                    "duration_status": "ESTIMATED_ACCEPTED",
                    "tts_text_ref": "tts_copy_text.txt#E1",
                    "planned_tts_duration_sec": 3.0,
                    "tts_duration_status": "ESTIMATED_ACCEPTED",
                    "estimated_tts_duration_sec": 2.8,
                    "audio_policy": "tts_on_source_off",
                    "visual_strategy": "source_visual_hold",
                },
                {
                    "edit_id": "E2",
                    "source_ref": "S1",
                    "source_order": 1,
                    "timeline_order": 2,
                    "assembly_role": "verified_speaker_quote",
                    "time_start": "00:03",
                    "time_end": "00:08",
                    "track": "audio.speaker_source",
                    "semantic_lane": "speaker_source",
                    "resolved_capcut_track": None,
                    "resolved_by": "000short-production-agent",
                    "caption_type": "speaker_quote",
                    "visible_text_role": "speaker_quote",
                    "audio_role": "audio.speaker_source",
                    "duration_basis": "source_range",
                    "duration_status": "SOURCE_AUDIO_LOCKED",
                    "source_audio_range": {"start": "00:03", "end": "00:08"},
                    "source_audio_ref": "10_analysis/audio/vocals.wav",
                    "source_audio_provenance": "demucs_full_source_vocals",
                    "quote_verification_status": "VERIFIED_STT",
                    "audio_policy": "source_on_tts_off",
                    "visual_strategy": "source_visual_action",
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
                    "source_block_id": "S3",
                    "original_order": 3,
                    "urakkai_order": 1,
                },
                {
                    "edit_id": "E2",
                    "source_block_id": "S1",
                    "original_order": 1,
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
    write_json(
        root / "20_script" / "tts_duration_probe.json",
        {
            "status": "ESTIMATED_ACCEPTED",
            "tts_items": [
                {
                    "edit_id": "E1",
                    "planned_tts_duration_sec": 3.0,
                    "estimated_tts_duration_sec": 2.8,
                    "within_tolerance": True,
                }
            ],
        },
    )
    write_json(
        root / "20_script" / "tts_timing_reconciliation_gate.json",
        {
            "status": "PASS",
            "tts_duration_status": "ESTIMATED_ACCEPTED",
            "reconciliation_action": "none",
        },
    )
    source = root / "00_source" / "source.mp4"
    write_valid_source_mp4(source)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    source_lock = {
        "status": "PASS",
        "canonical_url": "https://www.youtube.com/shorts/fixture123",
        "video_id": "fixture123",
        "local_source_path": "00_source/source.mp4",
        "sha256": source_sha256,
        "duration_sec": 8.0,
    }
    write_json(root / "10_analysis" / "source_identity_lock.json", source_lock)
    write_source_voice_separation_fixture(root, source_sha256)
    write_json(
        root / "10_analysis" / "source_evidence.json",
        {
            "status": "PASS",
            "video_id": "fixture123",
            "source_fingerprint_sha256": source_sha256,
            "ffprobe_status": "PASS",
            "has_video_stream": True,
            "probed_duration_sec": 8.0,
            "source": {
                "status": "PASS",
                "local_source_path": "00_source/source.mp4",
                "sha256": source_sha256,
                "duration_sec": 8.0,
            },
            "scene_detection": {"status": "PASS", "scene_count": 1},
            "stt": {
                "status": "PASS",
                "verified_ranges": [
                    {"source_ref": "S1", "start": "00:03", "end": "00:08"}
                ],
            },
            "ocr": {"status": "NOT_REQUIRED", "reason": "fixture has no text dependency"},
            "audio_vad": {
                "status": "PASS",
                "speech_ranges": [{"start": "00:03", "end": "00:08"}],
            },
        },
    )
    write_json(
        root / "10_analysis" / "crosscheck_report.json",
        {
            "status": "PASS",
            "video_id": "fixture123",
            "source_fingerprint_sha256": source_sha256,
            "analysis_hint_saved": True,
            "hint_vs_evidence_compared": True,
            "mismatches_recorded": True,
            "supported": [],
            "contradicted": [],
            "uncertain": [],
            "needs_manual_review": [],
        },
    )
    write_json(
        root / "00_source" / "source_manifest.json",
        {
            **source_lock,
            "source_identity_lock_path": "10_analysis/source_identity_lock.json",
            "source_evidence_path": "10_analysis/source_evidence.json",
            "crosscheck_report_path": "10_analysis/crosscheck_report.json",
        },
    )
    write_json(
        root / "10_analysis" / "tikitaka_source_request.json",
        {
            "status": "PASS",
            "owner_skill": "00-tikitaka",
            "requested_source_url": source_lock["canonical_url"],
            "requested_video_id": source_lock["video_id"],
            "user_stage_decision": "stage_2_full",
        },
    )
    for relative in (
        "20_script/report1_handoff.json",
        "20_script/script_handoff_gate.json",
        "20_script/timeline_design.json",
    ):
        path = root / relative
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["source_fingerprint_sha256"] = source_sha256
        write_json(path, payload)
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
    def test_tikitaka_source_request_requires_pass_and_exact_owner(self):
        module = load_source_module_no_bytecode("stage2_tikitaka_source_request_status", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "10_analysis" / "tikitaka_source_request.json"
            request = json.loads(path.read_text(encoding="utf-8"))
            request["status"] = "FAIL"
            request.pop("owner_skill")
            write_json(path, request)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_REQUEST_BINDING"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_contract_youtube_url_must_exactly_match_tikitaka_request(self):
        module = load_source_module_no_bytecode("stage2_tikitaka_exact_url", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_valid_tikitaka_v2_package(root)
            contract["source_url"] = "https://youtu.be/fixture123"

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_REQUEST_BINDING"):
                module.validate_stage2_tikitaka_handoff(root, contract)

    def test_current_tikitaka_request_must_match_source_lock(self):
        module = load_source_module_no_bytecode("stage2_tikitaka_source_mismatch", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = create_valid_tikitaka_v2_package(root)
            write_json(
                root / "10_analysis" / "tikitaka_source_request.json",
                {
                    "status": "PASS",
                    "owner_skill": "00-tikitaka",
                    "requested_source_url": "https://www.youtube.com/shorts/BRAlwARPPFo",
                    "requested_video_id": "BRAlwARPPFo",
                    "user_stage_decision": "stage_2_full",
                },
            )
            contract["source_url"] = "https://www.youtube.com/shorts/BRAlwARPPFo"

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_REQUEST_BINDING"):
                module.validate_stage2_tikitaka_handoff(root, contract)

    def test_tikitaka_handoff_artifacts_must_share_source_fingerprint(self):
        module = load_source_module_no_bytecode("stage2_handoff_fingerprint_mismatch", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            source_lock = json.loads(
                (root / "10_analysis" / "source_identity_lock.json").read_text(encoding="utf-8")
            )
            expected_sha = source_lock["sha256"]
            for relative in (
                "20_script/report1_handoff.json",
                "20_script/script_handoff_gate.json",
                "20_script/timeline_design.json",
            ):
                path = root / relative
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["source_fingerprint_sha256"] = expected_sha
                write_json(path, payload)
            report1_path = root / "20_script" / "report1_handoff.json"
            report1 = json.loads(report1_path.read_text(encoding="utf-8"))
            report1["source_fingerprint_sha256"] = "0" * 64
            write_json(report1_path, report1)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_HANDOFF_FINGERPRINT"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_real_ffprobe_rejects_text_disguised_as_source_mp4(self):
        module = load_source_module_no_bytecode("stage2_real_ffprobe_text_source", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            source = root / "00_source" / "source.mp4"
            write(source, "fixture-source-media")
            fake_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            for relative in (
                "10_analysis/source_identity_lock.json",
                "00_source/source_manifest.json",
            ):
                path = root / relative
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["sha256"] = fake_sha
                write_json(path, payload)
            for relative in (
                "10_analysis/source_evidence.json",
                "10_analysis/crosscheck_report.json",
            ):
                path = root / relative
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["source_fingerprint_sha256"] = fake_sha
                write_json(path, payload)
            for relative in (
                "20_script/report1_handoff.json",
                "20_script/script_handoff_gate.json",
                "20_script/timeline_design.json",
            ):
                path = root / relative
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["source_fingerprint_sha256"] = fake_sha
                write_json(path, payload)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_MEDIA_FFPROBE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_block_role_map_requires_caption_type_to_match_timeline(self):
        module = load_source_module_no_bytecode("stage2_role_caption_mismatch", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "block_role_map.json"
            role_map = json.loads(path.read_text(encoding="utf-8"))
            role_map["roles"][0].pop("caption_type")
            write_json(path, role_map)

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_block_role_map_rejects_duplicate_edit_ids(self):
        module = load_source_module_no_bytecode("stage2_duplicate_role_ids", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "block_role_map.json"
            role_map = json.loads(path.read_text(encoding="utf-8"))
            role_map["roles"].append(dict(role_map["roles"][0]))
            write_json(path, role_map)

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_edit_block_sequence_must_match_timeline_order(self):
        module = load_source_module_no_bytecode("stage2_sequence_semantics", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "block_map.json"
            block_map = json.loads(path.read_text(encoding="utf-8"))
            block_map["edit_block_sequence"] = ["E2", "E1"]
            write_json(path, block_map)

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_block_provenance_must_match_timeline(self):
        module = load_source_module_no_bytecode("stage2_block_provenance", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "block_map.json"
            block_map = json.loads(path.read_text(encoding="utf-8"))
            block_map["blocks"][0]["source_block_id"] = "WRONG"
            write_json(path, block_map)

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_voice_switch_semantics_must_match_timeline_audio_policy(self):
        module = load_source_module_no_bytecode("stage2_voice_semantics", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "block_voice_switch_map.json"
            voice_map = json.loads(path.read_text(encoding="utf-8"))
            voice_map["switches"][0]["source_audio"] = "on"
            voice_map["switches"][0]["tts"] = "off"
            write_json(path, voice_map)

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_source_evidence_requires_real_analysis_sections(self):
        module = load_source_module_no_bytecode("stage2_evidence_sections", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "10_analysis" / "source_evidence.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            evidence["stt"] = {}
            write_json(path, evidence)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_EVIDENCE_REQUIRED"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_crosscheck_requires_completed_comparison(self):
        module = load_source_module_no_bytecode("stage2_crosscheck_semantics", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "10_analysis" / "crosscheck_report.json"
            crosscheck = json.loads(path.read_text(encoding="utf-8"))
            crosscheck["hint_vs_evidence_compared"] = False
            write_json(path, crosscheck)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_EVIDENCE_REQUIRED"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_speaker_quote_requires_matching_verified_stt_range(self):
        module = load_source_module_no_bytecode("stage2_quote_evidence_link", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "10_analysis" / "source_evidence.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            evidence["stt"]["verified_ranges"] = []
            write_json(path, evidence)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_QUOTE_EVIDENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_source_evidence_requires_video_probe_fields(self):
        module = load_source_module_no_bytecode("stage2_missing_probe_evidence", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "10_analysis" / "source_evidence.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            evidence.pop("ffprobe_status")
            evidence.pop("has_video_stream")
            evidence.pop("probed_duration_sec")
            write_json(path, evidence)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_EVIDENCE_PROBE_REQUIRED"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_status_only_source_manifest_is_rejected(self):
        module = load_source_module_no_bytecode("stage2_status_only_manifest", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            write_json(root / "00_source" / "source_manifest.json", {"status": "PASS"})

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_IDENTITY_LOCK"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_contract_flags_cannot_replace_report1_file_approval(self):
        module = load_source_module_no_bytecode("stage2_report1_contract_bypass", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "report1_handoff.json"
            report1 = json.loads(path.read_text(encoding="utf-8"))
            report1.pop("report1_approved")
            report1.pop("voice_audio_route_decided")
            write_json(path, report1)

            with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_APPROVAL_TTS_DECISION"):
                module.validate_stage2_tikitaka_handoff(
                    root,
                    {"report1_approved": True, "voice_audio_route_decided": True},
                )

    def test_broken_block_role_map_json_is_rejected(self):
        module = load_source_module_no_bytecode("stage2_broken_role_map", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            write(root / "20_script" / "block_role_map.json", "{broken")

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_timeline_and_block_map_edit_ids_must_match(self):
        module = load_source_module_no_bytecode("stage2_map_id_mismatch", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "block_map.json"
            block_map = json.loads(path.read_text(encoding="utf-8"))
            block_map["edit_block_sequence"] = ["WRONG_1", "WRONG_2"]
            for index, block in enumerate(block_map["blocks"], start=1):
                block["edit_id"] = f"WRONG_{index}"
            write_json(path, block_map)

            with self.assertRaisesRegex(module.GateFail, "WAIT_HANDOFF_MAP_COHERENCE"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_valid_tikitaka_v2_handoff_passes_standalone_validator(self):
        module = load_source_module_no_bytecode("stage2_handoff_valid", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)

            result = module.validate_stage2_tikitaka_handoff(root)

            self.assertEqual(result["stage2_tikitaka_handoff_status"], "PASS")
            self.assertEqual(result["stage2_tikitaka_source_of_truth"], "20_script/timeline_design.json")

    def test_production_completion_requires_integrated_blueprint(self):
        module = load_source_module_no_bytecode("stage2_production_blueprint_required", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            with self.assertRaisesRegex(module.GateFail, "FAIL_DESIGN_BLUEPRINT_MISSING"):
                module.validate_stage2_tikitaka_handoff(root, require_production_blueprint=True)

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

    def test_v3_missing_expanded_timeline_field_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_v3_field_missing", STAGE2_VALIDATOR)
        required_fields = [
            "source_ref",
            "source_order",
            "timeline_order",
            "assembly_role",
            "visible_text_role",
            "audio_role",
            "duration_basis",
            "duration_status",
            "visual_strategy",
        ]
        for field in required_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                create_valid_tikitaka_v2_package(root)
                path = root / "20_script" / "timeline_design.json"
                timeline = json.loads(path.read_text(encoding="utf-8"))
                del timeline["segments"][0][field]
                write_json(path, timeline)

                with self.assertRaisesRegex(module.GateFail, "WAIT_TIMELINE_DESIGN_REPAIR"):
                    module.validate_stage2_tikitaka_handoff(root)

    def test_v3_duplicate_timeline_order_without_parallel_group_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_duplicate_order", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "timeline_design.json"
            timeline = json.loads(path.read_text(encoding="utf-8"))
            timeline["segments"][1]["timeline_order"] = timeline["segments"][0]["timeline_order"]
            write_json(path, timeline)

            with self.assertRaisesRegex(module.GateFail, "duplicate timeline_order"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_v3_duplicate_timeline_order_with_parallel_group_passes_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_parallel_order", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "timeline_design.json"
            timeline = json.loads(path.read_text(encoding="utf-8"))
            timeline["segments"][0]["parallel_group_id"] = "PG1"
            timeline["segments"][1]["parallel_group_id"] = "PG1"
            timeline["segments"][1]["timeline_order"] = timeline["segments"][0]["timeline_order"]
            write_json(path, timeline)

            result = module.validate_stage2_tikitaka_handoff(root)

            self.assertEqual(result["stage2_tikitaka_handoff_status"], "PASS")

    def test_v3_unsupported_duration_status_blocks_stage2(self):
        module = load_source_module_no_bytecode("stage2_handoff_duration_status", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "timeline_design.json"
            timeline = json.loads(path.read_text(encoding="utf-8"))
            timeline["segments"][0]["duration_status"] = "MADE_UP"
            write_json(path, timeline)

            with self.assertRaisesRegex(module.GateFail, "unsupported duration_status"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_v3_audio_role_narration_requires_tts_timing_gate_even_when_caption_is_tts_caption(self):
        module = load_source_module_no_bytecode("stage2_handoff_audio_role_tts_timing", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "timeline_design.json"
            timeline = json.loads(path.read_text(encoding="utf-8"))
            timeline["segments"][0]["caption_type"] = "tts_caption"
            timeline["segments"][0]["audio_role"] = "audio.narration_tts"
            write_json(path, timeline)
            role_path = root / "20_script" / "block_role_map.json"
            role_map = json.loads(role_path.read_text(encoding="utf-8"))
            role_map["roles"][0]["caption_type"] = "tts_caption"
            write_json(role_path, role_map)
            (root / "20_script" / "tts_duration_probe.json").unlink()

            with self.assertRaisesRegex(module.GateFail, "WAIT_TTS_TIMING_RELOCK"):
                module.validate_stage2_tikitaka_handoff(root)

    def test_v3_tts_caption_audio_role_none_does_not_require_tts_audio_files(self):
        module = load_source_module_no_bytecode("stage2_handoff_tts_caption_only", STAGE2_VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_valid_tikitaka_v2_package(root)
            path = root / "20_script" / "timeline_design.json"
            timeline = json.loads(path.read_text(encoding="utf-8"))
            timeline["segments"] = [
                {
                    "edit_id": "E1",
                    "source_ref": "S1",
                    "source_order": 1,
                    "timeline_order": 1,
                    "assembly_role": "reaction_caption",
                    "time_start": "00:00",
                    "time_end": "00:03",
                    "track": "T3",
                    "caption_type": "tts_caption",
                    "visible_text_role": "tts_caption",
                    "audio_role": "none",
                    "duration_basis": "fixed_design_duration",
                    "duration_status": "FIXED_DESIGN_LOCKED",
                    "audio_policy": "tts_caption_only",
                    "visual_strategy": "source_visual_hold",
                }
            ]
            write_json(path, timeline)
            write_json(
                root / "20_script" / "block_map.json",
                {
                    "edit_block_sequence": ["E1"],
                    "blocks": [
                        {
                            "edit_id": "E1",
                            "source_block_id": "S1",
                            "original_order": 1,
                            "urakkai_order": 1,
                        }
                    ],
                },
            )
            write_json(
                root / "20_script" / "block_role_map.json",
                {"roles": [{"edit_id": "E1", "caption_type": "tts_caption"}]},
            )
            write_json(
                root / "20_script" / "block_voice_switch_map.json",
                {"switches": [{"edit_id": "E1", "source_audio": "off", "tts": "off"}]},
            )
            for relative in [
                "20_script/tts_copy_text.txt",
                "20_script/tts_duration_probe.json",
                "20_script/tts_timing_reconciliation_gate.json",
            ]:
                (root / relative).unlink()

            result = module.validate_stage2_tikitaka_handoff(root)

            self.assertEqual(result["stage2_tikitaka_handoff_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
