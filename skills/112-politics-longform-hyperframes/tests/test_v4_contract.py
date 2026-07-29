#!/usr/bin/env python3
"""Regression tests for the opt-in V4 contract; dynamic gates run separately."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"
EXAMPLE = SKILL / "examples" / "v4-validation-project"
SCRIPTS = SKILL / "scripts"
V3_PROFILE_SHA256 = "7302d597c8938035af34f4f0b0bd745be906fe9d6d989a6c93e8616c94bbbcad"
V3_REFERENCES_SHA256 = "db754edce08ef7e46ab3d2d4f4d535b1a945c69388ba32a858381dfa8d2bdcbb"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"module spec unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TestV4Profile(unittest.TestCase):
    def test_v3_authority_files_are_byte_identical(self):
        self.assertEqual(
            sha256_file(ASSETS / "political-documentary-defaults.json"),
            V3_PROFILE_SHA256,
        )
        self.assertEqual(
            sha256_file(ASSETS / "political-documentary-reference-frames.json"),
            V3_REFERENCES_SHA256,
        )

    def test_v4_is_opt_in_and_rolls_back_to_v3(self):
        profile = json.loads(
            (ASSETS / "political-documentary-v4.json").read_text(encoding="utf-8")
        )
        self.assertEqual(profile["profile_id"], "politics_documentary_broadcast_v4")
        self.assertEqual(profile["extends_profile_id"], "politics_documentary_broadcast_v3")
        self.assertFalse(profile["default_profile"])
        self.assertEqual(
            profile["activation"]["rollback_profile_id"],
            "politics_documentary_broadcast_v3",
        )

    def test_profile_resolver_keeps_v3_as_default(self):
        module = load_module(
            "resolve_visual_profile_test", SCRIPTS / "resolve_visual_profile.py"
        )
        default_id, default_path = module.resolve_profile(None)
        v4_id, v4_path = module.resolve_profile("politics_documentary_broadcast_v4")
        self.assertEqual(default_id, "politics_documentary_broadcast_v3")
        self.assertEqual(default_path.name, "political-documentary-defaults.json")
        self.assertEqual(v4_id, "politics_documentary_broadcast_v4")
        self.assertEqual(v4_path.name, "political-documentary-v4.json")

    def test_skill_declares_v4_without_changing_default(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_VISUAL_PROFILE=politics_documentary_broadcast_v3", text)
        self.assertIn("OPTIONAL_VISUAL_PROFILE=politics_documentary_broadcast_v4", text)
        self.assertIn("ROLLBACK_PROFILE=politics_documentary_broadcast_v3", text)
        self.assertIn("political-documentary-v4.md", text)

    def test_required_dynamic_gates_are_exact(self):
        profile = json.loads(
            (ASSETS / "political-documentary-v4.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            profile["required_gates"],
            [
                "PASS_CHAPTER_ACTIVE_STATE",
                "PASS_SEMANTIC_VISUAL_SYNC",
                "PASS_SOURCE_VIDEO_FOCUS_LINES",
                "PASS_AUDIO_LOUDNESS_NORMALIZATION",
            ],
        )


class TestV4VisualTimeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.timeline = json.loads(
            (EXAMPLE / "visual_timeline_v4.json").read_text(encoding="utf-8")
        )
        cls.html = (EXAMPLE / "index.html").read_text(encoding="utf-8")

    def test_four_chapters_have_distinct_active_frames(self):
        chapters = self.timeline["chapters"]
        self.assertEqual([item["chapter_id"] for item in chapters], ["01", "02", "03", "04"])
        self.assertEqual(len({item["active_frame_ms"] for item in chapters}), 4)
        self.assertTrue(all(item["active_state"] == "current" for item in chapters))

    def test_semantic_events_have_required_fields_and_sync(self):
        required = {"start_ms", "end_ms", "semantic_role", "active_state"}
        events = self.timeline["semantic_events"]
        self.assertGreaterEqual(len(events), 3)
        for event in events:
            self.assertTrue(required.issubset(event))
            self.assertLessEqual(
                abs(event["start_ms"] - event["srt_start_ms"]),
                self.timeline["sync_tolerance_ms"],
            )
            for field in required:
                self.assertIn(f'data-{field.replace("_", "-")}', self.html)

    def test_semantic_roles_use_evidence_colors_not_people(self):
        profile = json.loads(
            (ASSETS / "political-documentary-v4.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(profile["semantic_colors"]),
            {
                "verified_fact",
                "allegation_unverified",
                "rebuttal_conflict_risk",
                "conclusion_alternative",
            },
        )
        self.assertIn("미확인", self.html)
        self.assertIn("person_or_party_color_assignment", profile["forbidden"])
        self.assertIn("gold_positive_highlight_for_allegation", profile["forbidden"])

    def test_focus_line_contract_uses_transparent_svg(self):
        focus = self.timeline["focus_events"][0]
        self.assertEqual(focus["format"], "transparent_svg")
        self.assertEqual(focus["enter_end_ms"] - focus["start_ms"], 200)
        self.assertTrue(600 <= focus["end_ms"] - focus["enter_end_ms"] <= 1200)
        focus_markup = self.html.split('id="source-focus-lines"', 1)[1].split("</svg>", 1)[0]
        self.assertNotIn("<rect", focus_markup)
        self.assertIn("focus-ray-group", focus_markup)

    def test_example_has_no_render_time_remote_assets(self):
        self.assertNotIn("http://", self.html)
        self.assertNotIn("https://", self.html)
        self.assertIn("assets/vendor/gsap.min.js", self.html)


class TestV4AudioContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(
            (ASSETS / "political-documentary-v4.json").read_text(encoding="utf-8")
        )
        cls.normalizer = load_module(
            "normalize_v4_audio_test", SCRIPTS / "normalize_v4_audio.py"
        )

    def test_audio_targets_and_mix_order(self):
        audio = self.profile["audio"]
        self.assertEqual(audio["normalization"], "ffmpeg_loudnorm_2pass")
        self.assertEqual(audio["integrated_lufs"], -14.0)
        self.assertLessEqual(audio["true_peak_dbtp_max"], -1.0)
        self.assertLessEqual(audio["lra_max"], 11.0)
        self.assertLess(audio["final_encode_headroom_db"], 0.0)
        self.assertFalse(audio["bgm_normalize_to_voice_target"])
        self.assertFalse(audio["sfx_normalize_to_voice_target"])
        self.assertLess(
            audio["mix_order"].index("normalize_voice_clips"),
            audio["mix_order"].index("duck_bgm"),
        )
        self.assertEqual(audio["mix_order"][-1], "measure_final_master")

    def test_gain_outlier_is_a_hard_failure(self):
        receipt = {
            "applied_gain_db": 18.5,
            "output": {
                "integrated_lufs": -14.0,
                "true_peak_dbtp": -1.2,
                "lra_lu": 4.0,
            },
        }
        errors = self.normalizer.assess_normalized_audio(
            receipt,
            target_i=-14.0,
            target_tp=-1.0,
            target_lra=11.0,
            lufs_tolerance=0.5,
            max_abs_gain_db=18.0,
        )
        self.assertTrue(any(error.startswith("GAIN_OUTLIER") for error in errors))

    def test_normal_gain_receipt_passes(self):
        receipt = {
            "applied_gain_db": 7.2,
            "output": {
                "integrated_lufs": -14.1,
                "true_peak_dbtp": -1.3,
                "lra_lu": 5.0,
            },
        }
        self.assertEqual(
            self.normalizer.assess_normalized_audio(
                receipt,
                target_i=-14.0,
                target_tp=-1.0,
                target_lra=11.0,
                lufs_tolerance=0.5,
                max_abs_gain_db=18.0,
            ),
            [],
        )


class TestV4Scripts(unittest.TestCase):
    def test_scripts_compile_without_writing_pyc(self):
        for name in (
            "resolve_visual_profile.py",
            "normalize_v4_audio.py",
            "build_v4_sample.py",
            "validate_v4_evidence.py",
        ):
            path = SCRIPTS / name
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_dynamic_validator_reads_render_pixels_and_audio(self):
        text = (SCRIPTS / "validate_v4_evidence.py").read_text(encoding="utf-8")
        self.assertIn("extract_frame", text)
        self.assertIn("ImageChops.difference", text)
        self.assertIn("measure_loudness", text)
        self.assertIn("render_path", text)
        self.assertNotIn("STATIC_ONLY_PASS", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
