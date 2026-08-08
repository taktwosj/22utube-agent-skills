import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
STAGE02 = SKILL_ROOT / "steps" / "02-original-blueprint.md"
REPORTING = SKILL_ROOT / "references" / "structure-blueprint-reporting.md"
TEMPLATE = SKILL_ROOT / "templates" / "original-capcut-grid.md"


class OriginalCapCutGridContractTest(unittest.TestCase):
    def test_stage02_requires_a_populated_root_normalized_original_grid(self):
        required_rows = (
            "T1",
            "T2",
            "A9 TTS",
            "A9_TEXT",
            "A10 작가 나레이션",
            "A10 화자발언 1",
            "A10 화자발언 2",
            "A10 화자발언 3",
            "STATE 상황설명문구",
        )
        self.assertIn("templates/original-capcut-grid.md", SKILL.read_text(encoding="utf-8"))
        for path in (STAGE02, REPORTING):
            text = path.read_text(encoding="utf-8")
            self.assertIn("ORIGINAL_CAPCUT_GRID_REQUIRED_ROWS", text, path.name)
            for row in required_rows:
                self.assertIn(row, text, f"{path.name}: {row}")
            self.assertIn("bare `없음`, `비움`, `UNVERIFIED`", text, path.name)

    def test_original_grid_template_contains_every_required_root_lane(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("ORIGINAL_CAPCUT_GRID_REQUIRED_ROWS", text)
        for row in (
            "| T1 |",
            "| T2 |",
            "| A9 TTS 재현 대본 |",
            "| A9_TEXT TTS 표시문구 |",
            "| A10 작가 나레이션 |",
            "| A10 화자발언 1 |",
            "| A10 화자발언 2 |",
            "| A10 화자발언 3 |",
            "| STATE 상황설명문구 |",
        ):
            self.assertIn(row, text)


if __name__ == "__main__":
    unittest.main()
