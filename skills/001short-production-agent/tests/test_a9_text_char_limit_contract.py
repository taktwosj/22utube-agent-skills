from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_capcut_grids


class A9TextCharLimitContractTest(unittest.TestCase):
    """steps/03, protocol.json, and the validator must agree on the target
    A9_TEXT per-line char limit. A 2026-08-22 audit found steps/03 saying 10
    while protocol.json and the validator said 15; this pins all three to 15
    so a future edit to any one of them fails loudly instead of drifting."""

    def test_all_three_sources_agree_on_15(self) -> None:
        protocol = json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))
        protocol_limit = protocol["grid_harness"]["target_a9_text_max_chars_per_line"]

        validator_limit = validate_capcut_grids.LINE_LIMITS[("urakkai", "A9_TEXT")][1]

        steps03 = (SKILL / "steps" / "03-first-recommendation.md").read_text(encoding="utf-8")
        match = re.search(r"target `A9_TEXT`.*?한 줄 (\d+)자 이하", steps03)
        self.assertIsNotNone(match, "steps/03 must state the target A9_TEXT per-line char limit")
        steps03_limit = int(match.group(1))

        self.assertEqual(protocol_limit, 15)
        self.assertEqual(validator_limit, 15)
        self.assertEqual(steps03_limit, 15)


if __name__ == "__main__":
    unittest.main()
