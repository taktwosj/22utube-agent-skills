from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_politics_caption_layout as validator


class CaptionLayoutV2Tests(unittest.TestCase):
    def test_internal_source_tts_validates_referenced_srt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            srt = root / "source.srt"
            srt.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\n정책 방향은 같았지만\n시행 준비는 충분했나\n",
                encoding="utf-8",
            )
            cards = root / "cards.json"
            cards.write_text(
                json.dumps(
                    {
                        "cards": [
                            {
                                "card_id": "C001",
                                "lower_mode": "SOURCE_TTS",
                                "source_srt_file": str(srt),
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate_cards(cards), [])

    def test_internal_narration_tts_missing_srt_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cards = Path(temporary) / "cards.json"
            cards.write_text(
                json.dumps(
                    {"cards": [{"card_id": "N001", "lower_mode": "NARRATION_TTS"}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            findings = validator.validate_cards(cards)
            self.assertIn("CAPTION_SRT_REFERENCE_REQUIRED", {row["code"] for row in findings})


if __name__ == "__main__":
    unittest.main()
