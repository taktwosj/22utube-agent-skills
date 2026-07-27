#!/usr/bin/env python3
"""초벌 대본 마크다운 파서.

GPT 는 산문을 쓴다. 엄격한 JSON 을 요구하면 cue 번호를 세다가 틀리고,
그 오류가 대본 오류로 둔갑한다. 그래서 산문은 자유롭게 두고 기계가 필요한
네 가지만 출처 줄 하나에서 받는다.

    어느 소스 · 어느 구간 · 무엇을 뺐나 · 원문 그대로인가

cue 번호는 선택이다. 타임코드만 있으면 SRT 에서 역산한다.
"""
from __future__ import annotations

import re

QUOTE_MODE = {"직접": "DIRECT", "간접": "INDIRECT", "요약": "SUMMARY"}

# 연속 영상에서 빼도 화면이 어긋나지 않는 것. 그 밖의 생략은 실제 컷이므로
# 블록을 나눠 선언해야 한다.
FILLER_SKIP_CLASSES = ("간투사", "중복발화", "비언어")

FM_RE = re.compile(r"(?s)\A---\s*\n(.*?)\n---\s*\n")
CH_RE = re.compile(r"^##\s+CHAPTER\s+(\d+)\s*(?:[-—]\s*(.*))?$")
NAR_RE = re.compile(r"^###\s*\[나레이션\]\s*$")
SRC_RE = re.compile(r"^###\s*\[원본\]\s*(.*)$")
GROUND_RE = re.compile(r"^근거:\s*(.+)$")
TC_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$")


class DraftFormatError(ValueError):
    """양식 위반. 내용 오류가 아니라 읽을 수 없다는 뜻이다."""


def _tc(token):
    m = TC_RE.match(token.strip())
    if not m:
        raise DraftFormatError(f"타임코드 형식 아님: {token!r}")
    h, mi, s, ms = m.groups()
    return (int(h or 0) * 3600 + int(mi) * 60 + int(s)
            + int((ms or "0").ljust(3, "0")) / 1000)


def _cue_list(token):
    """'414,417-419' -> [414, 417, 418, 419]"""
    out = []
    for part in token.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def _parse_source_line(rest, line_no):
    """`S05 | 11:23~20:07 | cue 412-468 | 생략 414,417 | 간투사 | 직접`"""
    fields = [f.strip() for f in rest.split("|")]
    if len(fields) < 2:
        raise DraftFormatError(f"{line_no}행: 출처 줄에 '|' 구분 항목이 없다")

    sid = fields[0]
    if not re.fullmatch(r"S\d{2,}", sid):
        raise DraftFormatError(f"{line_no}행: source_id 가 없거나 형식이 아니다 {sid!r}")

    seg = {"type": "SOURCE_VIDEO", "source_id": sid,
           "time_in": None, "time_out": None,
           "cue_from": None, "cue_to": None,
           "cues_skipped": [], "skip_class": None, "quote_mode": None}

    for f in fields[1:]:
        if "~" in f and not f.startswith(("cue", "생략")):
            a, b = f.split("~", 1)
            seg["time_in"], seg["time_out"] = _tc(a), _tc(b)
        elif f.startswith("cue"):
            rng = _cue_list(f[3:])
            seg["cue_from"], seg["cue_to"] = rng[0], rng[-1]
            # 'cue 1,3' 을 1-3 으로 뭉개면 신고 없는 cue 2 가 대조에 끼어든다.
            # 빈틈은 생략으로 신고해야 한다.
            gap = sorted(set(range(rng[0], rng[-1] + 1)) - set(rng))
            if gap:
                seg["cue_gap_unreported"] = gap
        elif f.startswith("생략"):
            seg["cues_skipped"] = _cue_list(f[2:])
        elif f in QUOTE_MODE:
            seg["quote_mode"] = QUOTE_MODE[f]
        elif f:
            seg["skip_class"] = f

    # 원본 블록은 화면에 뜰 발화 자막이다. 원문과 문자 대조가 가능해야 하므로
    # 직접만 허용한다. 간접·요약은 GPT 가 다시 쓴 문장이고, 그건 나레이션이다.
    # 여기서 간접을 허용하면 자막 fidelity 를 검증할 방법이 없어진다.
    if seg["quote_mode"] is None:
        raise DraftFormatError(
            f"{line_no}행: 인용 방식이 없다. 원본 블록은 '직접' 이어야 한다")
    if seg["quote_mode"] != "DIRECT":
        raise DraftFormatError(
            f"{line_no}행: 원본 블록은 '직접' 전용이다. 옮겨 쓴 문장이면 "
            "[나레이션] 블록으로 옮기고 근거로 이 구간을 지목해라")
    if seg["time_in"] is None and seg["cue_from"] is None:
        raise DraftFormatError(f"{line_no}행: 타임코드도 cue 범위도 없다")
    return seg


