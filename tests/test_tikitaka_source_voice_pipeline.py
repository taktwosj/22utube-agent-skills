from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
PREPARER = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "prepare_source_voice.py"
)
VALIDATOR = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "validate_source_voice_separation.py"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_wav(path: Path, *, duration_sec: float = 1.0, sample_rate_hz: int = 48000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(duration_sec * sample_rate_hz)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate_hz)
        handle.writeframes(b"\x00\x00\x00\x00" * frame_count)


def build_valid_voice_package(root: Path) -> dict:
    source = root / "00_source" / "source.mp4"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"source-video")
    source_fingerprint = sha256_file(source)
    write_json(
        root / "10_analysis" / "source_identity_lock.json",
        {
            "status": "PASS",
            "local_source_path": "00_source/source.mp4",
            "sha256": source_fingerprint,
            "duration_sec": 1.0,
        },
    )
    source_audio = root / "10_analysis" / "audio" / "full_source_audio.wav"
    vocals = root / "10_analysis" / "audio" / "vocals.wav"
    write_wav(source_audio)
    write_wav(vocals)
    manifest = {
        "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "source_fingerprint_sha256": source_fingerprint,
        "separation_engine": "demucs",
        "separation_model": "htdemucs",
        "separation_scope": "FULL_SOURCE_AUDIO",
        "source_audio_path": "10_analysis/audio/full_source_audio.wav",
        "source_audio_sha256": sha256_file(source_audio),
        "demucs_input_sha256": sha256_file(source_audio),
        "vocals_path": "10_analysis/audio/vocals.wav",
        "vocals_sha256": sha256_file(vocals),
        "source_duration_sec": 1.0,
        "source_audio_duration_sec": 1.0,
        "vocals_duration_sec": 1.0,
        "duration_tolerance_sec": 0.25,
        "sample_rate_hz": 48000,
        "source_voice_music_removed": True,
        "q_segment_source": "10_analysis/audio/vocals.wav",
        "no_vocals_used": False,
        "created_by": "prepare_source_voice.py",
    }
    write_json(root / "10_analysis" / "source_voice_separation.json", manifest)
    return manifest


class SourceVoicePreparationTests(unittest.TestCase):
    def test_full_source_audio_is_demucs_input_before_stable_vocals_are_created(self):
        module = load_source_module_no_bytecode("prepare_source_voice_order", PREPARER)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source-video")
            calls: list[list[str]] = []

            def fake_run(command, **kwargs):
                cmd = [str(value) for value in command]
                calls.append(cmd)
                if Path(cmd[0]).name.lower().startswith("ffprobe"):
                    target = Path(cmd[-1])
                    payload = {
                        "format": {"duration": "1.000000"},
                        "streams": [
                            {
                                "codec_type": "audio",
                                "sample_rate": "48000",
                                "channels": 2,
                            }
                        ],
                    }
                    if target.suffix.lower() == ".mp4":
                        payload["streams"].append({"codec_type": "video"})
                    return subprocess.CompletedProcess(cmd, 0, json.dumps(payload), "")
                if "-m" in cmd and "demucs.separate" in cmd:
                    output_root = Path(cmd[cmd.index("-o") + 1])
                    model = cmd[cmd.index("-n") + 1]
                    vocals = output_root / model / "full_source_audio" / "vocals.wav"
                    write_wav(vocals)
                    write_wav(vocals.with_name("no_vocals.wav"))
                    return subprocess.CompletedProcess(cmd, 0, "", "")
                output = Path(cmd[-1])
                write_wav(output)
                return subprocess.CompletedProcess(cmd, 0, "", "")

            with (
                mock.patch.object(
                    module.shutil,
                    "which",
                    side_effect=lambda name: f"{name}.exe",
                ),
                mock.patch.object(module.importlib.util, "find_spec", return_value=object()),
                mock.patch.object(module.subprocess, "run", side_effect=fake_run),
            ):
                result = module.prepare_source_voice(
                    root,
                    Path("00_source/source.mp4"),
                )

            demucs_call = next(cmd for cmd in calls if "demucs.separate" in cmd)
            self.assertEqual(
                Path(demucs_call[-1]),
                root / "10_analysis" / "audio" / "full_source_audio.wav",
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["separation_scope"], "FULL_SOURCE_AUDIO")
            self.assertEqual(
                result["q_segment_source"],
                "10_analysis/audio/vocals.wav",
            )
            self.assertTrue((root / result["vocals_path"]).is_file())
            self.assertFalse((root / "10_analysis" / "audio" / "no_vocals.wav").exists())

    def test_no_audio_stream_writes_no_source_speech_skip(self):
        module = load_source_module_no_bytecode("prepare_source_voice_no_audio", PREPARER)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"silent-source-video")
            probe = {
                "format": {"duration": "1.000000"},
                "streams": [{"codec_type": "video"}],
            }
            completed = subprocess.CompletedProcess(
                ["ffprobe"],
                0,
                json.dumps(probe),
                "",
            )
            with (
                mock.patch.object(
                    module.shutil,
                    "which",
                    side_effect=lambda name: f"{name}.exe",
                ),
                mock.patch.object(module.subprocess, "run", return_value=completed),
            ):
                result = module.prepare_source_voice(
                    root,
                    Path("00_source/source.mp4"),
                )

            self.assertEqual(result["status"], "NOT_REQUIRED_NO_SOURCE_SPEECH")
            self.assertEqual(result["confirmation_source"], "no_audio_stream")
            self.assertTrue(result["no_source_speech_confirmed"])

    def test_manual_no_speech_skip_requires_confirmation_source(self):
        module = load_source_module_no_bytecode("prepare_source_voice_skip_guard", PREPARER)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source-video")
            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_VOICE_SEPARATION"):
                module.prepare_source_voice(
                    root,
                    Path("00_source/source.mp4"),
                    no_source_speech_confirmed=True,
                )


