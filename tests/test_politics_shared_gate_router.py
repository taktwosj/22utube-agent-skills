"""P07 111-politics-longform separated G00-G90 lane tests (RED first)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "111-politics-longform"
WORKFLOW = SKILL_DIR / "workflow.yaml"
VALIDATOR = SKILL_DIR / "scripts" / "validate_stage_gate.py"
RUNNER = SKILL_DIR / "scripts" / "workflow_runner.py"
GATES = [
    SKILL_DIR / "references" / "gates" / name
    for name in (
        "G00_INTAKE.md",
        "G10_DESIGN.md",
        "G20_MANUAL_DIALOGUE_TWO_PASS.md",
        "G30_AUDIO.md",
        "G40_CAPTION_SRT.md",
        "G50_TRACK_PLAN.md",
        "G60_CLEAN_ASSEMBLY.md",
        "G70_UPLOAD_PACKAGE.md",
        "G80_RENDER.md",
        "G90_FINAL_QC.md",
    )
]
SCHEMAS = [
    SKILL_DIR / "schemas" / name
    for name in (
        "politics_editorial_lock.schema.json",
        "politics_audio_lock.schema.json",
        "politics_caption_lock.schema.json",
        "politics_track_plan.schema.json",
        "politics_assembly_contract.schema.json",
    )
]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _write_wav(path: Path, seconds: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8_000)
        handle.writeframes(b"\0\0" * 8_000 * seconds)


def _events(*items: tuple[str, str, str]) -> list[dict]:
    return [
        {
            "event_id": f"evt-{index:06d}",
            "gate": gate,
            "event_type": event_type,
            "actor": actor,
        }
        for index, (event_type, gate, actor) in enumerate(items, 1)
    ]


class P07FileAndRoutingTests(unittest.TestCase):
    def test_all_required_files_exist(self):
        for path in [WORKFLOW, VALIDATOR, RUNNER, *GATES, *SCHEMAS]:
            self.assertTrue(path.is_file(), f"missing P07 file: {path}")

    def test_politics_owns_g00_to_g90(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for gate in (
            "G00",
            "G10",
            "G20",
            "G30",
            "G40",
            "G50",
            "G60",
            "G60.USER",
            "G70",
            "G80",
            "G90",
        ):
            self.assertIn(gate, text)
        self.assertIn("111-politics-longform", text)

    def test_politics_main_does_not_route_to_shorts_skills(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("cross_lane_handoff_forbidden: true", text)
        self.assertNotIn("received_from_skill: 00-tikitaka", text)
        self.assertNotIn("to_skill: 000short-production-agent", text)
        self.assertNotIn("skills/000short-production-agent", text)

    def test_politics_derived_short_stays_in_111(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("politics_derived_short", text)
        self.assertIn("derived_short_owner: 111-politics-longform", text)

    def test_politics_derived_short_uses_shrtjungchi(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("derived_short_capcut_root: SHRTJUNGCHI", text)
        self.assertNotIn("derived_short_capcut_root: shrt white", text)


@unittest.skipUnless(VALIDATOR.is_file(), "P07 validator not implemented yet")
class P07ValidatorBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = _load("politics_stage_gate_validator", VALIDATOR)

    def test_g00_locks_profile_and_mode(self):
        result = self.validator.validate_g00(
            intake={
                "schema_version": "politics-intake-v1",
                "episode_id": "POL_TEST",
                "content_profile": "politics_longform",
                "production_mode": "source_led",
                "requested_target": "capcut_ready",
                "source_fingerprint": "A" * 64,
                "status": "LOCKED",
            }
        )
        self.assertEqual(result["status"], "PASS", result)

    def test_g00_rejects_mode_change_without_user_confirmation(self):
        result = self.validator.validate_g00(
            intake={
                "schema_version": "politics-intake-v1",
                "episode_id": "POL_TEST",
                "content_profile": "politics_longform",
                "production_mode": "narrated",
                "requested_target": "capcut_ready",
                "source_fingerprint": "A" * 64,
                "status": "LOCKED",
            },
            previous_lock={"production_mode": "source_led"},
        )
        self.assertEqual(result["status"], "WAIT_USER_INPUT", result)
        self.assertEqual(result["next_action"], "WAIT_USER_EDITORIAL_CONFIRMATION")

    def test_g20_requires_same_conversation_two_pass_and_manual_returns(self):
        bad = self.validator.validate_g20(
            editorial_lock={
                "schema_version": "politics-editorial-lock-v1",
                "episode_id": "POL_TEST",
                "content_profile": "politics_longform",
                "production_mode": "narrated",
                "editorial_status": "LOCKED",
                "round1_conversation_id": "CHAT-A",
                "round2_conversation_id": "CHAT-B",
                "round1_return_sha256": "A" * 64,
                "round2_return_sha256": "B" * 64,
                "script_sha256": "C" * 64,
            },
            review_result={"status": "PASS"},
            ledger_events=[],
        )
        self.assertEqual(bad["status"], "FAIL")

    def test_g20_narrated_cannot_pass_without_manual_return_ledger(self):
        result = self.validator.validate_g20(
            editorial_lock={
                "schema_version": "politics-editorial-lock-v1",
                "episode_id": "POL_TEST",
                "content_profile": "politics_longform",
                "production_mode": "narrated",
                "editorial_status": "LOCKED",
                "round1_conversation_id": "CHAT-A",
                "round2_conversation_id": "CHAT-A",
                "round1_return_sha256": "A" * 64,
                "round2_return_sha256": "B" * 64,
                "script_sha256": "C" * 64,
            },
            review_result={"status": "PASS"},
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G20_MANUAL_RETURN_LEDGER_REQUIRED",
            {error["code"] for error in result["errors"]},
        )

    def _audio_fixture(self, root: Path, mode: str) -> dict:
        audio = root / "30_audio_srt" / "audio.wav"
        _write_wav(audio)
        evidence = root / "30_audio_srt" / "probe.json"
        _write_json(
            evidence,
            {
                "audio_sha256": _sha(audio),
                "measured_duration_us": 1_000_000,
                "ffprobe_verified": True,
            },
        )
        return {
            "schema_version": "politics-audio-lock-v1",
            "episode_id": "POL_TEST",
            "production_mode": mode,
            "status": "NOT_REQUIRED" if mode == "source_led" else "PASS",
            "reason_code": "NO_GENERATED_TTS" if mode == "source_led" else None,
            "audio_source": "SOURCE_CLIP" if mode == "source_led" else "NARRATION",
            "audio_path": "30_audio_srt/audio.wav",
            "audio_sha256": _sha(audio),
            "measured_duration_us": 1_000_000,
            "measurement_evidence_path": "30_audio_srt/probe.json",
            "measurement_evidence_sha256": _sha(evidence),
            "ffprobe_verified": True,
        }

    def test_source_led_g30_no_generated_tts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.validator.validate_g30(
                audio_lock=self._audio_fixture(Path(tmp), "source_led"),
                artifact_root=Path(tmp),
            )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["next_action"], "PREPARE_G40")

    def test_narrated_g30_requires_audio_measurement(self):
        result = self.validator.validate_g30(
            audio_lock={
                "schema_version": "politics-audio-lock-v1",
                "episode_id": "POL_TEST",
                "production_mode": "narrated",
                "status": "PASS",
                "audio_source": "NARRATION",
            }
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G30_NO_MEASURED_AUDIO",
            {error["code"] for error in result["errors"]},
        )

    def test_user_corrected_srt_remains_authority(self):
        result = self.validator.validate_g40(
            caption_lock={
                "schema_version": "politics-caption-lock-v1",
                "episode_id": "POL_TEST",
                "production_mode": "narrated",
                "status": "PASS",
                "srt_path": "30_audio_srt/final.srt",
                "srt_sha256": "A" * 64,
                "cue_count": 3,
                "audio_lock_sha256": "B" * 64,
                "user_corrected_srt_applicable": True,
                "user_corrected_srt_sha256": "C" * 64,
                "final_corrected_caption_fidelity": "PASS",
            },
            audio_lock={"status": "PASS", "measured_duration_us": 1_000_000},
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G40_USER_CORRECTED_SRT_NOT_AUTHORITY",
            {error["code"] for error in result["errors"]},
        )

    def test_g60_static_pass_never_implies_visual_pass(self):
        result = self.validator.validate_g60(
            assembly_contract={
                "schema_version": "politics-assembly-contract-v1",
                "episode_id": "POL_TEST",
                "content_profile": "politics_longform",
                "capcut_root": "jungchilong_base_v3_intro15",
                "static_harness_status": "PASS",
                "reference_only_material_count": 0,
                "reference_only_timeline_count": 0,
                "unapproved_visible_text_count": 0,
                "structural_contamination": False,
            },
            track_plan={"status": "PASS"},
        )
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["next_action"], "WAIT_USER_VISUAL_GATE")
        self.assertFalse(result["auto_advance_allowed"])

    def test_g70_forces_release_false(self):
        result = self.validator.validate_g70(
            upload_package={"release_allowed": True},
            ledger_events=_events(("USER_VISUAL_PASS", "G60.USER", "USER")),
        )
        self.assertEqual(result["status"], "FAIL")

    def test_g90_rejects_release_without_g80_evidence(self):
        result = self.validator.validate_g90(
            final_qc={"schema_version": "politics-final-qc-v1"},
            ledger_events=_events(
                ("FINAL_QC_PASS", "G90", "VALIDATOR"),
                ("UPLOAD_APPROVED", "G90", "USER"),
            ),
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertIn(
            "FAIL_G90_REQUIRES_G80",
            {error["code"] for error in result["errors"]},
        )


@unittest.skipUnless(RUNNER.is_file(), "P07 runner not implemented yet")
class P07RunnerSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = _load("politics_workflow_runner", RUNNER)

    def test_runner_rejects_non_deterministic_and_external_actions(self):
        for action in (
            "CALL_LLM",
            "PAID_TTS",
            "UPLOAD_VIDEO",
            "OPEN_CAPCUT",
            "AUTO_RETRY",
        ):
            decision = self.runner.decide(
                {
                    "schema_version": "gate-result-v1",
                    "status": "PASS",
                    "lane": "politics_longform",
                    "gate": "G20",
                    "next_action": action,
                    "auto_advance_allowed": True,
                    "auto_advance_class": "DETERMINISTIC_ONLY",
                }
            )
            self.assertEqual(decision["decision"], "STOP", action)

    def test_runner_preserves_manual_wait_and_release_boundaries(self):
        for action in (
            "WAIT_USER_VISUAL_GATE",
            "WAIT_UPLOAD_APPROVAL",
            "EPISODE_RELEASED",
        ):
            decision = self.runner.decide(
                {
                    "schema_version": "gate-result-v1",
                    "status": "PASS",
                    "lane": "politics_longform",
                    "gate": "G90",
                    "next_action": action,
                    "auto_advance_allowed": False,
                    "auto_advance_class": "NONE",
                }
            )
            self.assertEqual(decision["decision"], "WAIT", action)


if __name__ == "__main__":
    unittest.main()