def parse_draft_md(text):
    """마크다운 초벌 대본을 검사 함수가 먹는 구조로 바꾼다."""
    fm = FM_RE.match(text)
    if not fm:
        raise DraftFormatError(
            "머리말이 없다. episode_id · source_packet_sha256 · "
            "narration_blocks · source_clips 를 --- 블록에 적어라")

    head = {}
    for line in fm.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            head[k.strip()] = v.strip()

    draft = {
        "episode_id": head.get("episode_id"),
        "source_packet_sha256": head.get("source_packet_sha256"),
        "declared_counts": {
            "narration_blocks": int(head.get("narration_blocks", 0)),
            "source_clips": int(head.get("source_clips", 0)),
        },
        "chapters": [],
    }

    body_from = text[:fm.end()].count("\n")
    chapter = None
    seg = None
    buf = []
    counters = {}

    def close_segment():
        nonlocal seg, buf
        if seg is None:
            return
        if seg["type"] == "SOURCE_VIDEO":
            # '>' 아닌 줄을 조용히 버리면 안 된다. 버려진 문장은 검증을
            # 통과하는데 확정 대본 파일에는 그대로 남는다. 아무도 대조하지
            # 않은 주장이 화면에 뜬다.
            stray = [l for l in buf
                     if l.strip() and not l.strip().startswith(">")]
            if stray:
                raise DraftFormatError(
                    f"{seg['segment_id']}: 원본 블록에 인용 아닌 줄이 있다 "
                    f"({stray[0].strip()[:40]!r}). 설명은 [나레이션] 으로 옮겨라")
            quoted = [l.strip()[1:].strip() for l in buf
                      if l.strip().startswith(">")]
            seg["text"] = " ".join(q for q in quoted if q).strip()
            if not seg["text"]:
                raise DraftFormatError(
                    f"{seg['segment_id']}: 원본 블록에 인용 본문이 없다")
        else:
            seg["text"] = "\n".join(
                l for l in buf if not GROUND_RE.match(l)).strip()
            if not seg["text"]:
                raise DraftFormatError(
                    f"{seg['segment_id']}: 나레이션 본문이 비어 있다")
        chapter["segments"].append(seg)
        seg, buf = None, []

    def new_id(kind):
        n = chapter["chapter_number"]
        counters.setdefault((n, kind), 0)
        counters[(n, kind)] += 1
        return f"C{n}-{kind}{counters[(n, kind)]:02d}"

    for offset, line in enumerate(text[fm.end():].splitlines(), body_from + 1):
        stripped = line.strip()

        m = CH_RE.match(stripped)
        if m:
            close_segment()
            chapter = {"chapter_number": int(m.group(1)),
                       "chapter_title": (m.group(2) or "").strip(),
                       "segments": []}
            draft["chapters"].append(chapter)
            continue

        if NAR_RE.match(stripped):
            close_segment()
            if chapter is None:
                raise DraftFormatError(f"{offset}행: CHAPTER 밖의 세그먼트")
            seg = {"type": "NARRATION", "grounding": [], "quote_mode": None,
                   "source_id": None, "cue_from": None, "cue_to": None,
                   "segment_id": new_id("N")}
            continue

        m = SRC_RE.match(stripped)
        if m:
            close_segment()
            if chapter is None:
                raise DraftFormatError(f"{offset}행: CHAPTER 밖의 세그먼트")
            seg = _parse_source_line(m.group(1), offset)
            seg["segment_id"] = new_id("S")
            continue

        if seg is None:
            continue

        m = GROUND_RE.match(stripped)
        if m and seg["type"] == "NARRATION":
            for ref in m.group(1).split(";"):
                parts = ref.split()
                if len(parts) < 2:
                    raise DraftFormatError(f"{offset}행: 근거 형식 오류 {ref!r}")
                rng = _cue_list(parts[1])
                seg["grounding"].append({"source_id": parts[0],
                                         "cue_from": rng[0], "cue_to": rng[-1]})
        buf.append(line)

    close_segment()

    # 빈 대본이 통과하면 안 된다. 챕터 0개 · 세그먼트 0개인 파일도
    # "위반 0건" 으로 보고돼 승인 대상이 될 수 있다.
    if not draft["chapters"]:
        raise DraftFormatError("CHAPTER 가 하나도 없다")
    for ch in draft["chapters"]:
        if not ch["segments"]:
            raise DraftFormatError(
                f"CHAPTER {ch['chapter_number']} 에 세그먼트가 없다")
    for key in ("episode_id", "source_packet_sha256"):
        if not draft.get(key) and key == "episode_id":
            raise DraftFormatError(f"머리말에 {key} 가 없다")
    total = sum(len(ch["segments"]) for ch in draft["chapters"])
    if total == 0:
        raise DraftFormatError("세그먼트가 하나도 없다")
    return draft


