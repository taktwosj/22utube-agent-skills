#!/usr/bin/env python3
"""잠금 게이트 계약.

네 가지를 막는다.

    옛 검수로 새 대본 잠그기       SHA 결합
    승인 후 파일 바꿔치기          경로별 SHA 고정
    실행자의 자기승인              출처 필드 + 사건 분리
    잠금 전 잠긴 척하기            이름 순서 (final -> locked)

세 번째는 위조를 불가능하게 만들지 못한다. 파일을 쓸 수 있는 쪽은 필드도
쓸 수 있다. 비용을 올리고 귀속시키는 장치다.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import gate_script_lock as g                                 # noqa: E402

SHA_A = "a" * 64
SHA_B = "b" * 64
REV_EVENT = "REV-20260727-001"
APP_EVENT = "APP-20260727-001"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class LockCase(unittest.TestCase):
    def setUp(self):
        self.ep = Path(tempfile.mkdtemp(prefix="ep_"))
        (self.ep / "20_script").mkdir(parents=True)
        (self.ep / "90_reports").mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.ep, ignore_errors=True)

    def write_all(self, report_sha=None, review_sha=None,
                  approval_sha=None, violations=0, verdict="APPROVED",
                  approved=True, origin="claude_external",
                  recorded_by="CLAUDE", executor="CODEX",
                  review_event=REV_EVENT, ref_review_event=REV_EVENT,
                  approval_event=APP_EVENT, approval_origin="user_message",
                  script_name=g.APPROVAL_TARGET,
                  review_name="claude_review_v1.md",
                  report_override=None, **override):
        script = self.ep / "20_script" / script_name
        script.write_text("# 확정 대본\n", encoding="utf-8")
        # 대본 SHA 는 실파일에서 온다. 세 증거는 기본으로 이걸 가리키고,
        # 어긋난 상황을 만들 때만 SHA_B 를 넘긴다.
        self.script_sha = digest(script)
        report_sha = report_sha or self.script_sha
        review_sha = review_sha or self.script_sha
        approval_sha = approval_sha or self.script_sha

        report = self.ep / "90_reports" / "verification_report_v1.json"
        checks = {name: {"violations": [], "count": 0}
                  for name in g.REQUIRED_CHECKS}
        if violations:
            first = g.REQUIRED_CHECKS[0]
            checks[first] = {"violations": ["x"] * violations,
                             "count": violations}
        payload = {"schema": g.VERIFICATION_SCHEMA,
                   "total_violations": violations,
                   "script_sha256": report_sha,
                   "checks": checks}
        payload.update(report_override or {})
        report.write_text(json.dumps(payload, ensure_ascii=False),
                          encoding="utf-8")

        review = self.ep / "20_script" / review_name
        body = f"verdict: {verdict}\nscript_sha256: {review_sha}\n"
        if origin:
            body += f"review_origin: {origin}\n"
        if recorded_by:
            body += f"recorded_by: {recorded_by}\n"
        if review_event:
            body += f"claude_review_event_id: {review_event}\n"
        review.write_text(body, encoding="utf-8")

        approval = {
            "approved": approved,
            "approved_script_path": f"20_script/{script_name}",
            "approved_script_sha256": approval_sha,
            "claude_review_path": f"20_script/{review_name}",
            "claude_review_sha256": digest(review),
            "verification_report_path":
                "90_reports/verification_report_v1.json",
            "verification_report_sha256": digest(report),
            "user_approval_origin": approval_origin,
            "user_approval_event_id": approval_event,
            "claude_review_event_id": ref_review_event,
            "executor": executor,
        }
        approval.update(override)
        (self.ep / "20_script" / "user_approval.json").write_text(
            json.dumps(approval, ensure_ascii=False), encoding="utf-8")

    def run_gate(self, script_sha=None):
        files, errors = g.collect(self.ep)
        return g.evaluate(files, errors, script_sha=script_sha)[0]

    def assertCode(self, code):
        found = self.run_gate()
        self.assertTrue(any(code in v for v in found),
                        f"{code} 가 안 나왔다: {found}")


class TestHappyPath(LockCase):
    def test_all_evidence_same_sha_passes(self):
        self.write_all()
        self.assertEqual(self.run_gate(), [])


class TestMissingEvidence(LockCase):
    def test_nothing_present(self):
        self.assertCode("WAIT_USER_SCRIPT_APPROVAL")

    def test_missing_review_file(self):
        self.write_all()
        (self.ep / "20_script" / "claude_review_v1.md").unlink()
        self.assertCode("FAIL_APPROVAL_PATH_MISSING")

    def test_missing_machine_report(self):
        self.write_all()
        (self.ep / "90_reports" / "verification_report_v1.json").unlink()
        self.assertCode("FAIL_APPROVAL_PATH_MISSING")


class TestPathScope(LockCase):
    """범위 밖 경로는 무시가 아니라 하드 실패다.

    무시하고 다른 파일을 고르면 그게 fallback 이고, fallback 이 있으면
    경로 지목이 무의미해진다.
    """

    def test_parent_traversal_is_hard_failure(self):
        self.write_all(claude_review_path="../../다른회차/claude_review_v1.md")
        self.assertCode("FAIL_APPROVAL_PATH_OUT_OF_SCOPE")

    def test_absolute_path_outside_episode_is_hard_failure(self):
        self.write_all(approved_script_path="C:/Windows/System32/x.md")
        self.assertCode("FAIL_APPROVAL_PATH_OUT_OF_SCOPE")

    def test_no_fallback_after_scope_violation(self):
        """실재하는 후보가 있어도 대신 고르지 않는다."""
        self.write_all(claude_review_path="../../x/claude_review_v1.md")
        found = self.run_gate()
        self.assertTrue(any("FAIL_APPROVAL_PATH_OUT_OF_SCOPE" in v
                            for v in found))
        self.assertTrue(any("WAIT_CLAUDE_REVIEW" in v for v in found))


class TestPrematureLockName(LockCase):
    """게이트 통과 전에 이름이 locked 면 상태가 증거보다 앞선다."""

    def test_locked_name_before_gate_is_rejected(self):
        self.write_all(script_name=g.LOCKED_OUTPUT)
        self.assertCode("FAIL_PREMATURE_LOCK_NAME")

    def test_final_name_is_accepted(self):
        self.write_all()
        self.assertEqual(self.run_gate(), [])


class TestStaleReview(LockCase):
    def test_review_of_older_script(self):
        self.write_all(review_sha=SHA_B)
        self.assertCode("FAIL_STALE_REVIEW_SHA")

    def test_approval_of_older_script(self):
        self.write_all(approval_sha=SHA_B)
        self.assertCode("FAIL_STALE_REVIEW_SHA")

    def test_verification_of_older_script(self):
        self.write_all(report_sha=SHA_B)
        self.assertCode("FAIL_STALE_REVIEW_SHA")

    def test_script_replaced_after_all_three_signed_off(self):
        """실제로 대본 파일을 바꾼다. script_sha 인자를 주입하는 게 아니다.

        인자 주입은 게이트가 무엇을 비교하는지 시험하지 않는다. 세 증거가
        전부 옛 대본을 가리키는데 파일만 새것인 상황을 만든다.
        """
        self.write_all()
        (self.ep / "20_script" / g.APPROVAL_TARGET).write_text(
            "# 승인 뒤에 바꿔치기한 대본\n", encoding="utf-8")
        found = self.run_gate()
        self.assertTrue(any("FAIL_STALE_REVIEW_SHA" in v for v in found),
                        f"바꿔치기를 못 잡았다: {found}")

    def test_review_edited_after_approval(self):
        self.write_all()
        p = self.ep / "20_script" / "claude_review_v1.md"
        p.write_text(p.read_text(encoding="utf-8") + "추가\n", encoding="utf-8")
        self.assertCode("FAIL_STALE_REVIEW_SHA")

    def test_report_edited_after_approval(self):
        self.write_all()
        p = self.ep / "90_reports" / "verification_report_v1.json"
        p.write_text(json.dumps({"total_violations": 0,
                                 "script_sha256": SHA_A, "x": 1}),
                     encoding="utf-8")
        self.assertCode("FAIL_STALE_REVIEW_SHA")

    def test_script_edited_after_approval(self):
        self.write_all()
        p = self.ep / "20_script" / g.APPROVAL_TARGET
        p.write_text("# 다른 대본\n", encoding="utf-8")
        self.assertCode("FAIL_STALE_REVIEW_SHA")

    def test_missing_report_sha_in_approval(self):
        self.write_all(verification_report_sha256=None)
        self.assertCode("FAIL_STALE_REVIEW_SHA")


class TestExplicitPathPinning(LockCase):
    def test_unapproved_newer_file_is_ignored(self):
        self.write_all()
        (self.ep / "20_script" / "claude_review_v99.md").write_text(
            f"verdict: APPROVED\nscript_sha256: {SHA_B}\n", encoding="utf-8")
        self.assertEqual(self.run_gate(), [],
                         "승인서가 지목하지 않은 v99 가 선택됐다")


class TestSelfApproval(LockCase):
    def test_review_written_by_executor(self):
        self.write_all(recorded_by="CODEX", executor="CODEX")
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_missing_review_origin(self):
        self.write_all(origin=None)
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_wrong_review_origin(self):
        self.write_all(origin="self")
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_approval_not_from_user_message(self):
        self.write_all(approval_origin="inferred")
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_review_event_mismatch(self):
        self.write_all(review_event="REV-OTHER")
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_shared_event_id_is_rejected(self):
        """검수와 승인이 같은 사건 id 면 두 사건인지 구분되지 않는다."""
        self.write_all(review_event=REV_EVENT, ref_review_event=REV_EVENT,
                       approval_event=REV_EVENT)
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_missing_approval_event(self):
        self.write_all(approval_event=None)
        self.assertCode("FAIL_SELF_APPROVAL")

    def test_approval_without_review_reference(self):
        self.write_all(ref_review_event=None)
        self.assertCode("FAIL_SELF_APPROVAL")


class TestFakeVerificationReport(LockCase):
    """두 필드만 있는 가짜 보고서로 통과할 수 없어야 한다."""

    def test_false_is_not_zero_violations(self):
        """Python 에서 False == 0 이다. truthiness 로 보면 뚫린다."""
        self.write_all(report_override={"total_violations": False})
        self.assertCode("FAIL_VERIFICATION_REPORT_SHAPE")

    def test_string_zero_is_rejected(self):
        self.write_all(report_override={"total_violations": "0"})
        self.assertCode("FAIL_VERIFICATION_REPORT_SHAPE")

    def test_two_field_report_is_rejected(self):
        p = self.ep / "90_reports" / "verification_report_v1.json"
        self.write_all()
        sha = json.loads(
            (self.ep / "20_script" / "user_approval.json")
            .read_text(encoding="utf-8"))["approved_script_sha256"]
        p.write_text(json.dumps({"total_violations": 0,
                                 "script_sha256": sha}), encoding="utf-8")
        self.assertCode("FAIL_VERIFICATION_REPORT_SHAPE")

    def test_missing_check_entry_is_rejected(self):
        self.write_all()
        p = self.ep / "90_reports" / "verification_report_v1.json"
        rep = json.loads(p.read_text(encoding="utf-8"))
        rep["checks"].pop("quote_fidelity")
        p.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
        self.assertCode("FAIL_VERIFICATION_REPORT_SHAPE")

    def test_total_not_matching_check_counts_is_rejected(self):
        self.write_all()
        p = self.ep / "90_reports" / "verification_report_v1.json"
        rep = json.loads(p.read_text(encoding="utf-8"))
        rep["checks"]["quote_fidelity"] = {"violations": ["x"], "count": 1}
        p.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
        self.assertCode("FAIL_VERIFICATION_REPORT_SHAPE")


class TestVerdictAndViolations(LockCase):
    def test_machine_violations_block(self):
        self.write_all(violations=3)
        self.assertCode("WAIT_DRAFT_VERIFICATION")

    def test_non_approved_verdict_blocks(self):
        self.write_all(verdict="REWORK_REQUIRED")
        self.assertCode("WAIT_CLAUDE_REVIEW")

    def test_unapproved_user_blocks(self):
        self.write_all(approved=False)
        self.assertCode("WAIT_USER_SCRIPT_APPROVAL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
