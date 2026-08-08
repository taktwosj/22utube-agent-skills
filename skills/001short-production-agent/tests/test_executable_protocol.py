import copy
import hashlib
import importlib.util
import json
import subprocess
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_final_evidence(report: dict, root: Path) -> None:
    source = root / "source.mp4"
    vmake = root / "vmake-final.mp4"
    for path, color in ((source, "red"), (vmake, "blue")):
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=16x16:d=0.2", "-r", "10", "-pix_fmt", "yuv420p", str(path)],
            check=True,
        )
    screen = root / "capcut-screen.png"
    screen.write_bytes(b"screen-evidence")
    draft = root / "draft_content.json"
    draft.write_text('{"duration":200000}', encoding="utf-8")
    def duration(path: Path) -> float:
        return float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            check=True, capture_output=True, text=True,
        ).stdout.strip())
    source_duration = duration(source)
    vmake_duration = duration(vmake)
    report.update({
        "source_file_evidence": {
            "local_path": str(source), "sha256": sha256(source), "duration": source_duration,
            "approved_source_time_ranges": [[0, round(source_duration * 1_000_000)]],
        },
        "vmake_final_download": {
            "downloaded_file_path": str(vmake), "sha256": sha256(vmake),
            "size_bytes": vmake.stat().st_size, "duration": vmake_duration,
            "is_actual_vmake_final_download": True,
        },
        "capcut_visual_confirmation": {
            "actual_project_name": report["capcut_project_name"],
            "screen_confirmation_status": "PASS",
            "screen_evidence_path": str(screen),
            "screen_evidence_sha256": sha256(screen),
            "draft_readback": {"local_path": str(draft), "sha256": sha256(draft)},
            "final_project_hash": sha256(draft),
        },
        "completion_claim": "CAPCUT_PROJECT_COMPLETE",
    })


