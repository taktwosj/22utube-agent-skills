from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "00-tikitaka" / "SKILL.md"
SINGLE_SOURCE = (
    ROOT
    / "skills"
    / "00-tikitaka"
    / "shorts_script_analysis_single_source_v20260706.md"
)


class TikitakaProductionTypeContractTests(unittest.TestCase):
    def test_tikitaka_decides_story_and_production_type_before_draft(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "Story And Production Type Gate",
            "story_type",
            "production_type",
            "Story Type Matrix (S1-S7)",
            "S1 reversal_preview",
            "S2 ranking_reorder",
            "S3 tikitaka_variety",
            "S4 observation_caption",
            "S5 emotion_payoff",
            "S6 info_explainer",
            "S7 card_story",
            "full_tts_bgm",
            "bgm_caption_only",
            "narration_plus_speaker",
            "original_audio_caption",
            "tts_intro_original_body",
            "instagram_card_tts",
            "Tikitaka must decide these before writing the first draft",
            "yellow_lower_caption is not default",
            "CapCut layers: T1/T2 top, T3 TTS, T4/T5 quote, T6 situation/card",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_instagram_card_tts_is_situation_caption_not_speaker_or_tts(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "instagram_card_tts",
            "card_asset_role",
            "visual_situation_card",
            "caption_type=situation_caption",
            "visible_text_role=situation",
            "capcut_text_layer=T6",
            "not speaker_quote",
            "not tts_narration",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_routes_stage_scope_before_production(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "Stage Scope Gate",
            "stage_1_script",
            "stage_2_full",
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
            "WAIT_USER_STAGE_DECISION",
            "G0 INTAKE",
            "G1 STAGE 1",
            "G2 STAGE 1 STOP",
            "G3 STAGE 2 ENTRY",
            "G4 FINAL",
            "stage_gate_todo.md",
            "stage_scope_report.md",
            "REWORK_IN_NEW_CHAT_ANALYZE_FIRST",
            "MIDDLE_PACKAGE_REWORK_REVIEW_GATE",
            "REPORT_BEFORE_ACTION",
            "INTERACTIVE_SCRIPT_APPROVAL",
            "URAKKAI_DIRECTION_CHECKPOINT",
            "SCRIPT_APPROVAL_CHECKPOINT",
            "TEMPLATE_APPROVAL_CHECKPOINT",
            "DRAFT_FAST_EXPLICIT_ONLY",
            "A generic",
            "진행/해줘",
            "is not stage-2 permission",
            "Do not choose DRAFT_FAST just because the output is not upload-ready",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)
        self.assertNotIn("Continuation Mode Gate", text)

    def test_report_one_is_korean_yes_no_script_approval_report(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "Report 1 Contract",
            "보고서1",
            "대본 승인용",
            "한글 우선",
            "예/아니오 단답",
            "상단",
            "timed 중단",
            "중단 TTS 글자만 복사",
            "사용자 OK 대기",
            "TTS_USER_DECISION_WAIT",
            "사용자가 OK한 뒤",
            "사용자 제공 TTS",
            "Codex/API TTS 생성",
            "보고서2로 이동",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_report_one_names_000short_as_next_skill_for_report_two(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "다음 스킬: 000short-production-agent",
            "다음 단계: 보고서2 / CAPCUT_OPENABLE_PROJECT",
            "다음 채팅에 붙일 지시",
            "Use $000short-production-agent",
            "보고서1 승인 + TTS/오디오 방식 결정",
            "00-tikitaka는 보고서2를 작성하지 않는다",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_audio_policy_preserves_full_narration(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "narration_duration_policy=preserve_full_tts",
            "production_adjustment=extend_visual_or_shift_source_audio",
            "narration=TTS lane",
            "source_audio=on/off/duck by segment",
            "bgm=separate optional/required lane",
            "source_video_audio=muted unless explicitly extracted as source_audio",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_urakkai_requires_edit_order_and_voice_switch_handoff(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "SCRIPT_LOCK_PACKAGE",
            "CAPCUT_EDIT_READY",
            "original_block_map",
            "wow_point_map",
            "urakkai_order_map",
            "edit_block_sequence",
            "block_map.json",
            "block_role_map",
            "block_voice_switch_map",
            "tts_copy_text",
            "script_handoff_gate.json",
            "SCRIPT_HANDOFF_GATE",
            "source_block_id",
            "edit_id",
            "original_order",
            "urakkai_order",
            "voice_switch_locked",
            "capcut_allowed",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_script_lock_package_is_stage_one_contract(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "Stage 1 = SCRIPT_LOCK_PACKAGE",
            "shorts type locked",
            "source structure summary",
            "urakkai structure locked",
            "wow point reordered",
            "source-to-urakkai delta table",
            "block role map",
            "block audio map",
            "TTS copy body",
            "source voice ON/OFF/duck ranges locked",
            "script_status: SCRIPT_LOCK_PACKAGE",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_script_handoff_pass_is_capcut_openable_permission_not_final_lock(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "capcut_permission: CAPCUT_OPENABLE_PROJECT_ALLOWED",
            "production_status: WAIT_CAPCUT_OPENABLE_PROJECT",
            "persona_mode/script_gate/n8n are FINAL_LOCK blockers",
            "not CAPCUT_OPENABLE_PROJECT blockers",
            "final_report_allowed=false",
            "continue to 000short-production-agent",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_defines_middle_caption_roles_without_bottom_body_text(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "display_zone=middle_under_video",
            "speaker_quote",
            "tts_narration",
            "situation_caption",
            "caption_type",
            "included_in_tts_copy=false",
            "bottom_body_caption_forbidden",
            "wow_overlay_text is optional",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_tikitaka_requires_timeline_design_before_handoff_and_humanize_gate(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "Tikitaka Current Order",
            "TTS Copy Text Naming Rule",
            "Purpose Of 1차설계서",
            "1차설계서",
            "timeline_design.json",
            "timeline_design_gate.json",
            "humanize_korean_gate.json",
            "block_role_map.json",
            "tts_copy_text.txt",
            "shorts_design_type",
            "Allowed values:",
            "SD1",
            "SD2",
            "SD3",
            "SD4",
            "unknown",
            "Humanize Korean",
            "T1/T2/TTS",
            "화자발언",
            "상황설명",
            "00script-writer is not a default stage",
            "Humanize may change wording only",
            "time_start/time_end/track/caption_type/audio_policy",
            "Do not run SCRIPT_HANDOFF_GATE before humanize_korean_gate.json=PASS",
            "TTS 만들 글자만 복사` is a legacy alias of `중단 TTS 글자만 복사`",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)

        section_start = text.index("Tikitaka Current Order")
        section_end = text.index("## Gemini Raw Intake First")
        section = text[section_start:section_end]
        order = [
            "source evidence",
            "1차설계서",
            "timeline_design.json",
            "timeline_design_gate.json",
            "humanize_korean_gate.json",
            "block_role_map.json",
            "tts_copy_text.txt",
            "script_handoff_gate.json",
            "report1_handoff.json",
        ]
        positions = [section.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))

    def test_tts_make_copy_is_legacy_alias_not_prohibited_output(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        single_source_text = SINGLE_SOURCE.read_text(encoding="utf-8")

        self.assertIn("Canonical contract label", skill_text)
        self.assertNotIn("Canonical user-facing label", skill_text)
        self.assertIn("중단 TTS 글자만 복사", skill_text)
        self.assertIn("Internal artifact", skill_text)
        self.assertIn("tts_copy_text.txt", skill_text)
        self.assertIn("Allowed alias", single_source_text)
        self.assertIn("TTS 만들 글자만 복사", single_source_text)

        prohibited_start = single_source_text.index("## Prohibited Current Outputs")
        prohibited_end = single_source_text.index("## Production Boundary")
        prohibited_section = single_source_text[prohibited_start:prohibited_end]
        prohibited_lines = [line.strip() for line in prohibited_section.splitlines()]
        self.assertNotIn("- `TTS 만들 글자만 복사`", prohibited_lines)

    def test_timeline_design_uses_semantic_audio_tracks_before_capcut_resolution(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "timeline_design.json audio track",
            "audio.narration_tts",
            "audio.speaker_source",
            "audio.sfx",
            "audio.bgm",
            "semantic_lane",
            "resolved_capcut_track",
            "resolved_by",
            "000short-production-agent",
            "Stage 1에서는 A9/A10/A11/A12",
            "실제 CapCut A-track 매핑은 Stage 2",
            "오디오 / 나레이션·TTS",
            "오디오 / 화자발언·원본화자",
            "오디오 / SFX",
            "오디오 / BGM",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
