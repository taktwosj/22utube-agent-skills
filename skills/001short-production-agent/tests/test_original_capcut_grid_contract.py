import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_design_lock
import validate_original_blueprint
from validate_capcut_grids import REQUIRED_ROWS, render_chat_report, validate_grid, validate_grids


SKILL = SKILL_ROOT / "SKILL.md"
STAGE02 = SKILL_ROOT / "steps" / "02-original-blueprint.md"
STAGE03 = SKILL_ROOT / "steps" / "03-first-recommendation.md"
STAGE04 = SKILL_ROOT / "steps" / "04-user-approval.md"
STAGE07 = SKILL_ROOT / "steps" / "07-audio.md"
STAGE08 = SKILL_ROOT / "steps" / "08-capcut-assembly.md"
ORCHESTRATOR = SKILL_ROOT / "references" / "production-orchestrator.md"
ORIGINAL_TEMPLATE = SKILL_ROOT / "templates" / "original-capcut-grid.md"
URAKKAI_TEMPLATE = SKILL_ROOT / "templates" / "urakkai-capcut-grid.md"
EXECUTION_SPEC = SKILL_ROOT.parents[1] / "docs" / "001SHORT_NORMAL_FAST_EXECUTION_SPEC.md"
ORIGINAL_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "original_grid_8.pass.md"


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
    def test_stage02_documents_exact_field_id_to_header_mapping(self):
        stage02 = STAGE02.read_text(encoding="utf-8")
        for field_id, header in (
            ("situation_action", "상황·행동"),
            ("lead_speaker", "주도 화자"),
            ("delivery_mode", "전달 방식"),
            ("narrative_function", "서사 기능"),
            ("split_basis", "구조 분리 근거"),
        ):
            self.assertIn(f"`{field_id}` ↔ `{header}`", stage02)

    def test_execution_spec_lists_every_required_release_blocker_file(self):
        spec = EXECUTION_SPEC.read_text(encoding="utf-8")
        for relative in (
            "scripts/validate_original_blueprint.py",
            "scripts/validate_stage.py",
            "scripts/build_episode_capcut.py",
            "scripts/capcut_model.py",
            "scripts/validate_capcut_project.py",
            "schemas/structure_snapshot.schema.json",
            "references/matt-auxiliary-routing.md",
            "templates/human-design-blueprint.md",
            "tests/test_validate_stage_router.py",
        ):
            self.assertIn(relative, spec)

    def test_original_blueprint_rejects_unverified_and_placeholder_field_values(self):
        for value in ("미확인", "아직 미확인입니다", "TBD", "placeholder", "<later>", "-"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                artifact = Path(td) / "original-blueprint.md"
                artifact.write_text(
                    "| 원본 구조 | source range | 상황·행동 | 주도 화자 | 전달 방식 | 서사 기능 | 구조 분리 근거 |\n"
                    "|---|---|---|---|---|---|---|\n"
                    f"| B01 | 0~1 | 행동 | 화자 | 외국인 발화 | 도입 | {value} |\n",
                    encoding="utf-8",
                )
                result = validate_original_blueprint.validate_original_blueprint(artifact)
                self.assertEqual(result["status"], "FAIL")
                self.assertIn(
                    "ORIGINAL_BLUEPRINT_BEAT_FIELD_PLACEHOLDER",
                    {row["code"] for row in result["errors"]},
                )

    def test_original_grid_requires_five_category_source_transcript_before_table(self):
        source = ORIGINAL_FIXTURE.read_text(encoding="utf-8")
        legacy_table = "# 원본표\n\n" + source[source.index("| 레이어 \\ 원본 시간 |") :]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "original.md"
            path.write_text(legacy_table, encoding="utf-8")
            _grid, errors = validate_grid(path, "original", require_source_transcript=True)
        self.assertIn("ORIGINAL_TRANSCRIPT_REQUIRED", {row["code"] for row in errors})

    def test_original_transcript_matches_every_b_segment_and_renders_before_grid(self):
        source = ORIGINAL_FIXTURE.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "original.md"
            path.write_text(source, encoding="utf-8")
            validation = validate_grids(path, URAKKAI_TEMPLATE)
            self.assertNotIn(
                "ORIGINAL_TRANSCRIPT_REQUIRED",
                {row["code"] for row in validation["errors"]},
            )
            original, errors = validate_grid(path, "original")
            self.assertEqual(errors, [])
            self.assertEqual(tuple(block.segment_id for block in original.source_transcript), tuple(f"B{i:02d}" for i in range(1, 9)))
            report = original.markdown()
            self.assertLess(report.index("### B01 00.0–03.9"), report.index("| 레이어 \\ 원본 시간 |"))

    def test_original_transcript_rejects_field_reorder_unresolved_ocr_and_added_tts(self):
        valid = ORIGINAL_FIXTURE.read_text(encoding="utf-8")
        cases = {
            "field_order": (
                valid.replace(
                    '\"화자발언\" 없음\n<나레이션> \"케이크 상태가 이상해\"',
                    '<나레이션> \"케이크 상태가 이상해\"\n\"화자발언\" 없음',
                    1,
                ),
                "ORIGINAL_TRANSCRIPT_FIELD_ORDER_INVALID",
            ),
            "ocr": (
                valid.replace("화면 OCR: 없음", "화면 OCR: 미확인", 1),
                "WAIT_OCR_UNRESOLVED",
            ),
            "tts": (
                valid.replace("TTS나레이션 없음", "TTS나레이션 새로 만든 해설", 1),
                "ORIGINAL_TRANSCRIPT_TTS_FORBIDDEN",
            ),
            "absence": (
                valid.replace('\"화자발언\" 없음', '\"화자발언\" 비움', 1),
                "ORIGINAL_TRANSCRIPT_ABSENCE_VALUE_INVALID",
            ),
        }
        with tempfile.TemporaryDirectory() as td:
            for name, (text, expected) in cases.items():
                with self.subTest(name=name):
                    path = Path(td) / f"{name}.md"
                    path.write_text(text, encoding="utf-8")
                    _grid, errors = validate_grid(path, "original")
                    self.assertIn(expected, {row["code"] for row in errors})

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
        transcript = harness["original_source_transcript"]
        self.assertEqual(tuple(transcript["field_order"]), (
            "(상황설명)", '"화자발언"', "<나레이션>", "TTS화자발언", "TTS나레이션",
        ))
        self.assertEqual(transcript["original_tts_value"], "없음")
        self.assertEqual(transcript["unresolved_ocr_error"], "WAIT_OCR_UNRESOLVED")
        self.assertEqual(
            transcript["contract_version"],
            "001short-original-source-transcript-v1",
        )
        self.assertEqual(transcript["legacy_without_version"], "RESUME_UNCHANGED")
        self.assertEqual(transcript["caller_version_override"], "FORBIDDEN")
        self.assertEqual(
            transcript["evidence_schema"],
            "schemas/original_source_evidence.schema.json",
        )
        self.assertEqual(workflow["grid_harness"], {"authority": "protocol.json#/grid_harness"})
        self.assertEqual(
            workflow["original_source_transcript"]["authority"],
            "protocol.json#/grid_harness/original_source_transcript",
        )

    def test_original_beats_have_five_separate_observation_fields(self):
        protocol = json.loads((SKILL_ROOT / "protocol.json").read_text(encoding="utf-8"))
        contract = protocol["original_beat_contract"]
        self.assertEqual(
            contract["required_fields"],
            [
                "situation_action",
                "lead_speaker",
                "delivery_mode",
                "narrative_function",
                "split_basis",
            ],
        )
        self.assertEqual(contract["authority"], "source_observation_only")
        self.assertEqual(contract["urakkai_substitution"], "FORBIDDEN")

    def test_stage03_has_one_independent_author_and_preserves_original_grid(self):
        protocol = json.loads((SKILL_ROOT / "protocol.json").read_text(encoding="utf-8"))
        authoring = protocol["stage03_authoring"]
        self.assertEqual(authoring["author_count"], 1)
        self.assertEqual(authoring["author_role"], "task-owner")
        self.assertEqual(authoring["method"], "independent_urakkai")
        self.assertEqual(authoring["subworkers"], 0)
        self.assertEqual(authoring["original_grid_mutation"], "FORBIDDEN")

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
        self.assertIn("Demucs는 사용자가 선택한 두 stem 모드에서만", text)
        self.assertIn("CLEAN_ONLY`는 원본 A10을 그대로 쓰며 Demucs를 실행하지 않는다", text)


if __name__ == "__main__":
    unittest.main()
