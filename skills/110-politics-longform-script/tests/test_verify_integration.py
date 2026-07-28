#!/usr/bin/env python3
"""MD 초벌 대본 -> 파싱 -> 검증 종단 시험.

단위 시험은 각 검사가 제 일을 하는지 본다. 여기서는 실제 파일 한 벌이
게이트를 통과하거나 막히는지를 본다. 배선이 끊겨 있으면 개별 검사가 전부
초록이어도 아무것도 안 잡는다.
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import draft_md as dm                                        # noqa: E402
import verify_draft as vd                                    # noqa: E402

PACKET_SHA = "c" * 64

CUES = {
    "S05": [
        (412, "제가 그때 판단하기로는"),
        (413, "여러 정황을 봤을 때"),
        (414, "어 그러니까"),
        (415, "실패로 끝날 거라고 봐요"),
        (416, "그래서 반대했습니다"),
    ],
    "S02": [
        (10, "신천지 관련 의혹이 제기된 상태입니다"),
        (11, "당은 조사에 착수했습니다"),
    ],
}

PACKET = {
    "allegation_terms": ["신천지", "의혹"],
    "_actual_sha256": PACKET_SHA,
    "sources": [
        {"source_id": sid,
         "cues": [{"cue": n, "start": 100.0 + n, "end": 101.0 + n, "text": t}
                  for n, t in rows]}
        for sid, rows in CUES.items()
    ],
}

GOOD = f"""---
episode_id: PL_TEST
source_packet_sha256: {PACKET_SHA}
narration_blocks: 1
source_clips: 1
---

## CHAPTER 1 — 당권 경쟁

### [나레이션]
근거: S02 10-11
당은 조사에 착수했다고 밝혔습니다.

### [원본] S05 | 00:08:32~00:08:37 | cue 412-416 | 생략 414 | 간투사 | 직접
> 제가 그때 판단하기로는 여러 정황을 봤을 때 실패로 끝날 거라고 봐요 그래서 반대했습니다
"""


def check(md, packet=PACKET):
    d = dm.parse_draft_md(md)
    dm.backfill_cue_ranges(d, packet)
    report = vd.run_checks(d, packet)
    return {k: r["violations"] for k, r in report.items() if r["violations"]}


class TestCleanDraftPasses(unittest.TestCase):
    def test_no_violations(self):
        self.assertEqual(check(GOOD), {})

    def test_declared_skip_is_excluded_from_quote_comparison(self):
        """간투사 cue 414 를 신고하고 뺐다. 대조에서도 빠져야 한다."""
        self.assertNotIn("quote_fidelity", check(GOOD))

    def test_asr_speaker_markers_are_not_spoken_content(self):
        packet = copy.deepcopy(PACKET)
        packet["sources"][0]["cues"][0]["text"] = \
            ">> " + packet["sources"][0]["cues"][0]["text"]
        packet["sources"][0]["cues"][1]["text"] += " <<"
        self.assertNotIn("quote_fidelity", check(GOOD, packet))


class TestEachCheckFiresEndToEnd(unittest.TestCase):
    """배선 시험. 개별 검사가 실제 파이프라인에서 발화하는가."""

    def test_quote_fidelity(self):
        md = GOOD.replace("실패로 끝날 거라고 봐요", "실패로 끝날 것")
        self.assertIn("quote_fidelity", check(md))

    def test_forbidden_display_marks(self):
        for mark in (">>", "<<", "·"):
            with self.subTest(mark=mark):
                md = GOOD.replace("그래서 반대했습니다", f"그래서 {mark} 반대했습니다")
                self.assertIn("forbidden_display_marks", check(md))

    def test_undeclared_skip_breaks_quote_match(self):
        """생략을 신고하지 않고 빼면 대조에서 걸린다."""
        md = GOOD.replace(" | 생략 414 | 간투사", "")
        self.assertIn("quote_fidelity", check(md))

    def test_skip_without_class(self):
        md = GOOD.replace(" | 간투사", "")
        self.assertIn("skip_classification", check(md))

    def test_content_skip_must_split_blocks(self):
        md = GOOD.replace("간투사", "본문삭제")
        self.assertIn("skip_classification", check(md))

    def test_narration_quotes(self):
        md = GOOD.replace("당은 조사에 착수했다고 밝혔습니다.",
                          '"조사에 착수했다"고 밝혔습니다.')
        self.assertIn("narration_quotes", check(md))

    def test_allegation_stated_as_fact(self):
        md = GOOD.replace("당은 조사에 착수했다고 밝혔습니다.",
                          "신천지 개입이 사실로 드러났습니다.")
        self.assertIn("allegation_framing", check(md))

    def test_source_reference_out_of_range(self):
        md = GOOD.replace("cue 412-416", "cue 412-999")
        self.assertIn("source_reference", check(md))

    def test_unknown_source_id_with_explicit_cues_is_reported(self):
        """cue 범위가 있으면 backfill 이 건너뛴다. 내용 오류라 보고로 잡는다.

        크래시로 처리하면 나머지 검사가 안 돌아 지적이 한 번에 안 모인다.
        """
        md = GOOD.replace("[원본] S05", "[원본] S99")
        self.assertIn("source_reference", check(md))

    def test_unknown_source_id_without_cues_stops_parsing(self):
        """cue 를 역산해야 하는데 소스가 없으면 진행 자체가 불가능하다."""
        md = GOOD.replace("[원본] S05", "[원본] S99").replace(
            " | cue 412-416", "")
        with self.assertRaises(dm.DraftFormatError):
            check(md)

    def test_declared_counts_mismatch(self):
        md = GOOD.replace("narration_blocks: 1", "narration_blocks: 9")
        self.assertIn("declared_counts", check(md))

    def test_packet_fingerprint_mismatch(self):
        """다른 자막 묶음을 보고 쓴 대본은 걸린다."""
        md = GOOD.replace(PACKET_SHA, "d" * 64)
        self.assertIn("packet_binding", check(md))

    def test_missing_packet_fingerprint(self):
        md = GOOD.replace(f"source_packet_sha256: {PACKET_SHA}\n", "")
        self.assertIn("packet_binding", check(md))


class TestFormatErrorsStopVerification(unittest.TestCase):
    """양식 위반은 내용 검사 이전 문제다.

    여기서 안 멈추면 절반만 읽힌 대본을 검사하고 '위반 0건' 이라고 보고한다.
    """

    def test_source_block_with_indirect_mode(self):
        md = GOOD.replace("| 직접", "| 간접")
        with self.assertRaises(dm.DraftFormatError):
            check(md)

    def test_source_block_without_quote(self):
        md = GOOD.replace("> 제가 그때", "제가 그때")
        with self.assertRaises(dm.DraftFormatError):
            check(md)

    def test_no_frontmatter(self):
        md = GOOD.split("---\n", 2)[-1]
        with self.assertRaises(dm.DraftFormatError):
            check(md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
