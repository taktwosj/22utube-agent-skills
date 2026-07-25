from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
WORKFLOW = SKILL / "workflow.json"
GUIDE = SKILL / "references" / "parallel-execution.md"


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

    def test_only_one_gui_owner_exists(self):
        gui = self.contract["gui"]
        self.assertEqual(gui["max_owners"], 1)
        self.assertTrue(gui["mutual_exclusion"])
        self.assertEqual(set(gui["tools"]), {"vmake", "capcut"})

    def test_stage01_and_stage03_have_bounded_fanout(self):
        stage01 = self.contract["fanout"]["stage01"]
        stage03 = self.contract["fanout"]["stage03"]
        self.assertEqual(stage01["workers"], 3)
        self.assertEqual(len(stage01["lanes"]), 3)
        self.assertEqual(stage03["workers"], 4)
        self.assertEqual(len(stage03["lanes"]), 4)
        self.assertEqual(stage01["commit_status"], "SOURCE_OCR_VERIFIED")
        self.assertEqual(stage03["commit_status"], "FIRST_RECOMMENDATION_READY")

    def test_post_design_fanout_has_three_lanes_and_clean_visual_barrier(self):
        post = self.contract["fanout"]["after_final_design_locked"]
        self.assertEqual(post["trigger_status"], "FINAL_DESIGN_LOCKED")
        self.assertEqual(post["workers"], 3)
        self.assertEqual(
            [lane["id"] for lane in post["lanes"]],
            ["vmake_clean", "audio_prep", "stage08_readonly_preflight"],
        )
        self.assertIn("clean_visual_evidence", post["barrier"]["required_evidence"])
        self.assertEqual(
            post["barrier"]["sequential_state_advance"],
            ["CLEAN_VISUAL_READY", "AUDIO_CAPTION_VALIDATED"],
        )

    def test_stage06_validator_and_stage08_clean_visual_prerequisite_are_registered(self):
        checks = self.workflow["validation"]["checks"]
        self.assertEqual(checks["06"]["validator"], "scripts/validate_clean_visual.py")
        self.assertIn("clean_visual_evidence", checks["08"]["required_prerequisites"])

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
