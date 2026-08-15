from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
WORKFLOW = SKILL / "workflow.json"
GUIDE = SKILL / "references" / "parallel-execution.md"
UI_GUIDE = SKILL / "references" / "capcut-macos-ui-verification-fallback.md"
PROTOCOL_TESTING_GUIDE = SKILL / "references" / "executable-protocol-testing.md"


class ParallelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        cls.contract = cls.workflow["parallel_execution"]

    def test_normal_fast_is_default_and_one_owner_runs_stage01_through_stage04(self):
        profile = self.workflow["execution_profiles"]
        normal = profile["profiles"]["NORMAL_FAST"]
        self.assertEqual(profile["default"], "NORMAL_FAST")
        self.assertEqual(normal["task_owner_count"], 1)
        self.assertEqual(normal["stage_sequence"], ["01", "02", "03", "04"])
        self.assertEqual(normal["stage_execution"], "single_task_owner_sequential")
        self.assertEqual(normal["state_writer"], "task_owner")

    def test_normal_fast_disables_worker_promotion_revalidation_and_barrier_duplication(self):
        normal = self.workflow["execution_profiles"]["profiles"]["NORMAL_FAST"]
        self.assertFalse(normal["evidence_only_worker_candidates"])
        self.assertFalse(normal["coordinator_revalidation"])
        self.assertFalse(normal["barrier_duplication"])
        self.assertEqual(normal["validator_run"], "once_per_current_artifact_revision")
        self.assertEqual(normal["validator_rerun"], "after_proven_relevant_change_only")

        self.assertFalse(self.contract["enabled"])
        self.assertEqual(self.contract["mode"], "disabled_in_normal_fast")
        self.assertEqual(self.contract["max_workers"], 0)
        for lane in ("stage01", "stage03", "after_final_design_locked", "stage08_postbuild"):
            with self.subTest(lane=lane):
                fanout = self.contract["fanout"][lane]
                self.assertFalse(fanout["enabled"])
                self.assertEqual(fanout["workers"], 0)
                self.assertEqual(fanout["lanes"], [])

    def test_only_one_gui_owner_exists(self):
        gui = self.contract["gui"]
        self.assertEqual(gui["max_owners"], 1)
        self.assertTrue(gui["mutual_exclusion"])
        self.assertEqual(set(gui["tools"]), {"vmake", "capcut"})
        self.assertEqual(
            gui["computer_use_delivery_ladder"],
            ["background", "coordinate_if_recommended", "foreground_if_recommended"],
        )
        self.assertTrue(gui["recapture_after_state_change"])
        self.assertTrue(gui["foreground_requires_driver_recommendation"])

    def test_nonblocking_vmake_is_an_owner_job_not_worker_fanout(self):
        early_vmake = self.workflow["owner_background_jobs"]["after_source_identity_verified"]
        self.assertEqual(early_vmake["trigger_status"], "SOURCE_OCR_VERIFIED")
        self.assertEqual(early_vmake["owner"], "task_owner")
        self.assertEqual(early_vmake["job"], "vmake_submit")
        self.assertEqual(early_vmake["gui"], "vmake")
        self.assertTrue(early_vmake["nonblocking"])
        self.assertEqual(early_vmake["candidate_receipt"]["status_meaning"], "TECHNICAL_IDENTITY_ONLY")
        self.assertEqual(early_vmake["candidate_receipt"]["quality_authority"], "user")

    def test_stage06_validator_and_stage08_source_provisional_path_are_registered(self):
        checks = self.workflow["validation"]["checks"]
        self.assertEqual(checks["06"]["validator"], "scripts/validate_clean_visual.py")
        self.assertNotIn("clean_visual_evidence", checks["08"]["required_prerequisites"])
        self.assertIn("clean_visual_evidence", checks["08"]["optional_prerequisites"])
        self.assertEqual(
            checks["08"]["allowed_visual_asset_modes"],
            ["CLEAN_VISUAL_READY", "SOURCE_VIDEO_PROVISIONAL", "USER_APPROVED_NONMATCHING_CLEAN_SOURCE"],
        )
        stages = {stage["id"]: stage for stage in json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))["stages"]}
        self.assertEqual(stages["07"]["requires_state"], "FINAL_DESIGN_LOCKED_OR_CLEAN_VISUAL_READY")
        self.assertEqual(stages["08"]["requires_state"], "AUDIO_CAPTION_VALIDATED_WITH_ACCEPTED_VISUAL_MODE")

    def test_interim_capcut_never_waits_for_vmake_and_requires_clean_video_swap(self):
        interim = self.workflow["interim_capcut"]
        self.assertEqual(interim["allowed_when"]["after_status"], "FINAL_DESIGN_LOCKED")
        self.assertIn("PROCESSING", interim["allowed_when"]["vmake_status"])
        self.assertNotIn("vmake_remaining_minutes_strictly_greater_than", interim["allowed_when"])
        self.assertEqual(interim["video_asset"], "00_input/source.mp4")
        self.assertEqual(interim["video_volume"], 0)
        self.assertEqual(interim["a10_anchor"], "A10_VALIDATED_DEMUCS_VOCAL_STEM")
        self.assertEqual(interim["a10_volume"], 1)
        self.assertEqual(interim["status"], "SOURCE_VIDEO_PROVISIONAL")
        self.assertEqual(interim["on_clean_arrival"], "replace_existing_VIDEO_asset_only_keep_project_structure")
        self.assertEqual(interim["report_required"]["next_action"], "CLEAN_SOURCE_SWAP_NONBLOCKING")
        self.assertNotIn("paperclip_status", interim["report_required"])
        self.assertTrue(interim["batch_nonblocking"])
        self.assertIn("SOURCE_PROVISIONAL_RENDER", interim["allows"])
        self.assertEqual(interim["quality_authority"], "user")

    def test_stage09_is_user_manual_only(self):
        stage09 = self.contract["stage09"]
        self.assertEqual(stage09["mode"], "user_manual_only")
        self.assertEqual(stage09["max_workers"], 0)
        self.assertFalse(stage09["fanout"])
        self.assertEqual(stage09["state_writer"], "user_only")
        self.assertEqual(stage09["sequence"], ["WAIT_USER_CAPCUT_CHECK"])
        self.assertEqual(stage09["router_args"], [])

    def test_runtime_guides_describe_normal_fast_and_verified_gui_escalation(self):
        parallel = GUIDE.read_text(encoding="utf-8")
        ui = UI_GUIDE.read_text(encoding="utf-8")
        testing = PROTOCOL_TESTING_GUIDE.read_text(encoding="utf-8")
        self.assertIn("NORMAL_FAST", parallel)
        self.assertIn("single task-owner", parallel)
        self.assertIn("once per current artifact revision", parallel)
        self.assertIn("suspected_noop", ui)
        self.assertIn("background_unavailable", ui)
        self.assertIn("foreground", ui)
        self.assertIn("pressure-scenario transcript", testing)

    def test_reference_exists_and_legacy_numbered_gate_tokens_are_absent(self):
        self.assertTrue(GUIDE.is_file())
        combined = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in SKILL.rglob("*")
            if path.is_file()
        )
        banned = re.compile(r"\b" + "G" + r"(?:" + "|".join(str(n) for n in range(30, 100, 10)) + r")\b", re.I)
        self.assertIsNone(banned.search(combined))


if __name__ == "__main__":
    unittest.main()
