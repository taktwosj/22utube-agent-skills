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
    / "validate_visible_text_clean.py"
)


class VisibleTextCleanGateTests(unittest.TestCase):
    def test_track_id_t1_t2_allowed_but_visible_text_t1_t2_forbidden(self):
        module = load_source_module_no_bytecode("visible_text_clean_track_ids", VALIDATOR)

        module.validate_visible_text_clean(
            {
                "fixed_tracks": [
                    {"track_id": "T1", "role": "top_title_1", "text": "정상 제목"},
                    {"track_id": "T2", "role": "top_title_2", "text": "정상 부제"},
                ]
            }
        )

        with self.assertRaisesRegex(module.GateFail, "FAIL_VISIBLE_TEXT_PLACEHOLDER"):
            module.validate_visible_text_clean(
                {"fixed_tracks": [{"track_id": "T1", "role": "top_title_1", "text": "T1"}]}
            )

    def test_placeholder_operator_text_fails(self):
        module = load_source_module_no_bytecode("visible_text_clean_placeholder", VALIDATOR)

        with self.assertRaisesRegex(module.GateFail, "FAIL_VISIBLE_TEXT_PLACEHOLDER"):
            module.validate_visible_text_clean({"middle_text": [{"text": "의견입력"}]})

    def test_bracketed_timecode_marker_fails(self):
        module = load_source_module_no_bytecode("visible_text_clean_timecode", VALIDATOR)

        with self.assertRaisesRegex(module.GateFail, "FAIL_VISIBLE_TEXT_PLACEHOLDER"):
            module.validate_visible_text_clean({"middle_text": [{"text": "[00:00-00:03] 테스트"}]})


if __name__ == "__main__":
    unittest.main()