class ExecutableProtocolContractTest(unittest.TestCase):
    def test_skill_and_workflow_mandate_executable_protocol(self):
        skill_text = (SKILL / "references" / "production-orchestrator.md").read_text(encoding="utf-8")
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))
        tools = json.loads((SKILL / "tools.json").read_text(encoding="utf-8"))
        self.assertIn("## Intake and root", skill_text)
        self.assertIn("scripts/validate_source_intake.py", skill_text)
        self.assertIn("STOP_PROTOCOL_CONFLICT", skill_text)
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
            protocol["completion_report"]["cloud_sync_row_required_fields"],
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
                "source_file_evidence",
                "vmake_final_download",
                "capcut_visual_confirmation",
                "completion_claim",
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

    def test_urakkai_rejects_fake_split_and_a10_range_mismatch(self):
        module = load_validator()
        protocol = module.load_protocol(PROTOCOL)
        valid = json.loads((SKILL / "tests" / "fixtures" / "urakkai_reordered.pass.json").read_text(encoding="utf-8"))

        mismatched = json.loads(json.dumps(valid))
        mismatched["timeline"][0]["placements"][1]["source_range_us"] = [0, 1_000_000]
        self.assertIn(
            "URAKKAI_AUDIO_VIDEO_MAPPING_MISMATCH",
            module.validate_production_plan(mismatched, protocol),
        )

        fake = json.loads(json.dumps(valid))
        fake["order_signature"] = ["1A", "1B", "1C"]
        for index, row in enumerate(fake["timeline"]):
            row["segment_key"] = fake["order_signature"][index]
            source_range = [index * 1_000_000, (index + 1) * 1_000_000]
            row["placements"][0]["source_range_us"] = source_range
            row["placements"][1]["source_range_us"] = source_range
        self.assertIn("URAKKAI_FAKE_SPLIT", module.validate_production_plan(fake, protocol))

    def test_urakkai_tts_only_requires_muted_video_empty_a10_and_a9(self):
        module = load_validator()
        protocol = module.load_protocol(PROTOCOL)
        fixture = SKILL / "tests" / "fixtures" / "urakkai_tts_only.pass.json"
        valid = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(module.validate_production_plan(valid, protocol), [])

        a10_present = json.loads(json.dumps(valid))
        a10_present["timeline"][0]["placements"].append({
            "anchor": "A10", "operation": "clone_template_segment", "asset_key": "source_vocals",
            "source_range_us": [2_000_000, 3_000_000], "target_range_us": [0, 1_000_000], "volume": 1,
        })
        self.assertIn("URAKKAI_TTS_ONLY_A10_FORBIDDEN", module.validate_production_plan(a10_present, protocol))

        video_audible = json.loads(json.dumps(valid))
        video_audible["timeline"][0]["placements"][0]["volume"] = 1
        self.assertIn("URAKKAI_TTS_ONLY_VIDEO_NOT_MUTED", module.validate_production_plan(video_audible, protocol))

        no_tts = json.loads(json.dumps(valid))
        for row in no_tts["timeline"]:
            row["placements"] = [placement for placement in row["placements"] if placement["anchor"] != "A9"]
        self.assertIn("URAKKAI_TTS_ONLY_A9_REQUIRED", module.validate_production_plan(no_tts, protocol))

    def test_protocol_declares_final_shorts_hard_gates(self):
        module = load_validator()
        protocol = module.load_protocol(PROTOCOL)
        urakkai = protocol["production_modes"]["URAKKAI"]
        clean_only = protocol["production_modes"]["SOURCE_ORDER_UNCHANGED_CLEAN_ONLY"]
        self.assertIs(urakkai.get("fake_split_forbidden"), True)
        self.assertIs(urakkai.get("approved_final_order_required"), True)
        self.assertEqual(urakkai.get("allowed_audio_policies"), ["A10_RETAINED_SYNC", "TTS_ONLY_MUTE_SOURCE"])
        self.assertIs(clean_only.get("explicit_exception_to_multi_cut_gate"), True)
        self.assertEqual(clean_only.get("video_duration"), "FULL_LENGTH")
        self.assertEqual(clean_only.get("original_audio_duration"), "FULL_LENGTH")
        self.assertEqual(clean_only.get("source_order_change"), "FORBIDDEN")
        for field in ("source_file_evidence", "vmake_final_download", "capcut_visual_confirmation"):
            self.assertIn(field, protocol["completion_report"]["required_fields"])

    def test_vmake_direct_insert_and_local_runtime_urakkai_review_contract(self):
        module = load_validator()
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        skill_text = (SKILL / "references" / "production-orchestrator.md").read_text(encoding="utf-8")
        workflow = json.loads((SKILL / "workflow.json").read_text(encoding="utf-8"))

        invariants = protocol["invariants"]
        self.assertIs(invariants.get("vmake_full_download_required"), True)
        self.assertIs(invariants.get("vmake_direct_insert_required"), True)
        self.assertEqual(
            invariants.get("vmake_direct_insert_asset"),
            "40_assets_used/clean_source.mp4",
        )
        self.assertEqual(invariants.get("vmake_direct_insert_asset_key"), "clean_video")
        self.assertIs(invariants.get("vmake_nonblocking_source_provisional_allowed"), True)
        self.assertEqual(invariants.get("source_provisional_video_asset_key"), "source_video")

        review = protocol["urakkai_review_loop"]
        self.assertEqual(review["enabled_for"], ["URAKKAI"])
        self.assertEqual(review["preferred_provider"], "claude_cli")
        self.assertEqual(review["preferred_model"], "Claude Opus 5")
        self.assertEqual(review["effort"], "low")
        self.assertEqual(review["review_loop_count"], 1)
        self.assertEqual(review["reviews_per_loop"], 1)
        self.assertEqual(review["review_runner"], "current_local_runtime")
        self.assertEqual(review["approval_authority"], "user")
        self.assertEqual(review["fallback_provider"], "codex_cli")
        self.assertEqual(review["fallback_model"], "gpt-5.6-sol")
        self.assertEqual(review["fallback_effort"], "low")

        stage04 = next(stage for stage in workflow["production_stages"] if stage["id"] == "04")
        self.assertEqual(stage04["pass"], "WAIT_USER_URAKKAI_APPROVAL")
        self.assertEqual(workflow["blueprint_frontend"]["external_review"]["loop_count"], 1)
        self.assertEqual(workflow["external_actions"]["llm_calls"], "URAKKAI_STAGE_04_CLAUDE_CLI_WITH_CODEX_FALLBACK")
        self.assertIn("VMake Direct-Insert Contract", skill_text)
        self.assertIn("Urakkai Editorial Authority", skill_text)

        broken = json.loads(json.dumps(protocol, ensure_ascii=False))
        broken["invariants"]["vmake_direct_insert_required"] = False
        self.assertIn(
            "PROTOCOL_INVARIANT_FALSE:vmake_direct_insert_required",
            module.validate_protocol_document(broken),
        )
        broken = json.loads(json.dumps(protocol, ensure_ascii=False))
        broken["urakkai_review_loop"]["fallback_provider"] = "none"
        self.assertIn(
            "PROTOCOL_URAKKAI_REVIEW_GATE:fallback_provider",
            module.validate_protocol_document(broken),
        )

        invalid_plan = json.loads(
            (SKILL / "tests" / "fixtures" / "urakkai_reordered.pass.json").read_text(encoding="utf-8")
        )
        invalid_plan["timeline"][0]["placements"][0]["asset_key"] = "source_video"
        self.assertIn(
            "VMAKE_DIRECT_INSERT_ASSET_INVALID:source_video",
            module.validate_production_plan(invalid_plan, protocol),
        )
        provisional_plan = json.loads(
            (SKILL / "tests" / "fixtures" / "urakkai_reordered.pass.json").read_text(encoding="utf-8")
        )
        provisional_plan["visual_asset_mode"] = "SOURCE_VIDEO_PROVISIONAL"
        for row in provisional_plan["timeline"]:
            for placement in row["placements"]:
                if placement["anchor"] == "VIDEO":
                    placement["asset_key"] = "source_video"
        self.assertEqual(module.validate_production_plan(provisional_plan, protocol), [])
        provisional_plan["timeline"][0]["placements"][0]["asset_key"] = "clean_video"
        self.assertIn(
            "SOURCE_PROVISIONAL_ASSET_INVALID:clean_video",
            module.validate_production_plan(provisional_plan, protocol),
        )

    def test_urakkai_final_duration_is_not_forced_to_source_duration(self):
        module = load_validator()
        protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        invariants = protocol["invariants"]
        skill_text = (SKILL / "references" / "production-orchestrator.md").read_text(encoding="utf-8")

        self.assertIs(invariants.get("urakkai_final_duration_independent_from_source"), True)
        self.assertIs(invariants.get("clean_visual_duration_matches_source_before_edit"), True)
        self.assertIs(invariants.get("clean_only_full_source_duration_required"), True)
        self.assertIn("final duration is allowed to differ", skill_text)
        # The retired root-router assertion carried mojibake text; semantic coverage now lives above.
        _retired_legacy_assertion = """
        self.assertIn(
            "원본 전체 길이와 최종 프로젝트 전체 길이를 같게 강제하지 않는다",
            skill_text,
        )
            """

        broken = copy.deepcopy(protocol)
        broken["invariants"]["urakkai_final_duration_independent_from_source"] = False
        self.assertIn(
            "PROTOCOL_INVARIANT_FALSE:urakkai_final_duration_independent_from_source",
            module.validate_protocol_document(broken),
        )

    def test_completion_report_rejects_missing_final_shorts_evidence(self):
        module = load_validator()
        protocol = module.load_protocol(PROTOCOL)
        report = {
            "episode_id": "SH_TEST",
            "capcut_project_name": "SH_TEST_Hermes",
            "production_mode": "URAKKAI",
            "T1": "제목1",
            "T2": "제목2",
            "validation_status": "PASS",
            "capcut_cloud_destination": "User3160027826975의 공간/MAC",
            "capcut_cloud_row": {"name": "SH_TEST_Hermes", "size": "9MB", "duration": "00:09", "type": "프로젝트", "modified_time": "오늘"},
            "upload_title": "업로드 제목",
            "upload_description": "업로드 설명",
            "sources": [{"channel": "원본", "url": "https://example.com"}],
            "public_upload_status": "WAIT_APPROVAL",
        }
        errors = module.validate_completion_report(report, protocol)
        self.assertIn("SOURCE_FILE_EVIDENCE_MISSING", errors)
        self.assertIn("VMAKE_FINAL_DOWNLOAD_EVIDENCE_MISSING", errors)
        self.assertIn("CAPCUT_VISUAL_CONFIRMATION_MISSING", errors)

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
        for expected in (
            "UPLOAD_METADATA_MISSING:upload_title",
            "UPLOAD_METADATA_MISSING:upload_description",
            "UPLOAD_METADATA_MISSING:sources",
        ):
            self.assertIn(expected, errors)

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
        with tempfile.TemporaryDirectory() as td:
            add_final_evidence(report, Path(td))
            self.assertEqual(module.validate_completion_report(report, protocol), [])
            local_only = json.loads(json.dumps(report, ensure_ascii=False))
            local_only.pop("capcut_cloud_destination")
            local_only.pop("capcut_cloud_row")
            local_only["capcut_cloud_sync_status"] = "NOT_REQUESTED"
            self.assertEqual(module.validate_completion_report(local_only, protocol), [])
            substituted = json.loads(json.dumps(report, ensure_ascii=False))
            source_meta = substituted["source_file_evidence"]
            source_path = Path(source_meta["local_path"])
            substituted["vmake_final_download"] = {
                "downloaded_file_path": str(source_path),
                "sha256": source_meta["sha256"],
                "size_bytes": source_path.stat().st_size,
                "duration": source_meta["duration"],
                "is_actual_vmake_final_download": True,
            }
            self.assertIn(
                "VMAKE_FINAL_DOWNLOAD_EVIDENCE_INVALID",
                module.validate_completion_report(substituted, protocol),
            )
            render_claim = json.loads(json.dumps(report, ensure_ascii=False))
            render_claim["completion_claim"] = "UPLOAD_READY"
            self.assertIn(
                "RENDER_EVIDENCE_MISSING",
                module.validate_completion_report(render_claim, protocol),
            )
            incomplete_cloud_row = json.loads(json.dumps(report, ensure_ascii=False))
            incomplete_cloud_row["capcut_cloud_sync_status"] = "SYNCED"
            incomplete_cloud_row["capcut_cloud_sync_requested"] = True
            incomplete_cloud_row["capcut_cloud_destination"] = "home"
            del incomplete_cloud_row["capcut_cloud_row"]["size"]
            self.assertIn(
                "CAPCUT_CLOUD_ROW_MISSING",
                module.validate_completion_report(incomplete_cloud_row, protocol),
            )
            synced_home = json.loads(json.dumps(report, ensure_ascii=False))
            synced_home.update({
                "capcut_cloud_sync_status": "SYNCED",
                "capcut_cloud_sync_requested": True,
                "capcut_cloud_destination": "home",
            })
            self.assertEqual(module.validate_completion_report(synced_home, protocol), [])
            del synced_home["capcut_cloud_destination"]
            self.assertIn(
                "CAPCUT_CLOUD_DESTINATION_MISSING",
                module.validate_completion_report(synced_home, protocol),
            )
            report["public_upload_status"] = "UPLOADED"
            report["public_upload_approval"] = False
            self.assertIn(
                "PUBLIC_UPLOAD_NOT_APPROVED",
                module.validate_completion_report(report, protocol),
            )


if __name__ == "__main__":
    unittest.main()
