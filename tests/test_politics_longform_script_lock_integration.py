#!/usr/bin/env python3
"""110 producer -> 111 consumer integration for script_lock.json."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
S110 = REPO / "skills" / "110-politics-longform-script"
S111 = REPO / "skills" / "111-politics-longform-voice-srt"
sys.path.insert(0, str(S110 / "scripts"))
sys.path.insert(0, str(S111 / "scripts"))

import gate_script_lock as gate110  # noqa: E402
import gate_lock as gate111  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ScriptLockIntegrationCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix="PL_20260729_lock_integration_")
        self.ep = Path(self.tmp.name)
        (self.ep / "20_script").mkdir(parents=True)
        (self.ep / "90_reports").mkdir(parents=True)

        script = self.ep / "20_script" / "master_script_final.md"
        script.write_text("# 확정 대본\n\n검증된 본문입니다.\n", encoding="utf-8")
        packet = self.ep / "20_script" / "source_packet_v1.json"
        packet.write_text('{"sources": []}\n', encoding="utf-8")

        checks = {name: {"violations": [], "count": 0}
                  for name in gate110.REQUIRED_CHECKS}
        report = self.ep / "90_reports" / "verification_report_v1.json"
        report.write_text(json.dumps({
            "schema": gate110.VERIFICATION_SCHEMA,
            "script_sha256": digest(script),
            "source_packet_sha256_actual": digest(packet),
            "total_violations": 0,
            "checks": checks,
        }, ensure_ascii=False), encoding="utf-8")

        review = self.ep / "20_script" / "claude_review_v1.md"
        review.write_text(
            "verdict: APPROVED\n"
            f"script_sha256: {digest(script)}\n"
            "review_origin: claude_external\n"
            "recorded_by: CLAUDE\n"
            "claude_review_event_id: REV-INTEGRATION-001\n",
            encoding="utf-8")

        approval = self.ep / "20_script" / "user_approval.json"
        approval.write_text(json.dumps({
            "approved": True,
            "approved_script_path": "20_script/master_script_final.md",
            "approved_script_sha256": digest(script),
            "claude_review_path": "20_script/claude_review_v1.md",
            "claude_review_sha256": digest(review),
            "verification_report_path":
                "90_reports/verification_report_v1.json",
            "verification_report_sha256": digest(report),
            "user_approval_origin": "user_message",
            "user_approval_event_id": "APP-INTEGRATION-001",
            "claude_review_event_id": "REV-INTEGRATION-001",
            "executor": "CODEX",
        }, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def produce_lock(self):
        old_argv = sys.argv
        try:
            sys.argv = ["gate_script_lock.py", "--episode", str(self.ep),
                        "--write"]
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                return gate110.main()
        finally:
            sys.argv = old_argv

    def test_110_lock_passes_111_gate_without_translation(self):
        self.assertEqual(self.produce_lock(), 0)
        gate = gate111.Gate(self.ep, "tts")
        gate.run()
        self.assertEqual(gate.fails, [])

    def test_shared_schema_files_are_byte_identical(self):
        schema110 = S110 / "references" / "script_lock.schema.json"
        schema111 = S111 / "references" / "script_lock.schema.json"
        self.assertEqual(schema110.read_bytes(), schema111.read_bytes())

    def test_post_lock_evidence_edit_is_rejected_by_111(self):
        self.assertEqual(self.produce_lock(), 0)
        review = self.ep / "20_script" / "claude_review_v1.md"
        review.write_text(review.read_text(encoding="utf-8") + "tampered\n",
                          encoding="utf-8")
        gate = gate111.Gate(self.ep, "tts")
        gate.run()
        self.assertIn("EVIDENCE_SHA_MISMATCH",
                      {code for code, _ in gate.fails})


if __name__ == "__main__":
    unittest.main(verbosity=2)