class SourceVoiceValidationTests(unittest.TestCase):
    def test_valid_full_source_demucs_manifest_passes(self):
        module = load_source_module_no_bytecode("validate_source_voice_valid", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build_valid_voice_package(root)

            result = module.validate_source_voice_separation(root)

            self.assertEqual(result["source_voice_separation_status"], "PASS")
            self.assertEqual(
                result["source_voice_vocals_path"],
                str(root / "10_analysis" / "audio" / "vocals.wav"),
            )

    def test_hash_mismatch_fails_closed(self):
        module = load_source_module_no_bytecode("validate_source_voice_hash", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            manifest["vocals_sha256"] = "0" * 64
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_VOICE_HASH_BINDING"):
                module.validate_source_voice_separation(root)

    def test_source_fingerprint_must_match_identity_lock(self):
        module = load_source_module_no_bytecode("validate_source_voice_source_hash", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            manifest["source_fingerprint_sha256"] = "0" * 64
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_VOICE_HASH_BINDING"):
                module.validate_source_voice_separation(root)

    def test_full_source_scope_is_required(self):
        module = load_source_module_no_bytecode("validate_source_voice_scope", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            manifest["separation_scope"] = "PRE_CUT_QUOTES"
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "separation_scope"):
                module.validate_source_voice_separation(root)

    def test_demucs_input_hash_must_equal_full_source_audio_hash(self):
        module = load_source_module_no_bytecode("validate_source_voice_demucs_input", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            manifest["demucs_input_sha256"] = "0" * 64
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "Demucs input hash"):
                module.validate_source_voice_separation(root)

    def test_actual_wav_sample_rate_must_be_48000(self):
        module = load_source_module_no_bytecode("validate_source_voice_sample_rate", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            source_audio = root / manifest["source_audio_path"]
            write_wav(source_audio, sample_rate_hz=44100)
            manifest["source_audio_sha256"] = sha256_file(source_audio)
            manifest["demucs_input_sha256"] = sha256_file(source_audio)
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "WAV sample rate"):
                module.validate_source_voice_separation(root)

    def test_duration_drift_over_tolerance_fails(self):
        module = load_source_module_no_bytecode("validate_source_voice_duration", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            vocals = root / manifest["vocals_path"]
            write_wav(vocals, duration_sec=1.5)
            manifest["vocals_sha256"] = sha256_file(vocals)
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_VOICE_DURATION_PARITY"):
                module.validate_source_voice_separation(root)

    def test_pass_manifest_must_claim_music_removed_and_no_vocals_unused(self):
        module = load_source_module_no_bytecode("validate_source_voice_policy", VALIDATOR)
        for field, value in (
            ("source_voice_music_removed", False),
            ("no_vocals_used", True),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                manifest = build_valid_voice_package(root)
                manifest[field] = value
                write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

                with self.assertRaisesRegex(module.GateFail, field):
                    module.validate_source_voice_separation(root)

    def test_absolute_artifact_path_is_rejected(self):
        module = load_source_module_no_bytecode("validate_source_voice_absolute", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = build_valid_voice_package(root)
            manifest["vocals_path"] = str(
                (root / "10_analysis" / "audio" / "vocals.wav").resolve()
            )
            write_json(root / "10_analysis" / "source_voice_separation.json", manifest)

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_VOICE_SEPARATION"):
                module.validate_source_voice_separation(root)

    def test_unconfirmed_no_speech_skip_is_rejected(self):
        module = load_source_module_no_bytecode("validate_source_voice_skip", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source-video")
            source_fingerprint = sha256_file(source)
            write_json(
                root / "10_analysis" / "source_identity_lock.json",
                {
                    "status": "PASS",
                    "sha256": source_fingerprint,
                    "duration_sec": 1.0,
                },
            )
            write_json(
                root / "10_analysis" / "source_voice_separation.json",
                {
                    "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
                    "status": "NOT_REQUIRED_NO_SOURCE_SPEECH",
                    "owner_skill": "00-tikitaka",
                    "source_fingerprint_sha256": source_fingerprint,
                    "no_source_speech_confirmed": False,
                    "confirmation_source": "",
                    "source_voice_music_removed": False,
                    "no_vocals_used": False,
                },
            )

            with self.assertRaisesRegex(module.GateFail, "WAIT_SOURCE_VOICE_SEPARATION"):
                module.validate_source_voice_separation(root)

    def test_skip_with_explicit_user_confirmation_passes(self):
        module = load_source_module_no_bytecode("validate_source_voice_skip_valid", VALIDATOR)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source-video")
            source_fingerprint = sha256_file(source)
            write_json(
                root / "10_analysis" / "source_identity_lock.json",
                {
                    "status": "PASS",
                    "sha256": source_fingerprint,
                    "duration_sec": 1.0,
                },
            )
            write_json(
                root / "10_analysis" / "source_voice_separation.json",
                {
                    "gate_name": "SOURCE_VOICE_SEPARATION_GATE",
                    "status": "NOT_REQUIRED_NO_SOURCE_SPEECH",
                    "owner_skill": "00-tikitaka",
                    "source_fingerprint_sha256": source_fingerprint,
                    "no_source_speech_confirmed": True,
                    "confirmation_source": "user",
                    "source_voice_music_removed": False,
                    "no_vocals_used": False,
                },
            )

            result = module.validate_source_voice_separation(root)

            self.assertEqual(
                result["source_voice_separation_status"],
                "NOT_REQUIRED_NO_SOURCE_SPEECH",
            )


if __name__ == "__main__":
    unittest.main()
