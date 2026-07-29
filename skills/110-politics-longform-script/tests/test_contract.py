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
import gate_script_lock as gsl                               # noqa: E402
import draft_md as dm                                        # noqa: E402

DOCS = [SKILL / "SKILL.md"] + sorted((SKILL / "references").glob("*.md"))
CAPCUT_RE = re.compile(r"CapCut|캡컷", re.I)
RETENTION_EDITOR = SKILL / "references" / "retention-story-editor.md"
POLITICAL_NEWS_FRAMEWORK = (
    SKILL / "references" / "political-news-writing-framework.md"
)

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

    def test_script_lock_episode_id_pattern_is_closed(self):
        self.assertIsNotNone(
            gsl.EPISODE_ID_RE.fullmatch("PL_20260729_test_episode"))
        for bad in ("ep_test", "PL_test", "PL_20260729_Test", "../PL_20260729_x"):
            with self.subTest(bad=bad):
                self.assertIsNone(gsl.EPISODE_ID_RE.fullmatch(bad))


class TestRetentionStoryEditorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cls.editor_text = (
            RETENTION_EDITOR.read_text(encoding="utf-8")
            if RETENTION_EDITOR.is_file() else ""
        )

    def test_skill_links_editor_and_defines_internal_s2r_pass(self):
        self.assertTrue(
            RETENTION_EDITOR.is_file(),
            "references/retention-story-editor.md 가 없다",
        )
        self.assertIn(
            "[Retention Story Editor](references/retention-story-editor.md)",
            self.skill_text,
        )
        self.assertIn("S2R Retention Story Rewrite", self.skill_text)
        self.assertIn("PROJECT_GPT/Hermes 내부 작가 패스", self.skill_text)
        self.assertIn("새 승인 단계가 아니다", self.skill_text)

    def test_political_news_framework_is_required_for_news_longform(self):
        self.assertTrue(
            POLITICAL_NEWS_FRAMEWORK.is_file(),
            "references/political-news-writing-framework.md 가 없다",
        )
        framework = POLITICAL_NEWS_FRAMEWORK.read_text(encoding="utf-8")
        self.assertIn(
            "[Political News Writing Framework]"
            "(references/political-news-writing-framework.md)",
            self.skill_text,
        )
        self.assertIn(
            "[Political News Writing Framework]"
            "(political-news-writing-framework.md)",
            self.editor_text,
        )
        required = (
            "PP-RR-EE-PP",
            "댄 하먼",
            "짧은 기승전결",
            "정치평론 문체",
            "정청래가 차기 대선을 내려놓고",
            "이 영상의 범위",
            "소스팩",
            "증거로 제시했습니다",
            "대선 불출마를 가리킬 때는 `차기 대선`으로 통일하라",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, framework)

    def test_s4_is_mandatory_read_only_claude_review(self):
        self.assertIn("S4 최초 Claude 전체 검수는 필수", self.skill_text)
        self.assertIn("읽기 전용 검수자", self.skill_text)
        self.assertIn("지적서만 작성", self.skill_text)
        self.assertIn("대본을 수정하지 않는다", self.skill_text)

    def test_claude_first_codex_cli_fallback_is_explicit(self):
        required = (
            "Claude CLI에서 `opus`, `effort low`",
            "Claude 호출 자체가 실패했을 때만 Codex CLI",
            "`REWORK_REQUIRED`는 정상 검수 결과",
            "claude_call_failure_vN.json",
            "review_origin: codex_cli_external",
            "WAIT_REVIEW_UNAVAILABLE",
        )
        for phrase in required:
            self.assertIn(phrase, self.skill_text)

    def test_s6_required_and_omission_conditions_are_explicit(self):
        self.assertIn("S6 필수 조건", self.skill_text)
        self.assertIn("S4 verdict가 `APPROVED`가 아닌 경우", self.skill_text)
        self.assertIn("S4 이후 대본 파일 SHA가 변경된 경우", self.skill_text)
        self.assertIn("Claude 중요 지적을 반영한 경우", self.skill_text)
        self.assertIn("논지·챕터·직접인용·source 구간이 변경된 경우", self.skill_text)
        self.assertIn("사용자가 재검수를 요청한 경우", self.skill_text)
        self.assertIn("S6 생략 가능 조건", self.skill_text)
        self.assertIn("S4 verdict가 `APPROVED`", self.skill_text)
        self.assertIn("S4 이후 대본 바이트 변경이 0", self.skill_text)

    def test_binding_asr_and_advisory_limits_are_documented(self):
        combined = self.skill_text + "\n" + self.editor_text
        self.assertIn("WAIT_SOURCE_BINDING", combined)
        self.assertIn("WAIT_SOURCE_ASR_REVIEW", combined)
        self.assertIn("[EST]", self.editor_text)
        self.assertIn("validator의 PASS·FAIL 기준이 아니다", self.editor_text)
        self.assertIn("target_maximum_items: 12", self.editor_text)
        self.assertIn("hard_maximum: false", self.editor_text)

    def test_evidence_first_editorial_judgment_is_explicit(self):
        required = (
            "확인된 사실",
            "공식 판단",
            "당사자 주장",
            "미확정 쟁점",
            "제작진 평가",
            "REBUTTABLE",
            "PARTLY_VALID",
            "COUNTERARGUMENT_STRONGER",
            "UNRESOLVED",
            "영상만으로 동기를 단정하지 마라",
            "공식 수사·판결 전에는 범죄·불법을 확정하지 마라",
            "AI 합성·재연·패러디는 화면과 설명란에 고지하라",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.editor_text)

    def test_source_video_mix_uses_duration_not_block_counts(self):
        required = (
            "NARRATION_SHARE_TARGET = 30-50%",
            "SOURCE_VIDEO_SHARE_TARGET = 50-70%",
            "MIX_BASIS = MEASURED_DURATION",
            "BLOCK_COUNT_AS_RATIO = FORBIDDEN",
            "STAGE_110_RATIO_GATE = EDITORIAL_TARGET_ONLY",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.editor_text)

    def test_no_new_approval_state_or_cross_lane_dependency(self):
        combined = self.skill_text + "\n" + self.editor_text
        self.assertNotIn("USER_APPROVED_SCRIPT", combined)
        self.assertNotIn("119-politics-longform-capcut", self.editor_text)
        self.assertNotIn("000-politics-longform", self.editor_text)
        self.assertNotIn("CapCut", self.editor_text)
        self.assertNotIn("캡컷", self.editor_text)

    def test_existing_quote_fidelity_contract_is_preserved(self):
        verify_checks = {name for name, _fn, _code in vd.CHECKS}
        self.assertIn("quote_fidelity", verify_checks)
        self.assertNotIn("packet_text_match", verify_checks)
        self.assertIn("quote_fidelity", gsl.REQUIRED_CHECKS)
        self.assertNotIn("packet_text_match", gsl.REQUIRED_CHECKS)
        self.assertIn("quote_fidelity = SOURCE_PACKET_TEXT_ONLY",
                      self.editor_text)

    def test_forbidden_display_marks_are_enforced(self):
        self.assertIn("forbidden_display_marks", gsl.REQUIRED_CHECKS)
        self.assertIn("가운데점 `·`을 쓰지 않는다", self.skill_text)
        self.assertEqual(vd.normalize(">> 실제 발화 << 다음 화자"),
                         "실제 발화 다음 화자")

    def test_s2r_keeps_machine_draft_separate_from_review_notes(self):
        self.assertIn("`20_script/script_draft_v1.md`", self.editor_text)
        self.assertIn("첫 바이트는 `---`", self.editor_text)
        self.assertIn("A 제목을 파일에 쓰지 않는다", self.editor_text)
        self.assertIn("B와 C는 대본 파일에 쓰지 않는다", self.editor_text)

        machine_draft = """---
episode_id: TEST
source_packet_sha256: 0000000000000000000000000000000000000000000000000000000000000000
narration_blocks: 1
source_clips: 0
---

## CHAPTER 1 — TEST

### [나레이션]
테스트 문장입니다.
"""
        parsed = dm.parse_draft_md(machine_draft)
        self.assertEqual(parsed["declared_counts"]["narration_blocks"], 1)
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md("### A. 전체 수정 대본\n" + machine_draft)


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
