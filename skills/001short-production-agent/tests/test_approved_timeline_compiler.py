import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import compile_approved_timeline  # noqa: E402
from schema_runtime import validate_schema  # noqa: E402


class ApprovedTimelineCompilerTests(unittest.TestCase):
    def test_stage05_compiler_emits_production_role_rows_and_schema_validates(self):
        timeline = {
            "schema_version": "approved-timeline-v1",
            "episode_id": "SH_TEST",
            "source_fingerprint": "source-sha",
            "segments": [
                {
                    "segment_id": "SEG01",
                    "timeline_order": 1,
                    "role": "VIDEO",
                    "start": 0,
                    "duration": 3_000_000,
                    "source_ref": "source-id",
                },
                {
                    "segment_id": "SEG02",
                    "timeline_order": 2,
                    "role": "VIDEO",
                    "start": 3_000_000,
                    "duration": 2_000_000,
                    "source_ref": "source-id-2",
                },
            ],
        }
        plan = {
            "schema_version": "001short-production-plan-v1",
            "episode_id": "SH_TEST",
            "total_duration_us": 5_000_000,
            "timeline": [
                {
                    "segment_key": "GLOBAL_TITLES",
                    "target_range_us": [0, 5_000_000],
                    "placements": [
                        {"anchor": "T1", "target_range_us": [0, 5_000_000], "text": "title one"},
                        {"anchor": "T2", "target_range_us": [0, 5_000_000], "text": "title two"},
                    ],
                },
                {
                    "segment_key": "SEG01",
                    "target_range_us": [0, 3_000_000],
                    "placements": [
                        {"anchor": "VIDEO", "target_range_us": [0, 3_000_000]},
                        {"anchor": "A9", "target_range_us": [0, 3_000_000]},
                        {"anchor": "A9_TEXT", "target_range_us": [0, 3_000_000], "text": "caption"},
                    ],
                },
                {
                    "segment_key": "SEG02",
                    "target_range_us": [3_000_000, 5_000_000],
                    "placements": [
                        {"anchor": "VIDEO", "target_range_us": [3_000_000, 5_000_000]},
                        {"anchor": "STATE", "target_range_us": [3_000_000, 5_000_000], "text": "state"},
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            timeline_path = root / "approved_timeline.json"
            plan_path = root / "production_plan.json"
            output_path = root / "compiled" / "approved_timeline.json"
            timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
            plan_path.write_text(json.dumps(plan), encoding="utf-8")

            result = compile_approved_timeline.compile_timeline(timeline_path, plan_path, output_path)

            self.assertEqual(result["status"], "PASS")
            compiled = json.loads(output_path.read_text(encoding="utf-8"))
            roles = [row["role"] for row in compiled["segments"]]
            for role in ("STATE", "A9", "A9_TEXT", "T1", "T2"):
                self.assertIn(role, roles)
            self.assertEqual(
                next(row for row in compiled["segments"] if row["role"] == "T1")["duration"],
                5_000_000,
            )
            self.assertEqual(
                next(row for row in compiled["segments"] if row["role"] == "STATE")["source_ref"],
                "source-id-2",
            )
            schema = json.loads(
                (SKILL_ROOT / "schemas" / "approved_timeline.schema.json").read_text(encoding="utf-8")
            )
            self.assertEqual(validate_schema(compiled, schema), [])
            missing_state = dict(compiled)
            missing_state["segments"] = [row for row in compiled["segments"] if row["role"] != "STATE"]
            self.assertTrue(validate_schema(missing_state, schema))

            plan["timeline"][-1]["placements"] = [
                placement
                for placement in plan["timeline"][-1]["placements"]
                if placement["anchor"] != "STATE"
            ]
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            missing_output = root / "compiled" / "missing-role.json"
            missing_result = compile_approved_timeline.compile_timeline(
                timeline_path, plan_path, missing_output
            )
            self.assertEqual(missing_result["status"], "FAIL")
            self.assertIn("APPROVED_TIMELINE_ROLE_MISSING:STATE", missing_result["errors"][0]["detail"])
            self.assertFalse(missing_output.exists())


if __name__ == "__main__":
    unittest.main()
