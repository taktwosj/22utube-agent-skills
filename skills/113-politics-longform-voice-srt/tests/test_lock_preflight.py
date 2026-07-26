#!/usr/bin/env python3
"""게이트 우회 차단 테스트.

게이트를 만들어 둬도 스크립트를 직접 실행하면 그만이다. 실행 스크립트가
스스로 게이트를 부르는지, 잠긴 TTS 설정만 쓰는지 증명한다.

핵심 시나리오:
    잠금 없이 gen_narration_full.py 실행   -> 음성 생성 전에 종료
    잠금이 무효인 상태로 실행               -> 종료
    런타임 설정이 잠금과 다름                -> 종료

실행:
    py -3.14 -m unittest discover -s skills/113-politics-longform-voice-srt/tests
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
PREFLIGHT = SCRIPTS / "lock_preflight.py"
TTS_SCRIPT = SCRIPTS / "gen_narration_full.py"

sys.path.insert(0, str(SCRIPTS))
from lock_preflight import (  # noqa: E402
    LockGateError, assert_runtime_matches, locked_tts_params,
    require_gate, tts_params_fingerprint)

SCRIPT_BODY = "# 대본\n\n본문 한 줄입니다.\n"
INPUT_FILES = {
    "script":             "20_script/master_script.md",
    "source_map":         "20_script/source_map.json",
    "clip_manifest":      "10_analysis/clip_manifest.json",
    "intake_manifest":    "10_analysis/intake_manifest.json",
    "episode_lexicon":    "10_analysis/episode_lexicon.json",
    "machine_audit":      "90_reports/script_audit.json",
    "project_gpt_ruling": "20_script/project_gpt_ruling.json",
}
TTS = {"provider": "supertone", "voice_id": "V1", "model": "sona_speech_2",
       "speed": 1, "pitch_shift": 0, "pitch_variance": 1}


class PreflightCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        shas = {}
        for name, rel in INPUT_FILES.items():
            p = self.ep / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = (SCRIPT_BODY if name == "script"
                    else json.dumps({"stub": name})).encode("utf-8")
            p.write_bytes(data)
            shas[name] = hashlib.sha256(data).hexdigest()
        self.lock = {
            "schema_version": "politics-longform-script-lock.v1",
            "episode_id": "PL_20260101_test", "status": "SCRIPT_LOCKED",
            "lock_version": 1, "locked_at": "2026-01-01T00:00:00Z",
            "authority": {"script_authority": "PROJECT_GPT"},
            "locked_inputs": {n: {"path": r, "sha256": shas[n]}
                              for n, r in INPUT_FILES.items()},
            "ruling_summary": {
                "total_findings": 0, "approved_fix": 0, "rejected_no_change": 0,
                "deferred": 0, "unresolved": 0, "unresolved_high": 0,
                "unresolved_quote_mismatch": 0, "deferred_items": []},
            "editorial_decisions": {
                "chapter_order_approved": True, "source_media_verified": True,
                "clip_timecodes_verified": True, "hook_selection_approved": True,
                "lexicon_review_approved": True, "quote_accuracy_approved": True,
                "lexicon_conflicts": 0},
            "structure": {
                "chapter_count": 1, "narration_block_count": 1,
                "source_clip_count": 0, "logical_segment_count": 1,
                "chapters": [{"no": 1, "title": "장",
                              "script_line_range": [1, 3],
                              "segment_indices": [1]}],
                "segments": [{"index": 1, "segment_id": "SEG001",
                              "kind": "NARRATION", "chapter_no": 1,
                              "script_line_range": [3, 3],
                              "source_id": None, "source_timecode": None}]},
            "hooks": {}, "labels": {},
            "tts_params": dict(TTS),
            "render_target": {"canvas": "1920x1080", "fps": 30},
        }

    def tearDown(self):
        self.tmp.cleanup()

    def write_lock(self):
        (self.ep / "20_script" / "script_lock.json").write_text(
            json.dumps(self.lock, ensure_ascii=False), encoding="utf-8")

    # ---------------------------------------------------------- 게이트 호출
    def test_require_gate_passes_with_valid_lock(self):
        self.write_lock()
        lock = require_gate(self.ep, "tts")
        self.assertEqual(lock["status"], "SCRIPT_LOCKED")

    def test_require_gate_raises_without_lock(self):
        with self.assertRaises(LockGateError) as cm:
            require_gate(self.ep, "tts")
        self.assertIn("WAIT_SCRIPT_LOCK_GATE", str(cm.exception))

    def test_require_gate_raises_on_invalid_lock(self):
        self.lock["status"] = "DRAFT"
        self.write_lock()
        with self.assertRaises(LockGateError) as cm:
            require_gate(self.ep, "tts")
        self.assertIn("STATUS_NOT_LOCKED", str(cm.exception))

    # ---------------------------------------------------------- TTS 설정
    def test_locked_tts_params_returns_locked_values(self):
        self.assertEqual(locked_tts_params(self.lock)["speed"], 1)

    def test_locked_tts_params_missing_key_raises(self):
        del self.lock["tts_params"]["speed"]
        with self.assertRaises(LockGateError) as cm:
            locked_tts_params(self.lock)
        self.assertIn("TTS_PARAMS_INTEGRITY_FAIL", str(cm.exception))

    def test_runtime_speed_mismatch_raises(self):
        """speed 1.0 -> 1.2 면 길이가 달라져 시간축 전체가 바뀐다."""
        with self.assertRaises(LockGateError) as cm:
            assert_runtime_matches(TTS, {"speed": 1.2})
        self.assertIn("TTS_PARAMS_INTEGRITY_FAIL", str(cm.exception))

    def test_runtime_model_mismatch_raises(self):
        with self.assertRaises(LockGateError) as cm:
            assert_runtime_matches(TTS, {"model": "sona_speech_1"})
        self.assertIn("model", str(cm.exception))

    def test_runtime_match_passes(self):
        assert_runtime_matches(TTS, dict(TTS))

    def test_fingerprint_is_stable_and_order_independent(self):
        a = tts_params_fingerprint(TTS)
        b = tts_params_fingerprint(dict(reversed(list(TTS.items()))))
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)

    def test_fingerprint_changes_with_speed(self):
        other = dict(TTS, speed=1.2)
        self.assertNotEqual(tts_params_fingerprint(TTS),
                            tts_params_fingerprint(other))

    # ------------------------------------------------- 스크립트 직접 실행 차단
    def _run_tts_script(self):
        env = {
            "PATH": "", "SystemRoot": "C:\\Windows",
            "PYTHONIOENCODING": "utf-8",
            "PL_EPISODE_DIR": str(self.ep),
            "PL_REPO_EPISODE": str(self.ep),
        }
        return subprocess.run([sys.executable, str(TTS_SCRIPT)],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              env=env, timeout=180)

    def test_tts_script_without_lock_blocks(self):
        """잠금 없이 직접 실행해도 음성이 만들어지면 안 된다."""
        r = self._run_tts_script()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("WAIT_SCRIPT_LOCK_GATE", r.stdout + r.stderr)
        self.assertFalse((self.ep / "30_audio_srt" / "narration").exists())

    def test_tts_script_with_invalid_lock_blocks(self):
        self.lock["editorial_decisions"]["quote_accuracy_approved"] = False
        self.write_lock()
        r = self._run_tts_script()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("WAIT_SCRIPT_LOCK_GATE", r.stdout + r.stderr)

    def test_tts_script_has_no_hardcoded_voice_params(self):
        """잠금이 아니라 소스에 박힌 값을 쓰면 잠금이 무의미해진다.

        docstring 안의 언급은 설명이라 허용한다. 실행되는 대입문만 본다.
        """
        body = TTS_SCRIPT.read_text(encoding="utf-8")
        code = "\n".join(l for l in body.splitlines()
                         if not l.lstrip().startswith("#"))
        for pat in (r'VOICE_ID\s*=\s*["\']', r'MODEL\s*=\s*["\']',
                    r'"speed"\s*:\s*[\d.]', r'"pitch_shift"\s*:\s*[\d.]'):
            hits = [m.group(0) for m in __import__("re").finditer(pat, code)]
            self.assertEqual(hits, [], f"하드코딩 대입 잔존: {pat} -> {hits}")
        self.assertIn("locked_tts_params", code)
        self.assertIn("require_gate", code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
