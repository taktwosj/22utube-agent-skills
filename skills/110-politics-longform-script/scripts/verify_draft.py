#!/usr/bin/env python3
"""초벌 대본을 자막 원문과 대조한다.

검사 로직은 전부 (draft, packet) 를 받는 순수 함수다. 파일을 직접 읽지
않으므로 합성 픽스처와 실문서 양쪽으로 시험할 수 있다.

    py -3.14 verify_draft.py --episode <에피소드 경로>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import draft_md


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

QUOTE_RE = re.compile(r"[\"'“”‘’]")
ASR_SPEAKER_MARK_RE = re.compile(r"(?:^|\s)(?:>>|<<)(?=\s|$)")
FORBIDDEN_DISPLAY_MARKS = (">>", "<<", "·")

# 근거 없이 쓰면 의혹을 사실로 바꾸는 표현. 어간으로 둔다 --
# '드러났다' 로 고정하면 '드러났습니다' 가 빠져나간다.
#
# 이 목록은 완전하지 않다. 한국어 확정 서술은 열린 집합이라 열거로는 다
# 못 막는다. 기계는 흔한 형태를 걸러내고, 나머지는 사람 검수가 본다.
# 목록을 완전하다고 믿는 순간 사람 검수가 느슨해진다.
FACT_ASSERTION = (
    "드러났", "밝혀졌", "확인됐", "확인되었", "판명됐", "판명되었",
    "입증됐", "입증되었", "적발됐", "적발되었", "들통났",
    "사실이다", "사실입니다", "사실로", "사실이었",
    "밝혀진", "드러난", "확인된", "판명된",
    "한 것으로 나타났", "임이 확인", "임이 드러",
)
# 누가 말했는지를 밝히는 표현. '의혹' 은 여기 넣지 않는다 --
# '의혹이 사실로 드러났습니다' 가 통과해버린다. 주어가 있어야 주장이다.
ATTRIBUTION = (
    "주장", "말했", "밝혔", "다고 했", "제기", "라는 지적", "전했",
    "라고 봤", "혐의를 받",
)

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def iter_segments(draft):
    for ch in draft.get("chapters", []):
        for seg in ch.get("segments", []):
            yield ch, seg


def cue_index(packet):
    return {s["source_id"]: {c["cue"]: c for c in s["cues"]}
            for s in packet.get("sources", [])}


def normalize(text):
    """비발화 화자 표식과 공백만 정규화한다."""
    text = ASR_SPEAKER_MARK_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def check_forbidden_display_marks(draft, packet=None):
    """화면용 대본에 ASR 화자표식과 가운데점을 남기지 않는다."""
    violations = []
    for _, seg in iter_segments(draft):
        text = seg.get("text") or ""
        hits = [mark for mark in FORBIDDEN_DISPLAY_MARKS if mark in text]
        if hits:
            violations.append(
                f"{seg.get('segment_id')}: 금지 표시 {' '.join(hits)}")
    return violations


def check_source_references(draft, packet):
    """참조한 source_id 와 cue 범위가 실재하는가."""
    idx = cue_index(packet)
    violations = []
    for _, seg in iter_segments(draft):
        refs = []
        if seg.get("type") == "SOURCE_VIDEO":
            refs.append((seg.get("source_id"), seg.get("cue_from"),
                         seg.get("cue_to")))
        for g in seg.get("grounding") or []:
            refs.append((g.get("source_id"), g.get("cue_from"),
                         g.get("cue_to")))
        for sid, a, b in refs:
            sidname = seg.get("segment_id")
            if sid is None:
                violations.append(f"{sidname}: source_id 없음")
                continue
            if sid not in idx:
                violations.append(f"{sidname}: 없는 source_id {sid}")
                continue
            if a is None or b is None:
                violations.append(f"{sidname}: cue 범위 없음 ({sid})")
                continue
            if a > b:
                violations.append(f"{sidname}: cue 역전 {a}>{b} ({sid})")
                continue
            for c in (a, b):
                if c not in idx[sid]:
                    violations.append(
                        f"{sidname}: cue {c} 가 {sid} 범위 밖 "
                        f"(1~{len(idx[sid])})")
    return violations


def check_quote_fidelity(draft, packet):
    """DIRECT 인용이 원문과 문자 단위로 같은가."""
    idx = cue_index(packet)
    violations = []
    for _, seg in iter_segments(draft):
        if seg.get("quote_mode") != "DIRECT":
            continue
        sid = seg.get("source_id")
        a, b = seg.get("cue_from"), seg.get("cue_to")
        name = seg.get("segment_id")
        if sid not in idx or a is None or b is None:
            continue          # 참조 검사에서 이미 잡힌다
        # 신고된 생략은 빼고 대조한다. 안 빼면 간투사 제거가 전부
        # 불일치로 잡혀 거짓 양성이 쏟아진다.
        skipped = set(seg.get("cues_skipped") or [])
        cues = [idx[sid][c] for c in range(a, b + 1)
                if c in idx[sid] and c not in skipped]
        original = normalize(" ".join(c["text"] for c in cues))
        drafted = normalize(seg.get("text"))
        if drafted != original:
            violations.append(
                f"{name}: DIRECT 불일치\n"
                f"      원문 {original[:120]}\n"
                f"      대본 {drafted[:120]}")
    return violations


def check_quote_mode_marks(draft, packet=None):
    """INDIRECT·SUMMARY 에 따옴표를 쓰지 않았는가."""
    violations = []
    for _, seg in iter_segments(draft):
        mode = seg.get("quote_mode")
        if mode in (None, "DIRECT"):
            continue
        if QUOTE_RE.search(seg.get("text") or ""):
            violations.append(
                f"{seg.get('segment_id')}: {mode} 인데 따옴표가 있다. "
                "다듬은 문장에 따옴표를 남기면 직접인용으로 읽힌다")
    return violations


def check_allegation_framing(draft, packet):
    """의혹 사안을 확정 서술로 쓰지 않았는가."""
    # 빈 목록을 조용히 통과시키면 패킷에서 한 줄만 지워 법적 위험 게이트를
    # 통째로 끌 수 있다. 없으면 없다고 명시해야 한다.
    if "allegation_terms" not in packet:
        return ["source_packet 에 allegation_terms 가 없다. "
                "해당 없으면 allegation_terms_reviewed 로 명시해라"]
    terms = packet.get("allegation_terms") or []
    if not terms and not packet.get("allegation_terms_reviewed"):
        return ["allegation_terms 가 비어 있다. 의혹 사안이 없다면 "
                "allegation_terms_reviewed: true 로 확인 사실을 남겨라"]
    violations = []
    for _, seg in iter_segments(draft):
        if seg.get("type") == "SOURCE_VIDEO":
            continue          # 발화 인용은 화자의 말이다
        for sent in SENT_SPLIT.split(seg.get("text") or ""):
            if not any(t in sent for t in terms):
                continue
            hit = [v for v in FACT_ASSERTION if v in sent]
            if hit and not any(a in sent for a in ATTRIBUTION):
                violations.append(
                    f"{seg.get('segment_id')}: 의혹을 확정 서술로 씀 "
                    f"({', '.join(hit)}) -- {sent.strip()[:90]}")
    return violations


def check_declared_counts(draft, packet=None):
    """선언한 개수와 실제 세그먼트 수가 맞는가."""
    dec = draft.get("declared_counts") or {}
    if not dec:
        return ["declared_counts 없음"]
    n = sum(1 for _, s in iter_segments(draft) if s.get("type") == "NARRATION")
    c = sum(1 for _, s in iter_segments(draft)
            if s.get("type") == "SOURCE_VIDEO")
    v = []
    if dec.get("narration_blocks") != n:
        v.append(f"나레이션 선언 {dec.get('narration_blocks')} != 실제 {n}")
    if dec.get("source_clips") != c:
        v.append(f"원본 클립 선언 {dec.get('source_clips')} != 실제 {c}")
    return v


def check_packet_binding(draft, packet):
    """어느 자막 묶음을 보고 썼는지 지문이 맞는가.

    선언만 있고 대조하지 않으면 아무 값이나 적어도 통과한다. 실제 패킷
    SHA 를 packet 에 심어 넘기면 여기서 비교한다.
    """
    want = draft.get("source_packet_sha256")
    if not want:
        return ["source_packet_sha256 없음. 대본이 어느 자막을 봤는지 알 수 없다"]
    if not re.fullmatch(r"[0-9a-f]{64}", str(want)):
        return [f"source_packet_sha256 형식 오류: {want!r}"]
    actual = packet.get("_actual_sha256")
    if actual and actual != want:
        return [f"대본이 다른 자막 묶음을 보고 쓰였다 "
                f"({want[:12]} != {actual[:12]})"]
    return []


CHECKS = (
    ("source_reference", check_source_references, "FAIL_SOURCE_REFERENCE_INVALID"),
    ("quote_fidelity", check_quote_fidelity, "FAIL_QUOTE_FIDELITY"),
    ("quote_mode_marks", check_quote_mode_marks, "FAIL_QUOTE_FIDELITY"),
    ("forbidden_display_marks", check_forbidden_display_marks,
     "FAIL_FORBIDDEN_SCRIPT_MARK"),
    ("allegation_framing", check_allegation_framing,
     "FAIL_ALLEGATION_STATED_AS_FACT"),
    ("declared_counts", check_declared_counts, "WAIT_DRAFT_VERIFICATION"),
    ("packet_binding", check_packet_binding, "WAIT_DRAFT_VERIFICATION"),
    ("narration_quotes", draft_md.check_narration_has_no_quotes,
     "FAIL_QUOTE_FIDELITY"),
    ("skip_classification", draft_md.check_skip_classification,
     "FAIL_SKIP_NOT_CLASSIFIED"),
)


def run_checks(draft, packet):
    report = {}
    for name, fn, code in CHECKS:
        v = fn(draft, packet)
        report[name] = {"violations": v, "count": len(v),
                        "failure_code": code if v else None}
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default=os.environ.get("PL_EPISODE_DIR"))
    ap.add_argument("--draft", default="script_draft_v1.md",
                    help="20_script 안의 초벌 대본 파일명")
    args = ap.parse_args()
    if not args.episode:
        print("BLOCKED: --episode 또는 PL_EPISODE_DIR 가 필요하다",
              file=sys.stderr)
        return 2

    ep = Path(args.episode)
    dpath = ep / "20_script" / args.draft
    ppath = ep / "20_script" / "source_packet_v1.json"
    for p in (dpath, ppath):
        if not p.is_file():
            print(f"BLOCKED: 없음 {p}", file=sys.stderr)
            return 2

    packet = json.loads(ppath.read_text(encoding="utf-8"))
    packet["_actual_sha256"] = sha256_of(ppath)
    try:
        draft = draft_md.parse_draft_md(dpath.read_text(encoding="utf-8"))
        draft_md.backfill_cue_ranges(draft, packet)
    except draft_md.DraftFormatError as exc:
        # 양식 위반은 내용 검사 이전 문제다. 여기서 멈추지 않으면 절반만
        # 읽힌 대본을 검사하고 "위반 0건" 이라고 보고하게 된다.
        print(f"FAIL_DRAFT_FORMAT: {exc}", file=sys.stderr)
        return 1

    report = run_checks(draft, packet)
    total = sum(r["count"] for r in report.values())

    out = {
        "schema": "politics-longform-draft-verification.v1",
        "episode_id": draft.get("episode_id"),
        # 잠금 게이트가 이 값으로 "어느 대본을 검증했는가" 를 대조한다.
        "script_sha256": sha256_of(dpath),
        "draft_file": f"20_script/{args.draft}",
        "source_packet_sha256_declared": draft.get("source_packet_sha256"),
        "source_packet_sha256_actual": sha256_of(ppath),
        "total_violations": total,
        "status": "PASS" if total == 0 else "WAIT_DRAFT_VERIFICATION",
        "checks": report,
    }
    rdir = ep / "90_reports"
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "verification_report_v1.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    for name, r in report.items():
        print(f"{name:20} {r['count']:>3}건 {r['failure_code'] or 'OK'}")
        for v in r["violations"][:8]:
            print("    " + v)
    print(f"\n총 {total}건 -> {out['status']}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
