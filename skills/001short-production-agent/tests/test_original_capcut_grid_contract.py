import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
STAGE02 = SKILL_ROOT / "steps" / "02-original-blueprint.md"
STAGE03 = SKILL_ROOT / "steps" / "03-first-recommendation.md"
REPORTING = SKILL_ROOT / "references" / "structure-blueprint-reporting.md"
TEMPLATE = SKILL_ROOT / "templates" / "original-capcut-grid.md"
URAKKAI_TEMPLATE = SKILL_ROOT / "templates" / "urakkai-capcut-grid.md"


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
        self.assertIn("메시지 본문", STAGE02.read_text(encoding="utf-8"))

    def test_original_grid_template_contains_every_required_root_lane(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("ORIGINAL_CAPCUT_GRID_REQUIRED_ROWS", text)
        self.assertIn("레이어 / source 시간", text)
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

    def test_stage03_requires_a_target_time_by_layer_urakkai_grid(self):
        text = STAGE03.read_text(encoding="utf-8")
        self.assertIn("templates/urakkai-capcut-grid.md", text)
        self.assertIn("URAKKAI_CAPCUT_GRID_REQUIRED_ROWS", text)
        self.assertIn("메시지 본문", text)
        template = URAKKAI_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("레이어 / target 시간", template)
        for row in (
            "| VIDEO |",
            "| T1 |",
            "| T2 |",
            "| A9 TTS |",
            "| A9_TEXT |",
            "| A10 원본화자발언 |",
            "| A10_TEXT_WHITE |",
            "| A10_TEXT_YELLOW |",
            "| STATE |",
            "| A11 |",
            "| A12_RESERVED_EMPTY |",
            "| SCREEN |",
        ):
            self.assertIn(row, template)


if __name__ == "__main__":
    unittest.main()
