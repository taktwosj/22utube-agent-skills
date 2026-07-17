from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "top5isu-shorts"


class Top5IsuShortsContractTests(unittest.TestCase):
    def test_skill_is_registered_and_has_single_entrypoint_triggers(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        ui = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "manifests" / "skill-set.json").read_text(encoding="utf-8"))

        self.assertIn("name: top5isu-shorts", skill)
        for token in ("top5isu", "TOP5", "군림보", "gunlimbo"):
            self.assertIn(token, skill)
        self.assertIn("$top5isu-shorts", ui)
        self.assertIn("top5isu-shorts", {entry["name"] for entry in manifest["skills"]})

    def test_skill_is_a_standalone_factory_with_no_external_skill_handoff(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("standalone_factory=true", skill)
        self.assertIn("external_skill_handoff=forbidden", skill)
        for stage in ("INTAKE", "SCRIPT_DESIGN", "AUDIO_ASSETS", "CAPCUT_PROJECT", "FINAL_REPORT"):
            self.assertIn(stage, skill)
        self.assertNotIn("Require `00-tikitaka`", skill)
        self.assertNotIn("Route production to `000short-production-agent`", skill)
        self.assertIn("FINAL_LOCK", skill)
        self.assertIn("FAIL_SHRT_WHITE_FALLBACK_FORBIDDEN", skill)
        self.assertIn("fallback_allowed=false", skill)

    def test_skill_locks_profiles_template_coordinates_and_audio_measurement(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        for token in (
            "style_profile=top5",
            "style_profile=gunlimbo",
            "template_profile=top5isu_v1",
            "image_ui_y=-600",
            "image_json_transform_y=-0.15625",
            "ffmpeg loudnorm",
            "final_export_remeasure_required=true",
        ):
            self.assertIn(token, skill)

    def test_skill_locks_rework_manual_edit_and_final_project_report(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        report = (SKILL_ROOT / "references" / "report-contract.md").read_text(encoding="utf-8")
        production = (SKILL_ROOT / "references" / "production-contract.md").read_text(encoding="utf-8")

        for token in (
            "CLEAN_VIDEO_REWORK",
            "MANUAL_EDIT_EXPECTED",
            "manual_edit_difference_is_failure=false",
            "current_draft_reread_required=true",
            "validate_top5isu_assembly_report.py",
        ):
            self.assertIn(token, skill)
        self.assertIn("CapCut 프로젝트 파일 이름", report)
        self.assertIn("## 캣컵복사하기", report)
        self.assertIn("clean_video_rework", production)
        self.assertIn("WAIT_CLEAN_VIDEO_REVIEW", production)

    def test_references_and_schema_are_present_and_consistent(self):
        references = {
            "top5-profile.md": "ranking_item",
            "gunlimbo-profile.md": "speaker_mute_forbidden",
            "top5isu-template-contract.md": "archive_sha256",
            "handoff-contract.md": "No external skill handoff",
            "script-contract.md": "standalone_factory: true",
            "production-contract.md": "real editable CapCut project",
            "report-contract.md": "FINAL_LOCK",
        }
        for name, token in references.items():
            text = (SKILL_ROOT / "references" / name).read_text(encoding="utf-8")
            self.assertIn(token, text)

        schema = json.loads(
            (SKILL_ROOT / "schemas" / "top5isu-build-contract.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required = set(schema["required"])
        self.assertTrue(
            {
                "contract_version",
                "template_profile",
                "style_profile",
                "fallback_allowed",
                "image_ui_y",
                "image_json_transform_y",
                "audio_normalization",
            }.issubset(required)
        )
        self.assertEqual(schema["properties"]["template_profile"]["const"], "top5isu_v1")
        self.assertEqual(schema["properties"]["fallback_allowed"]["const"], False)


if __name__ == "__main__":
    unittest.main()
