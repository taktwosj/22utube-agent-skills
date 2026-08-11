from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_srt_text_fidelity as fidelity


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class SrtTextFidelityTests(unittest.TestCase):
    def test_line_break_and_split_preserve_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw.srt"
            display = root / "display.srt"
            raw.write_text(
                "1\n00:00:00,000 --> 00:00:04,000\n정책 방향과 실제 집행은 다른 문제입니다.\n",
                encoding="utf-8",
            )
            display.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\n정책 방향과 실제\n\n"
                "2\n00:00:02,000 --> 00:00:04,000\n집행은 다른 문제입니다.\n",
                encoding="utf-8",
            )
            result = fidelity.validate_pair(raw, display, ["SPLIT", "LINE_BREAK"])
            self.assertEqual(result["status"], "PASS")

    def test_internal_word_rewrite_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw.srt"
            display = root / "display.srt"
            raw.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\n정책 방향은 같았습니다.\n",
                encoding="utf-8",
            )
            display.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\n정책 노선은 같았습니다.\n",
                encoding="utf-8",
            )
            result = fidelity.validate_pair(raw, display, ["LINE_BREAK"])
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["code"], "SOURCE_TRANSCRIPT_TEXT_CHANGED")

    def test_clamp_allows_only_contiguous_edge_trim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw.srt"
            display = root / "display.srt"
            raw.write_text(
                "1\n00:00:00,000 --> 00:00:04,000\n앞부분 정책 방향과 실제 집행 뒷부분\n",
                encoding="utf-8",
            )
            display.write_text(
                "1\n00:00:01,000 --> 00:00:03,000\n정책 방향과 실제 집행\n",
                encoding="utf-8",
            )
            result = fidelity.validate_pair(raw, display, ["CLAMP", "LINE_BREAK"])
            self.assertEqual(result["status"], "PASS")

    def test_cards_require_current_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw.srt"
            display = root / "display.srt"
            raw.write_text("1\n00:00:00,000 --> 00:00:01,000\n원문\n", encoding="utf-8")
            display.write_text("1\n00:00:00,000 --> 00:00:01,000\n원문\n", encoding="utf-8")
            cards = root / "cards.json"
            cards.write_text(
                json.dumps(
                    {
                        "cards": [
                            {
                                "card_id": "C001",
                                "card_type": "SOURCE_VIDEO",
                                "lower_mode": "SRT",
                                "raw_transcript_path": str(raw),
                                "raw_transcript_sha256": "0" * 64,
                                "display_srt_path": str(display),
                                "display_srt_sha256": digest(display),
                                "display_transform": ["LINE_BREAK"],
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            findings = fidelity.validate_cards(cards)
            self.assertIn("RAW_TRANSCRIPT_SHA256_INVALID", {row["code"] for row in findings})


if __name__ == "__main__":
    unittest.main()
