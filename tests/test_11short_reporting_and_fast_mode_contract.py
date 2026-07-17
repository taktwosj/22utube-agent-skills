from __future__ import annotations

import json
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode


SKILL = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "000short-production-agent"
    / "SKILL.md"
)
SKILL_DIR = SKILL.parent
ROOT = SKILL.parents[2]
LAYOUT_CONTRACT = SKILL_DIR / "03_CAPCUT_LAYOUT_CONTRACT.md"
HARNESS_REQUIREMENTS = SKILL_DIR / "04_HARNESS_REQUIREMENTS.md"
REPORT_CONTRACT = SKILL_DIR / "07_DRAFT_FAST_REPORT_CONTRACT.md"
SIMILARITY_CONTRACT = SKILL_DIR / "08_SIMILARITY_LOOP_CONTRACT.md"
TIMELINE_GATE = SKILL_DIR / "scripts" / "validate_capcut_timeline_order.py"
PRODUCTION_GATE = SKILL_DIR / "scripts" / "validate_production_gate.py"
CONTRACT_FILES = [
    SKILL,
    SKILL_DIR / "02_PIPELINE_RULES.md",
    LAYOUT_CONTRACT,
    HARNESS_REQUIREMENTS,
    SKILL_DIR / "05_CODEX_EXECUTION_PROMPT.md",
    SKILL_DIR / "06_CAPCUT_CUT_ASSEMBLY_CONTRACT.md",
    REPORT_CONTRACT,
    SIMILARITY_CONTRACT,
    TIMELINE_GATE,
    PRODUCTION_GATE,
]


class ReportingAndFastModeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [str(path) for path in CONTRACT_FILES if not path.is_file()]
        if missing:
            raise AssertionError(f"missing contract file(s): {missing}")
        cls.text = "\n\n".join(
            f"\n<!-- {path.relative_to(ROOT)} -->\n" + path.read_text(encoding="utf-8")
            for path in CONTRACT_FILES
        )

    def test_report_contract_sections_are_present(self):
        required = [
            "## 11short Factory Report Contract",
            "DRAFT_FAST report shape",
            "FINAL_LOCK final report shape",
            "COPY_READY_OUTPUT_BLOCK",
            "CAPCUT_COPY_BLOCK_LAST",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_fast_mode_cost_budget_is_explicit(self):
        required = [
            "DRAFT_FAST_COST_BUDGET",
            "skill_rule_check=5-10%",
            "input_srt_tts=15-25%",
            "capcut_create_rebuild=35-45%",
            "korean_repair=0-5%",
            "final_verify_report=10-15%",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_korean_text_gate_blocks_mojibake_before_repair(self):
        required = [
            "KOREAN_TEXT_FAST_GATE",
            "NO_INLINE_KOREAN_IN_SHELL",
            "MOJIBAKE_PATTERN_FAIL",
            "draft_content.json text scan",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_capcut_mandatory_settings_are_visible_in_skill(self):
        required = [
            "QualityEnhance",
            "-14 LUFS",
            "smart_color_adjust",
            "clear",
            "sharpen",
            "particle",
            "30-50",
            "5-30",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_draft_fast_disarms_final_lock_only_gates(self):
        required = [
            "DRAFT_FAST_WORKING_DRAFT_CREATED",
            "WORKING_DRAFT_CREATED",
            "technical_ready=true",
            "upload_ready=YES",
            "pre_capcut_script_package.md",
            "FINAL_LOCK only",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_current_template_defaults_include_shrt_white_black_and_insta(self):
        layout = LAYOUT_CONTRACT.read_text(encoding="utf-8")
        harness = HARNESS_REQUIREMENTS.read_text(encoding="utf-8")
        self.assertIn("shrt white", layout)
        self.assertIn("black", layout)
        self.assertIn("insta white", layout)
        self.assertIn("shrt white", harness)
        self.assertIn("black", harness)
        self.assertIn("insta white", harness)
        self.assertNotIn("subtitle_1", layout)
        self.assertIn("tts_caption/audio_role=none", layout)
        self.assertNotIn("verified_speaker_1", layout)

    def test_shrt_white_base_contract_preserves_operator_row_order(self):
        layout = LAYOUT_CONTRACT.read_text(encoding="utf-8")
        harness = HARNESS_REQUIREMENTS.read_text(encoding="utf-8")
        validator = TIMELINE_GATE.read_text(encoding="utf-8")

        for token in [
            "Shtr White Base",
        ]:
            self.assertNotIn(token, layout)

        for token in [
            "Shrt White Base - 2026-07-08",
            "shrt white",
            "T1 = top title 1",
            "T2 = top title 2",
            "T3 = TTS / 나레이션 자막",
            "T4 = \"화자발언\"",
            "T5 = (상황설명)",
            "V6 = 인스타 또는 블랙 템플릿 이미지",
            "E7 = 미러링 편집효과",
            "V8 = 원본영상, 음소거상태",
            "A9 = 나레이션",
            "A10 = 화자발언 / 원본화자 오디오",
            "A11 = 효과음, optional",
            "A12 = BGM",
            "Do not replace `shrt white` with `260708 short`",
            "hard-coded `REFERENCE_NAME`",
            "FAIL_STALE_DERIVED_REFERENCE_BUILDER",
            "this section overrides the older generic `T1~T6` table",
            "there is no `source_speech_2` row",
            "`T5` is the situation row",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, layout)

        for token in [
            "catcup_reference_layout_profile=shrt_white_base_v1",
            "catcup_reference_project=shrt white",
            "reference_project_name=shrt white",
            "derived_from_reference_project=true",
            "90_reports/build_*_base_v2.py",
            "`T1`, `T2`, `TTS`, `\"화자발언\"`, `(상황설명)`",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, harness)

        for token in [
            '"shrt_white_base_v1"',
            '"reference_project": "shrt white"',
            '"track_count": 12',
            '"text_track_count": 5',
            '"required_role_order"',
            '"source_speech_1"',
            '"situation_emotion"',
            '"draft_text_track_index_order": "descending"',
            '"260708 short"',
        ]:
            with self.subTest(token=token):
                self.assertIn(token, validator)

        module = load_source_module_no_bytecode("timeline_gate_shrt_white", TIMELINE_GATE)
        template = module.CATCUP_TEMPLATE_MASTERS["shrt_white_base_v1"]
        self.assertEqual(template["reference_project"], "shrt white")
        self.assertEqual(
            template["required_role_order"],
            (
                "top_title_1",
                "top_title_2",
                "tts",
                "source_speech_1",
                "situation_emotion",
            ),
        )
        self.assertEqual(template["draft_text_track_index_order"], "descending")
        with self.assertRaisesRegex(module.GateFail, "unsupported CatCup role"):
            module.parse_catcup_role_order(
                ["top_title_1", "top_title_2", "tts", "source_speech_1", "source_speech_2"],
                "catcup_text_role_order_top_to_bottom",
                template["required_role_order"],
            )

    def test_post_capcut_gate_fails_mojibake_text(self):
        module = load_source_module_no_bytecode("timeline_gate", TIMELINE_GATE)

        clean = {
            "materials": {
                "texts": [
                    {"id": "clean", "content": json.dumps({"text": "정상 자막"}, ensure_ascii=False)}
                ]
            }
        }
        self.assertEqual(module.validate_korean_text_fast_gate(clean)["korean_text_fast_gate"], "PASS")

        broken = {
            "materials": {
                "texts": [
                    {"id": "broken", "content": json.dumps({"text": "????"}, ensure_ascii=False)}
                ]
            }
        }
        with self.assertRaisesRegex(module.GateFail, "KOREAN_TEXT_FAST_GATE"):
            module.validate_korean_text_fast_gate(broken)

    def test_post_capcut_gate_requires_report1_handoff_pre_gate_evidence(self):
        module = load_source_module_no_bytecode("timeline_gate_report1_handoff_required", TIMELINE_GATE)

        with self.assertRaisesRegex(module.GateFail, "WAIT_REPORT1_HANDOFF_GATE"):
            module.validate_post_gate(
                Path("."),
                {
                    "status": "PASS",
                    "production_allowed": True,
                    "selected_remix_order": ["A"],
                },
                {
                    "draft_name": "test",
                    "actual_render_order": ["A"],
                },
                None,
            )

    def test_pre_capcut_gate_no_longer_requires_final_report_before_capcut(self):
        gate_text = PRODUCTION_GATE.read_text(encoding="utf-8")
        self.assertIn("pre_capcut_script_package_status", gate_text)
        self.assertNotIn("final_report_before_capcut", gate_text)

    def test_similarity_loop_contract_is_routed_and_bounded(self):
        required = [
            "08_SIMILARITY_LOOP_CONTRACT.md",
            "REFERENCE_FINGERPRINT_REQUIRED",
            "DRAFT_FAST_SIMILARITY_LOOP",
            "SIMILARITY_LOOP_MAX_ITERATIONS",
            "similarity_loop_ledger.jsonl",
            "WAIT_REFERENCE",
            "Do not use similarity loops to bypass",
            "SCRIPT_LOCK",
            "source.mp4",
            "patch only the failed similarity dimensions",
            "every dimension is PASS",
            "gate_integrity is reflective only",
            "dimension_vector_only",
            "still PATCH after the iteration limit",
            "template_profile_similarity",
            "middle_caption_format_similarity",
            "active_draft_cleanup",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_draft_fast_false_pass_is_blocked_by_template_loop_gates(self):
        required = [
            "DRAFT_FAST_REFERENCE_SIMILARITY_REQUIRED",
            "template_profile_match",
            "middle_caption_format_match",
            "reference_visual_preview_match",
            "active_draft_cleanup_gate",
            "FAIL_TEMPLATE_PROFILE_MISMATCH",
            "FAIL_MIDDLE_CAPTION_FORMAT_MISMATCH",
            "FAIL_PROJECT_CLEANUP",
            "SIMILARITY_LOOP_PASS is not DRAFT_FAST_PASS",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_draft_fast_report_separates_technical_visual_and_user_review(self):
        required = [
            "TECHNICAL_DRAFT_CHECK",
            "LOCAL_JSON_CHECK_PASS",
            "MEDIA_LINK_CHECK_PASS",
            "VISUAL_TEMPLATE_CHECK",
            "USER_CAPCUT_REVIEW_WAIT",
            "FINAL_LOCK_WAIT",
            "JSON PASS != 영상 PASS",
            "runtime HASH_MATCH != CapCut quality PASS",
            "DRAFT_FAST != FINAL_LOCK",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_report_two_is_final_report_with_upload_copy_until_user_export(self):
        required = [
            "Report 2 Contract",
            "보고서2",
            "WAIT_REPORT1_APPROVAL_TTS_DECISION",
            "report1_approved",
            "voice_audio_route_decided",
            "보고서1 승인",
            "TTS/오디오 방식 결정",
            "CapCut 프로젝트 생성 후 보고",
            "한글 우선",
            "예/아니오 단답",
            "기본 양식",
            "보고서2 시작",
            "최종보고서: 예",
            "REPORT2_FINAL",
            "제목:",
            "내용(출처 태그 포함):",
            "USER_CAPCUT_REVIEW_WAIT",
            "사용자가 CapCut을 열고 문제를 제시",
            "수정 후 다시 보고서2",
            "REPORT2_REVISED",
            "수동 편집 길이 변화",
            "MANUAL_EDIT_EXPECTED",
            "길이 차이만으로 FAIL 금지",
            "현재 draft_content.json 기준",
            "사용자가 내보내기로 영상 생성",
            "REPORT2_CLOSED_BY_USER_EXPORT",
            "보고서2 종료",
            "업로드 준비 완료",
            "명시 승인 전 아니오",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_stage_scope_gate_blocks_silent_project_file_default(self):
        required = [
            "Stage Scope Gate",
            "WAIT_USER_STAGE_DECISION",
            "stage_1_script",
            "stage_2_full",
            "G0 INTAKE",
            "G1 STAGE 1",
            "G2 STAGE 1 STOP",
            "G3 STAGE 2 ENTRY",
            "G4 FINAL",
            "G2 STAGE 1 STOP = 보고서1",
            "stage_gate_todo.md",
            "stage_scope_report.md",
            "RE-ENTRY",
            "REWORK_IN_NEW_CHAT_ANALYZE_FIRST",
            "MIDDLE_PACKAGE_REWORK_REVIEW_GATE",
            "REPORT_BEFORE_ACTION",
            "DRAFT_FAST_EXPLICIT_ONLY",
            "`DRAFT_FAST`",
            "`검토용 draft만`",
            "`검토용 드래프트만`",
            "`빠른 초안`",
            "`기술 초안`",
            "DRAFT_FAST does not waive `report1_approved + voice_audio_route_decided`",
            "AUTO_FULL_CAPCUT_PROJECT",
            "자동모드",
            "user says 자동모드 = stage_2_full",
            "슈퍼톤",
            "supertone",
            "tts 만들",
            "tts 생성",
            "tts mp3",
            "캣컵프로젝트파일까지",
            "캣컵 프로젝트 파일까지",
            "캐컷프로젝트파일까지",
            "capcut project",
            "INTERACTIVE_SCRIPT_APPROVAL",
            "project_file_request_mode=AUTO_FULL_CAPCUT_PROJECT",
            "URL_PLUS_GEMINI_PLUS_PROJECT_FILE",
            "The validator must still see the user-stage",
            "Do not default URL+Gemini intake to AUTO_FULL or DRAFT_FAST",
            "A generic `진행/해줘` next to stage-1 wording is not stage-2 permission",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

        forbidden = [
            "Every ordinary 11short factory run is `DRAFT_FAST` by default",
            "PROJECT_FILE_REQUEST_DEFAULT=AUTO_FULL_CAPCUT_PROJECT",
            "Production Mode Gate",
            "G2 STAGE 1 STOP = [DRAFT_FAST 쇼츠공장 보고]",
            "For stage-1 script-only work, use the `DRAFT_FAST report shape`",
            "1차 쇼츠공장 보고",
            "1차 report",
        ]
        for token in forbidden:
            with self.subTest(forbidden=token):
                self.assertNotIn(token, self.text)

    def test_final_capcut_project_gate_is_by_shorts_type_and_template(self):
        required = [
            "final_capcut_project_file",
            "shorts_type_template_matrix",
            "story_type",
            "production_type",
            "template_profile",
            "caption_layer_role_match",
            "caption_position_match",
            "reference_frame_similarity",
            "visual_screenshot_required",
            "source_caption_overlap_check",
            "capcut_processing_idle_check",
            "mandatory_capcut_media_settings_status",
            "WAIT_USER_CAPCUT_REVIEW",
            "WAIT_VISUAL_SCREENSHOT_REQUIRED",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_audio_assembly_contract_preserves_narration_and_separates_source_audio(self):
        required = [
            "Audio Assembly Contract",
            "Narration is never trimmed",
            "preserve the full audio duration",
            "shrt white canonical audio mapping",
            "audio.narration_tts  -> A9",
            "audio.speaker_source -> A10",
            "audio.sfx            -> A11",
            "audio.bgm            -> A12",
            "source video track",
            "source-video audio muted by default",
            "tikitaka_segment_audio_plan",
            "narration_not_trimmed",
            "source_audio_separated",
            "source_video_muted",
            "audio_loudness_normalize target -14 LUFS",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_capcut_edit_ready_is_goal_not_upload_ready(self):
        required = [
            "CAPCUT_EDIT_READY",
            "HUMAN_POLISH_READY",
            "CAPCUT_EDIT_READY_GATE",
            "human_polish_required",
            "manual_polish_items",
            "upload_ready is not the goal",
            "production pass is not the goal",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_production_requires_script_handoff_gate_and_block_map(self):
        required = [
            "SCRIPT_HANDOFF_GATE",
            "SCRIPT_LOCK_PACKAGE",
            "WAIT_SCRIPT_HANDOFF_GATE",
            "script_handoff_gate.json",
            "block_map.json",
            "edit_block_sequence",
            "block_voice_switch_map",
            "original_order",
            "urakkai_order",
            "edit_order implemented",
            "source_block_id",
            "edit_id",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_capcut_openable_project_uses_script_lock_package_as_source_of_truth(self):
        required = [
            "CAPCUT_OPENABLE_PROJECT",
            "2nd stage = CAPCUT_OPENABLE_PROJECT",
            "SCRIPT_LOCK_PACKAGE is the Source of Truth",
            "No SCRIPT_LOCK_PACKAGE, no CapCut build",
            "openable CapCut project",
            "opening in CapCut is not enough",
            "role map/audio map/TTS body reflected",
            "source video visual only",
            "embedded source audio muted",
            "timeline validation PASS",
            "project candidate",
            "production PASS candidate",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_capcut_openable_entry_is_separate_from_final_lock_validator(self):
        required = [
            "validate_capcut_openable_project_entry",
            "validate_shared_requirements is FINAL_LOCK only",
            "`persona_mode/script_gate` are FINAL_LOCK blockers",
            "n8n is a FINAL_LOCK blocker only when",
            "Ignore missing\nn8n evidence here unless the package explicitly requires n8n",
            "do not stop CapCut project creation",
            "next_gate: ASSET_PREP_GATE",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_template_base_must_be_neutral_not_episode_story_authority(self):
        required = [
            "neutral_base_template",
            "episode-specific project such as china-driver",
            "structure seed only",
            "not story/content authority",
            "replace with a neutral base template",
            "SCRIPT_LOCK_PACKAGE remains the Source of Truth",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_template_reference_must_be_resolved_before_capcut_build(self):
        required = [
            "TEMPLATE_REFERENCE_RESOLUTION_GATE",
            "reference_project_name",
            "reference_project_path",
            "user-visible CapCut reference project",
            "260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1",
            "prior derived",
            "FAIL_TEMPLATE_ROOT_NOT_RESOLVED",
            "Do not chain derivatives",
            "Do not create a helper-only fresh draft",
            "FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED",
            "FAIL_TEMPLATE_REFERENCE_MISMATCH",
            "report both the root template and any style/sample project",
            "template_profile is not satisfied by `neutral_base_template` text alone",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_capcut_lanes_follow_voice_switch_map(self):
        required = [
            "V1 source video",
            "A9 narration/TTS",
            "A10 speaker/source",
            "A11 SFX",
            "A12 BGM",
            "audio.speaker_source ON -> A10",
            "audio.narration_tts ON -> A9",
            "A9 OFF",
            "A10 OFF",
            "source_audio=on/off/duck",
            "tts=on/off",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
