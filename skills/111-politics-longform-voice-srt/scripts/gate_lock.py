#!/usr/bin/env python3
"""Validate the immutable script lock produced by 110.

111 does not re-audit script content. It verifies that the exact locked script and
the evidence already approved in 110 are still present, byte-identical, and bound
to the same review and user-approval events.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = "politics-longform-script-lock.v1"
LOCK_RELPATH = Path("20_script") / "script_lock.json"
LOCKED_SCRIPT_RELPATH = "20_script/master_script_locked.md"
PRODUCER = "110-politics-longform-script"
NEXT_STAGE = "111-politics-longform-voice-srt"
STAGES = ("assembly", "tts")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
EPISODE_ID_RE = re.compile(r"^PL_[0-9]{8}_[a-z0-9_]+$")
ALLOWED_REVIEWERS = ("CLAUDE", "CODEX_CLI")
REQUIRED_EVIDENCE = (
    "approved_script",
    "source_packet",
    "source_srt_review",
    "verification_report",
    "independent_review",
    "user_approval",
)
REQUIRED_VERIFICATION_CHECKS = (
    "source_reference", "quote_fidelity", "quote_mode_marks",
    "forbidden_display_marks", "allegation_framing", "declared_counts",
    "packet_binding", "narration_quotes", "skip_classification")
REQUIRED_REVIEW_ZERO_FIELDS = (
    "unresolved", "unresolved_high", "unresolved_quote_mismatch",
    "deferred_tts", "deferred_assembly")
REVIEW_ORIGIN_TO_AUTHORITY = {
    "claude_external": "CLAUDE",
    "codex_cli_external": "CODEX_CLI",
}
TOP_LEVEL_FIELDS = (
    "schema", "episode_id", "status", "lock_version", "locked_at",
    "produced_by", "script_sha256", "locked_script", "evidence",
    "events", "authority", "next_stage",
)

VERDICT_RE = re.compile(r"(?m)^verdict:\s*(\S+)\s*$")
REVIEW_SHA_RE = re.compile(
    r"(?m)^script_sha256:\s*([0-9a-f]{64})\s*$")
REVIEW_EVENT_RE = re.compile(
    r"(?m)^claude_review_event_id:\s*(\S+)\s*$")
REVIEW_ORIGIN_RE = re.compile(r"(?m)^review_origin:\s*(\S+)\s*$")
RECORDED_BY_RE = re.compile(r"(?m)^recorded_by:\s*(\S+)\s*$")
FALLBACK_REASON_RE = re.compile(r"(?m)^fallback_reason:\s*(\S+)\s*$")
FAILURE_PATH_RE = re.compile(
    r"(?m)^claude_failure_report_path:\s*(\S+)\s*$")
FAILURE_SHA_RE = re.compile(
    r"(?m)^claude_failure_report_sha256:\s*([0-9a-f]{64})\s*$")


def _review_int(body, name):
    match = re.search(rf"(?m)^{re.escape(name)}:\s*([0-9]+)\s*$", body)
    return int(match.group(1)) if match else None


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Gate:
    def __init__(self, episode, stage):
        self.episode = Path(episode).resolve()
        self.stage = stage
        self.fails = []
        self.checks = 0
        self.lock = {}
        self.paths = {}

    def fail(self, code, detail):
        self.fails.append((code, detail))

    def check(self, ok, code, detail):
        self.checks += 1
        if not ok:
            self.fail(code, detail)
        return ok

    def run(self):
        lock_path = self.episode / LOCK_RELPATH
        if not lock_path.is_file():
            self.fail("LOCK_MISSING", str(lock_path))
            return
        try:
            self.lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.fail("LOCK_UNPARSEABLE", f"{lock_path}: {exc}")
            return
        if not isinstance(self.lock, dict):
            self.fail("LOCK_ROOT_INVALID", "script_lock.json root is not object")
            return

        self._check_top_level()
        self._check_authority()
        self._check_events()
        self._check_files()
        self._check_evidence_bindings()

    def _check_top_level(self):
        lock = self.lock
        self.check(set(lock) == set(TOP_LEVEL_FIELDS),
                   "LOCK_FIELDS_INVALID",
                   f"got={sorted(lock)} expected={sorted(TOP_LEVEL_FIELDS)}")
        self.check(lock.get("schema") == SCHEMA_VERSION,
                   "SCHEMA_VERSION_MISMATCH",
                   f"{lock.get('schema')!r} != {SCHEMA_VERSION!r}")
        self.check(lock.get("episode_id") == self.episode.name,
                   "EPISODE_ID_MISMATCH",
                   f"{lock.get('episode_id')!r} != {self.episode.name!r}")
        self.check(bool(EPISODE_ID_RE.fullmatch(
                       str(lock.get("episode_id", "")))),
                   "EPISODE_ID_INVALID", repr(lock.get("episode_id")))
        self.check(lock.get("status") == "SCRIPT_LOCKED",
                   "STATUS_NOT_LOCKED", repr(lock.get("status")))
        version = lock.get("lock_version")
        self.check(isinstance(version, int) and not isinstance(version, bool)
                   and version >= 1,
                   "LOCK_VERSION_INVALID", repr(version))
        self.check(self._valid_datetime(lock.get("locked_at")),
                   "LOCKED_AT_INVALID", repr(lock.get("locked_at")))
        self.check(lock.get("produced_by") == PRODUCER,
                   "LOCK_PRODUCER_INVALID", repr(lock.get("produced_by")))
        self.check(lock.get("next_stage") == NEXT_STAGE,
                   "NEXT_STAGE_INVALID", repr(lock.get("next_stage")))
        self.check(bool(SHA_RE.fullmatch(str(lock.get("script_sha256", "")))),
                   "SCRIPT_SHA_MALFORMED", repr(lock.get("script_sha256")))
        self.check(lock.get("locked_script") == LOCKED_SCRIPT_RELPATH,
                   "LOCKED_SCRIPT_PATH_INVALID", repr(lock.get("locked_script")))

    @staticmethod
    def _valid_datetime(value):
        if not isinstance(value, str) or not value:
            return False
        try:
            parsed = datetime.datetime.fromisoformat(
                value.replace("Z", "+00:00"))
            return parsed.tzinfo is not None
        except ValueError:
            return False

    def _check_authority(self):
        authority = self.lock.get("authority")
        if not isinstance(authority, dict):
            self.fail("AUTHORITY_INVALID", repr(authority))
            return
        self.check(set(authority) == {"drafter", "reviewer", "final_lock"},
                   "AUTHORITY_FIELDS_INVALID", repr(sorted(authority)))
        self.check(authority.get("drafter") == "PROJECT_GPT",
                   "SCRIPT_AUTHORITY_INVALID", repr(authority.get("drafter")))
        reviewer = authority.get("reviewer")
        self.check(reviewer in ALLOWED_REVIEWERS,
                   "AUDIT_AUTHORITY_INVALID", repr(reviewer))
        self.check(authority.get("final_lock") == "USER",
                   "FINAL_LOCK_AUTHORITY_INVALID",
                   repr(authority.get("final_lock")))

    def _check_events(self):
        events = self.lock.get("events")
        if not isinstance(events, dict):
            self.fail("EVENTS_INVALID", repr(events))
            return
        expected = {"review_event_id", "claude_review_event_id",
                    "user_approval_event_id"}
        self.check(set(events) == expected, "EVENT_FIELDS_INVALID",
                   repr(sorted(events)))
        review = events.get("review_event_id")
        legacy_review = events.get("claude_review_event_id")
        user = events.get("user_approval_event_id")
        self.check(isinstance(review, str) and bool(review),
                   "REVIEW_EVENT_MISSING", repr(review))
        self.check(legacy_review == review,
                   "REVIEW_EVENT_MISMATCH",
                   f"{legacy_review!r} != {review!r}")
        self.check(isinstance(user, str) and bool(user),
                   "USER_APPROVAL_EVENT_MISSING", repr(user))
        if review and user:
            self.check(review != user, "SELF_APPROVAL_EVENT_REUSED",
                       f"review_event_id == user_approval_event_id == {review!r}")

    def _safe_path(self, name, rel):
        if not isinstance(rel, str) or not rel:
            self.fail("EVIDENCE_PATH_INVALID", f"{name}: {rel!r}")
            return None
        normalized = rel.replace("\\", "/")
        pure = PurePosixPath(normalized)
        if pure.is_absolute() or ".." in pure.parts or re.match(
                r"^[A-Za-z]:", normalized):
            self.fail("EVIDENCE_PATH_OUTSIDE_EPISODE", f"{name}: {rel}")
            return None
        target = (self.episode / Path(*pure.parts)).resolve()
        if target != self.episode and self.episode not in target.parents:
            self.fail("EVIDENCE_PATH_OUTSIDE_EPISODE", f"{name}: {rel}")
            return None
        return target

    def _check_files(self):
        script_path = self._safe_path(
            "locked_script", self.lock.get("locked_script"))
        if script_path is not None:
            self.paths["locked_script"] = script_path
            if not script_path.is_file():
                self.fail("LOCKED_SCRIPT_MISSING", str(script_path))
            elif sha256_of(script_path) != self.lock.get("script_sha256"):
                self.fail("SCRIPT_SHA_MISMATCH", str(script_path))

        evidence = self.lock.get("evidence")
        if not isinstance(evidence, dict):
            self.fail("EVIDENCE_INVALID", repr(evidence))
            return
        self.check(set(evidence) == set(REQUIRED_EVIDENCE),
                   "EVIDENCE_FIELDS_INVALID", repr(sorted(evidence)))
        for name in REQUIRED_EVIDENCE:
            entry = evidence.get(name)
            if not isinstance(entry, dict):
                self.fail("EVIDENCE_REQUIRED_MISSING", name)
                continue
            self.check(set(entry) == {"path", "sha256"},
                       "EVIDENCE_ENTRY_FIELDS_INVALID",
                       f"{name}: {sorted(entry)}")
            rel = entry.get("path")
            wanted_sha = entry.get("sha256")
            if not SHA_RE.fullmatch(str(wanted_sha or "")):
                self.fail("EVIDENCE_SHA_MALFORMED",
                          f"{name}: {wanted_sha!r}")
            path = self._safe_path(name, rel)
            if path is None:
                continue
            self.paths[name] = path
            if not path.is_file():
                self.fail("EVIDENCE_FILE_MISSING", f"{name}: {path}")
            elif SHA_RE.fullmatch(str(wanted_sha or "")):
                actual = sha256_of(path)
                if actual != wanted_sha:
                    self.fail("EVIDENCE_SHA_MISMATCH",
                              f"{name}: {actual} != {wanted_sha}")

        approved = self.paths.get("approved_script")
        locked = self.paths.get("locked_script")
        if approved and approved.is_file():
            self.check(sha256_of(approved) == self.lock.get("script_sha256"),
                       "APPROVED_SCRIPT_SHA_MISMATCH", str(approved))
        if approved and locked and approved.is_file() and locked.is_file():
            self.check(approved.read_bytes() == locked.read_bytes(),
                       "LOCKED_SCRIPT_NOT_BYTE_IDENTICAL",
                       f"{approved} != {locked}")

    def _load_json(self, name):
        path = self.paths.get(name)
        if path is None or not path.is_file():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.fail("EVIDENCE_JSON_INVALID", f"{name}: {exc}")
            return None
        if not isinstance(value, dict):
            self.fail("EVIDENCE_JSON_INVALID", f"{name}: root is not object")
            return None
        return value

    def _check_evidence_bindings(self):
        approval = self._load_json("user_approval")
        report = self._load_json("verification_report")
        source_review = self._load_json("source_srt_review")
        review_path = self.paths.get("independent_review")
        if approval is not None:
            self._check_approval(approval)
        if report is not None:
            self._check_report(report)
        if source_review is not None:
            self._check_source_review(source_review)
        if review_path is not None and review_path.is_file():
            self._check_review(review_path.read_text(encoding="utf-8"))

    def _check_approval(self, approval):
        evidence = self.lock.get("evidence") or {}
        events = self.lock.get("events") or {}
        self.check(approval.get("approved") is True,
                   "APPROVAL_NOT_APPROVED", repr(approval.get("approved")))
        self.check(approval.get("user_approval_origin") == "user_message",
                   "SELF_APPROVAL_INVALID",
                   repr(approval.get("user_approval_origin")))
        self.check(approval.get("approved_script_sha256")
                   == self.lock.get("script_sha256"),
                   "APPROVAL_SCRIPT_SHA_MISMATCH",
                   repr(approval.get("approved_script_sha256")))
        bindings = (
            ("approved_script", "approved_script_path",
             "approved_script_sha256"),
            ("verification_report", "verification_report_path",
             "verification_report_sha256"),
            ("independent_review", "claude_review_path",
             "claude_review_sha256"),
        )
        for name, path_key, sha_key in bindings:
            entry = evidence.get(name) or {}
            self.check(approval.get(path_key) == entry.get("path"),
                       "APPROVAL_EVIDENCE_PATH_MISMATCH",
                       f"{path_key}: {approval.get(path_key)!r} != "
                       f"{entry.get('path')!r}")
            self.check(approval.get(sha_key) == entry.get("sha256"),
                       "APPROVAL_EVIDENCE_SHA_MISMATCH",
                       f"{sha_key}: {approval.get(sha_key)!r} != "
                       f"{entry.get('sha256')!r}")
        self.check(approval.get("claude_review_event_id")
                   == events.get("review_event_id"),
                   "APPROVAL_REVIEW_EVENT_MISMATCH",
                   repr(approval.get("claude_review_event_id")))
        self.check(approval.get("user_approval_event_id")
                   == events.get("user_approval_event_id"),
                   "APPROVAL_USER_EVENT_MISMATCH",
                   repr(approval.get("user_approval_event_id")))

    def _check_report(self, report):
        evidence = self.lock.get("evidence") or {}
        total = report.get("total_violations")
        self.check(report.get("schema")
                   == "politics-longform-draft-verification.v1",
                   "VERIFICATION_SCHEMA_INVALID", repr(report.get("schema")))
        self.check(isinstance(total, int) and not isinstance(total, bool)
                   and total == 0,
                   "VERIFICATION_NOT_PASS", repr(total))
        self.check(report.get("script_sha256")
                   == self.lock.get("script_sha256"),
                   "VERIFICATION_SCRIPT_SHA_MISMATCH",
                   repr(report.get("script_sha256")))
        packet_sha = (evidence.get("source_packet") or {}).get("sha256")
        self.check(report.get("source_packet_sha256_actual") == packet_sha,
                   "VERIFICATION_SOURCE_PACKET_SHA_MISMATCH",
                   repr(report.get("source_packet_sha256_actual")))
        checks = report.get("checks")
        self.check(isinstance(checks, dict),
                   "VERIFICATION_CHECKS_INVALID", repr(checks))
        if not isinstance(checks, dict):
            return
        self.check(set(checks) == set(REQUIRED_VERIFICATION_CHECKS),
                   "VERIFICATION_CHECK_SET_INVALID",
                   f"got={sorted(checks)} expected={sorted(REQUIRED_VERIFICATION_CHECKS)}")
        counted = 0
        for name, check in checks.items():
            if not isinstance(check, dict):
                self.fail("VERIFICATION_CHECK_INVALID", f"{name}: not object")
                continue
            violations = check.get("violations")
            count = check.get("count")
            self.check(isinstance(violations, list),
                       "VERIFICATION_VIOLATIONS_INVALID", name)
            valid_count = (isinstance(count, int)
                           and not isinstance(count, bool) and count >= 0)
            self.check(valid_count, "VERIFICATION_COUNT_INVALID",
                       f"{name}: {count!r}")
            if valid_count:
                counted += count
                if isinstance(violations, list):
                    self.check(count == len(violations),
                               "VERIFICATION_COUNT_MISMATCH", name)
                self.check(count == 0, "VERIFICATION_CHECK_NOT_PASS",
                           f"{name}: {count}")
        if isinstance(total, int) and not isinstance(total, bool):
            self.check(counted == total, "VERIFICATION_TOTAL_MISMATCH",
                       f"{counted} != {total}")

    def _check_source_review(self, report):
        self.check(report.get("schema_version")
                   == "source_srt_quality_report_v1",
                   "SOURCE_SRT_REVIEW_SCHEMA_INVALID",
                   repr(report.get("schema_version")))
        self.check(report.get("episode_id") == self.episode.name,
                   "SOURCE_SRT_REVIEW_EPISODE_MISMATCH",
                   repr(report.get("episode_id")))
        self.check(report.get("status") == "PASS_110_SOURCE_SRT_REVIEWED",
                   "SOURCE_SRT_REVIEW_NOT_PASS", repr(report.get("status")))
        transcripts = report.get("transcripts")
        valid_transcripts = (
            isinstance(transcripts, dict) and bool(transcripts)
            and all(SHA_RE.fullmatch(str(value or ""))
                    for value in transcripts.values()))
        self.check(valid_transcripts, "SOURCE_SRT_REVIEW_TRANSCRIPTS_INVALID",
                   repr(transcripts))
        receipt = report.get("review_receipt")
        valid_receipt = isinstance(receipt, dict) and receipt.get("errors") == []
        self.check(valid_receipt, "SOURCE_SRT_REVIEW_RECEIPT_NOT_PASS",
                   repr(receipt))
        if not isinstance(receipt, dict):
            receipt = {}
        receipt_sha = receipt.get("sha256")
        self.check(bool(SHA_RE.fullmatch(str(receipt_sha or ""))),
                   "SOURCE_SRT_REVIEW_RECEIPT_SHA_INVALID", repr(receipt_sha))
        receipt_path = self._safe_path(
            "source_srt_review_receipt", receipt.get("path"))
        if receipt_path is not None:
            self.check(receipt_path.is_file(),
                       "SOURCE_SRT_REVIEW_RECEIPT_MISSING", str(receipt_path))
            if (receipt_path.is_file()
                    and SHA_RE.fullmatch(str(receipt_sha or ""))):
                self.check(sha256_of(receipt_path) == receipt_sha,
                           "SOURCE_SRT_REVIEW_RECEIPT_SHA_MISMATCH",
                           str(receipt_path))
        packet = self._load_json("source_packet")
        if packet is not None:
            binding = packet.get("source_srt_review") or {}
            evidence = (self.lock.get("evidence") or {}).get(
                "source_srt_review") or {}
            self.check(binding.get("sha256") == evidence.get("sha256"),
                       "SOURCE_SRT_REVIEW_BINDING_MISMATCH", repr(binding))
            self.check(binding.get("status") == report.get("status"),
                       "SOURCE_SRT_REVIEW_STATUS_BINDING_MISMATCH",
                       repr(binding))
            self.check(binding.get("review_receipt_sha256") == receipt_sha,
                       "SOURCE_SRT_REVIEW_RECEIPT_BINDING_MISMATCH",
                       repr(binding))

    def _check_review(self, body):
        events = self.lock.get("events") or {}
        verdict = VERDICT_RE.search(body)
        script_sha = REVIEW_SHA_RE.search(body)
        event = REVIEW_EVENT_RE.search(body)
        origin = REVIEW_ORIGIN_RE.search(body)
        recorder = RECORDED_BY_RE.search(body)
        self.check(bool(verdict and verdict.group(1) == "APPROVED"),
                   "REVIEW_NOT_APPROVED",
                   verdict.group(1) if verdict else "missing")
        self.check(bool(script_sha and script_sha.group(1)
                        == self.lock.get("script_sha256")),
                   "REVIEW_SCRIPT_SHA_MISMATCH",
                   script_sha.group(1) if script_sha else "missing")
        self.check(bool(event and event.group(1)
                        == events.get("review_event_id")),
                   "REVIEW_EVENT_MISMATCH",
                   event.group(1) if event else "missing")
        expected_reviewer = (self.lock.get("authority") or {}).get("reviewer")
        self.check(bool(origin and REVIEW_ORIGIN_TO_AUTHORITY.get(
                        origin.group(1)) == expected_reviewer),
                   "REVIEW_ORIGIN_MISMATCH",
                   origin.group(1) if origin else "missing")
        self.check(bool(recorder), "REVIEW_RECORDER_MISSING", "recorded_by")
        approval = self._load_json("user_approval") or {}
        if recorder:
            self.check(recorder.group(1) != approval.get("executor"),
                       "SELF_REVIEW_INVALID",
                       f"recorded_by={recorder.group(1)!r}")
        if origin and origin.group(1) == "codex_cli_external":
            reason = FALLBACK_REASON_RE.search(body)
            failure_path = FAILURE_PATH_RE.search(body)
            failure_sha = FAILURE_SHA_RE.search(body)
            self.check(bool(reason and reason.group(1) == "CLAUDE_CALL_FAILURE"),
                       "REVIEW_FALLBACK_POLICY_INVALID", "fallback_reason")
            self.check(bool(failure_path and failure_sha),
                       "REVIEW_FALLBACK_EVIDENCE_MISSING", "Claude failure")
            if failure_path and failure_sha:
                target = self._safe_path(
                    "claude_failure_report", failure_path.group(1))
                if target is not None:
                    valid = (target.is_file()
                             and sha256_of(target) == failure_sha.group(1))
                    self.check(valid, "REVIEW_FALLBACK_EVIDENCE_MISMATCH",
                               str(target))
                    if valid:
                        try:
                            failure = json.loads(target.read_text(encoding="utf-8"))
                        except Exception as exc:
                            self.fail("REVIEW_FALLBACK_EVIDENCE_INVALID", str(exc))
                        else:
                            self.check(
                                failure.get("schema")
                                == "politics-longform-review-fallback.v1"
                                and failure.get("status") == "CLAUDE_CALL_FAILED"
                                and failure.get("script_sha256")
                                == self.lock.get("script_sha256"),
                                "REVIEW_FALLBACK_EVIDENCE_INVALID",
                                repr(failure))
        for field in REQUIRED_REVIEW_ZERO_FIELDS:
            value = _review_int(body, field)
            self.check(value == 0, "REVIEW_UNRESOLVED_OR_DEFERRED",
                       f"{field}={value!r}")


def main():
    ap = argparse.ArgumentParser(description="110 script lock hard gate")
    ap.add_argument("--episode", default=os.environ.get("PL_EPISODE_DIR"),
                    help="episode directory (or PL_EPISODE_DIR)")
    ap.add_argument("--stage", choices=STAGES, help="downstream stage")
    ap.add_argument("--json", action="store_true", help="machine output")
    args = ap.parse_args()

    if not args.stage or not args.episode:
        print("BLOCKED: --stage and --episode/PL_EPISODE_DIR are required",
              file=sys.stderr)
        return 2

    gate = Gate(args.episode, args.stage)
    gate.run()
    if args.json:
        print(json.dumps(
            {"stage": args.stage, "episode": str(args.episode),
             "checks": gate.checks, "passed": not gate.fails,
             "failures": [{"code": code, "detail": detail}
                          for code, detail in gate.fails]},
            ensure_ascii=False, indent=1))
    elif gate.fails:
        print(f"BLOCKED stage={args.stage} failures={len(gate.fails)}")
        for code, detail in gate.fails:
            print(f"  {code}\n        {detail}")
    else:
        print(f"PASS stage={args.stage} checks={gate.checks}")
    return 1 if gate.fails else 0


if __name__ == "__main__":
    sys.exit(main())
