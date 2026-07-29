#!/usr/bin/env python3
"""확정 대본 잠금 게이트.

세 증거가 전부 있고, 넷이 같은 대본을 가리키고, 검수자와 실행자가 다를 때만
잠금을 쓴다.

    기계 검증 0건        verification_report_v*.json
    독립 최종 확인        Claude 우선, 호출 실패 시 Codex CLI 대체
    사용자 승인          user_approval.json

세 가지 원칙.

    SHA 결합       옛 검수로 새 대본을 잠글 수 없다
    경로 지목      승인서가 파일을 직접 가리킨다. 최신본 자동 선택 없음
    이름 순서      잠금 전 파일은 final, 게이트가 통과시켜야 locked 가 된다

출처 필드는 위조를 불가능하게 만들지 못한다. 파일을 쓸 수 있는 쪽은 필드도
쓸 수 있다. 하는 일은 비용을 올리고 누가 썼는지 귀속시키는 것이다.

    py -3.14 gate_script_lock.py --episode <경로> [--write]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
EPISODE_ID_RE = re.compile(r"^PL_[0-9]{8}_[a-z0-9_]+$")
ACCEPTED_VERDICT = "APPROVED"
REVIEW_ORIGIN_TO_AUTHORITY = {
    "claude_external": "CLAUDE",
    "codex_cli_external": "CODEX_CLI",
}

VERIFICATION_SCHEMA = "politics-longform-draft-verification.v1"
# verify_draft.CHECKS 와 같아야 한다. 하나라도 빠진 보고서는 전량 검증이
# 돌지 않았다는 뜻이다.
REQUIRED_CHECKS = ("source_reference", "quote_fidelity", "quote_mode_marks",
                   "forbidden_display_marks", "allegation_framing",
                   "declared_counts", "packet_binding", "narration_quotes",
                   "skip_classification")

# 승인 대상은 final. locked 는 이 게이트만 만든다.
APPROVAL_TARGET = "master_script_final.md"
LOCKED_OUTPUT = "master_script_locked.md"
SOURCE_PACKET_RELPATH = Path("20_script") / "source_packet_v1.json"

FIELD = {
    "script": ("approved_script_path", "approved_script_sha256"),
    "review": ("claude_review_path", "claude_review_sha256"),
    "report": ("verification_report_path", "verification_report_sha256"),
}


def _line(name):
    return re.compile(rf"(?m)^{name}:\s*(\S+)\s*$")


VERDICT_RE = _line("verdict")
REVIEW_SHA_RE = re.compile(r"(?m)^script_sha256:\s*([0-9a-f]{64})\s*$")
ORIGIN_RE = _line("review_origin")
RECORDER_RE = _line("recorded_by")
REVIEW_EVENT_RE = _line("claude_review_event_id")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(ep: Path):
    """승인서가 지목한 파일만 모은다.

    파일명으로 최신본을 고르지 않는다. v2 를 자동 선택하면 아무도 승인하지
    않은 v99 를 나중에 떨어뜨려 잠금을 바꿔칠 수 있다.

    범위를 벗어난 경로는 조용히 넘기지 않는다. 넘기고 다른 파일을 고르면
    그게 곧 fallback 이고, fallback 이 있으면 경로 지목이 무의미해진다.
    """
    files = {"script": None, "report": None, "review": None,
             "approval": None, "source_packet": None}
    errors = []

    approval_path = ep / "20_script" / "user_approval.json"
    if not approval_path.is_file():
        return files, errors
    files["approval"] = approval_path

    source_packet = ep / SOURCE_PACKET_RELPATH
    if source_packet.is_file():
        files["source_packet"] = source_packet

    try:
        ap = json.loads(approval_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"FAIL_APPROVAL_UNREADABLE: user_approval.json {exc}")
        return files, errors

    root = ep.resolve()
    for key, (path_field, _) in FIELD.items():
        rel = ap.get(path_field)
        if not rel:
            continue
        p = (ep / rel).resolve()
        if root != p and root not in p.parents:
            errors.append(
                f"FAIL_APPROVAL_PATH_OUT_OF_SCOPE: {path_field}={rel} 가 "
                "에피소드 밖을 가리킨다")
            continue
        if p.is_file():
            files[key] = p
        else:
            errors.append(f"FAIL_APPROVAL_PATH_MISSING: {path_field}={rel}")
    return files, errors


def check_pinned_hashes(approval, files):
    """지목한 경로의 실제 내용이 승인 시점과 같은가."""
    v = []
    for key, (path_field, sha_field) in FIELD.items():
        if files[key] is None:
            continue
        want = approval.get(sha_field)
        if not want:
            v.append(f"FAIL_STALE_REVIEW_SHA: 승인서에 {sha_field} 없음")
            continue
        got = sha256_of(files[key])
        if got != want:
            v.append(f"FAIL_STALE_REVIEW_SHA: {path_field} 의 내용이 승인 이후 "
                     f"바뀌었다 ({got[:12]} != {want[:12]})")
    return v


def check_provenance(approval, files):
    """자기승인 차단.

    두 사건을 따로 기록하고, 승인서가 검수 사건을 참조하게 한다. 하나의
    event_id 를 공유하면 두 사건인지 한 사건인지 구분되지 않는다.
    """
    v = []
    if approval.get("user_approval_origin") != "user_message":
        v.append("FAIL_SELF_APPROVAL: user_approval_origin 이 "
                 "user_message 가 아니다")
    if not approval.get("user_approval_event_id"):
        v.append("FAIL_SELF_APPROVAL: user_approval_event_id 없음")
    if not approval.get("claude_review_event_id"):
        v.append("FAIL_SELF_APPROVAL: 승인서가 검수 사건을 참조하지 않는다")
    if (approval.get("user_approval_event_id")
            and approval.get("user_approval_event_id")
            == approval.get("claude_review_event_id")):
        v.append("FAIL_SELF_APPROVAL: 검수와 승인이 같은 사건 id 다")

    if files["review"] is None:
        return v
    body = files["review"].read_text(encoding="utf-8")
    origin = ORIGIN_RE.search(body)
    recorder = RECORDER_RE.search(body)
    event = REVIEW_EVENT_RE.search(body)
    if (not origin
            or origin.group(1) not in REVIEW_ORIGIN_TO_AUTHORITY):
        v.append("FAIL_SELF_APPROVAL: 검수본 review_origin 이 "
                 "허용된 외부 검수자가 아니다")
    if not recorder:
        v.append("FAIL_SELF_APPROVAL: 검수본에 recorded_by 없음")
    elif recorder.group(1) == approval.get("executor"):
        v.append(f"FAIL_SELF_APPROVAL: 검수자와 실행자가 같다 "
                 f"({recorder.group(1)})")
    if not event:
        v.append("FAIL_SELF_APPROVAL: 검수본에 claude_review_event_id 없음")
    elif event.group(1) != approval.get("claude_review_event_id"):
        v.append("FAIL_SELF_APPROVAL: 검수본과 승인서의 검수 사건 id 가 다르다")
    return v


def evaluate(files, path_errors=(), script_sha=None):
    """(위반 목록, SHA 표). 파일을 쓰지 않는다."""
    v = list(path_errors)
    shas = {}

    if files["approval"] is None:
        return v + ["WAIT_USER_SCRIPT_APPROVAL: user_approval.json 없음"], shas
    approval = json.loads(files["approval"].read_text(encoding="utf-8"))

    if files["script"] is None:
        v.append(f"WAIT_SCRIPT_NOT_FINALIZED: {APPROVAL_TARGET} 없음")
    else:
        if files["script"].name != APPROVAL_TARGET:
            v.append(f"FAIL_PREMATURE_LOCK_NAME: 승인 대상은 "
                     f"{APPROVAL_TARGET} 다 ({files['script'].name})")
        shas["script"] = script_sha or sha256_of(files["script"])

    if files["report"] is None:
        v.append("WAIT_MACHINE_VERIFICATION: verification_report 없음")
    else:
        rep = json.loads(files["report"].read_text(encoding="utf-8"))
        # False == 0 이라 truthiness 로 보면 {"total_violations": false} 가
        # 통과한다. 형식까지 못박는다.
        n = rep.get("total_violations")
        if not isinstance(n, int) or isinstance(n, bool):
            v.append(f"FAIL_VERIFICATION_REPORT_SHAPE: total_violations 가 "
                     f"정수가 아니다 ({n!r})")
        elif n != 0:
            v.append(f"WAIT_DRAFT_VERIFICATION: 위반 {n}건")

        # 두 필드만 있는 가짜 보고서를 막는다. 실제 검증이 돌았다는 증거는
        # 검사 항목이 전부 실려 있다는 것이다.
        if rep.get("schema") != VERIFICATION_SCHEMA:
            v.append(f"FAIL_VERIFICATION_REPORT_SHAPE: schema 가 "
                     f"{VERIFICATION_SCHEMA} 가 아니다")
        checks = rep.get("checks")
        if not isinstance(checks, dict):
            v.append("FAIL_VERIFICATION_REPORT_SHAPE: checks 가 없다")
        else:
            missing = sorted(set(REQUIRED_CHECKS) - set(checks))
            if missing:
                v.append(f"FAIL_VERIFICATION_REPORT_SHAPE: 검사 항목 누락 "
                         f"{missing}")
            if isinstance(n, int) and not isinstance(n, bool):
                counted = sum(c.get("count", 0) for c in checks.values()
                              if isinstance(c, dict))
                if counted != n:
                    v.append(f"FAIL_VERIFICATION_REPORT_SHAPE: 합계 불일치 "
                             f"({counted} != {n})")
        shas["report"] = rep.get("script_sha256")
        if files["source_packet"] is None:
            v.append("BLOCKED_SOURCE_PACKET_NOT_BUILT: source_packet_v1.json 없음")
        else:
            packet_sha = sha256_of(files["source_packet"])
            if rep.get("source_packet_sha256_actual") != packet_sha:
                v.append("FAIL_STALE_REVIEW_SHA: verification_report 의 "
                         "source_packet_sha256_actual 이 실제 패킷과 다르다")

    if files["review"] is None:
        v.append("WAIT_CLAUDE_REVIEW: claude_review 없음")
    else:
        body = files["review"].read_text(encoding="utf-8")
        m = VERDICT_RE.search(body)
        if not m:
            v.append("WAIT_CLAUDE_REVIEW: verdict 줄이 없다")
        elif m.group(1) != ACCEPTED_VERDICT:
            v.append(f"WAIT_CLAUDE_REVIEW: verdict={m.group(1)}")
        s = REVIEW_SHA_RE.search(body)
        shas["review"] = s.group(1) if s else None

    if approval.get("approved") is not True:
        v.append("WAIT_USER_SCRIPT_APPROVAL: approved 가 true 가 아니다")
    shas["approval"] = approval.get("approved_script_sha256")

    present = {k: s for k, s in shas.items() if s}
    for k, s in present.items():
        if not SHA_RE.fullmatch(str(s)):
            v.append(f"FAIL_STALE_REVIEW_SHA: {k} 의 script_sha256 형식 오류")
    if len(set(present.values())) > 1:
        detail = ", ".join(f"{k}={str(s)[:12]}"
                           for k, s in sorted(present.items()))
        v.append(f"FAIL_STALE_REVIEW_SHA: 대상 대본이 서로 다르다 ({detail}). "
                 "옛 검수로 수정본을 잠글 수 없다")
    for k in ("script", "report", "review"):
        if files[k] is not None and not shas.get(k):
            v.append(f"FAIL_STALE_REVIEW_SHA: {k} 에 script_sha256 이 없다")

    v.extend(check_pinned_hashes(approval, files))
    v.extend(check_provenance(approval, files))
    return v, shas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default=os.environ.get("PL_EPISODE_DIR"))
    ap.add_argument("--write", action="store_true",
                    help=f"통과하면 {LOCKED_OUTPUT} 와 script_lock.json 을 쓴다")
    args = ap.parse_args()
    if not args.episode:
        print("BLOCKED: --episode 또는 PL_EPISODE_DIR 가 필요하다",
              file=sys.stderr)
        return 2

    ep = Path(args.episode)
    if not EPISODE_ID_RE.fullmatch(ep.name):
        print(f"BLOCKED: episode_id 형식 오류 {ep.name!r}", file=sys.stderr)
        return 2
    files, path_errors = collect(ep)
    violations, shas = evaluate(files, path_errors)

    for k, p in files.items():
        print(f"{k:10} {p if p else '없음'}")
    if violations:
        print("\nBLOCKED", file=sys.stderr)
        for x in violations:
            print("  " + x, file=sys.stderr)
        return 1

    approval = json.loads(files["approval"].read_text(encoding="utf-8"))
    review_body = files["review"].read_text(encoding="utf-8")
    review_origin = ORIGIN_RE.search(review_body)
    reviewer_authority = REVIEW_ORIGIN_TO_AUTHORITY.get(
        review_origin.group(1) if review_origin else "", "UNKNOWN")
    def evidence(path):
        return {"path": path.relative_to(ep).as_posix(),
                "sha256": sha256_of(path)}

    lock = {
        "schema": "politics-longform-script-lock.v1",
        "episode_id": ep.name,
        "status": "SCRIPT_LOCKED",
        "lock_version": 1,
        "locked_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "produced_by": "110-politics-longform-script",
        "script_sha256": shas["script"],
        "locked_script": f"20_script/{LOCKED_OUTPUT}",
        "evidence": {
            "approved_script": evidence(files["script"]),
            "source_packet": evidence(files["source_packet"]),
            "verification_report": evidence(files["report"]),
            "independent_review": evidence(files["review"]),
            "user_approval": evidence(files["approval"]),
        },
        "events": {
            "review_event_id": approval.get("claude_review_event_id"),
            "claude_review_event_id": approval.get("claude_review_event_id"),
            "user_approval_event_id": approval.get("user_approval_event_id"),
        },
        "authority": {"drafter": "PROJECT_GPT", "reviewer": reviewer_authority,
                      "final_lock": "USER"},
        "next_stage": "111-politics-longform-voice-srt",
    }
    print(f"\nPASS  script_sha256 {shas['script']}")
    if args.write:
        locked = ep / "20_script" / LOCKED_OUTPUT
        locked.write_bytes(files["script"].read_bytes())
        out = ep / "20_script" / "script_lock.json"
        out.write_text(json.dumps(lock, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print(f"WROTE {locked}\nWROTE {out}")
    else:
        print("(--write 없이 실행. 잠금 파일을 쓰지 않았다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
