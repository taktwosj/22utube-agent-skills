"""Canonical 110 script-lock fixture for 111 tests."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_valid_lock(ep):
    ep = Path(ep)
    (ep / "20_script").mkdir(parents=True, exist_ok=True)
    (ep / "90_reports").mkdir(parents=True, exist_ok=True)

    final_script = ep / "20_script" / "master_script_final.md"
    locked_script = ep / "20_script" / "master_script_locked.md"
    script_body = "# 확정 대본\n\n검증된 본문입니다.\n"
    final_script.write_text(script_body, encoding="utf-8")
    locked_script.write_text(script_body, encoding="utf-8")

    packet = ep / "20_script" / "source_packet_v1.json"
    packet.write_text('{"sources": []}\n', encoding="utf-8")
    script_sha = digest(locked_script)

    report = ep / "90_reports" / "verification_report_v1.json"
    report.write_text(json.dumps({
        "schema": "politics-longform-draft-verification.v1",
        "script_sha256": script_sha,
        "source_packet_sha256_actual": digest(packet),
        "total_violations": 0,
        "checks": {},
    }, ensure_ascii=False), encoding="utf-8")

    review = ep / "20_script" / "claude_review_v1.md"
    review.write_text(
        "verdict: APPROVED\n"
        f"script_sha256: {script_sha}\n"
        "review_origin: claude_external\n"
        "recorded_by: CLAUDE\n"
        "claude_review_event_id: REV-TEST-001\n",
        encoding="utf-8")

    approval = ep / "20_script" / "user_approval.json"
    approval.write_text(json.dumps({
        "approved": True,
        "approved_script_path": "20_script/master_script_final.md",
        "approved_script_sha256": script_sha,
        "claude_review_path": "20_script/claude_review_v1.md",
        "claude_review_sha256": digest(review),
        "verification_report_path": "90_reports/verification_report_v1.json",
        "verification_report_sha256": digest(report),
        "user_approval_origin": "user_message",
        "user_approval_event_id": "APP-TEST-001",
        "claude_review_event_id": "REV-TEST-001",
        "executor": "CODEX",
    }, ensure_ascii=False), encoding="utf-8")

    def entry(path):
        return {"path": Path(path).relative_to(ep).as_posix(),
                "sha256": digest(path)}

    lock = {
        "schema": "politics-longform-script-lock.v1",
        "episode_id": ep.name,
        "status": "SCRIPT_LOCKED",
        "lock_version": 1,
        "locked_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "produced_by": "110-politics-longform-script",
        "script_sha256": script_sha,
        "locked_script": "20_script/master_script_locked.md",
        "evidence": {
            "approved_script": entry(final_script),
            "source_packet": entry(packet),
            "verification_report": entry(report),
            "independent_review": entry(review),
            "user_approval": entry(approval),
        },
        "events": {
            "review_event_id": "REV-TEST-001",
            "claude_review_event_id": "REV-TEST-001",
            "user_approval_event_id": "APP-TEST-001",
        },
        "authority": {
            "drafter": "PROJECT_GPT",
            "reviewer": "CLAUDE",
            "final_lock": "USER",
        },
        "next_stage": "111-politics-longform-voice-srt",
    }
    (ep / "20_script" / "script_lock.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
    return lock


def rewrite_lock(ep, lock):
    (Path(ep) / "20_script" / "script_lock.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2), encoding="utf-8")
