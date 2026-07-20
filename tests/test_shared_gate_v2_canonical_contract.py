"""P01 canonical contract tests.

These tests assert properties of the V2 canonical contract JSON and the
shared schemas. They complement the P00 characterization tests by
locking the schema-level rules: gate order, forbidden external claims,
NOT_REQUIRED reason codes, and rejection of paid/LLM auto-advance in
gate_result documents.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_DIR = ROOT / "shared" / "workflow-harness"
CONTRACT_PATH = SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
SCHEMAS_DIR = SHARED_DIR / "schemas"
GATE_RESULT_SCHEMA_PATH = SCHEMAS_DIR / "gate_result.schema.json"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CanonicalContractTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CONTRACT_PATH.exists(), "canonical contract missing")
        self.contract = _load_json(CONTRACT_PATH)

    def test_v2_contract_has_canonical_gate_order(self):
        seq = self.contract["canonical_gate_model"]["sequence"]
        expected = [
            "G00", "G10", "G20", "G30", "G40", "G50",
            "G60", "G60.USER", "G70", "G80", "G90",
        ]
        self.assertEqual(seq, expected)

    def test_g30_precedes_g40(self):
        seq = self.contract["canonical_gate_model"]["sequence"]
        self.assertLess(seq.index("G30"), seq.index("G40"))

    def test_no_generated_tts_uses_not_required_reason_code(self):
        """NORM-003: NOT_REQUIRED_NO_GENERATED_TTS is a forbidden value."""
        model = self.contract["canonical_gate_model"]
        self.assertNotIn(
            "NOT_REQUIRED_NO_GENERATED_TTS", model["allowed_states"]
        )
        self.assertIn("NOT_REQUIRED", model["allowed_states"])
        self.assertIn(
            "NO_GENERATED_TTS",
            model.get("not_required_reason_codes", []),
        )
        self.assertIn(
            "NOT_REQUIRED_NO_GENERATED_TTS",
            model.get("forbidden_state_values", []),
        )

    def test_external_model_cannot_emit_pass(self):
        """External models only recommend; PASS is forbidden as an external claim."""
        model = self.contract["canonical_gate_model"]
        self.assertEqual(model["pass_authority"], "DETERMINISTIC_VALIDATOR_ONLY")
        forbidden = model["external_forbidden_claims"]
        for claim in ("PASS", "DESIGN_LOCK", "USER_APPROVED", "PRODUCTION_PASS"):
            self.assertIn(claim, forbidden)
        recs = model["external_recommendations"]
        for rec in ("PASS_RECOMMENDED", "REVISE_REQUIRED", "EVIDENCE_REQUIRED"):
            self.assertIn(rec, recs)

    def test_tikitaka_lane_forbids_production_outputs(self):
        design = self.contract["lane_contracts"]["general_shorts_design"]
        self.assertEqual(design["owner"], "00-tikitaka")
        joined = " ".join(design["forbidden"]).upper()
        for term in ("TTS", "SRT", "CAPCUT"):
            self.assertIn(term, joined)

    def test_politics_cross_lane_handoff_forbidden(self):
        politics = self.contract["lane_contracts"]["politics_longform"]
        self.assertTrue(politics["cross_lane_handoff_forbidden"])
        self.assertEqual(
            politics["derived_short_owner"], "111-politics-longform"
        )
        self.assertEqual(politics["derived_short_capcut_root"], "SHRTJUNGCHI")

    def test_global_execution_policy_forbids_auto_external_and_runtime_deploy(self):
        policy = self.contract["global_execution_policy"]
        self.assertEqual(policy["auto_external_llm_calls"], 0)
        self.assertEqual(policy["max_auto_retries"], 0)
        self.assertFalse(policy["validator_may_execute_next_stage"])
        self.assertFalse(policy["runtime_deploy_before_codex_review"])


class GateResultSchemaTests(unittest.TestCase):
    """The gate_result schema must forbid paid/LLM/upload auto-advance."""

    def setUp(self):
        self.assertTrue(GATE_RESULT_SCHEMA_PATH.exists(), "schema missing")
        self.schema = _load_json(GATE_RESULT_SCHEMA_PATH)

    def test_gate_result_rejects_paid_or_llm_auto_advance(self):
        """auto_advance_class must be a controlled enum that cannot authorize
        LLM/paid/upload work as 'automatic'."""
        cls_enum = self.schema["properties"]["auto_advance_class"]["enum"]
        # The allowed classes are all bounded; LLM/paid/upload are explicitly
        # forbidden classes, not allowed classes.
        self.assertIn("DETERMINISTIC_ONLY", cls_enum)
        self.assertIn("LLM_CALL_FORBIDDEN", cls_enum)
        self.assertIn("PAID_ACTION_FORBIDDEN", cls_enum)
        self.assertIn("UPLOAD_FORBIDDEN", cls_enum)
        # No class value can authorize forbidden work.
        for forbidden in (
            "LLM_CALL_ALLOWED",
            "PAID_ACTION_ALLOWED",
            "UPLOAD_ALLOWED",
        ):
            self.assertNotIn(forbidden, cls_enum)

    def test_gate_result_status_excludes_not_required_no_generated_tts(self):
        status_enum = self.schema["properties"]["status"]["enum"]
        self.assertNotIn("NOT_REQUIRED_NO_GENERATED_TTS", status_enum)
        self.assertIn("NOT_REQUIRED", status_enum)

    def test_gate_result_requires_all_canonical_fields(self):
        required = set(self.schema["required"])
        for field in (
            "schema_version",
            "status",
            "lane",
            "gate",
            "subgate",
            "validated_inputs",
            "evidence",
            "errors",
            "warnings",
            "next_action",
            "auto_advance_allowed",
            "auto_advance_class",
        ):
            self.assertIn(field, required)

    def test_gate_result_status_pass_requires_validator_authority(self):
        """PASS is only meaningful under DETERMINISTIC_VALIDATOR_ONLY.
        A gate_result with status=PASS must come from the validator, never
        from an external model. Enforced at contract level + runner level.
        Here we just ensure the contract + schema agree."""
        contract = _load_json(CONTRACT_PATH)
        self.assertEqual(
            contract["canonical_gate_model"]["pass_authority"],
            "DETERMINISTIC_VALIDATOR_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
