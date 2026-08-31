#!/usr/bin/env python3
"""Humanize KR pre-lock gate tests.

The humanizer may improve narration only. This suite proves that its receipt
blocks source-bound facts, direct quotes, numeric values, names, or the user's
no-defensive-narration rule from silently changing.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import verify_humanize_korean_gate as hg  # noqa: E402

PACKET_SHA = "a" * 64

BEFORE = f"""---
episode_id: PL_20260831_humanize_test
source_packet_sha256: {PACKET_SHA}
narration_blocks: 1
source_clips: 1
---

## CHAPTER 1 — 당청의 간격

### [나레이션]
근거: S01 1-2
청와대는 연대의 판을 꺼냈습니다.
김민석의 메시지는 다른 방향으로 갑니다.
지지율은 38.9%입니다.

### [원본] S01 | cue 1-2 | 직접
> 용혜인 후보자 인선은 오늘 발표됐습니다
"""

AFTER = BEFORE.replace(
    "청와대는 연대의 판을 꺼냈습니다.\n김민석의 메시지는 다른 방향으로 갑니다.\n지지율은 38.9%입니다.",
    "청와대가 연대의 판을 꺼냈습니다.\n김민석은 다른 방향으로 움직입니다.\n지지율은 38.9%입니다.",
)

PACKET = {
    "schema": "politics-longform-source-packet.v1",
    "lexicon": ["김민석", "용혜인", "청와대", "연대", "지지율"],
    "sources": [
        {
            "source_id": "S01",
            "title": "용혜인 후보자 인선 발표",
            "channel": "청와대",
            "cues": [],
        }
    ],
}


class GateCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="humanize-korean-gate-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.before = self.root / "before.md"
        self.after = self.root / "after.md"
        self.packet = self.root / "source_packet_v1.json"
        self.before.write_text(BEFORE, encoding="utf-8")
        self.after.write_text(AFTER, encoding="utf-8")
        self.packet.write_text(json.dumps(PACKET, ensure_ascii=False), encoding="utf-8")

    def report(self, after_text=None, packet=None):
        if after_text is not None:
            self.after.write_text(after_text, encoding="utf-8")
        if packet is not None:
            self.packet.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
        return hg.build_report(
            before_path=self.before,
            after_path=self.after,
            source_packet_path=self.packet,
            episode_id="PL_20260831_humanize_test",
        )

    def check(self, name, report=None):
        report = report or self.report()
        return report["checks"][name]


class TestUpstreamPin(unittest.TestCase):
    def test_v2_3_2_snapshot_is_present_and_hash_bound(self):
        self.assertEqual(hg.verify_upstream_snapshot(), [])


class TestHumanizeFidelity(GateCase):
    def test_narration_only_rewrite_passes(self):
        report = self.report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["total_violations"], 0)
        for name in hg.REQUIRED_CHECKS:
            with self.subTest(check=name):
                self.assertEqual(report["checks"][name]["violations"], [])

    def test_direct_quote_edit_is_blocked(self):
        report = self.report(AFTER.replace("후보자 인선", "후보 인선"))
        self.assertNotEqual(self.check("QUOTE", report)["violations"], [])
        self.assertEqual(report["status"], "WAIT_HUMANIZE_FIDELITY")

    def test_numeric_literal_change_is_blocked(self):
        report = self.report(AFTER.replace("38.9%", "39%"))
        self.assertNotEqual(self.check("NUMBER", report)["violations"], [])
        self.assertEqual(report["status"], "WAIT_HUMANIZE_FIDELITY")

    def test_protected_name_removal_is_blocked(self):
        report = self.report(AFTER.replace("김민석은", "그는"))
        self.assertNotEqual(self.check("NAME", report)["violations"], [])
        self.assertEqual(report["status"], "WAIT_HUMANIZE_FIDELITY")

    def test_source_binding_change_is_blocked_as_fact_change(self):
        report = self.report(AFTER.replace(PACKET_SHA, "b" * 64))
        self.assertNotEqual(self.check("FACT", report)["violations"], [])
        self.assertEqual(report["status"], "WAIT_HUMANIZE_FIDELITY")

    def test_user_banned_defensive_narration_is_blocked(self):
        report = self.report(AFTER.replace(
            "지지율은 38.9%입니다.", "지지율은 38.9%입니다. 단정하지 않겠습니다."))
        self.assertNotEqual(self.check("DIRECT_VOICE", report)["violations"], [])
        self.assertEqual(report["status"], "WAIT_HUMANIZE_STYLE")

    def test_source_packet_lexicon_terms_are_factual_anchors(self):
        packet = copy.deepcopy(PACKET)
        packet["lexicon"].append("다른 방향")
        report = self.report(AFTER.replace("다른 방향", "별도 방향"), packet)
        self.assertNotEqual(self.check("FACT", report)["violations"], [])


class TestReceiptShape(GateCase):
    def test_receipt_binds_before_after_packet_and_upstream(self):
        report = self.report()
        self.assertEqual(report["schema"], hg.SCHEMA)
        self.assertEqual(report["before"]["path"], "before.md")
        self.assertEqual(report["after"]["path"], "after.md")
        self.assertEqual(report["source_packet"]["path"], "source_packet_v1.json")
        self.assertEqual(report["upstream"], hg.UPSTREAM_PIN)
        self.assertEqual(set(report["checks"]), set(hg.REQUIRED_CHECKS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
