from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_episode_capcut as builder
import build_episode_locks
import production_profile
import track_template_matrix as templates
import validate_capcut_project
import validate_design_lock
import validate_executable_protocol


PRESET_ROOT = SKILL_ROOT / "presets" / "foreign-viral-dialogue-v1"
PROFILE_PATH = PRESET_ROOT / "profile.json"
EXPECTED_SELECTOR = {
    "schema_version": "001short-production-profile-v1",
    "profile_id": "foreign-viral-dialogue-v1",
    "assembly_type": "3",
    "template_profile": "shrt_black_headline_dialogue_v1",
    "production_mode": "URAKKAI",
    "audio_policy": "A10_REASSEMBLED_SYNC",
}


def _base_timeline(extra: list[dict]) -> dict:
    duration = 3_000_000
    return {
        "primary_speaker_id": "SON",
        "segments": [
            {"segment_id": "V01", "role": "VIDEO", "start": 0, "duration": duration},
            {"segment_id": "FX", "role": "SCREEN_EFFECT", "start": 0, "duration": duration},
            {"segment_id": "WHITE", "role": "SCREEN_WHITE", "start": 0, "duration": duration},
            {"segment_id": "T1", "role": "T1", "content_type": "TITLE", "text": "엄마와 아들", "start": 0, "duration": duration},
            {
                "segment_id": "T2", "role": "T2", "content_type": "TITLE",
                "text": "하필 처녀파티 출동", "emphasis_range": [3, 7],
                "start": 0, "duration": duration,
            },
            {"segment_id": "SOURCE", "role": "SOURCE_CREDIT", "text": "출처 : 원본 채널", "start": 0, "duration": duration},
            *extra,
        ],
    }


