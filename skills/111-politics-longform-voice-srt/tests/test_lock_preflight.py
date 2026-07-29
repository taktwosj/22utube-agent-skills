#!/usr/bin/env python3
"""Direct execution must require both the 110 script lock and 111 TTS lock."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
TTS_SCRIPT = SCRIPTS / "gen_narration_full.py"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lock_fixture import rewrite_lock, write_valid_lock  # noqa: E402
from lock_preflight import (  # noqa: E402
    LockGateError, assert_runtime_matches, locked_tts_params,
    require_gate, tts_params_fingerprint)

TTS = {"provider": "supertone", "voice_id": "V1",
       "model": "sona_speech_2", "speed": 1,
       "pitch_shift": 0, "pitch_variance": 1}


class PreflightCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="PL_20260729_preflight_")
        self.ep = Path(self.tmp.name)
        self.lock = write_valid_lock(self.ep)

    def tearDown(self):
        self.tmp.cleanup()

    def write_tts_lock(self, **updates):
        payload = {
            "schema": "politics-longform-tts-params-lock.v1",
            "status": "TTS_PARAMS_LOCKED",
            "authority": "PROJECT_GPT",
            "script_sha256": self.lock["script_sha256"],
            "tts_params": dict(TTS),
        }
        payload.update(updates)
        path = self.ep / "30_audio_srt" / "tts_params_lock_v1.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_require_gate_passes_with_110_lock(self):
        result = require_gate(self.ep, "tts")
        self.assertEqual(result["status"], "SCRIPT_LOCKED")

    def test_require_gate_raises_without_lock(self):
        (self.ep / "20_script" / "script_lock.json").unlink()
        with self.assertRaises(LockGateError) as cm:
            require_gate(self.ep, "tts")
        self.assertIn("WAIT_SCRIPT_LOCK_GATE", str(cm.exception))

    def test_require_gate_raises_on_invalid_lock(self):
        self.lock["status"] = "DRAFT"
        rewrite_lock(self.ep, self.lock)
        with self.assertRaises(LockGateError) as cm:
            require_gate(self.ep, "tts")
        self.assertIn("STATUS_NOT_LOCKED", str(cm.exception))

    def test_missing_tts_lock_waits_after_script_gate(self):
        with self.assertRaises(LockGateError) as cm:
            locked_tts_params(self.lock, self.ep)
        self.assertIn("WAIT_TTS_PARAMS_LOCK", str(cm.exception))

    def test_tts_lock_returns_project_gpt_values(self):
        self.write_tts_lock()
        self.assertEqual(locked_tts_params(self.lock, self.ep), TTS)

    def test_tts_lock_must_match_script_sha(self):
        self.write_tts_lock(script_sha256="a" * 64)
        with self.assertRaises(LockGateError) as cm:
            locked_tts_params(self.lock, self.ep)
        self.assertIn("script_sha256 불일치", str(cm.exception))

    def test_tts_lock_requires_project_gpt_authority(self):
        self.write_tts_lock(authority="CODEX")
        with self.assertRaises(LockGateError) as cm:
            locked_tts_params(self.lock, self.ep)
        self.assertIn("authority 불일치", str(cm.exception))

    def test_tts_lock_missing_key_raises(self):
        params = dict(TTS)
        del params["speed"]
        self.write_tts_lock(tts_params=params)
        with self.assertRaises(LockGateError) as cm:
            locked_tts_params(self.lock, self.ep)
        self.assertIn("tts_params 키 누락", str(cm.exception))

    def test_tts_lock_rejects_extra_param(self):
        self.write_tts_lock(tts_params=dict(TTS, extra=1))
        with self.assertRaises(LockGateError):
            locked_tts_params(self.lock, self.ep)

    def test_tts_lock_rejects_extra_top_level_field(self):
        self.write_tts_lock(extra=True)
        with self.assertRaises(LockGateError):
            locked_tts_params(self.lock, self.ep)

    def test_tts_lock_rejects_empty_voice_id(self):
        self.write_tts_lock(tts_params=dict(TTS, voice_id=""))
        with self.assertRaises(LockGateError):
            locked_tts_params(self.lock, self.ep)

    def test_tts_lock_rejects_non_positive_speed(self):
        self.write_tts_lock(tts_params=dict(TTS, speed=-100))
        with self.assertRaises(LockGateError):
            locked_tts_params(self.lock, self.ep)

    def test_tts_lock_rejects_non_numeric_pitch_shift(self):
        self.write_tts_lock(tts_params=dict(TTS, pitch_shift="bad"))
        with self.assertRaises(LockGateError):
            locked_tts_params(self.lock, self.ep)

    def test_tts_lock_rejects_zero_pitch_variance(self):
        self.write_tts_lock(tts_params=dict(TTS, pitch_variance=0))
        with self.assertRaises(LockGateError):
            locked_tts_params(self.lock, self.ep)

    def test_runtime_speed_mismatch_raises(self):
        with self.assertRaises(LockGateError):
            assert_runtime_matches(TTS, {"speed": 1.2})

    def test_runtime_match_passes(self):
        assert_runtime_matches(TTS, dict(TTS))

    def test_fingerprint_is_order_independent(self):
        first = tts_params_fingerprint(TTS)
        second = tts_params_fingerprint(dict(reversed(list(TTS.items()))))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_narration_script_reads_separate_tts_lock(self):
        body = TTS_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("locked_tts_params(SCRIPT_LOCK, EPISODE)", body)
        self.assertNotIn('SCRIPT_LOCK["tts_params"]', body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
