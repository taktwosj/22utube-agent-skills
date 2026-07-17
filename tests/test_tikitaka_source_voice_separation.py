from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    load_source_module_no_bytecode,
    write_source_voice_separation_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
PREPARE = (
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
TIKITAKA_SKILL = ROOT / "skills" / "00-tikitaka" / "SKILL.md"
SINGLE_SOURCE_CONTRACT = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "shorts_script_analysis_single_source_v20260706.md"
)
HARNESS = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "tikitaka_harness_runner.py"
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class TikitakaSourceVoiceSeparationTests(unittest.TestCase):
    def test_tikitaka_contract_requires_full_source_demucs_before_q_cutting(self) -> None:
        tikitaka = TIKITAKA_SKILL.read_text(encoding="utf-8")
        single_source = SINGLE_SOURCE_CONTRACT.read_text(encoding="utf-8")
        harness = HARNESS.read_text(encoding="utf-8")

        for token in [
            "Full-Source Demucs Preprocessing",
            "10_analysis/audio/full_source_audio.wav",
            "10_analysis/audio/vocals.wav",
            "WAIT_DEMUCS_AVAILABLE",
            "WAIT_SOURCE_VOICE_Q_PROVENANCE",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, tikitaka)
        self.assertIn("Demucs FULL_SOURCE_AUDIO separation", single_source)
        self.assertIn("do not use raw mixed audio as a fallback", single_source)
        self.assertIn(
            '"source_voice_separation": source_voice_separation_status(work_dir)',
            harness,
        )

    def test_validator_accepts_full_source_demucs_fixture(self) -> None:
        module = load_source_module_no_bytecode(
            "source_voice_validator_pass",
            VALIDATOR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_sha256 = "a" * 64
            write_json(
                root / "10_analysis" / "source_identity_lock.json",
                {"sha256": source_sha256, "duration_sec": 8.0},
            )
            write_source_voice_separation_fixture(root, source_sha256)

            result = module.validate_source_voice_separation(root)

            self.assertEqual(result["source_voice_separation_status"], "PASS")
            self.assertTrue(result["source_voice_vocals_path"].endswith("vocals.wav"))

    def test_validator_rejects_manifest_bound_to_a_different_source(self) -> None:
        module = load_source_module_no_bytecode(
            "source_voice_validator_hash",
            VALIDATOR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "10_analysis" / "source_identity_lock.json",
                {"sha256": "a" * 64, "duration_sec": 8.0},
            )
            write_source_voice_separation_fixture(root, "b" * 64)

            with self.assertRaisesRegex(
                module.GateFail,
                "WAIT_SOURCE_VOICE_HASH_BINDING",
            ):
                module.validate_source_voice_separation(root)

    def test_validator_rejects_stems_shorter_than_locked_source(self) -> None:
        module = load_source_module_no_bytecode(
            "source_voice_validator_truncated",
            VALIDATOR,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_sha256 = "a" * 64
            write_json(
                root / "10_analysis" / "source_identity_lock.json",
                {"sha256": source_sha256, "duration_sec": 8.0},
            )
            write_source_voice_separation_fixture(
                root,
                source_sha256,
                duration_sec=1.0,
            )

            with self.assertRaisesRegex(
                module.GateFail,
                "WAIT_SOURCE_VOICE_DURATION_PARITY",
            ):
                module.validate_source_voice_separation(root)

    def test_prepare_allows_only_explicit_no_speech_skip(self) -> None:
        module = load_source_module_no_bytecode(
            "source_voice_prepare_skip",
            PREPARE,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "00_source" / "source.mp4"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"source")

            result = module.prepare_source_voice(
                root,
                Path("00_source/source.mp4"),
                no_source_speech_confirmed=True,
                confirmation_source="user",
            )

            self.assertEqual(result["status"], "NOT_REQUIRED_NO_SOURCE_SPEECH")
            self.assertEqual(
                result["source_fingerprint_sha256"],
                hashlib.sha256(source.read_bytes()).hexdigest(),
            )
            self.assertIs(result["source_voice_music_removed"], False)

    def test_prepare_rejects_episode_root_escape(self) -> None:
        module = load_source_module_no_bytecode(
            "source_voice_prepare_escape",
            PREPARE,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "episode"
            root.mkdir()
            outside = root.parent / "outside.mp4"
            outside.write_bytes(b"source")

            with self.assertRaisesRegex(module.GateFail, "path escapes episode root"):
                module.prepare_source_voice(root, outside)


if __name__ == "__main__":
    unittest.main()
