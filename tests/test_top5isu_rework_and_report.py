from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import load_source_module_no_bytecode
from test_top5isu_validators import minimal_content


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "top5isu-shorts"
REPORT_VALIDATOR = SKILL_ROOT / "scripts" / "validate_top5isu_assembly_report.py"
REWORK_VALIDATOR = SKILL_ROOT / "scripts" / "validate_top5isu_rework_intake.py"
DRAFT_VALIDATOR = SKILL_ROOT / "scripts" / "validate_top5isu_capcut_draft.py"


class Top5IsuReworkAndReportTests(unittest.TestCase):
    def test_assembly_report_ends_with_exact_capcut_project_name(self):
        module = load_source_module_no_bytecode("top5isu_assembly_report", REPORT_VALIDATOR)
        project_name = "HERMES_역사춘_세종_001"
        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td) / project_name
            project_dir.mkdir()
            (project_dir / "draft_content.json").write_text("{}", encoding="utf-8")
            report = f"""# 조립도 보고서

## 프로젝트 실체
CapCut 프로젝트명: {project_name}
CapCut 프로젝트 폴더명: {project_name}
CapCut 프로젝트 경로: {project_dir}
CapCut 프로젝트 파일 이름: {project_name}

## 설계 반영 및 검증
capcut_draft: PASS
visual_playback_review: PASS

## 사용자 수동 편집
manual_edit_policy=MANUAL_EDIT_EXPECTED
manual_edit_difference_is_failure=false
current_draft_reread_required=true

## 캣컵복사하기
{project_name}
"""
            result = module.validate_assembly_report_text(report, project_name)
            self.assertEqual(result["assembly_report_status"], "PASS")
            self.assertEqual(result["capcut_project_name"], project_name)
            self.assertTrue(result["manual_edit_expected"])

            with self.assertRaisesRegex(module.GateFail, "FAIL_CAPCUT_PROJECT_NAME"):
                module.validate_assembly_report_text(report, "DIFFERENT_PROJECT")

            with self.assertRaisesRegex(module.GateFail, "FAIL_ASSEMBLY_REPORT"):
                module.validate_assembly_report_text(
                    report.replace(f"CapCut 프로젝트 파일 이름: {project_name}\n", ""),
                    project_name,
                )

            (project_dir / "draft_content.json").unlink()
            project_dir.rmdir()
            with self.assertRaisesRegex(module.GateFail, "FAIL_CAPCUT_PROJECT_PATH"):
                module.validate_assembly_report_text(report, project_name)

    def test_manual_capcut_edits_are_expected_and_not_structural_failures(self):
        module = load_source_module_no_bytecode("top5isu_manual_edit", DRAFT_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            draft = Path(td)
            content = minimal_content()
            content["duration"] += 5_000_000
            content["canvas_config"] = {"width": 720, "height": 1280, "ratio": "9:16"}
            content["tracks"][0]["segments"] = content["tracks"][0]["segments"][:5]
            content["tracks"].append({"name": "USER_ADDED_TEXT", "type": "text", "segments": [{}]})
            (draft / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")

            with self.assertRaises(module.GateFail):
                module.validate_top5isu_capcut_draft(draft, "top5", None)

            result = module.validate_top5isu_capcut_draft(
                draft,
                "top5",
                None,
                manual_edit_expected=True,
            )
            self.assertEqual(result["top5isu_capcut_draft_status"], "PASS_MANUAL_EDIT_EXPECTED")
            self.assertTrue(result["current_draft_reread"])
            self.assertFalse(result["manual_edit_difference_is_failure"])

            (draft / "draft_content.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(module.GateFail, "FAIL_TOP5ISU_DRAFT"):
                module.validate_top5isu_capcut_draft(
                    draft,
                    "top5",
                    None,
                    manual_edit_expected=True,
                )

    def test_clean_video_rework_intake_preserves_provenance_and_requires_clean_checks(self):
        module = load_source_module_no_bytecode("top5isu_clean_rework", REWORK_VALIDATOR)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            clean_video = root / "clean_source.mp4"
            clean_video.write_bytes(b"not-empty-test-video")
            manifest = {
                "intake_mode": "clean_video_rework",
                "clean_video_path": clean_video.name,
                "source_short_ref": "existing-short-001",
                "derived_from_existing_short": True,
                "captions_removed": True,
                "text_overlays_removed": True,
                "clean_visual_review_status": "PASS",
                "ocr_overlay_check_status": "PASS",
            }
            result = module.validate_rework_intake(
                manifest,
                root,
                media_probe=lambda _: {"status": "PASS", "duration_sec": 32.5},
            )
            self.assertEqual(result["rework_intake_status"], "PASS")
            self.assertEqual(result["source_role"], "clean_video_rework")
            self.assertEqual(result["source_short_ref"], "existing-short-001")
            self.assertTrue(result["rework_allowed"])

            manifest["ocr_overlay_check_status"] = "WAIT"
            with self.assertRaisesRegex(module.GateFail, "WAIT_CLEAN_VIDEO_REVIEW"):
                module.validate_rework_intake(
                    manifest,
                    root,
                    media_probe=lambda _: {"status": "PASS", "duration_sec": 32.5},
                )


if __name__ == "__main__":
    unittest.main()
