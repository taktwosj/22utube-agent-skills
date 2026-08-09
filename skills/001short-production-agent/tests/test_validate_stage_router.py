import io
import json
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


class ValidateStageRouterTest(unittest.TestCase):
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
            audio.write_text("{}", encoding="utf-8"); caption.write_text("{}", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
