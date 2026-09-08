# -*- coding: utf-8 -*-
"""움직이는 설명카드(NARRATION_VIDEO)가 조립까지 통하는지 본다.

정지 PNG 대신 하이퍼프레임 영상을 쓰는 회차가 있다. 컴파일러와 GRID 는 이미
NARRATION_VIDEO 를 알고 있었지만 V8 빌더만 거부해서, 컴파일은 통과하고 빌드에서
V8_CARD_TYPE_UNSUPPORTED 로 죽었다.

영상은 인용 클립이 아니라 설명카드다. 그래서
  - 이미지 트랙(정지 카드와 같은 자리)에 들어가고
  - 나레이션 음성이 붙고
  - `출처` 자막이 붙지 않는다
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V8 = ROOT / "skills" / "119-politics-longform-capcut" / "scripts" / "build_politics_v8_project.py"
GEN_SCRIPT = ROOT / "skills" / "spine-script-119" / "scripts" / "gen_script.py"
GEN_EVIDENCE = ROOT / "skills" / "spine-script-119" / "scripts" / "gen_evidence.py"


class NarrationVideoCardTests(unittest.TestCase):
    def test_v8_builder_handles_narration_video(self):
        text = V8.read_text(encoding="utf-8")
        self.assertIn('elif kind == "NARRATION_VIDEO":', text)
        self.assertIn('raise RuntimeError(f"V8_VIDEO_REQUIRED:{card[\'card_id\']}")', text)

    def test_narration_video_rides_the_image_track(self):
        """설명카드 자리는 이미지 트랙이다. 출처 트랙이 아니다."""
        text = V8.read_text(encoding="utf-8")
        branch = text.split('elif kind == "NARRATION_VIDEO":', 1)[1].split("else:", 1)[0]
        self.assertIn("target_track=image_track", branch)
        self.assertIn('kind="video"', branch)
        self.assertIn("has_audio=False", branch)

    def test_narration_video_gets_no_source_label(self):
        """`출처` 자막은 인용 클립에만 붙는다."""
        text = V8.read_text(encoding="utf-8")
        branch = text.split('elif kind == "NARRATION_VIDEO":', 1)[1].split("else:", 1)[0]
        code = " ".join(
            line for line in branch.splitlines() if not line.strip().startswith("#"))
        self.assertNotIn("출처", code)
        self.assertNotIn("source_display_label", code)
        self.assertNotIn("clone_text", code)

    def test_narration_video_gets_narration_audio(self):
        text = V8.read_text(encoding="utf-8")
        self.assertIn('if kind in {"NARRATION_IMAGE", "NARRATION_VIDEO"}:', text)

    def test_unknown_card_type_still_raises(self):
        self.assertIn("V8_CARD_TYPE_UNSUPPORTED", V8.read_text(encoding="utf-8"))

    def test_spine_emits_narration_video_when_hyperframe_exists(self):
        text = GEN_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('root / "hyperframes"', text)
        self.assertIn("NARRATION_VIDEO' if moving else 'NARRATION_IMAGE", text)

    def test_moving_card_drops_the_inset_style_profile(self):
        """인셋 템플릿으로 렌더한 물건이 아니므로 style_profile 을 비운다.

        비우지 않으면 preflight 가 INSET_CARD_IMAGE_REQUIRED 로 막는다.
        """
        text = GEN_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("'N/A' if moving else 'DEMOCRATIC_BLUE_INSET_CARD_V2'", text)

    def test_evidence_emits_video_fields(self):
        text = GEN_EVIDENCE.read_text(encoding="utf-8")
        for field in ("video_file", "video_sha256", "video_start_us", "video_duration_us"):
            self.assertIn(field, text)

    def test_evidence_clamps_video_to_card_duration(self):
        """영상이 나레이션보다 길어도 카드 길이만큼만 쓴다."""
        text = GEN_EVIDENCE.read_text(encoding="utf-8")
        self.assertIn('"video_duration_us": r["target_duration_us"]', text)

    def test_sources_parse(self):
        for path in (V8, GEN_SCRIPT, GEN_EVIDENCE):
            ast.parse(path.read_text(encoding="utf-8"), path.name)


if __name__ == "__main__":
    unittest.main()
