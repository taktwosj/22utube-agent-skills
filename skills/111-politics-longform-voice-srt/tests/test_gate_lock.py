#!/usr/bin/env python3
"""Evidence-integrity tests for the 110 script lock consumed by 111."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
GATE = SKILL / "scripts" / "gate_lock.py"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gate_lock import Gate  # noqa: E402
from _lock_fixture import rewrite_lock, write_valid_lock  # noqa: E402


class GateCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="PL_20260729_gate_")
        self.ep = Path(self.tmp.name)
        self.lock = write_valid_lock(self.ep)

    def tearDown(self):
        self.tmp.cleanup()

    def run_gate(self, stage="tts"):
        gate = Gate(self.ep, stage)
        gate.run()
        return gate

    def assertBlocked(self, code):
        rewrite_lock(self.ep, self.lock)
        gate = self.run_gate()
        self.assertIn(code, {item[0] for item in gate.fails}, gate.fails)

    def mutate_json_evidence(self, name, update):
        entry = self.lock["evidence"][name]
        path = self.ep / entry["path"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        update(payload)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        entry["sha256"] = __import__("hashlib").sha256(
            path.read_bytes()).hexdigest()

    def mutate_review(self, transform):
        entry = self.lock["evidence"]["independent_review"]
        path = self.ep / entry["path"]
        path.write_text(transform(path.read_text(encoding="utf-8")),
                        encoding="utf-8")
        entry["sha256"] = __import__("hashlib").sha256(
            path.read_bytes()).hexdigest()

    def test_valid_110_lock_passes_tts(self):
        self.assertEqual(self.run_gate("tts").fails, [])

    def test_valid_110_lock_passes_assembly_entry_check(self):
        self.assertEqual(self.run_gate("assembly").fails, [])

    def test_missing_lock_blocks(self):
        (self.ep / "20_script" / "script_lock.json").unlink()
        self.assertIn("LOCK_MISSING",
                      {code for code, _ in self.run_gate().fails})

    def test_wrong_schema_blocks(self):
        self.lock["schema"] = "legacy"
        self.assertBlocked("SCHEMA_VERSION_MISMATCH")

    def test_legacy_top_level_fields_block(self):
        self.lock["tts_params"] = {"speed": 1}
        self.assertBlocked("LOCK_FIELDS_INVALID")

    def test_wrong_episode_blocks(self):
        self.lock["episode_id"] = "PL_20260729_other"
        self.assertBlocked("EPISODE_ID_MISMATCH")

    def test_status_must_be_locked(self):
        self.lock["status"] = "DRAFT"
        self.assertBlocked("STATUS_NOT_LOCKED")

    def test_producer_must_be_110(self):
        self.lock["produced_by"] = "manual"
        self.assertBlocked("LOCK_PRODUCER_INVALID")

    def test_next_stage_must_be_111(self):
        self.lock["next_stage"] = "112-politics-longform-hyperframes"
        self.assertBlocked("NEXT_STAGE_INVALID")

    def test_authority_is_pinned(self):
        self.lock["authority"]["drafter"] = "CODEX"
        self.assertBlocked("SCRIPT_AUTHORITY_INVALID")

    def test_codex_cli_policy_remains_separate_blocker(self):
        self.lock["authority"]["reviewer"] = "CODEX_CLI"
        self.assertBlocked("REVIEW_POLICY_MISMATCH")

    def test_missing_required_evidence_blocks(self):
        del self.lock["evidence"]["source_packet"]
        self.assertBlocked("EVIDENCE_REQUIRED_MISSING")

    def test_absolute_evidence_path_blocks(self):
        self.lock["evidence"]["source_packet"]["path"] = "C:/other/x.json"
        self.assertBlocked("EVIDENCE_PATH_OUTSIDE_EPISODE")

    def test_parent_traversal_blocks(self):
        self.lock["evidence"]["source_packet"]["path"] = "../../x.json"
        self.assertBlocked("EVIDENCE_PATH_OUTSIDE_EPISODE")

    def test_tampered_review_file_blocks(self):
        path = self.ep / self.lock["evidence"]["independent_review"]["path"]
        path.write_text(path.read_text(encoding="utf-8") + "tamper\n",
                        encoding="utf-8")
        self.assertBlocked("EVIDENCE_SHA_MISMATCH")

    def test_locked_script_hash_mismatch_blocks(self):
        path = self.ep / self.lock["locked_script"]
        path.write_text("changed\n", encoding="utf-8")
        self.assertBlocked("SCRIPT_SHA_MISMATCH")

    def test_locked_script_must_equal_approved_script(self):
        path = self.ep / self.lock["evidence"]["approved_script"]["path"]
        path.write_text("changed\n", encoding="utf-8")
        self.lock["evidence"]["approved_script"]["sha256"] = \
            __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        self.assertBlocked("APPROVED_SCRIPT_SHA_MISMATCH")

    def test_approval_false_blocks(self):
        self.mutate_json_evidence(
            "user_approval", lambda value: value.update(approved=False))
        self.assertBlocked("APPROVAL_NOT_APPROVED")

    def test_approval_script_sha_mismatch_blocks(self):
        self.mutate_json_evidence(
            "user_approval",
            lambda value: value.update(approved_script_sha256="a" * 64))
        self.assertBlocked("APPROVAL_SCRIPT_SHA_MISMATCH")

    def test_approval_review_path_mismatch_blocks(self):
        self.mutate_json_evidence(
            "user_approval",
            lambda value: value.update(claude_review_path="20_script/x.md"))
        self.assertBlocked("APPROVAL_EVIDENCE_PATH_MISMATCH")

    def test_report_violations_block(self):
        self.mutate_json_evidence(
            "verification_report",
            lambda value: value.update(total_violations=1))
        self.assertBlocked("VERIFICATION_NOT_PASS")

    def test_report_script_sha_mismatch_blocks(self):
        self.mutate_json_evidence(
            "verification_report",
            lambda value: value.update(script_sha256="b" * 64))
        self.assertBlocked("VERIFICATION_SCRIPT_SHA_MISMATCH")

    def test_report_source_packet_sha_mismatch_blocks(self):
        self.mutate_json_evidence(
            "verification_report",
            lambda value: value.update(source_packet_sha256_actual="b" * 64))
        self.assertBlocked("VERIFICATION_SOURCE_PACKET_SHA_MISMATCH")

    def test_review_verdict_must_be_approved(self):
        self.mutate_review(lambda body: body.replace(
            "verdict: APPROVED", "verdict: REWORK_REQUIRED"))
        self.assertBlocked("REVIEW_NOT_APPROVED")

    def test_review_script_sha_mismatch_blocks(self):
        self.mutate_review(lambda body: __import__("re").sub(
            r"script_sha256: [0-9a-f]{64}",
            "script_sha256: " + "c" * 64, body))
        self.assertBlocked("REVIEW_SCRIPT_SHA_MISMATCH")

    def test_review_event_mismatch_blocks(self):
        self.mutate_review(lambda body: body.replace(
            "REV-TEST-001", "REV-OTHER"))
        self.assertBlocked("REVIEW_EVENT_MISMATCH")

    def test_review_and_user_events_must_differ(self):
        self.lock["events"]["user_approval_event_id"] = "REV-TEST-001"
        self.assertBlocked("SELF_APPROVAL_EVENT_REUSED")

    def test_missing_args_exit_2(self):
        result = subprocess.run(
            [sys.executable, str(GATE), "--stage", "tts"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", env={"PATH": ""}, timeout=30)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
