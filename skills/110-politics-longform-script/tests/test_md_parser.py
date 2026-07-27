#!/usr/bin/env python3
"""초벌 대본 MD 파서 계약.

GPT 는 마크다운을 쓴다. 엄격한 JSON 을 요구하면 cue 번호를 세다가 틀린다.
그래서 산문은 자유롭게 두고 출처 줄 하나만 고정 형식으로 받는다.

목표 상태를 적는다. 파서가 아직 없으므로 지금은 실패한다 (RED).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import draft_md as dm                                        # noqa: E402

SAMPLE = """---
episode_id: PL_TEST
source_packet_sha256: 0000000000000000000000000000000000000000000000000000000000000000
narration_blocks: 1
source_clips: 2
---

# 제목

## CHAPTER 1 — 수사와 기소의 분리

### [나레이션]
근거: S05 412-431
지금 벌어지는 일은 노선 다툼이 아닙니다.

### [원본] S05 | 00:11:23.400~00:20:07.120 | cue 412-468 | 생략 414,417-419 | 간투사 | 직접
> 실패로 끝날 거라고 봐요

### [원본] S02 | 00:03:10~00:03:40 | 직접
> 앞으로 지켜보겠다는 취지였습니다
"""

PACKET = {
    "sources": [
        {"source_id": "S02",
         "cues": [{"cue": i, "start": 180.0 + i, "end": 181.0 + i,
                   "text": f"에스투 {i}"} for i in range(1, 60)]},
        {"source_id": "S05",
         "cues": [{"cue": i, "start": 600.0 + i, "end": 601.0 + i,
                   "text": f"에스오오 {i}"} for i in range(1, 600)]},
    ]
}


class TestFrontmatter(unittest.TestCase):
    def test_header_fields_are_read(self):
        d = dm.parse_draft_md(SAMPLE)
        self.assertEqual(d["episode_id"], "PL_TEST")
        self.assertEqual(d["source_packet_sha256"], "0" * 64)
        self.assertEqual(d["declared_counts"],
                         {"narration_blocks": 1, "source_clips": 2})

    def test_missing_frontmatter_is_an_error(self):
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md("## CHAPTER 1\n\n### [나레이션]\n본문\n")


class TestSegments(unittest.TestCase):
    def setUp(self):
        self.d = dm.parse_draft_md(SAMPLE)
        self.segs = [s for ch in self.d["chapters"] for s in ch["segments"]]

    def test_chapter_title_is_kept(self):
        self.assertEqual(self.d["chapters"][0]["chapter_number"], 1)
        self.assertIn("수사와 기소", self.d["chapters"][0]["chapter_title"])

    def test_narration_grounding_is_parsed(self):
        n = self.segs[0]
        self.assertEqual(n["type"], "NARRATION")
        self.assertEqual(n["grounding"],
                         [{"source_id": "S05", "cue_from": 412,
                           "cue_to": 431}])
        self.assertIn("노선 다툼", n["text"])
        self.assertNotIn("근거:", n["text"])

    def test_source_segment_fields(self):
        s = self.segs[1]
        self.assertEqual(s["type"], "SOURCE_VIDEO")
        self.assertEqual(s["source_id"], "S05")
        self.assertEqual((s["cue_from"], s["cue_to"]), (412, 468))
        self.assertEqual(s["cues_skipped"], [414, 417, 418, 419])
        self.assertEqual(s["skip_class"], "간투사")
        self.assertEqual(s["quote_mode"], "DIRECT")
        self.assertEqual(s["text"], "실패로 끝날 거라고 봐요")

    def test_source_blocks_are_direct_only(self):
        """원본 블록은 화면에 뜰 발화 자막이다. 옮겨 쓰면 대조가 불가능하다."""
        self.assertEqual([s["quote_mode"] for s in self.segs[1:]],
                         ["DIRECT", "DIRECT"])

    def test_indirect_in_source_block_is_rejected(self):
        text = SAMPLE.replace("00:03:40 | 직접", "00:03:40 | 간접")
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md(text)

    def test_summary_in_source_block_is_rejected(self):
        text = SAMPLE.replace("00:03:40 | 직접", "00:03:40 | 요약")
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md(text)

    def test_segment_ids_are_generated(self):
        self.assertEqual([s["segment_id"] for s in self.segs],
                         ["C1-N01", "C1-S01", "C1-S02"])


class TestTimecodeBackfill(unittest.TestCase):
    """cue 번호가 없으면 타임코드에서 역산한다. GPT 가 안 세도 되게."""

    def test_cue_range_is_derived_from_timecode(self):
        d = dm.parse_draft_md(SAMPLE)
        dm.backfill_cue_ranges(d, PACKET)
        s = [x for ch in d["chapters"] for x in ch["segments"]][2]
        self.assertIsNotNone(s["cue_from"])
        self.assertIsNotNone(s["cue_to"])
        self.assertLessEqual(s["cue_from"], s["cue_to"])

    def test_explicit_cue_range_is_not_overwritten(self):
        d = dm.parse_draft_md(SAMPLE)
        dm.backfill_cue_ranges(d, PACKET)
        s = [x for ch in d["chapters"] for x in ch["segments"]][1]
        self.assertEqual((s["cue_from"], s["cue_to"]), (412, 468))

    def test_timecode_outside_source_is_reported(self):
        text = SAMPLE.replace("00:03:10~00:03:40", "09:59:00~09:59:30")
        d = dm.parse_draft_md(text)
        with self.assertRaises(dm.DraftFormatError):
            dm.backfill_cue_ranges(d, PACKET)


class TestSkipClassification(unittest.TestCase):
    """연속 영상에서 발화 cue 만 빼면 자막과 화면이 어긋난다.

    간투사 제거는 허용, 그 밖의 생략은 실제 영상 컷이므로 블록을 나눠야 한다.
    """

    def test_filler_skip_is_allowed(self):
        d = dm.parse_draft_md(SAMPLE)
        self.assertEqual(dm.check_skip_classification(d, PACKET), [])

    def test_unclassified_skip_is_rejected(self):
        text = SAMPLE.replace("| 생략 414,417-419 | 간투사 ", "| 생략 414,417-419 ")
        d = dm.parse_draft_md(text)
        self.assertNotEqual(dm.check_skip_classification(d, PACKET), [])

    def test_content_skip_must_be_split_into_blocks(self):
        """라벨만 바꾸는 게 아니라, 실제로 본문 cue 를 빼고 안 나눈 상태다."""
        text = SAMPLE.replace("| 생략 414,417-419 | 간투사 |",
                              "| 생략 414,417-419 | 본문삭제 |")
        d = dm.parse_draft_md(text)
        found = dm.check_skip_classification(d, PACKET)
        self.assertNotEqual(found, [])
        self.assertTrue(any("나눠 선언" in f for f in found), found)

    def test_splitting_into_two_blocks_is_accepted(self):
        """지시대로 나누면 통과한다. 반려에 출구가 있음을 증명한다."""
        text = SAMPLE.replace(
            "### [원본] S05 | 00:11:23.400~00:20:07.120 | cue 412-468 "
            "| 생략 414,417-419 | 간투사 | 직접\n> 실패로 끝날 거라고 봐요\n",
            "### [원본] S05 | cue 412-413 | 직접\n> 앞 구간\n\n"
            "### [원본] S05 | cue 420-468 | 직접\n> 뒤 구간\n")
        d = dm.parse_draft_md(text)
        self.assertEqual(dm.check_skip_classification(d, PACKET), [])

    def test_unreported_cue_gap_is_caught(self):
        """'cue 412,468' 을 412-468 로 뭉개면 신고 없는 cue 가 끼어든다."""
        text = SAMPLE.replace("cue 412-468", "cue 412,468")
        d = dm.parse_draft_md(text)
        self.assertNotEqual(dm.check_skip_classification(d, PACKET), [])


class TestNarrationQuotes(unittest.TestCase):
    """직전 회차 최악의 지적. 다듬은 문장을 따옴표에 넣어 인용처럼 보이게 했다."""

    def test_clean_narration_passes(self):
        d = dm.parse_draft_md(SAMPLE)
        self.assertEqual(dm.check_narration_has_no_quotes(d, PACKET), [])

    def test_quotation_in_narration_is_flagged(self):
        text = SAMPLE.replace("노선 다툼이 아닙니다.",
                              '"실패로 끝날 것"이라는 말이 나왔습니다.')
        d = dm.parse_draft_md(text)
        self.assertNotEqual(dm.check_narration_has_no_quotes(d, PACKET), [])

    def test_curly_quotation_in_narration_is_flagged(self):
        text = SAMPLE.replace("노선 다툼이 아닙니다.",
                              "“실패로 끝날 것”이라는 말이 나왔습니다.")
        d = dm.parse_draft_md(text)
        self.assertNotEqual(dm.check_narration_has_no_quotes(d, PACKET), [])


class TestMalformedSourceLine(unittest.TestCase):
    def test_missing_quote_mode(self):
        text = SAMPLE.replace(" | 간투사 | 직접", " | 간투사")
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md(text)

    def test_missing_source_id(self):
        text = SAMPLE.replace("[원본] S05 |", "[원본] |")
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md(text)

    def test_source_segment_without_quote_block(self):
        text = SAMPLE.replace("> 실패로 끝날 거라고 봐요\n", "")
        with self.assertRaises(dm.DraftFormatError):
            dm.parse_draft_md(text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