class ForeignViralDialoguePresetTest(unittest.TestCase):
    def test_selector_resolves_without_a_forked_engine(self):
        payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload, EXPECTED_SELECTOR)
        resolved = production_profile.resolve_production_profile(payload)
        self.assertEqual(resolved.execution_strategy, "original_audio_caption")
        self.assertEqual(resolved.audio_source, "REASSEMBLED_VOCAL_STEM")
        self.assertEqual(resolved.track_layout, templates.V3_TRACK_LAYOUT)
        self.assertEqual(list(PRESET_ROOT.rglob("*.py")), [])

    def test_profile_routes_glitch_and_declares_two_line_dialogue_policy(self):
        profile = templates.track_template_profile(
            templates.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE
        )
        self.assertEqual(profile.track_layout, templates.V3_TRACK_LAYOUT)
        self.assertEqual(
            dict(profile.state_track_by_effect),
            {"GLITCH_SHAKE": templates.TRACK_INDEX["STATE_GLITCH"]},
        )
        self.assertEqual(
            profile.dialogue_text_style_policy,
            templates.SPEAKER_BLUE_DIALOGUE_WHITE_TWO_LINE,
        )
        self.assertEqual(
            profile.headline_text_style_policy,
            templates.YELLOW_RED_YELLOW_EMPHASIS,
        )
        self.assertIn("SOURCE_CREDIT", profile.full_span_roles)

    def test_design_lock_requires_two_dialogue_lines_and_allows_glitch_state(self):
        dialogue = {
            "segment_id": "D01", "role": "A10_TEXT", "start": 0,
            "duration": 1_000_000, "text": "아들\n무슨 일이야?",
            "content_type": "SPEAKER", "caption_role": "A10_TEXT",
            "speaker_id": "SON", "color_role": "WHITE",
        }
        state = {
            "segment_id": "S01", "role": "STATE", "start": 1_000_000,
            "duration": 500_000, "text": "그대로 떠나는 딸",
            "content_type": "STATE", "caption_role": "STATE",
            "state_effect": "GLITCH_SHAKE",
        }
        errors = validate_design_lock.validate_role_contract(
            _base_timeline([dialogue, state]),
            3_000_000,
            template_profile=templates.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE,
        )
        self.assertEqual(errors, [])

        invalid = dict(dialogue, text="무슨 일이야?")
        errors = validate_design_lock.validate_role_contract(
            _base_timeline([invalid, state]),
            3_000_000,
            template_profile=templates.FOREIGN_VIRAL_DIALOGUE_TEMPLATE_PROFILE,
        )
        self.assertIn(
            "DIALOGUE_TWO_LINE_FORMAT_REQUIRED",
            {row["code"] for row in errors},
        )

    def test_builder_preserves_blue_speaker_and_white_dialogue_ranges(self):
        material = {
            "content": json.dumps({
                "text": "엄마\n뭐..?!",
                "styles": [
                    {"range": [0, 2], "fill": {"content": {"solid": {"color": [0.0862745, 0.545098, 1.0]}}}},
                    {"range": [2, 8], "fill": {"content": {"solid": {"color": [1.0, 1.0, 1.0]}}}},
                ],
            }, ensure_ascii=False),
        }
        builder._set_text(
            material,
            "아들\n무슨 일이야?",
            "A10_TEXT",
            style_policy=templates.SPEAKER_BLUE_DIALOGUE_WHITE_TWO_LINE,
        )
        rich = json.loads(material["content"])
        self.assertEqual(rich["text"], "아들\n무슨 일이야?")
        self.assertEqual([style["range"] for style in rich["styles"]], [[0, 2], [2, 10]])
        self.assertTrue(material["is_rich_text"])
        self.assertEqual(
            validate_capcut_project._rich_text(material, allow_partition=True),
            ("아들\n무슨 일이야?", True),
        )
        self.assertEqual(
            validate_capcut_project._rich_text(material),
            ("아들\n무슨 일이야?", False),
        )
        self.assertTrue(validate_capcut_project._dialogue_style_valid(material, rich["text"]))

        rich["styles"][0]["fill"]["content"]["solid"]["color"] = [1.0, 0.0, 0.0]
        material["content"] = json.dumps(rich, ensure_ascii=False)
        self.assertFalse(validate_capcut_project._dialogue_style_valid(material, rich["text"]))

    def test_rich_text_partition_rejects_gaps_and_overlap(self):
        def material(ranges):
            return {"content": json.dumps({
                "text": "엄마\n대사",
                "styles": [{"range": row} for row in ranges],
            }, ensure_ascii=False)}

        self.assertFalse(validate_capcut_project._rich_text(material([[0, 2], [2, 5]]))[1])
        self.assertTrue(validate_capcut_project._rich_text(
            material([[0, 2], [2, 5]]), allow_partition=True,
        )[1])
        self.assertFalse(validate_capcut_project._rich_text(
            material([[0, 2], [3, 5]]), allow_partition=True,
        )[1])
        self.assertFalse(validate_capcut_project._rich_text(
            material([[0, 3], [2, 5]]), allow_partition=True,
        )[1])

    def test_builder_preserves_yellow_red_yellow_headline_ranges(self):
        material = {
            "content": json.dumps({
                "text": "역대급 충치의 정체",
                "styles": [
                    {"range": [0, 4], "fill": {"content": {"solid": {"color": [1.0, 230 / 255, 0.0]}}}},
                    {"range": [4, 6], "fill": {"content": {"solid": {"color": [1.0, 16 / 255, 16 / 255]}}}},
                    {"range": [6, 10], "fill": {"content": {"solid": {"color": [1.0, 230 / 255, 0.0]}}}},
                ],
            }, ensure_ascii=False),
        }
        text = "하필 처녀파티에 출동한 경찰관"
        builder._set_text(
            material,
            text,
            "T2",
            style_policy=templates.YELLOW_RED_YELLOW_EMPHASIS,
            emphasis_range=[3, 9],
        )
        rich = json.loads(material["content"])
        self.assertEqual(
            [style["range"] for style in rich["styles"]],
            [[0, 3], [3, 9], [9, len(text)]],
        )
        self.assertTrue(validate_capcut_project._headline_style_valid(
            material, text, [3, 9],
        ))

    def test_state_subrange_is_legal_only_inside_host_beat(self):
        base = {
            "timeline": [{
                "segment_key": "B01",
                "target_range_us": [0, 2_000_000],
                "placements": [{
                    "anchor": "STATE",
                    "operation": "replace_text_preserve_style",
                    "text": "그대로",
                    "target_range_us": [200_000, 600_000],
                }],
            }],
            "original_order": ["B01"],
            "final_order": ["B01"],
        }
        view = validate_executable_protocol._normalize_plan(base)
        self.assertNotIn("TIMELINE_TARGET_RANGE_MISMATCH:0:STATE", view["errors"])

        base["timeline"][0]["placements"][0]["target_range_us"] = [1_800_000, 2_200_000]
        view = validate_executable_protocol._normalize_plan(base)
        self.assertIn("TIMELINE_TARGET_RANGE_MISMATCH:0:STATE", view["errors"])

    def test_plan_keeps_multiple_progressive_state_cues_at_their_own_ranges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in (
                "30_audio_srt/audio_lock.json",
                "00_input/source_identity.json",
                "20_script/original-capcut-grid.md",
                "20_script/urakkai-capcut-grid.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
            timeline = {"segments": [
                {"segment_id": "S01", "role": "STATE", "start": 100_000, "duration": 300_000, "text": "그대로"},
                {"segment_id": "S02", "role": "STATE", "start": 400_000, "duration": 500_000, "text": "그대로 떠난다"},
                {"segment_id": "D01", "role": "A10_TEXT", "start": 0, "duration": 1_000_000, "text": "엄마\n무슨 일이야?"},
                {"segment_id": "D02", "role": "A10_TEXT", "start": 1_000_000, "duration": 1_000_000, "text": "아들\n약속이 있거든"},
            ]}
            plan = {
                "type": "3", "audio_policy": "A10_REASSEMBLED_SYNC",
                "execution_strategy": "original_audio_caption", "DUR": 2_000_000,
                "T1": "첫 줄", "T2": "둘째 줄", "source_credit": "출처 : 채널",
                "V": [
                    ["V01", "B02", 0, 1_000_000, 1_000_000, 2_000_000],
                    ["V02", "B01", 1_000_000, 2_000_000, 0, 1_000_000],
                ],
                "cues": [],
            }
            resolved = production_profile.resolve_production_profile(EXPECTED_SELECTOR)
            result = build_episode_locks.build_production_plan(
                "EP", root, plan, timeline,
                {"source_fingerprint": "source"},
                {
                    "audio_source": "REASSEMBLED_VOCAL_STEM",
                    "source_audio": [
                        {"clip_id": "V01", "mode": "on"},
                        {"clip_id": "V02", "mode": "on"},
                    ],
                },
                "home_windows_black_headline_dialogue_v1", ["B01", "B02"],
                resolved,
            )
            states = [row for row in result["timeline"][0]["placements"] if row["anchor"] == "STATE"]
            self.assertEqual(
                [row["target_range_us"] for row in states],
                [[100_000, 400_000], [400_000, 900_000]],
            )
            self.assertNotIn("STATE_GLITCH", result["cleared_anchors"])
            protocol = json.loads(
                validate_executable_protocol.DEFAULT_PROTOCOL.read_text(encoding="utf-8")
            )
            self.assertEqual(
                validate_executable_protocol.validate_production_plan(result, protocol),
                [],
            )

            default_selector = dict(
                EXPECTED_SELECTOR,
                profile_id="fixture-default-type3",
                template_profile=templates.V3_TEMPLATE_PROFILE,
            )
            default_profile = production_profile.resolve_production_profile(default_selector)
            self.assertIn(
                "STATE_GLITCH",
                build_episode_locks.cleared_anchors_for_profile(plan, default_profile),
            )


if __name__ == "__main__":
    unittest.main()