def backfill_cue_ranges(draft, packet):
    """cue 범위가 비면 타임코드로 채운다. 소스 밖 타임코드는 오류다."""
    index = {s["source_id"]: s["cues"] for s in packet.get("sources", [])}
    for ch in draft["chapters"]:
        for seg in ch["segments"]:
            if seg["type"] != "SOURCE_VIDEO":
                continue
            if seg["cue_from"] is not None:
                # 둘 다 있으면 대조한다. 명시 cue 가 역산을 건너뛰게만 하면
                # 타임코드가 딴 데를 가리켜도 아무도 모른다.
                if seg["time_in"] is None:
                    continue
                cues = index.get(seg["source_id"]) or []
                span = [c for c in cues
                        if seg["cue_from"] <= c["cue"] <= seg["cue_to"]]
                if span and (span[-1]["end"] <= seg["time_in"]
                             or span[0]["start"] >= seg["time_out"]):
                    raise DraftFormatError(
                        f"{seg['segment_id']}: cue {seg['cue_from']}-"
                        f"{seg['cue_to']} 와 타임코드 구간이 겹치지 않는다")
                continue
            cues = index.get(seg["source_id"])
            if not cues:
                raise DraftFormatError(
                    f"{seg['segment_id']}: 없는 source_id {seg['source_id']}")
            hit = [c["cue"] for c in cues
                   if c["end"] > seg["time_in"] and c["start"] < seg["time_out"]]
            if not hit:
                raise DraftFormatError(
                    f"{seg['segment_id']}: 타임코드가 {seg['source_id']} 범위 밖이다 "
                    f"({seg['time_in']:.1f}~{seg['time_out']:.1f}초)")
            seg["cue_from"], seg["cue_to"] = hit[0], hit[-1]
    return draft


QUOTE_CHARS = re.compile(r"[\"'“”‘’]")


def check_narration_has_no_quotes(draft, packet=None):
    """나레이션은 GPT 가 쓴 문장이다. 따옴표를 쓰면 인용으로 읽힌다.

    직전 회차 최악의 지적이 정확히 이것이었다 — 다듬은 문장을 따옴표에 넣어
    직접인용처럼 보이게 했다. 인용하고 싶으면 [원본] 블록을 써라. 그러면
    원문과 자동 대조된다.
    """
    violations = []
    for ch in draft["chapters"]:
        for seg in ch["segments"]:
            if seg["type"] != "NARRATION":
                continue
            if QUOTE_CHARS.search(seg.get("text") or ""):
                violations.append(
                    f"{seg['segment_id']}: 나레이션에 따옴표가 있다. "
                    "인용이면 [원본] 블록으로 옮겨 원문 대조를 받아라")
    return violations


def check_skip_classification(draft, packet=None):
    """생략이 간투사 제거인지 실제 영상 컷인지 구분한다.

    연속 영상인데 발화 cue 만 빼면 자막과 화면이 어긋난다. 실제로 자른
    것이면 원본 블록을 둘로 나눠 선언해야 한다.
    """
    violations = []
    for ch in draft["chapters"]:
        for seg in ch["segments"]:
            gap = set(seg.get("cue_gap_unreported") or [])
            undeclared = sorted(gap - set(seg.get("cues_skipped") or []))
            if undeclared:
                violations.append(
                    f"{seg['segment_id']}: cue 목록에 빈틈이 있는데 생략으로 "
                    f"신고하지 않았다 {undeclared}")
            if not seg.get("cues_skipped"):
                continue
            cls = seg.get("skip_class")
            if not cls:
                violations.append(
                    f"{seg['segment_id']}: 생략 사유가 없다. "
                    f"허용 분류 {' / '.join(FILLER_SKIP_CLASSES)}")
            elif cls not in FILLER_SKIP_CLASSES:
                violations.append(
                    f"{seg['segment_id']}: '{cls}' 는 실제 영상 컷이다. "
                    "원본 블록을 구간별로 나눠 선언해라")
    return violations
