import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_design_lock
from validate_capcut_grids import REQUIRED_ROWS


SKILL = SKILL_ROOT / "SKILL.md"
STAGE02 = SKILL_ROOT / "steps" / "02-original-blueprint.md"
STAGE03 = SKILL_ROOT / "steps" / "03-first-recommendation.md"
STAGE04 = SKILL_ROOT / "steps" / "04-user-approval.md"
STAGE07 = SKILL_ROOT / "steps" / "07-audio.md"
STAGE08 = SKILL_ROOT / "steps" / "08-capcut-assembly.md"
ORCHESTRATOR = SKILL_ROOT / "references" / "production-orchestrator.md"
ORIGINAL_TEMPLATE = SKILL_ROOT / "templates" / "original-capcut-grid.md"
URAKKAI_TEMPLATE = SKILL_ROOT / "templates" / "urakkai-capcut-grid.md"


def table_roles(path: Path, header: str) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(f"| {header} |"))
    return tuple(
        line.strip().strip("|").split("|", 1)[0].strip()
        for line in lines[start + 2 : start + 2 + len(REQUIRED_ROWS)]
    )


def base_timeline(extra: list[dict]) -> dict:
    rows = [
        {"segment_id": "V", "role": "VIDEO", "start": 0, "duration": 10},
        {"segment_id": "T1", "role": "T1", "start": 0, "duration": 10, "text": "제목", "content_type": "TITLE"},
        {"segment_id": "T2", "role": "T2", "start": 0, "duration": 10, "text": "부제", "content_type": "TITLE"},
        {"segment_id": "SW", "role": "SCREEN_WHITE", "start": 0, "duration": 10},
        {"segment_id": "SE", "role": "SCREEN_EFFECT", "start": 0, "duration": 10},
    ]
    return {"segments": rows + extra, "audio_policy": "A10_RETAINED_SYNC", "primary_speaker_id": "P1"}


class OriginalCapCutGridContractTest(unittest.TestCase):
    def test_both_templates_use_the_same_exact_15_row_order(self):
        self.assertEqual(table_roles(ORIGINAL_TEMPLATE, "레이어 \\ 원본 시간"), REQUIRED_ROWS)
        self.assertEqual(table_roles(URAKKAI_TEMPLATE, "레이어 \\ 목표 시간"), REQUIRED_ROWS)

    def test_three_phase_docs_require_full_chat_report_and_builder_gate(self):
        joined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SKILL, STAGE02, STAGE03, STAGE04, STAGE08)
        )
        for token in (
            "원본표 → 우라까이표 → CapCut 조립",
            "scripts/validate_capcut_grids.py",
            "TABLE_EMPTY_CELL_FORBIDDEN",
            "TABLE_UNVERIFIED_CELL",
            "대화창",
            "프로젝트 파일명",
            "프로젝트 전체 경로",
        ):
            self.assertIn(token, joined)

    def test_protocol_and_workflow_declare_the_complete_grid_harness(self):
        protocol = json.loads((SKILL_ROOT / "protocol.json").read_text(encoding="utf-8"))
        workflow = json.loads((SKILL_ROOT / "workflow.json").read_text(encoding="utf-8"))
        harness = protocol["grid_harness"]
        self.assertEqual(tuple(harness["row_order"]), REQUIRED_ROWS)
        self.assertEqual(harness["validator"], "scripts/validate_capcut_grids.py")
        self.assertTrue(harness["builder_preflight_before_writes"])
        self.assertTrue(harness["chat_report_required_in_auto_mode"])
        self.assertEqual(workflow["grid_harness"], {"authority": "protocol.json#/grid_harness"})

    def test_stage_docs_preserve_required_artifacts_and_exact_handoff_command(self):
        self.assertIn("20_script/original-blueprint.md", STAGE02.read_text(encoding="utf-8"))
        self.assertIn("20_script/first-recommendation.md", STAGE03.read_text(encoding="utf-8"))
        self.assertIn("20_script/URAKKAI_BLUEPRINT.md", STAGE04.read_text(encoding="utf-8"))
        command = "scripts/validate_conversation_handoff.py --handoff <path>"
        self.assertIn(command, SKILL.read_text(encoding="utf-8"))
        self.assertIn(command, ORCHESTRATOR.read_text(encoding="utf-8"))

    def test_a9_text_and_state_allow_15_characters_but_only_two_lines(self):
        state = {
            "segment_id": "S",
            "role": "STATE",
            "start": 0,
            "duration": 10,
            "text": "123456789012345",
            "content_type": "STATE",
            "caption_role": "STATE",
            "state_effect": "LASER_CUT",
        }
        errors = validate_design_lock.validate_role_contract(base_timeline([state]), 10)
        self.assertNotIn("STATE_TEXT_TOO_LONG", {row["code"] for row in errors})

        state["text"] = "첫줄\n둘째줄\n셋째줄"
        errors = validate_design_lock.validate_role_contract(base_timeline([state]), 10)
        self.assertIn("CAPTION_TOO_MANY_LINES", {row["code"] for row in errors})

        a9_text = {
            "segment_id": "A9T",
            "role": "A9_TEXT",
            "start": 0,
            "duration": 10,
            "text": "1234567890123456",
            "content_type": "TTS",
            "caption_role": "A9_TEXT",
            "cue_id": "Q",
        }
        a9 = {
            "segment_id": "A9",
            "role": "A9",
            "start": 0,
            "duration": 10,
            "text": "1234567890123456",
            "content_type": "TTS",
            "cue_id": "Q",
        }
        errors = validate_design_lock.validate_role_contract(base_timeline([a9, a9_text]), 10)
        self.assertIn("CAPTION_LINE_TOO_LONG", {row["code"] for row in errors})

    def test_state_only_requires_no_a9_or_a10_audio(self):
        text = STAGE07.read_text(encoding="utf-8")
        self.assertIn("STATE_LASER만 있으면 TTS 엔진을 호출하지 않는다", text)
        self.assertIn("A10이 있을 때만 Demucs", text)


if __name__ == "__main__":
    unittest.main()
