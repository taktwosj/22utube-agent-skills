import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_stage
from common import sha256_file


class ValidateStageRouterTest(unittest.TestCase):
    def test_stage03_and_stage04_accept_unchanged_stage02_locks_without_advancing(self):
        for stage, status in (
            ("03", "ORIGINAL_BLUEPRINT_READY"),
            ("04", "FIRST_RECOMMENDATION_READY"),
        ):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as td:
                episode = Path(td) / "episode"
                workflow = episode / "90_workflow"
                script = episode / "20_script"
                workflow.mkdir(parents=True)
                script.mkdir()
                blueprint = script / "original-blueprint.md"
                grid = script / "original-capcut-grid.md"
                blueprint.write_text("locked blueprint", encoding="utf-8")
                grid.write_text("locked grid", encoding="utf-8")
                payload = {
                    "episode_id": "EP", "current_stage": stage, "status": status,
                    "original_blueprint_path": str(blueprint.resolve()),
                    "original_blueprint_sha256": sha256_file(blueprint),
                    "original_capcut_grid_path": str(grid.resolve()),
                    "original_capcut_grid_sha256": sha256_file(grid),
                }
                state = workflow / "state.json"
                state.write_text(json.dumps(payload), encoding="utf-8")
                stdout = io.StringIO()
                with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state)]), redirect_stdout(stdout):
                    self.assertEqual(validate_stage.main(), 0)
                self.assertIn('"stage02_input_locks": "PASS"', stdout.getvalue())
                self.assertEqual(json.loads(state.read_text(encoding="utf-8")), payload)

    def test_stage08_and_stage09_reject_v1_structure_snapshot_before_dispatch(self):
        for stage, status in (
            ("08", "AUDIO_CAPTION_VALIDATED"),
            ("09", "CAPCUT_STATIC_VALIDATED"),
        ):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as td:
                episode = Path(td) / "episode"
                workflow = episode / "90_workflow"
                workflow.mkdir(parents=True)
                state = workflow / "state.json"
                state.write_text(json.dumps({
                    "episode_id": "EP", "current_stage": stage, "status": status,
                    "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                }), encoding="utf-8")
                snapshot = episode / "50_capcut_project" / "structure_snapshot.json"
                snapshot.parent.mkdir()
                snapshot.write_text(json.dumps({
                    "schema_version": "001short-structure-snapshot-v1",
                }), encoding="utf-8")
                stdout = io.StringIO()
                with (
                    patch.object(sys, "argv", [
                        "validate_stage.py", "--state", str(state), "--snapshot", str(snapshot),
                    ]),
                    patch.object(validate_stage, "_receipt_error", return_value=None),
                    patch.object(validate_stage, "_run", return_value={"status": "PASS", "errors": [], "evidence": {}}) as run,
                    redirect_stdout(stdout),
                ):
                    self.assertEqual(validate_stage.main(), 1)
                self.assertIn("STRUCTURE_SNAPSHOT_MIGRATION_REQUIRED", stdout.getvalue())
                run.assert_not_called()

    def test_stage09_discovers_canonical_v1_structure_snapshot_without_router_args(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            workflow.mkdir(parents=True)
            state = workflow / "state.json"
            state.write_text(json.dumps({
                "episode_id": "EP", "current_stage": "09",
                "status": "CAPCUT_STATIC_VALIDATED",
            }), encoding="utf-8")
            snapshot = episode / "50_capcut_project" / "structure_snapshot.json"
            snapshot.parent.mkdir()
            snapshot.write_text(json.dumps({
                "schema_version": "001short-structure-snapshot-v1",
            }), encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", ["validate_stage.py", "--state", str(state)]),
                patch.object(validate_stage, "_run", return_value={"status": "PASS", "errors": [], "evidence": {}}) as run,
                redirect_stdout(stdout),
            ):
                self.assertEqual(validate_stage.main(), 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["errors"][0]["code"], "STRUCTURE_SNAPSHOT_MIGRATION_REQUIRED")
            run.assert_not_called()

    def test_stage09_snapshot_precedence_is_explicit_then_state_then_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            workflow.mkdir(parents=True)
            canonical = episode / "50_capcut_project" / "structure_snapshot.json"
            canonical.parent.mkdir()
            canonical.write_text(json.dumps({
                "schema_version": "001short-structure-snapshot-v1",
            }), encoding="utf-8")
            state_snapshot = workflow / "state-snapshot.json"
            state_snapshot.write_text(json.dumps({
                "schema_version": "001short-structure-snapshot-v2",
            }), encoding="utf-8")
            explicit_snapshot = workflow / "explicit-snapshot.json"
            explicit_snapshot.write_text(json.dumps({
                "schema_version": "001short-structure-snapshot-v2",
            }), encoding="utf-8")
            state = workflow / "state.json"

            cases = (
                ("state", "90_workflow/state-snapshot.json", None),
                ("explicit", "50_capcut_project/structure_snapshot.json", explicit_snapshot),
            )
            for name, state_declared, explicit in cases:
                with self.subTest(name=name):
                    state.write_text(json.dumps({
                        "episode_id": "EP", "current_stage": "09",
                        "status": "CAPCUT_STATIC_VALIDATED",
                        "structure_snapshot_path": state_declared,
                    }), encoding="utf-8")
                    argv = ["validate_stage.py", "--state", str(state)]
                    if explicit is not None:
                        argv.extend(["--snapshot", str(explicit)])
                    stdout = io.StringIO()
                    with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                        self.assertEqual(validate_stage.main(), 3)
                    payload = json.loads(stdout.getvalue())
                    self.assertEqual(payload["errors"][0]["code"], "MANUAL_FINALIZATION_REQUIRED")

    def test_stage03_and_stage04_fail_closed_when_stage02_artifact_changes_after_lock(self):
        for stage, status, mutated_name in (
            ("03", "ORIGINAL_BLUEPRINT_READY", "original-blueprint.md"),
            ("04", "FIRST_RECOMMENDATION_READY", "original-capcut-grid.md"),
        ):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as td:
                episode = Path(td) / "episode"
                workflow = episode / "90_workflow"
                script = episode / "20_script"
                workflow.mkdir(parents=True)
                script.mkdir()
                blueprint = script / "original-blueprint.md"
                grid = script / "original-capcut-grid.md"
                blueprint.write_text("locked blueprint", encoding="utf-8")
                grid.write_text("locked grid", encoding="utf-8")
                state = workflow / "state.json"
                state.write_text(json.dumps({
                    "episode_id": "EP", "current_stage": stage, "status": status,
                    "original_blueprint_path": str(blueprint.resolve()),
                    "original_blueprint_sha256": sha256_file(blueprint),
                    "original_capcut_grid_path": str(grid.resolve()),
                    "original_capcut_grid_sha256": sha256_file(grid),
                }), encoding="utf-8")
                (script / mutated_name).write_text("mutated after lock", encoding="utf-8")
                stdout = io.StringIO()
                with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state)]), redirect_stdout(stdout):
                    self.assertEqual(validate_stage.main(), 1)
                self.assertIn("STAGE02_LOCK_SHA_MISMATCH", stdout.getvalue())

    def test_stage02_rejects_invalid_original_grid(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            script = episode / "20_script"
            workflow.mkdir(parents=True)
            script.mkdir()
            state = workflow / "state.json"
            state.write_text(json.dumps({
                "episode_id": "EP", "current_stage": "02", "status": "SOURCE_OCR_VERIFIED",
            }), encoding="utf-8")
            (script / "original-blueprint.md").write_text(
                "| 원본 구조 | source range | 상황·행동 | 주도 화자 | 전달 방식 | 서사 기능 | 구조 분리 근거 |\n"
                "|---|---|---|---|---|---|---|\n"
                "| B01 | 0~1 | 행동 | 화자 | 외국인 발화 | 도입 | 시작 |\n",
                encoding="utf-8",
            )
            (script / "original-capcut-grid.md").write_text(
                "| 레이어 \\ 원본 시간 | B01 0.0–1.0 |\n|---|---|\n| T1 | 제목 |\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state), "--advance"]), redirect_stdout(stdout):
                self.assertEqual(validate_stage.main(), 1)
            self.assertIn("TABLE_ROW_MISSING", stdout.getvalue())
            self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["current_stage"], "02")

    def test_stage02_requires_blueprint_and_grid_bxx_sets_to_match(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            script = episode / "20_script"
            workflow.mkdir(parents=True)
            script.mkdir()
            state = workflow / "state.json"
            state.write_text(json.dumps({
                "episode_id": "EP", "current_stage": "02", "status": "SOURCE_OCR_VERIFIED",
            }), encoding="utf-8")
            (script / "original-blueprint.md").write_text(
                "| 원본 구조 | source range | 상황·행동 | 주도 화자 | 전달 방식 | 서사 기능 | 구조 분리 근거 |\n"
                "|---|---|---|---|---|---|---|\n"
                "| B01 | 0~1 | 행동 | 화자 | 외국인 발화 | 도입 | 시작 |\n",
                encoding="utf-8",
            )
            (script / "original-capcut-grid.md").write_text(
                (SKILL / "tests" / "fixtures" / "original_grid_8.pass.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state), "--advance"]), redirect_stdout(stdout):
                self.assertEqual(validate_stage.main(), 1)
            self.assertIn("ORIGINAL_BEAT_GRID_BXX_MISMATCH", stdout.getvalue())
            self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["current_stage"], "02")

    def test_stage02_advance_validates_each_original_blueprint_beat(self):
        header = (
            "| 원본 구조 | source range | 상황·행동 | 주도 화자 | 전달 방식 | 서사 기능 | 구조 분리 근거 |\n"
            "|---|---|---|---|---|---|---|\n"
        )
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            script = episode / "20_script"
            workflow.mkdir(parents=True)
            script.mkdir()
            state_path = workflow / "state.json"
            state_payload = {
                "episode_id": "EP", "current_stage": "02", "status": "SOURCE_OCR_VERIFIED",
            }
            state_path.write_text(json.dumps(state_payload), encoding="utf-8")
            blueprint = script / "original-blueprint.md"
            blueprint.write_text(
                header
                + "| B01 | 0.0~1.0 | 인물이 문을 연다 | 인물 | 외국인 발화 | 도입 | 행동 시작 |\n"
                + "| B02 | 1.0~2.0 | 상대가 답한다 | 상대 | 외국인 발화 | 응답 |  |\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state_path), "--advance"]), redirect_stdout(stdout):
                self.assertEqual(validate_stage.main(), 1)
            self.assertIn("ORIGINAL_BLUEPRINT_BEAT_FIELD_EMPTY", stdout.getvalue())
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), state_payload)

            blueprint.write_text(
                header + "| B01 | 0.0~1.0 | 인물이 문을 연다 | 인물 | 외국인 발화 | 도입 | 행동 시작 |\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state_path), "--advance"]), redirect_stdout(stdout):
                self.assertEqual(validate_stage.main(), 1)
            self.assertIn("TABLE_FILE_MISSING", stdout.getvalue())
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), state_payload)

            blueprint.write_text(
                header
                + "".join(
                    f"| B{index:02d} | {index - 1}.0~{index}.0 | 행동 {index} | 화자 {index} | 외국인 발화 | 전개 | 변화 {index} |\n"
                    for index in range(1, 9)
                ),
                encoding="utf-8",
            )
            original_grid = script / "original-capcut-grid.md"
            original_grid.write_text(
                (SKILL / "tests" / "fixtures" / "original_grid_8.pass.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state_path), "--advance"]):
                self.assertEqual(validate_stage.main(), 0)
            advanced = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual((advanced["current_stage"], advanced["status"]), ("03", "ORIGINAL_BLUEPRINT_READY"))
            self.assertEqual(
                validate_stage._state_declared_path(state_path, advanced["original_blueprint_path"]),
                blueprint.resolve(),
            )
            self.assertEqual(advanced["original_blueprint_sha256"], sha256_file(blueprint))
            self.assertEqual(
                validate_stage._state_declared_path(state_path, advanced["original_capcut_grid_path"]),
                original_grid.resolve(),
            )
            self.assertEqual(advanced["original_capcut_grid_sha256"], sha256_file(original_grid))

    def test_protocol_is_entry_state_authority(self):
        self.assertEqual(validate_stage.STAGE_ENTRY_STATUS["07"], "FINAL_DESIGN_LOCKED_OR_CLEAN_VISUAL_READY")
        self.assertEqual(validate_stage.STAGE_ENTRY_STATUS["08"], "AUDIO_CAPTION_VALIDATED_WITH_ACCEPTED_VISUAL_MODE")
        self.assertTrue(validate_stage._entry_state_matches({"status": "FINAL_DESIGN_LOCKED"}, validate_stage.STAGE_ENTRY_STATUS["07"]))
        self.assertTrue(validate_stage._entry_state_matches({"status": "CLEAN_VISUAL_READY"}, validate_stage.STAGE_ENTRY_STATUS["07"]))
        self.assertTrue(validate_stage._entry_state_matches({"status": "AUDIO_CAPTION_VALIDATED", "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL"}, validate_stage.STAGE_ENTRY_STATUS["08"]))
        self.assertTrue(validate_stage._entry_state_matches({"status": "AUDIO_CAPTION_VALIDATED", "visual_asset_mode": "USER_APPROVED_NONMATCHING_CLEAN_SOURCE"}, validate_stage.STAGE_ENTRY_STATUS["08"]))

    def test_stage07_public_advance_is_atomic_and_records_canonical_locks(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"; workflow = episode / "90_workflow"; workflow.mkdir(parents=True)
            state_path = workflow / "state.json"
            state_path.write_text(json.dumps({"episode_id": "EP", "current_stage": "07", "status": "FINAL_DESIGN_LOCKED"}), encoding="utf-8")
            audio = episode / "audio_lock.json"; caption = episode / "caption_lock.json"
            audio.write_text(json.dumps({"schema_version": "001short-audio-lock-v4"}), encoding="utf-8")
            timing = episode / "caption_timing.json"
            timing.write_text(json.dumps({"schema_version": "001short-caption-timing-evidence-v2"}), encoding="utf-8")
            caption.write_text(json.dumps({"schema_version": "001short-caption-lock-v2", "caption_timing_evidence_path": str(timing)}), encoding="utf-8")
            argv = ["validate_stage.py", "--state", str(state_path), "--audio-lock", str(audio), "--caption-lock", str(caption), "--advance"]
            with patch.object(sys, "argv", argv), patch.object(validate_stage, "_receipt_error", return_value=None), patch.object(validate_stage, "_run", return_value={"status": "PASS", "errors": [], "evidence": {}}):
                self.assertEqual(validate_stage.main(), 0)
            advanced = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual((advanced["current_stage"], advanced["status"]), ("08", "AUDIO_CAPTION_VALIDATED"))
            self.assertEqual(Path(advanced["audio_lock_path"]), audio.resolve())
            self.assertEqual(Path(advanced["caption_lock_path"]), caption.resolve())
            self.assertFalse(state_path.with_name("state.json.tmp").exists())

    def test_stage08_provisional_does_not_require_clean_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            workflow = Path(td) / "episode" / "90_workflow"; workflow.mkdir(parents=True)
            state_path = workflow / "state.json"
            state_path.write_text(json.dumps({"episode_id": "EP", "current_stage": "08", "status": "AUDIO_CAPTION_VALIDATED", "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL", "audio_lock_path": "audio.json", "audio_lock_sha256": "0" * 64, "caption_lock_path": "caption.json", "caption_lock_sha256": "0" * 64}), encoding="utf-8")
            seen = []
            def receipt(_state, _path, name):
                seen.append(name)
                return None
            argv = ["validate_stage.py", "--state", str(state_path)]
            with patch.object(sys, "argv", argv), patch.object(validate_stage, "_receipt_error", side_effect=receipt), patch.object(validate_stage, "_run", return_value={"status": "PASS", "errors": [], "evidence": {}}):
                self.assertEqual(validate_stage.main(), 0)
            self.assertEqual(seen, ["design_lock", "audio_lock", "caption_lock"])

    def test_stage09_manual_terminal_does_not_dispatch_render_or_create_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"; workflow = episode / "90_workflow"; workflow.mkdir(parents=True)
            state_path = workflow / "state.json"
            state_path.write_text(
                json.dumps({
                    "episode_id": "EP", "current_stage": "09",
                    "status": "CAPCUT_STATIC_VALIDATED",
                    "next_action": "WAIT_USER_CAPCUT_CHECK",
                }),
                encoding="utf-8",
            )
            render = episode / "60_exports" / "render.mp4"
            evidence = episode / "60_exports" / "render_validation.json"
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", [
                    "validate_stage.py", "--state", str(state_path),
                    "--render", str(render), "--evidence", str(evidence),
                ]),
                patch.object(validate_stage, "_receipt_error", return_value=None),
                patch.object(validate_stage, "_run", return_value={"status": "PASS", "errors": [], "evidence": {}}) as run,
                redirect_stdout(stdout),
            ):
                self.assertEqual(validate_stage.main(), 3)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "WAIT")
            self.assertEqual(payload["errors"][0]["code"], "MANUAL_FINALIZATION_REQUIRED")
            run.assert_not_called()
            self.assertFalse(evidence.exists())

    def test_noncanonical_state_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "state.json"; state.write_text("{}", encoding="utf-8")
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state)]):
                self.assertEqual(validate_stage.main(), 1)

    def test_state_artifact_paths_are_episode_root_relative_and_cannot_escape(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            workflow.mkdir(parents=True)
            state = workflow / "state.json"
            inside = episode / "20_script" / "receipt.json"
            inside.parent.mkdir()
            inside.write_text("{}", encoding="utf-8")
            self.assertEqual(
                validate_stage._state_declared_path(state, "20_script/receipt.json"),
                inside.resolve(),
            )
            for raw in ("../outside.json", str((Path(td) / "outside.json").resolve())):
                with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "STATE_ARTIFACT_PATH_UNSAFE"):
                    validate_stage._state_declared_path(state, raw)

    def test_stage05_advance_binds_design_and_plan_validation_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"
            workflow = episode / "90_workflow"
            workflow.mkdir(parents=True)
            state_path = workflow / "state.json"
            state_path.write_text(json.dumps({
                "episode_id": "EP", "current_stage": "05", "status": "URAKKAI_AUTO_APPROVED",
            }), encoding="utf-8")
            evidence = episode / "20_script" / "design_lock_evidence.json"
            evidence.parent.mkdir()
            evidence.write_text(json.dumps({"status": "PASS", "episode_id": "EP"}), encoding="utf-8")
            plan = evidence.with_name("production_plan.json")
            plan.write_text(json.dumps({"schema_version": "001short-production-plan-v2", "episode_id": "EP"}), encoding="utf-8")
            receipt = workflow / "production_plan_validation.json"
            argv = [
                "validate_stage.py", "--state", str(state_path),
                "--handoff", str(evidence), "--source-identity", str(evidence),
                "--timeline", str(evidence), "--design-lock-evidence", str(evidence),
                "--production-plan", str(plan), "--production-plan-receipt", str(receipt),
                "--advance",
            ]
            seen = {}
            def run(check, args):
                if check == "design_lock":
                    seen["design_lock_evidence"] = args.design_lock_evidence
                    return {"status": "PASS", "errors": [], "evidence": {}}
                return {
                    "status": "PASS", "errors": [],
                    "evidence": {"episode_id": "EP", "production_plan_path": str(plan.resolve()), "production_plan_sha256": sha256_file(plan)},
                }
            with patch.object(sys, "argv", argv), patch.object(validate_stage, "_run", side_effect=run):
                self.assertEqual(validate_stage.main(), 0)
            advanced = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(seen["design_lock_evidence"], evidence)
            self.assertEqual(validate_stage._state_declared_path(state_path, advanced["design_lock_evidence_path"]), evidence.resolve())
            self.assertEqual(advanced["design_lock_evidence_sha256"], sha256_file(evidence))
            self.assertEqual(validate_stage._state_declared_path(state_path, advanced["production_plan_path"]), plan.resolve())
            self.assertEqual(validate_stage._state_declared_path(state_path, advanced["production_plan_validation_receipt_path"]), receipt.resolve())
            self.assertEqual(advanced["production_plan_validation_receipt_sha256"], sha256_file(receipt))

    def test_stage05_missing_episode_id_is_deterministic_failure(self):
        with tempfile.TemporaryDirectory() as td:
            workflow = Path(td) / "episode" / "90_workflow"; workflow.mkdir(parents=True)
            state = workflow / "state.json"
            state.write_text(json.dumps({"current_stage": "05", "status": "URAKKAI_AUTO_APPROVED"}), encoding="utf-8")
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state)]), redirect_stdout(stdout):
                self.assertEqual(validate_stage.main(), 1)
            self.assertIn("STATE_REQUIRED_FIELD_MISSING:episode_id", stdout.getvalue())

    def test_stage07_advance_rejects_legacy_lock_versions(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"; workflow = episode / "90_workflow"; workflow.mkdir(parents=True)
            state = workflow / "state.json"; state.write_text(json.dumps({"episode_id": "EP", "current_stage": "07", "status": "FINAL_DESIGN_LOCKED"}), encoding="utf-8")
            audio = episode / "audio.json"; audio.write_text(json.dumps({"schema_version": "001short-audio-lock-v3"}), encoding="utf-8")
            caption = episode / "caption.json"; caption.write_text(json.dumps({"schema_version": "001short-caption-lock-v1"}), encoding="utf-8")
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["validate_stage.py", "--state", str(state), "--audio-lock", str(audio), "--caption-lock", str(caption), "--advance"]), patch.object(validate_stage, "_run", return_value={"status": "PASS", "errors": [], "evidence": {}}), redirect_stdout(stdout):
                self.assertEqual(validate_stage.main(), 1)
            self.assertIn("AUDIO_LOCK_MIGRATION_REQUIRED", stdout.getvalue())

    def test_state_resolver_rejects_mocked_reparse_component(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"; workflow = episode / "90_workflow"; workflow.mkdir(parents=True)
            state = workflow / "state.json"
            target = episode / "20_script" / "receipt.json"; target.parent.mkdir(); target.write_text("{}", encoding="utf-8")
            with patch("common._is_reparse_point", side_effect=lambda path: os.path.realpath(path) == os.path.realpath(target.parent)):
                with self.assertRaisesRegex(ValueError, "STATE_ARTIFACT_PATH_UNSAFE"):
                    validate_stage._state_declared_path(state, "20_script/receipt.json")

    def test_state_resolver_rejects_actual_symlink_component_when_supported(self):
        with tempfile.TemporaryDirectory() as td:
            episode = Path(td) / "episode"; workflow = episode / "90_workflow"; workflow.mkdir(parents=True)
            state = workflow / "state.json"
            real = episode / "real"; real.mkdir(); (real / "receipt.json").write_text("{}", encoding="utf-8")
            alias = episode / "alias"
            try:
                alias.symlink_to(real, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "STATE_ARTIFACT_PATH_UNSAFE"):
                validate_stage._state_declared_path(state, "alias/receipt.json")


if __name__ == "__main__":
    unittest.main()
