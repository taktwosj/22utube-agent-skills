#!/usr/bin/env python3
"""112 정치 다큐 기본 디자인 프리셋 계약 테스트."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL / "SKILL.md"
REFERENCE = SKILL / "references" / "political-documentary-design-preset.md"
PRESET = SKILL / "assets" / "political-documentary-defaults.json"


class TestPoliticalDocumentaryPreset(unittest.TestCase):
    def test_skill_links_the_fixed_profile(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("political-documentary-design-preset.md", text)
        self.assertIn("assets/political-documentary-defaults.json", text)
        self.assertIn("PROFILE_OVERRIDE=LATEST_EXPLICIT_USER_INSTRUCTION_ONLY", text)

    def test_machine_preset_has_locked_values(self):
        data = json.loads(PRESET.read_text(encoding="utf-8"))
        self.assertEqual(data["profile_id"], "politics_documentary_broadcast_v1")
        self.assertTrue(data["locked_by_default"])
        self.assertEqual(data["palette"]["background"], "#071426")
        self.assertEqual(data["palette"]["accent_cyan"], "#21C7D9")
        self.assertEqual(data["palette"]["accent_mustard"], "#F4C542")
        self.assertEqual(data["source"]["label"], "ACTUAL_YOUTUBE_CHANNEL_NAME")
        self.assertFalse(data["source"]["internal_source_id_visible"])
        self.assertEqual(data["comment_cta"]["line_1"], "댓글로 의견 부탁드립니다.")
        self.assertEqual(data["comment_cta"]["line_2"], "구독과 좋아요 부탁드립니다.")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
