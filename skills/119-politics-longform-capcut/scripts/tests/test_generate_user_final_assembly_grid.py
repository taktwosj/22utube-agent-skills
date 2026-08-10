import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_user_final_assembly_grid as grid


class UserFinalAssemblyGridTests(unittest.TestCase):
    def test_horizontal_grid_uses_actual_card_times(self):
        document = {
            "cta_like_subscribe": "OFF",
            "cards": [
                {
                    "card_id": "C001",
                    "card_type": "INTRO",
                    "target_start_us": 0,
                    "target_duration_us": 5_000_000,
                },
                {
                    "card_id": "C002",
                    "card_type": "SOURCE_VIDEO",
                    "target_start_us": 5_000_000,
                    "target_duration_us": 10_000_000,
                    "source_start_us": 60_000_000,
                    "source_duration_us": 10_000_000,
                    "source_id": "S01",
                    "source_channel": "MBCNEWS",
                    "source_date": "2026.08.10",
                    "lower_mode": "SOURCE_TTS",
                    "lower_text": "첫째 줄\n둘째 줄",
                },
            ],
        }
        rendered = grid.render(document)
        self.assertIn("00:00–00:05", rendered)
        self.assertIn("00:05–00:15", rendered)
        self.assertIn("01:00–01:10", rendered)
        self.assertIn("S01", rendered)
        self.assertIn("READ-ONLY VIEW", rendered)

    def test_gap_is_rejected(self):
        document = {
            "cards": [
                {
                    "card_id": "C001",
                    "card_type": "INTRO",
                    "target_start_us": 0,
                    "target_duration_us": 5_000_000,
                },
                {
                    "card_id": "C002",
                    "card_type": "SOURCE_VIDEO",
                    "target_start_us": 6_000_000,
                    "target_duration_us": 1_000_000,
                },
            ]
        }
        with self.assertRaisesRegex(RuntimeError, "GRID_TIMELINE_INVALID"):
            grid.render(document)


if __name__ == "__main__":
    unittest.main()
