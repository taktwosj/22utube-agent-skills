from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL / "scripts" / "validate_stage.py"


class ValidateStageRouterTests(unittest.TestCase):
    def write_audio_caption(self, root: Path) -> tuple[Path, Path]:
        audio = root / "source.wav"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=0.4",
                "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(audio),
            ],
            check=True,
        )
        duration = 400_000
        audio_lock = root / "audio_lock.json"
        audio_lock.write_text(
            json.dumps(
                {
                    "schema_version": "001short-audio-lock-v3",
                    "episode_id": "SH_TEST_STAGE07",
                    "status": "PASS",
                    "audio_source": "SOURCE_CLIP",
                    "audio_path": audio.name,
                    "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
                    "measured_duration_us": duration,
                    "audio_codec": "pcm_s16le",
                    "ffprobe_verified": True,
                    "a10_separation": {
                        "override": "A10_CAPCUT_SEPARATION_USER_OVERRIDE",
                        "method": "CAPCUT_BUILT_IN_VOCAL_SEPARATION",
                        "status": "DEFERRED_TO_STAGE08",
                        "required_before": "USER_APPROVED_AND_RENDER",
                    },
                    "role_files": [
                        {
                            "role": "A10",
                            "audio_path": audio.name,
                            "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
                            "measured_duration_us": duration,
                            "audio_codec": "pcm_s16le",
                            "ffprobe_verified": True,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        srt = root / "final.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:00,200\ntest\n", encoding="utf-8")
        caption = root / "caption_lock.json"
        caption.write_text(
            json.dumps(
                {
                    "schema_version": "001short-caption-lock-v1",
                    "episode_id": "SH_TEST_STAGE07",
                    "status": "PASS",
                    "audio_lock_path": audio_lock.name,
                    "audio_lock_sha256": hashlib.sha256(audio_lock.read_bytes()).hexdigest(),
                    "final_srt_path": srt.name,
                    "final_srt_sha256": hashlib.sha256(srt.read_bytes()).hexdigest(),
                    "final_cue_count": 1,
                    "cues": [
                        {"cue_id": "1", "start_us": 0, "end_us": 200000, "text": "test"}
                    ],
                    "all_cues_within_measured_audio": True,
                    "no_overlap_verified": True,
                }
            ),
            encoding="utf-8",
        )
        return audio_lock, caption

    def run_stage(
        self, stage: str, status: str, *, design_lock: bool = False, **state_values: str
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = Path(directory) / "state.json"
            if design_lock:
                evidence = root / "design_lock_evidence.json"
                evidence.write_text(
                    json.dumps(
                        {
                            "schema_version": "001short-design-lock-evidence-v1",
                            "status": "PASS",
                            "episode_id": "SH_TEST_STAGE07",
                            "handoff_path": "handoff.json",
                            "handoff_sha256": "a" * 64,
                            "source_identity_path": "source_identity.json",
                            "source_identity_sha256": "b" * 64,
                            "source_media_path": "source.mp4",
                            "source_media_sha256": "c" * 64,
                            "timeline_path": "timeline.json",
                            "timeline_sha256": "d" * 64,
                            "source_fingerprint": "sha256:test",
                        }
                    ),
                    encoding="utf-8",
                )
                state_values.update(
                    {
                        "design_lock_evidence_path": str(evidence),
                        "design_lock_evidence_sha256": hashlib.sha256(
                            evidence.read_bytes()
                        ).hexdigest(),
                    }
                )
            state.write_text(
                json.dumps(
                    {
                        "episode_id": "SH_TEST_STAGE07",
                        "current_stage": stage,
                        "status": status,
                        **state_values,
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), "--state", str(state)],
                capture_output=True,
                text=True,
                check=False,
            )
        return completed, json.loads(completed.stdout)

    def test_stage07_accepts_final_design_locked_before_clean_visual(self):
        completed, payload = self.run_stage("07", "FINAL_DESIGN_LOCKED")

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["status"], "WAIT")
        self.assertEqual(
            payload["errors"],
            [{"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": "design_lock"}],
        )

    def test_stage07_accepts_clean_visual_ready(self):
        completed, payload = self.run_stage("07", "CLEAN_VISUAL_READY")

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["status"], "WAIT")
        self.assertEqual(
            payload["errors"],
            [{"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": "design_lock"}],
        )

    def test_stage08_accepts_audio_lock_with_source_video_provisional(self):
        completed, payload = self.run_stage(
            "08",
            "AUDIO_CAPTION_VALIDATED",
            visual_asset_mode="SOURCE_VIDEO_PROVISIONAL",
        )

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["status"], "WAIT")
        self.assertEqual(
            payload["errors"],
            [{"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": "design_lock"}],
        )

    def test_stage08_source_video_provisional_does_not_require_clean_visual(self):
        completed, payload = self.run_stage(
            "08",
            "AUDIO_CAPTION_VALIDATED",
            design_lock=True,
            visual_asset_mode="SOURCE_VIDEO_PROVISIONAL",
        )

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["status"], "WAIT")
        self.assertEqual(
            payload["errors"],
            [{"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": "audio_lock"}],
        )

    def test_stage07_pass_can_advance_state_to_stage08(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "design_lock_evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "001short-design-lock-evidence-v1",
                        "status": "PASS",
                        "episode_id": "SH_TEST_STAGE07",
                        "handoff_path": "handoff.json",
                        "handoff_sha256": "a" * 64,
                        "source_identity_path": "source_identity.json",
                        "source_identity_sha256": "b" * 64,
                        "source_media_path": "source.mp4",
                        "source_media_sha256": "c" * 64,
                        "timeline_path": "timeline.json",
                        "timeline_sha256": "d" * 64,
                        "source_fingerprint": "sha256:test",
                    }
                ),
                encoding="utf-8",
            )
            audio_lock, caption_lock = self.write_audio_caption(root)
            state = root / "state.json"
            state.write_text(
                json.dumps(
                    {
                        "episode_id": "SH_TEST_STAGE07",
                        "current_stage": "07",
                        "status": "FINAL_DESIGN_LOCKED",
                        "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                        "design_lock_evidence_path": str(evidence),
                        "design_lock_evidence_sha256": hashlib.sha256(
                            evidence.read_bytes()
                        ).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(VALIDATOR),
                    "--state",
                    str(state),
                    "--audio-lock",
                    str(audio_lock),
                    "--caption-lock",
                    str(caption_lock),
                    "--advance",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            advanced = json.loads(state.read_text(encoding="utf-8"))

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(advanced["current_stage"], "08")
        self.assertEqual(advanced["status"], "AUDIO_CAPTION_VALIDATED")
        self.assertEqual(advanced["audio_lock_path"], str(audio_lock.resolve()))
        self.assertEqual(advanced["caption_lock_path"], str(caption_lock.resolve()))

    def test_stage08_accepts_legacy_design_lock_field_from_episode_root(self):
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            workflow = episode / "90_workflow"
            scripts = episode / "20_script"
            workflow.mkdir()
            scripts.mkdir()
            evidence = scripts / "design_lock_evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "001short-design-lock-evidence-v1",
                        "status": "PASS",
                        "episode_id": "SH_TEST_STAGE07",
                        "handoff_path": "handoff.json",
                        "handoff_sha256": "a" * 64,
                        "source_identity_path": "source_identity.json",
                        "source_identity_sha256": "b" * 64,
                        "source_media_path": "source.mp4",
                        "source_media_sha256": "c" * 64,
                        "timeline_path": "timeline.json",
                        "timeline_sha256": "d" * 64,
                        "source_fingerprint": "sha256:test",
                    }
                ),
                encoding="utf-8",
            )
            state = workflow / "state.json"
            state.write_text(
                json.dumps(
                    {
                        "episode_id": "SH_TEST_STAGE07",
                        "current_stage": "08",
                        "status": "AUDIO_CAPTION_VALIDATED",
                        "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL",
                        "design_lock_evidence": "20_script/design_lock_evidence.json",
                        "design_lock_evidence_sha256": hashlib.sha256(
                            evidence.read_bytes()
                        ).hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), "--state", str(state)],
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(payload["status"], "WAIT")
        self.assertEqual(
            payload["errors"],
            [{"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": "audio_lock"}],
        )

if __name__ == "__main__":
    unittest.main()
