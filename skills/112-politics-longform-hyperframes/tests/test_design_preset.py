#!/usr/bin/env python3
"""112 정치 다큐 기본 디자인 프리셋 계약 테스트."""

from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL / "SKILL.md"
REFERENCE = SKILL / "references" / "political-documentary-design-preset.md"
VISUAL_GRAMMAR = SKILL / "references" / "narration-visual-grammar.md"
VISUAL_REFERENCE = SKILL / "references" / "visual-reference-frames.md"
PRESET = SKILL / "assets" / "political-documentary-defaults.json"
REFERENCE_MANIFEST = SKILL / "assets" / "political-documentary-reference-frames.json"


class TestPoliticalDocumentaryPreset(unittest.TestCase):
    def test_skill_links_the_fixed_profile(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("political-documentary-design-preset.md", text)
        self.assertIn("assets/political-documentary-defaults.json", text)
        self.assertIn("PROFILE_OVERRIDE=LATEST_EXPLICIT_USER_INSTRUCTION_ONLY", text)

    def test_machine_preset_has_locked_values(self):
        data = json.loads(PRESET.read_text(encoding="utf-8"))
        self.assertEqual(data["profile_id"], "politics_documentary_broadcast_v3")
        self.assertTrue(data["locked_by_default"])
        self.assertEqual(data["palette"]["background"], "#071426")
        self.assertEqual(data["palette"]["accent_cyan"], "#21C7D9")
        self.assertEqual(data["palette"]["accent_mustard"], "#F4C542")
        self.assertEqual(data["source"]["label"], "ACTUAL_YOUTUBE_CHANNEL_NAME")
        self.assertFalse(data["source"]["internal_source_id_visible"])
        self.assertEqual(data["comment_cta"]["line_1"], "댓글로 의견 부탁드립니다.")
        self.assertEqual(data["comment_cta"]["line_2"], "구독과 좋아요 부탁드립니다.")
        self.assertEqual(data["comment_cta"]["header_position"], "RIGHT_TOP")
        self.assertTrue(data["comment_cta"]["show_on_chapter_frames"])
        self.assertFalse(data["comment_cta"]["bottom_right_visible"])
        self.assertTrue(data["comment_cta"]["final_end_card"])

    def test_narration_visual_grammar_is_locked(self):
        data = json.loads(PRESET.read_text(encoding="utf-8"))
        system = data["narration_visual_system"]
        self.assertEqual(
            system["templates"],
            [
                "FLOW_NODES",
                "TIMELINE_PATH",
                "CORE_ORBIT",
                "COMPARE_SPLIT",
                "STEP_PROGRESS",
                "QUOTE_SPOTLIGHT",
            ],
        )
        self.assertIsNone(system["fallback_template"])
        self.assertEqual(system["minimum_unique_templates_for_six_chapters"], 4)
        self.assertEqual(system["maximum_consecutive_same_template"], 1)
        self.assertEqual(system["maximum_major_shapes_per_screen"], 5)
        self.assertEqual(system["sync_authority"], "FINAL_SRT")
        self.assertFalse(system["source_video_overlay_diagrams"])
        self.assertFalse(system["external_image_generation_default"])
        self.assertEqual(
            system["person_cutout_policy"],
            "USER_APPROVED_REFERENCE_OR_EXISTING_ASSET",
        )

        text = VISUAL_GRAMMAR.read_text(encoding="utf-8")
        for name in system["templates"]:
            self.assertIn(name, text)
        self.assertIn("같은 문법 연속 사용", text)
        self.assertIn("챕터 CTA 상단 우측", text)
        self.assertIn("승인 대본 밖 문구 추가 0건", text)

    def test_user_reference_frames_are_exact_and_linked(self):
        data = json.loads(PRESET.read_text(encoding="utf-8"))
        manifest = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            data["visual_reference_manifest"],
            "assets/political-documentary-reference-frames.json",
        )
        self.assertEqual(manifest["profile_id"], data["profile_id"])
        self.assertEqual(
            [item["type"] for item in manifest["frames"]],
            data["approved_screen_types"],
        )
        for item in manifest["frames"]:
            path = SKILL / item["path"]
            self.assertTrue(path.is_file(), item["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(digest, item["sha256"])

        text = VISUAL_REFERENCE.read_text(encoding="utf-8")
        for item in manifest["frames"]:
            self.assertIn(item["type"], text)

    def test_thumbnail_handoff_is_exact(self):
        data = json.loads(PRESET.read_text(encoding="utf-8"))
        handoff = data["thumbnail_handoff"]
        self.assertEqual(handoff["recommended_image_people_count"], 3)
        self.assertTrue(handoff["same_person_allowed"])
        self.assertEqual(handoff["hook_word_count"], 3)
        self.assertEqual(handoff["main_copy_count"], 1)
        self.assertEqual(
            handoff["field_order"],
            [
                "추천 이미지 인물 3명",
                "후킹 단어 3개",
                "메인 문구 1",
                "보조 문구 2",
                "디자인",
            ],
        )

    def test_reference_contains_no_internal_source_label_default(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("SOURCE_LABEL=ACTUAL_YOUTUBE_CHANNEL_NAME", text)
        self.assertIn("SOURCE_INTERNAL_ID_VISIBLE=false", text)
        self.assertIn("게임 HUD·사이버펑크 인상 0", text)
        self.assertIn("HEADER_COMMENT_POSITION=RIGHT_TOP", text)
        self.assertIn("FINAL_CTA_END_CARD=true", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
