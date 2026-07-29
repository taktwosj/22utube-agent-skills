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
from _lock_fixture import digest, rewrite_lock, write_valid_lock  # noqa: E402


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

    def test_codex_cli_fallback_passes_same_contract(self):
        self.lock["authority"]["reviewer"] = "CODEX_CLI"
        failure = self.ep / "90_reports" / "claude_call_failure_v1.json"
        failure.write_text(json.dumps({
            "schema": "politics-longform-review-fallback.v1",
            "status": "CLAUDE_CALL_FAILED",
            "script_sha256": self.lock["script_sha256"],
        }), encoding="utf-8")
        review = self.ep / self.lock["evidence"]["independent_review"]["path"]
        body = review.read_text(encoding="utf-8")
        body = body.replace("review_origin: claude_external",
                            "review_origin: codex_cli_external")
        body = body.replace("recorded_by: CLAUDE",
                            "recorded_by: CODEX_CLI_REVIEWER")
        body += ("fallback_reason: CLAUDE_CALL_FAILURE\n"
                 "claude_failure_report_path: "
                 "90_reports/claude_call_failure_v1.json\n"
                 f"claude_failure_report_sha256: {digest(failure)}\n")
        review.write_text(body, encoding="utf-8")
        self.lock["evidence"]["independent_review"]["sha256"] = digest(review)
        approval = self.ep / self.lock["evidence"]["user_approval"]["path"]
        payload = json.loads(approval.read_text(encoding="utf-8"))
        payload["claude_review_sha256"] = digest(review)
        approval.write_text(json.dumps(payload), encoding="utf-8")
        self.lock["evidence"]["user_approval"]["sha256"] = digest(approval)
        rewrite_lock(self.ep, self.lock)
        gate = Gate(self.ep, "tts")
        gate.run()
        self.assertEqual(gate.fails, [])

    def test_codex_cli_without_failure_evidence_blocks(self):
        self.lock["authority"]["reviewer"] = "CODEX_CLI"
        self.mutate_review(lambda body: body.replace(
            "review_origin: claude_external", "review_origin: codex_cli_external"
        ).replace("recorded_by: CLAUDE", "recorded_by: CODEX_CLI_REVIEWER"))
        self.assertBlocked("REVIEW_FALLBACK_EVIDENCE_MISSING")

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

    def test_report_check_violation_cannot_hide_behind_zero_total(self):
        def update(value):
            value["checks"]["quote_fidelity"] = {
                "violations": ["changed quote"], "count": 1}
            value["total_violations"] = 0
        self.mutate_json_evidence("verification_report", update)
        self.assertBlocked("VERIFICATION_CHECK_NOT_PASS")

    def test_report_check_count_must_match_violation_list(self):
        def update(value):
            value["checks"]["quote_fidelity"] = {
                "violations": ["changed quote"], "count": 0}
        self.mutate_json_evidence("verification_report", update)
        self.assertBlocked("VERIFICATION_COUNT_MISMATCH")

    def test_report_boolean_count_is_rejected(self):
        self.mutate_json_evidence(
            "verification_report",
            lambda value: value["checks"]["quote_fidelity"].update(count=False))
        self.assertBlocked("VERIFICATION_COUNT_INVALID")

    def test_report_missing_security_check_is_rejected(self):
        self.mutate_json_evidence(
            "verification_report",
            lambda value: value["checks"].pop("quote_fidelity"))
        self.assertBlocked("VERIFICATION_CHECK_SET_INVALID")

    def test_report_extra_check_is_rejected(self):
        self.mutate_json_evidence(
            "verification_report",
            lambda value: value["checks"].update(
                fake={"violations": [], "count": 0}))
        self.assertBlocked("VERIFICATION_CHECK_SET_INVALID")

    def test_source_srt_review_wait_status_blocks(self):
        self.mutate_json_evidence(
            "source_srt_review",
            lambda value: value.update(status="WAIT_USER_SOURCE_TERM_CONFIRMATION"))
        self.assertBlocked("SOURCE_SRT_REVIEW_NOT_PASS")

    def test_source_srt_review_receipt_errors_block(self):
        self.mutate_json_evidence(
            "source_srt_review",
            lambda value: value["review_receipt"].update(
                errors=["audio comparison receipt missing"]))
        self.assertBlocked("SOURCE_SRT_REVIEW_RECEIPT_NOT_PASS")

    def test_source_srt_review_packet_binding_mismatch_blocks(self):
        self.mutate_json_evidence(
            "source_packet",
            lambda value: value["source_srt_review"].update(sha256="a" * 64))
        self.assertBlocked("SOURCE_SRT_REVIEW_BINDING_MISMATCH")

    def test_inferred_user_approval_is_rejected(self):
        self.mutate_json_evidence(
            "user_approval",
            lambda value: value.update(user_approval_origin="inferred"))
        self.assertBlocked("SELF_APPROVAL_INVALID")

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

    def test_review_origin_must_match_authority(self):
        self.mutate_review(lambda body: body.replace(
            "review_origin: claude_external", "review_origin: codex_cli_external"))
        self.assertBlocked("REVIEW_ORIGIN_MISMATCH")

    def test_executor_cannot_record_own_review(self):
        self.mutate_review(lambda body: body.replace(
            "recorded_by: CLAUDE", "recorded_by: CODEX"))
        self.assertBlocked("SELF_REVIEW_INVALID")

    def test_unresolved_high_blocks(self):
        self.mutate_review(lambda body: body.replace(
            "unresolved_high: 0", "unresolved_high: 3"))
        self.assertBlocked("REVIEW_UNRESOLVED_OR_DEFERRED")

    def test_deferred_tts_blocks(self):
        self.mutate_review(lambda body: body.replace(
            "deferred_tts: 0", "deferred_tts: 1"))
        self.assertBlocked("REVIEW_UNRESOLVED_OR_DEFERRED")

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
