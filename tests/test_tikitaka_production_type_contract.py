from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "00-tikitaka" / "SKILL.md"


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

    def test_tikitaka_routes_auto_full_vs_interactive_approval_before_production(self):
        text = SKILL.read_text(encoding="utf-8")

        for token in [
            "AUTO_FULL_CAPCUT_PROJECT",
            "INTERACTIVE_SCRIPT_APPROVAL",
            "URL_PLUS_GEMINI_PLUS_PROJECT_FILE",
            "URAKKAI_DIRECTION_CHECKPOINT",
            "SCRIPT_APPROVAL_CHECKPOINT",
            "TEMPLATE_APPROVAL_CHECKPOINT",
            "DRAFT_FAST_EXPLICIT_ONLY",
            "Do not stop at DRAFT_EYE_REVIEW when the user explicitly asks for project-file completion",
            "Do not choose DRAFT_FAST just because the output is not upload-ready",
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


if __name__ == "__main__":
    unittest.main()
