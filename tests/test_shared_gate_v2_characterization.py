"""P00 characterization tests for SHARED-GATE-SEPARATED-LANES-V2.

These tests capture the V2 canonical contract BEFORE any implementation
exists. They MUST fail ("red") at the start of P00 because none of the
V2 artifacts, schemas, or router wiring exist yet. Per the TDD policy
(NORM-005 / NORM-006 intentional behavior changes included), each
behavior change is verified by a failing test first.

The expected_red is: the V2 canonical contract files and routers do
not exist yet, so every assertion that reads a V2-only path or asserts
a V2-only property fails.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "docs" / "migrations" / "shared-gates-separated-lanes-v2"
SHARED_DIR = ROOT / "shared" / "workflow-harness"
SKILLS = ROOT / "skills"


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class BaselineFreezeCharacterizationTests(unittest.TestCase):
    """P00 requires a recorded baseline.json describing the frozen baseline."""

    def test_baseline_json_exists_and_records_required_evidence(self):
        baseline_path = MIGRATION_DIR / "baseline.json"
        self.assertTrue(
            baseline_path.exists(),
            "baseline.json must be written in P00 to freeze the baseline state",
        )
        baseline = _read_json(baseline_path)
        self.assertEqual(
            baseline["repository"]["baseline_commit"],
            "b455c976a82c4ab9bb59cd672eec09e3cca36937",
        )
        self.assertEqual(baseline["baseline_unittest"]["result"], "PASS")
        self.assertEqual(baseline["baseline_unittest"]["tests_run"], 276)
        self.assertEqual(baseline["baseline_verify_repo"]["result"], "PASS")
        # Three skill tree hashes must be recorded.
        hashes = baseline["baseline_skill_source_tree_sha256_from_work_order"]
        for skill in (
            "00-tikitaka",
            "000short-production-agent",
            "111-politics-longform",
        ):
            self.assertIn(skill, hashes)
            self.assertTrue(hashes[skill])


class CanonicalGateModelCharacterizationTests(unittest.TestCase):
    """V2 canonical gate order: G30 (audio + measured duration) precedes
    G40 (measured-audio-based caption/SRT). NORM-002 hard_fail=FAIL_G30_G40_ORDER."""

    def test_shared_gates_contract_json_exists(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(
            contract_path.exists(),
            "V2 canonical contract JSON must exist (created in P01)",
        )

    def test_canonical_gate_sequence_has_g30_before_g40(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        sequence = contract["canonical_gate_model"]["sequence"]
        self.assertIn("G30", sequence)
        self.assertIn("G40", sequence)
        self.assertLess(
            sequence.index("G30"),
            sequence.index("G40"),
            "NORM-002: G30 (audio + measured duration) must precede "
            "G40 (measured-audio-based caption/SRT)",
        )

    def test_g30_definition_mentions_measured_duration(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        defs = contract["canonical_gate_model"]["definitions"]
        self.assertIn("G30", defs)
        self.assertIn("G40", defs)
        g30_upper = defs["G30"].upper()
        self.assertIn(
            "AUDIO",
            g30_upper,
            "G30 must cover audio asset selection/generation + measured duration",
        )
        self.assertIn("DURATION", g30_upper)
        g40_upper = defs["G40"].upper()
        self.assertIn("CAPTION", g40_upper)
        self.assertIn("SRT", g40_upper)

    def test_not_required_no_generated_tts_is_forbidden_value(self):
        """NORM-003: NOT_REQUIRED_NO_GENERATED_TTS must not appear as a state."""
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        allowed_states = contract["canonical_gate_model"]["allowed_states"]
        self.assertNotIn(
            "NOT_REQUIRED_NO_GENERATED_TTS",
            allowed_states,
            "NORM-003: forbidden value must not be in allowed_states",
        )
        self.assertIn("NOT_REQUIRED", allowed_states)


class ExternalAuthorityCharacterizationTests(unittest.TestCase):
    """External model never emits PASS. PASS only from deterministic validator."""

    def test_external_forbidden_claims_include_pass(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        forbidden = contract["canonical_gate_model"][
            "external_forbidden_claims"
        ]
        self.assertIn("PASS", forbidden)
        self.assertIn("DESIGN_LOCK", forbidden)
        self.assertIn("USER_APPROVED", forbidden)

    def test_pass_authority_is_deterministic_validator_only(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        self.assertEqual(
            contract["canonical_gate_model"]["pass_authority"],
            "DETERMINISTIC_VALIDATOR_ONLY",
        )


class LaneOwnershipCharacterizationTests(unittest.TestCase):
    """NORM-005 / NORM-006: lane ownership boundaries."""

    def test_lane_contracts_present(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        lanes = contract["lane_contracts"]
        for lane in (
            "general_shorts_design",
            "general_shorts_production",
            "politics_longform",
        ):
            self.assertIn(lane, lanes)

    def test_tikitaka_owns_only_g00_g10_g20(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        design = contract["lane_contracts"]["general_shorts_design"]
        self.assertEqual(design["owner"], "00-tikitaka")
        self.assertEqual(design["gates"], ["G00", "G10", "G20"])
        forbidden = design["forbidden"]
        # Must not produce production outputs.
        joined = " ".join(forbidden).upper()
        self.assertIn("TTS", joined)
        self.assertIn("SRT", joined)
        self.assertIn("CAPCUT", joined)

    def test_shorts_production_owns_g30_through_g90(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        prod = contract["lane_contracts"]["general_shorts_production"]
        self.assertEqual(prod["owner"], "000short-production-agent")
        self.assertEqual(
            prod["gates"],
            ["G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"],
        )

    def test_politics_owns_g00_through_g90_end_to_end(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        politics = contract["lane_contracts"]["politics_longform"]
        self.assertEqual(politics["owner"], "111-politics-longform")
        self.assertEqual(
            politics["gates"],
            [
                "G00",
                "G10",
                "G20",
                "G30",
                "G40",
                "G50",
                "G60",
                "G60.USER",
                "G70",
                "G80",
                "G90",
            ],
        )

    def test_politics_derived_short_stays_inside_111(self):
        """NORM-006: politics-derived shorts owned by 111 and use SHRTJUNGCHI."""
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        politics = contract["lane_contracts"]["politics_longform"]
        self.assertEqual(politics["derived_short_owner"], "111-politics-longform")
        self.assertEqual(politics["derived_short_capcut_root"], "SHRTJUNGCHI")
        self.assertTrue(politics["cross_lane_handoff_forbidden"])


class ManualExternalTransportCharacterizationTests(unittest.TestCase):
    """NORM-005: external review transport is USER manual, not automatic API.

    These tests assert that V2 forbids automatic external LLM calls and
    that browser-assisted review is no longer mandatory."""

    def test_global_execution_policy_zero_external_calls(self):
        contract_path = (
            SHARED_DIR / "contract" / "shared_gates_separated_lanes_v2.json"
        )
        self.assertTrue(contract_path.exists(), "contract missing")
        contract = _read_json(contract_path)
        policy = contract["global_execution_policy"]
        self.assertEqual(policy["auto_external_llm_calls"], 0)
        self.assertEqual(policy["max_auto_retries"], 0)
        self.assertFalse(policy["validator_may_execute_next_stage"])
        self.assertFalse(policy["runtime_deploy_before_codex_review"])


if __name__ == "__main__":
    unittest.main()
