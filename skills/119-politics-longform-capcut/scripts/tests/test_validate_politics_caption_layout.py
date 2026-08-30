import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_politics_caption_layout as validator


class CaptionLayoutTests(unittest.TestCase):
    def test_line_limit_is_fifteen_visible_characters_and_ignores_spaces(self):
        self.assertEqual(
            validator.validate_caption("여러분의 패배도", label="x"),
            [],
        )
        self.assertEqual(
            validator.validate_caption("민주당의 패배도 아닙니다", label="x"),
            [],
        )
        findings = validator.validate_caption("가" * 16, label="x")
        self.assertIn(
            "CAPTION_LINE_HARD_LIMIT_EXCEEDED",
            {row["code"] for row in findings},
        )

    def test_two_lines_fail_for_v8_single_line_slot(self):
        text = "123456789012345\n123456789012345"
        findings = validator.validate_caption(text, label="x")
        self.assertIn("CAPTION_MAX_LINES_EXCEEDED", {row["code"] for row in findings})

    def test_three_lines_fail(self):
        findings = validator.validate_caption("첫째 줄\n둘째 줄\n셋째 줄", label="x")
        self.assertIn("CAPTION_MAX_LINES_EXCEEDED", {row["code"] for row in findings})

    def test_one_line_over_fifteen_fails(self):
        findings = validator.validate_caption("1234567890123456", label="x")
        self.assertIn(
            "CAPTION_AVERAGE_LINE_LENGTH_EXCEEDED",
            {row["code"] for row in findings},
        )

    def test_line_over_hard_limit_fails(self):
        findings = validator.validate_caption(
            "12345678901\n1234567890123456789012", label="x"
        )
        self.assertIn(
            "CAPTION_LINE_HARD_LIMIT_EXCEEDED",
            {row["code"] for row in findings},
        )

    def test_commentary_sequence_requires_exactly_two_input_lines(self):
        findings = validator.validate_caption(
            "한 줄 논평", label="x", exact_two_lines=True
        )
        self.assertIn(
            "COMMENTARY_REQUIRES_EXACTLY_2_LINES",
            {row["code"] for row in findings},
        )

    def test_cards_commentary_two_lines_pass_as_sequential_single_line_cues(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cards.json"
            path.write_text(
                json.dumps(
                    {
                        "cards": [
                            {
                                "card_id": "C001",
                                "lower_mode": "VIDEO100_EXPLAINER",
                                "lower_text": "정책 방향은 같았지만\n시행 준비는 충분했나",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate_cards(path), [])

    def test_srt_three_lines_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "test.srt"
            path.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\n첫째\n둘째\n셋째\n",
                encoding="utf-8",
            )
            findings = validator.validate_srt(path)
            self.assertIn(
                "CAPTION_MAX_LINES_EXCEEDED",
                {row["code"] for row in findings},
            )

    def test_blank_line_fails(self):
        findings = validator.validate_caption("첫째 줄\n\n둘째 줄", label="x")
        self.assertIn("CAPTION_EMPTY_LINE", {row["code"] for row in findings})

    def test_user_facing_commentary_alias_requires_two_input_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cards.json"
            path.write_text(
                json.dumps(
                    {
                        "cards": [
                            {
                                "card_id": "C001",
                                "lower_mode": "COMMENTARY_2LINE",
                                "lower_text": "한 줄 논평",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            findings = validator.validate_cards(path)
            self.assertIn(
                "COMMENTARY_REQUIRES_EXACTLY_2_LINES",
                {row["code"] for row in findings},
            )

    def test_user_facing_srt_alias_validates_referenced_srt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            srt = root / "source.srt"
            srt.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\n첫째 줄\n둘째 줄\n",
                encoding="utf-8",
            )
            cards = root / "cards.json"
            cards.write_text(
                json.dumps(
                    {
                        "cards": [
                            {
                                "card_id": "C001",
                                "lower_mode": "SRT",
                                "source_srt_file": str(srt),
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            findings = validator.validate_cards(cards)
            self.assertIn("CAPTION_MAX_LINES_EXCEEDED", {row["code"] for row in findings})


if __name__ == "__main__":
    unittest.main()
