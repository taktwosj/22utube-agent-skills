from __future__ import annotations

import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "skills"
    / "000short-production-agent"
    / "scripts"
    / "validate_top_title_full_duration.py"
)


def valid_plan() -> dict:
    return {
        "project_duration_sec": 12.0,
        "fixed_tracks": [
            {"track_id": "T1", "role": "top_title_1", "start_sec": 0, "end_sec": 12.0},
            {"track_id": "T2", "role": "top_title_2", "start_sec": 0, "end_sec": 12.0},
        ],
    }


class TopTitleFullDurationTests(unittest.TestCase):
    def test_t1_t2_full_duration_passes(self):
        module = load_source_module_no_bytecode("top_title_full_duration_valid", VALIDATOR)

        result = module.validate_top_title_full_duration(valid_plan())

        self.assertEqual(result["top_title_full_duration_status"], "PASS")

    def test_t1_shorter_than_project_duration_fails(self):
        module = load_source_module_no_bytecode("top_title_full_duration_short", VALIDATOR)
        plan = valid_plan()
        plan["fixed_tracks"][0]["end_sec"] = 8.0

        with self.assertRaisesRegex(module.GateFail, "FAIL_TOP_TITLE_DURATION"):
            module.validate_top_title_full_duration(plan)

    def test_t2_missing_fails(self):
        module = load_source_module_no_bytecode("top_title_full_duration_missing", VALIDATOR)
        plan = valid_plan()
        plan["fixed_tracks"] = plan["fixed_tracks"][:1]

        with self.assertRaisesRegex(module.GateFail, "FAIL_TOP_TITLE_DURATION"):
            module.validate_top_title_full_duration(plan)


if __name__ == "__main__":
    unittest.main()
