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

    def test_current_template_defaults_are_black_and_insta_only(self):
        layout = LAYOUT_CONTRACT.read_text(encoding="utf-8")
        harness = HARNESS_REQUIREMENTS.read_text(encoding="utf-8")
        self.assertIn("black", layout)
        self.assertIn("insta white", layout)
        self.assertIn("black", harness)
        self.assertIn("insta white", harness)
        self.assertIn("there is no separate official", self.text)
        self.assertNotIn("subtitle_1", layout)
        self.assertNotIn("tts_caption", layout)
        self.assertNotIn("verified_speaker_1", layout)

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

    def test_draft_fast_is_explicit_only_and_project_file_defaults_to_auto_full(self):
        required = [
            "DRAFT_FAST_EXPLICIT_ONLY",
            "AUTO_FULL_CAPCUT_PROJECT",
            "INTERACTIVE_SCRIPT_APPROVAL",
            "PROJECT_FILE_REQUEST_DEFAULT",
            "URL_PLUS_GEMINI_PLUS_PROJECT_FILE",
            "Do not default ordinary project-file requests to DRAFT_FAST",
            "DRAFT_FAST is allowed only when the user explicitly says",
            "perfect local CapCut project file",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

        forbidden = [
            "Every ordinary 11short factory run is `DRAFT_FAST` by default",
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
            "A10 narration / TTS lane",
            "A9 source_audio lane",
            "A8 bgm lane",
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
            "persona_mode/script_gate/n8n are FINAL_LOCK blockers",
            "not CAPCUT_OPENABLE_PROJECT blockers",
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

    def test_capcut_lanes_follow_voice_switch_map(self):
        required = [
            "V1 source video",
            "A10 TTS narration",
            "A9 source_audio",
            "A8 SFX",
            "A7 BGM",
            "speaker_quote = A9 ON + A10 OFF",
            "tts_narration = A10 ON + A9 OFF",
            "situation_caption = A9 OFF + A10 OFF by default",
            "source_audio=on/off/duck",
            "tts=on/off",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
