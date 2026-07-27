#!/usr/bin/env python3
"""110 스킬 계약 테스트.

검사가 지금 상태를 통과시키는지가 아니라, 위반을 실제로 잡는지를 본다.
각 검사마다 통과 픽스처와 위반 픽스처를 짝으로 둔다.
"""
from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import verify_draft as vd                                    # noqa: E402
import build_source_packet as bsp                            # noqa: E402

DOCS = [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md"))
CAPCUT_RE = re.compile(r"CapCut|캡컷", re.I)

REQUIRED_ANCHORS = {
    "SKILL.md": (
        r"(?m)^CapCut lane\(119\) = OUT_OF_SCOPE\s*$",
        r"(?m)^KEEP_UNCHANGED = [A-Za-z]:[\\/]\S*119-politics-longform-capcut\s*$",
        r"(?m)^KEEP_UNCHANGED = [A-Za-z]:[\\/]\S*000-politics-longform\s*$",
        r"(?m)^MODIFY_119_OR_ITS_WORKTREE = FORBIDDEN\s*$",
        r"(?m)^MODIFY_000_OR_ITS_WORKTREE = FORBIDDEN\s*$",
        r"(?m)^NEXT_STAGE = 111-politics-longform-voice-srt\s*$",
        r"FAIL_CAPCUT_DEPENDENCY_DETECTED",
    ),
}


RULE_SECTIONS = ("Lane 경계", "금지 산출물", "권위 분담")
RULE_PHRASES = ("OUT_OF_SCOPE", "FORBIDDEN", "KEEP_UNCHANGED", "금지",
                "않는다", "아니다", "FAIL_")


def iter_blocks(text):
    """(시작 줄, 문단, 상위 섹션). 제목은 문단에서 빠지므로 따로 물고 간다.

    빈 줄로만 자르면 '## 금지 산출물' 제목이 본문과 분리돼 금지 문맥이
    사라진다. 실제로 이 테스트가 처음 잡은 것이 그 경우였다.
    """
    section, buf, start = "", [], 1
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            if buf:
                yield start, "\n".join(buf), section
                buf = []
            section = line.lstrip("# ").strip()
            continue
        if not line.strip():
            if buf:
                yield start, "\n".join(buf), section
                buf = []
            continue
        if not buf:
            start = line_no
        buf.append(line)
    if buf:
        yield start, "\n".join(buf), section


def in_rule_context(block, section):
    return (any(name in section for name in RULE_SECTIONS)
            or any(p in block for p in RULE_PHRASES))


def anchors(text, doc_name):
    return [f"{doc_name}: 앵커 소실 {p}"
            for p in REQUIRED_ANCHORS.get(doc_name, ())
            if not re.search(p, text)]


PACKET = {
    "allegation_terms": ["신천지", "의혹"],
    "sources": [{
        "source_id": "S02",
        "cues": [
            {"cue": 1, "start": 0.0, "end": 2.0, "text": "제가 그때"},
            {"cue": 2, "start": 2.0, "end": 5.0,
             "text": "실패로 끝날 거라고 봐요"},
            {"cue": 3, "start": 5.0, "end": 8.0, "text": "그래서 반대했습니다"},
        ],
    }],
}

DRAFT = {
    "episode_id": "TEST",
    "source_packet_sha256": "0" * 64,
    "declared_counts": {"narration_blocks": 1, "source_clips": 1},
    "chapters": [{
        "chapter_number": 1,
        "segments": [
            {"segment_id": "C1-N01", "type": "NARRATION",
             "text": "신천지 관련 의혹이 제기됐습니다.",
             "grounding": [{"source_id": "S02", "cue_from": 1, "cue_to": 3,
                            "quote_mode": "SUMMARY"}]},
            {"segment_id": "C1-S01", "type": "SOURCE_VIDEO",
             "source_id": "S02", "cue_from": 2, "cue_to": 2,
             "quote_mode": "DIRECT", "text": "실패로 끝날 거라고 봐요"},
        ],
    }],
}


def mutate(**seg_patch):
    """세그먼트 하나를 고친 대본 사본을 낸다."""
    d = copy.deepcopy(DRAFT)
    target = seg_patch.pop("_target", 1)
    d["chapters"][0]["segments"][target].update(seg_patch)
    return d


class TestBoundaryDeclarations(unittest.TestCase):
    def test_real_documents_keep_anchors(self):
        for path in DOCS:
            with self.subTest(doc=path.name):
                self.assertEqual(
                    anchors(path.read_text(encoding="utf-8"), path.name), [])

    def test_anchor_removal_is_caught(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for pat in REQUIRED_ANCHORS["SKILL.md"]:
            with self.subTest(anchor=pat):
                damaged = re.sub(pat, "", text)
                self.assertNotEqual(damaged, text, "앵커가 원래 없다")
                self.assertNotEqual(anchors(damaged, "SKILL.md"), [])

    def test_capcut_only_in_ban_clauses(self):
        for path in DOCS:
            for line_no, block, section in iter_blocks(
                    path.read_text(encoding="utf-8")):
                if not CAPCUT_RE.search(block):
                    continue
                with self.subTest(doc=path.name, line=line_no):
                    self.assertTrue(
                        in_rule_context(block, section),
                        f"{path.name}:{line_no} [{section}] "
                        "금지 선언 밖 CapCut 언급")


class TestBaselineDraftPasses(unittest.TestCase):
    def test_clean_draft_has_no_violations(self):
        report = vd.run_checks(DRAFT, PACKET)
        for name, r in report.items():
            with self.subTest(check=name):
                self.assertEqual(r["violations"], [])


class TestViolationsAreCaught(unittest.TestCase):
    """위반 픽스처. 직전 회차 대본 감사에서 실제로 나온 유형이다."""

    def test_direct_quote_ending_changed(self):
        # 실제 사례: 원문 "실패로 끝날 거라고 봐요" -> 대본 "실패로 끝날 것"
        d = mutate(text="그 선택이 실패로 끝날 것")
        self.assertNotEqual(vd.check_quote_fidelity(d, PACKET), [])

    def test_direct_quote_single_char_change(self):
        d = mutate(text="실패로 끝날 거라고 봐요.")
        self.assertNotEqual(vd.check_quote_fidelity(d, PACKET), [])

    def test_indirect_keeping_quotation_marks(self):
        d = mutate(quote_mode="INDIRECT", text="\"실패로 끝날 것\"이라고 봤다")
        self.assertNotEqual(vd.check_quote_mode_marks(d, PACKET), [])

    def test_summary_keeping_curly_quotes(self):
        d = mutate(quote_mode="SUMMARY", text="“실패로 끝난다”는 취지였다")
        self.assertNotEqual(vd.check_quote_mode_marks(d, PACKET), [])

    def test_unknown_source_id(self):
        d = mutate(source_id="S99")
        self.assertNotEqual(vd.check_source_references(d, PACKET), [])

    def test_cue_out_of_range(self):
        d = mutate(cue_from=2, cue_to=99)
        self.assertNotEqual(vd.check_source_references(d, PACKET), [])

    def test_cue_reversed(self):
        d = mutate(cue_from=3, cue_to=1)
        self.assertNotEqual(vd.check_source_references(d, PACKET), [])

    def test_grounding_reference_also_checked(self):
        d = mutate(_target=0, grounding=[{"source_id": "S99", "cue_from": 1,
                                          "cue_to": 2}])
        self.assertNotEqual(vd.check_source_references(d, PACKET), [])

    def test_allegation_stated_as_fact(self):
        d = mutate(_target=0, text="신천지 개입이 사실로 드러났습니다.")
        self.assertNotEqual(vd.check_allegation_framing(d, PACKET), [])

    def test_allegation_with_attribution_passes(self):
        d = mutate(_target=0,
                   text="신천지 개입 의혹이 사실로 드러났다고 주장했습니다.")
        self.assertEqual(vd.check_allegation_framing(d, PACKET), [])

    def test_declared_count_mismatch(self):
        d = copy.deepcopy(DRAFT)
        d["declared_counts"]["narration_blocks"] = 7
        self.assertNotEqual(vd.check_declared_counts(d, PACKET), [])

    def test_missing_packet_fingerprint(self):
        d = copy.deepcopy(DRAFT)
        d.pop("source_packet_sha256")
        self.assertNotEqual(vd.check_packet_binding(d, PACKET), [])


class TestSrtParsing(unittest.TestCase):
    SRT = ("1\n00:00:00,000 --> 00:00:02,000\n제가 그때\n\n"
           "5\n00:00:02,000 --> 00:00:05,000\n실패로 끝날\n거라고 봐요\n\n")

    def test_cues_are_renumbered_from_one(self):
        """원본 번호가 튀어도 순서가 곧 번호다. 대본은 순번으로 참조한다."""
        cues, _dropped = bsp.parse_srt(self.SRT)
        self.assertEqual([c["cue"] for c in cues], [1, 2])

    def test_multiline_cue_is_joined(self):
        cues, _dropped = bsp.parse_srt(self.SRT)
        self.assertEqual(cues[1]["text"], "실패로 끝날 거라고 봐요")

    def test_timecodes_parsed(self):
        cues, _dropped = bsp.parse_srt(self.SRT)
        self.assertEqual((cues[1]["start"], cues[1]["end"]), (2.0, 5.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
