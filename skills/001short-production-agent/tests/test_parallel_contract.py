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

    def test_workers_are_evidence_only_and_coordinator_owns_canonical_writes(self):
        self.assertEqual(self.contract["mode"], "evidence_only")
        self.assertEqual(self.contract["max_workers"], 4)
        self.assertTrue(self.contract["workers"]["unique_root_required"])
        self.assertIn("{worker_id}", self.contract["workers"]["root_template"])
        self.assertIn("{task_id}", self.contract["workers"]["root_template"])
        self.assertEqual(
            self.contract["canonical_writes"]["owner"],
            "coordinator_only",
        )
        self.assertEqual(
            self.contract["canonical_writes"]["state_advance"],
            "barrier_pass_then_sequential_only",
        )

    def test_worker_live_transcripts_are_recorded_but_never_promoted_as_authority(self):
        transcripts = self.contract["workers"]["live_transcripts"]
        self.assertTrue(transcripts["record_paths_when_available"])
        self.assertEqual(transcripts["authority"], "observation_only")
        self.assertTrue(transcripts["artifact_reverification_required"])
        self.assertEqual(
            transcripts["parent_session_end_behavior"],
            "do_not_treat_delegation_as_durable",
        )

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

    def test_stage01_and_stage03_have_bounded_fanout(self):
        early_vmake = self.contract["fanout"]["after_source_identity_verified"]
        stage01 = self.contract["fanout"]["stage01"]
        stage03 = self.contract["fanout"]["stage03"]
        self.assertEqual(early_vmake["trigger_status"], "SOURCE_OCR_VERIFIED")
        self.assertEqual(early_vmake["lanes"][0]["id"], "vmake_submit")
        self.assertEqual(early_vmake["lanes"][0]["gui"], "vmake")
        self.assertEqual(early_vmake["candidate_receipt"]["status_meaning"], "TECHNICAL_IDENTITY_ONLY")
        self.assertEqual(early_vmake["candidate_receipt"]["quality_authority"], "user")
        self.assertEqual(stage01["workers"], 3)
        self.assertEqual(len(stage01["lanes"]), 3)
        self.assertEqual(stage03["workers"], 4)
        self.assertEqual(len(stage03["lanes"]), 4)
        self.assertEqual(stage01["commit_status"], "SOURCE_OCR_VERIFIED")
        self.assertEqual(stage03["commit_status"], "FIRST_RECOMMENDATION_READY")

    def test_post_design_fanout_has_three_lanes_and_nonblocking_clean_visual(self):
        post = self.contract["fanout"]["after_final_design_locked"]
        self.assertEqual(post["trigger_status"], "FINAL_DESIGN_LOCKED")
        self.assertEqual(post["workers"], 3)
        self.assertEqual(
            [lane["id"] for lane in post["lanes"]],
            ["vmake_candidate_finalize", "audio_prep", "stage08_readonly_preflight"],
        )
        self.assertIsNone(post["lanes"][0]["gui"])
        self.assertNotIn("clean_visual_evidence", post["barrier"]["required_evidence"])
        self.assertIn("clean_visual_evidence", post["barrier"]["nonblocking_evidence"])
        self.assertEqual(
            post["barrier"]["sequential_state_advance"],
            ["AUDIO_CAPTION_VALIDATED"],
        )

    def test_stage06_validator_and_stage08_source_provisional_path_are_registered(self):
        checks = self.workflow["validation"]["checks"]
        self.assertEqual(checks["06"]["validator"], "scripts/validate_clean_visual.py")
        self.assertNotIn("clean_visual_evidence", checks["08"]["required_prerequisites"])
        self.assertIn("clean_visual_evidence", checks["08"]["optional_prerequisites"])
        self.assertEqual(
            checks["08"]["allowed_visual_asset_modes"],
            ["CLEAN_VISUAL_READY", "SOURCE_VIDEO_PROVISIONAL"],
        )
        stages = {stage["id"]: stage for stage in json.loads((SKILL / "protocol.json").read_text(encoding="utf-8"))["stages"]}
        self.assertEqual(stages["07"]["requires_state"], "FINAL_DESIGN_LOCKED_OR_CLEAN_VISUAL_READY")
        self.assertEqual(stages["08"]["requires_state"], "AUDIO_CAPTION_VALIDATED_WITH_CLEAN_OR_SOURCE_VIDEO_PROVISIONAL")

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
        self.assertEqual(interim["report_required"]["paperclip_status"], "IN_REVIEW")
        self.assertTrue(interim["batch_nonblocking"])
        self.assertIn("SOURCE_PROVISIONAL_RENDER", interim["allows"])
        self.assertEqual(interim["quality_authority"], "user")

    def test_stage08_postbuild_checks_are_read_only_and_stage09_is_serial(self):
        postbuild = self.contract["fanout"]["stage08_postbuild"]
        self.assertEqual(postbuild["mode"], "read_only_validation")
        self.assertLessEqual(postbuild["workers"], self.contract["max_workers"])
        self.assertTrue(postbuild["immutable_snapshot_required"])

        stage09 = self.contract["stage09"]
        self.assertEqual(stage09["mode"], "strict_serial")
        self.assertEqual(stage09["max_workers"], 1)
        self.assertFalse(stage09["fanout"])
        self.assertEqual(
            stage09["router_args"],
            [
                "--stage09-review-evidence",
                "--stage09-review-sha256",
                "--approved-evidence-root",
                "--capcut-evidence",
                "--capcut-sha256",
                "--render",
                "--render-sha256",
                "--evidence",
            ],
        )

    def test_runtime_guides_require_transcript_evidence_and_verified_gui_escalation(self):
        parallel = GUIDE.read_text(encoding="utf-8")
        ui = UI_GUIDE.read_text(encoding="utf-8")
        testing = PROTOCOL_TESTING_GUIDE.read_text(encoding="utf-8")
        self.assertIn("live_transcripts", parallel)
        self.assertIn("observation_only", parallel)
        self.assertIn("artifact_reverification_required", parallel)
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
