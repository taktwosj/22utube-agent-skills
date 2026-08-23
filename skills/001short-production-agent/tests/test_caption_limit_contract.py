import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_design_lock
from validate_capcut_grids import LINE_LIMITS

from schema_runtime import validate_schema

PROTOCOL_PATH = SKILL_ROOT / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
GRID_HARNESS = PROTOCOL["grid_harness"]
ORIGINAL_TEMPLATE = SKILL_ROOT / "templates" / "original-capcut-grid.md"
URAKKAI_TEMPLATE = SKILL_ROOT / "templates" / "urakkai-capcut-grid.md"


class CaptionLimitContractTest(unittest.TestCase):
    """protocol.json, the grid harness and the design lock each keep their own copy
    of the caption budgets.  A9_TEXT was once 10 in protocol.json while both
    validators still enforced 15, so the operator's decision never reached the
    build.  These assertions fail the moment one copy moves without the others."""

    def test_grid_harness_matches_protocol(self):
        self.assertEqual(
            LINE_LIMITS[("urakkai", "A9_TEXT")],
            (
                GRID_HARNESS["target_a9_text_max_lines"],
                GRID_HARNESS["target_a9_text_max_chars_per_line"],
            ),
        )
        self.assertEqual(
            LINE_LIMITS[("original", "A9_TEXT")],
            (
                GRID_HARNESS["original_a9_text_max_lines"],
                GRID_HARNESS["original_a9_text_max_chars_per_line"],
            ),
        )
        for table in ("original", "urakkai"):
            self.assertEqual(
                LINE_LIMITS[(table, "STATE_LASER")],
                (
                    GRID_HARNESS["state_laser_max_lines"],
                    GRID_HARNESS["state_laser_max_chars_per_line"],
                ),
            )

    def test_design_lock_matches_protocol(self):
        # The design lock inspects the assembled project, which carries the
        # urakkai A9_TEXT, so it follows the target budget rather than the
        # original one.
        self.assertEqual(
            validate_design_lock.MAX_LINE_LENGTH_BY_ROLE["A9_TEXT"],
            GRID_HARNESS["target_a9_text_max_chars_per_line"],
        )
        self.assertEqual(
            validate_design_lock.MAX_LINE_COUNT_BY_ROLE["A9_TEXT"],
            GRID_HARNESS["target_a9_text_max_lines"],
        )
        self.assertEqual(
            validate_design_lock.MAX_LINE_LENGTH_BY_ROLE["STATE"],
            GRID_HARNESS["state_laser_max_chars_per_line"],
        )
        self.assertEqual(
            validate_design_lock.MAX_LINE_COUNT_BY_ROLE["STATE"],
            GRID_HARNESS["state_laser_max_lines"],
        )

    def test_templates_quote_the_enforced_numbers(self):
        target = GRID_HARNESS["target_a9_text_max_chars_per_line"]
        original = GRID_HARNESS["original_a9_text_max_chars_per_line"]
        urakkai_text = URAKKAI_TEMPLATE.read_text(encoding="utf-8")
        original_text = ORIGINAL_TEMPLATE.read_text(encoding="utf-8")
        self.assertRegex(urakkai_text, rf"`A9_TEXT`는 \*\*한 줄 {target}자 이하")
        self.assertRegex(original_text, rf"`A9_TEXT`와 `STATE_LASER`는 한 줄 {original}자 이하")

    def _a9_text_codes(self, length: int) -> set[str]:
        rows = validate_design_lock.validate_role_contract(
            {
                "segments": [
                    {
                        "segment_id": "S",
                        "role": "A9_TEXT",
                        "start": 0,
                        "duration": 10,
                        "text": "가" * length,
                        "content_type": "A9_TEXT",
                        "caption_role": "A9_TEXT",
                    }
                ]
            },
            10,
        )
        return {row["code"] for row in rows}

    def test_a9_text_budget_is_enforced_at_the_protocol_number(self):
        limit = GRID_HARNESS["target_a9_text_max_chars_per_line"]
        self.assertNotIn("CAPTION_LINE_TOO_LONG", self._a9_text_codes(limit))
        self.assertIn("CAPTION_LINE_TOO_LONG", self._a9_text_codes(limit + 1))



class ProtocolSchemaContractTest(unittest.TestCase):
    """Nothing validated protocol.json against schemas/executable_protocol.schema.json,
    so the schema quietly fell three changes behind: it never learned the
    source_intake_receipt and vocal_stem_manifest pointers, it still required the
    old cloud_row_required_fields name, and its URAKKAI policy enum was missing
    SOURCE_ORDER_CLEAN_AUDIO - a policy protocol.json has been allowing all along."""

    def test_protocol_validates_against_its_own_schema(self):
        schema = json.loads(
            (SKILL_ROOT / "schemas" / "executable_protocol.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(validate_schema(PROTOCOL, schema), [])


if __name__ == "__main__":
    unittest.main()

