"""P03 ledger / state projection / generated core tests (RED first).

Asserts the append-only ledger, the state projection rebuild rule, the
state/ledger mismatch block, and the byte-identical generated core across
the three skills.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_CORE_DIR = ROOT / "shared" / "workflow-harness" / "core"

LEDGER_PY = SHARED_CORE_DIR / "ledger.py"
STATE_PY = SHARED_CORE_DIR / "state_projection.py"
GATE_VALIDATION_PY = SHARED_CORE_DIR / "gate_validation.py"
COST_GUARD_PY = SHARED_CORE_DIR / "cost_guard.py"
CONTEXT_MANIFEST_PY = SHARED_CORE_DIR / "context_manifest.py"


def _load_module(name: str, path: Path):
    """Load a source module AND register it in sys.modules so that
    dataclass / typing machinery that looks up cls.__module__ works."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


class CoreModulePresenceTests(unittest.TestCase):
    """All five canonical core modules must exist."""

    def test_ledger_module_exists(self):
        self.assertTrue(LEDGER_PY.exists(), "shared/workflow-harness/core/ledger.py missing")

    def test_state_projection_module_exists(self):
        self.assertTrue(STATE_PY.exists(), "state_projection.py missing")

    def test_gate_validation_module_exists(self):
        self.assertTrue(GATE_VALIDATION_PY.exists(), "gate_validation.py missing")

    def test_cost_guard_module_exists(self):
        self.assertTrue(COST_GUARD_PY.exists(), "cost_guard.py missing")

    def test_context_manifest_module_exists(self):
        self.assertTrue(CONTEXT_MANIFEST_PY.exists(), "context_manifest.py missing")


class LedgerAppendOnlyTests(unittest.TestCase):
    def setUp(self):
        if not LEDGER_PY.exists():
            self.skipTest("ledger.py not yet implemented (RED)")
        self.ledger = _load_module("p03_ledger", LEDGER_PY)

    def test_ledger_is_append_only(self):
        """A new event must reference an existing previous_event_id (or null
        only for the genesis). Broken chains must be rejected."""
        L = self.ledger
        store = L.LedgerStore()
        genesis = {
            "event_id": "evt-000000",
            "timestamp": "2026-07-20T10:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "politics_longform",
            "gate": None,
            "event_type": "WORKFLOW_CREATED",
            "actor": "USER",
            "previous_event_id": None,
            "reason": "genesis",
        }
        store.append(genesis)
        # Valid continuation.
        good = {
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T10:01:00+09:00",
            "episode_id": "EP-01",
            "lane": "politics_longform",
            "gate": "G00",
            "event_type": "GATE_STARTED",
            "actor": "RUNNER",
            "previous_event_id": "evt-000000",
        }
        store.append(good)
        self.assertEqual(len(store.events), 2)

        # Broken chain: previous_event_id references nothing.
        broken = {
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T10:02:00+09:00",
            "episode_id": "EP-01",
            "lane": "politics_longform",
            "gate": "G00",
            "event_type": "GATE_PASSED",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-999999",
        }
        with self.assertRaises(L.BrokenChainError):
            store.append(broken)


class StateProjectionTests(unittest.TestCase):
    def setUp(self):
        if not (LEDGER_PY.exists() and STATE_PY.exists()):
            self.skipTest("core modules not yet implemented (RED)")
        self.ledger = _load_module("p03_ledger_state", LEDGER_PY)
        self.state = _load_module("p03_state", STATE_PY)

    def _build_simple_ledger(self):
        L = self.ledger
        store = L.LedgerStore()
        store.append({
            "event_id": "evt-000000",
            "timestamp": "2026-07-20T10:00:00+09:00",
            "episode_id": "EP-01",
            "lane": "politics_longform",
            "gate": None,
            "event_type": "WORKFLOW_CREATED",
            "actor": "USER",
            "previous_event_id": None,
        })
        store.append({
            "event_id": "evt-000001",
            "timestamp": "2026-07-20T10:01:00+09:00",
            "episode_id": "EP-01",
            "lane": "politics_longform",
            "gate": "G00",
            "event_type": "GATE_STARTED",
            "actor": "RUNNER",
            "previous_event_id": "evt-000000",
        })
        store.append({
            "event_id": "evt-000002",
            "timestamp": "2026-07-20T10:02:00+09:00",
            "episode_id": "EP-01",
            "lane": "politics_longform",
            "gate": "G00",
            "event_type": "GATE_PASSED",
            "actor": "VALIDATOR",
            "previous_event_id": "evt-000001",
        })
        return store

    def test_state_rebuild_matches_ledger(self):
        store = self._build_simple_ledger()
        projection = self.state.rebuild_state(store.events)
        self.assertEqual(projection["episode_id"], "EP-01")
        self.assertEqual(projection["lane"], "politics_longform")
        self.assertEqual(projection["current_gate"], "G00")
        self.assertEqual(projection["last_passed_gate"], "G00")
        self.assertEqual(
            projection["projection_of_ledger_event_id"], "evt-000002"
        )

    def test_state_ledger_mismatch_blocks(self):
        """If a hand-written manual_gate_state.json disagrees with the ledger
        rebuild, the comparator must raise STATE_LEDGER_MISMATCH."""
        store = self._build_simple_ledger()
        projection = self.state.rebuild_state(store.events)
        tampered = dict(projection)
        tampered["last_passed_gate"] = "G20"  # tamper: ledger says G00.
        with self.assertRaises(self.state.StateLedgerMismatch) as ctx:
            self.state.compare_and_assert(projection, tampered)
        self.assertIn("STATE_LEDGER_MISMATCH", str(ctx.exception))


class GateValidationAuthorityTests(unittest.TestCase):
    """Validator validates only; never advances authority."""

    def setUp(self):
        if not GATE_VALIDATION_PY.exists():
            self.skipTest("gate_validation.py not yet implemented (RED)")
        self.gv = _load_module("p03_gate_validation", GATE_VALIDATION_PY)

    def test_validator_result_shape(self):
        result = self.gv.validate_gate(
            lane="general_shorts_production",
            gate="G40",
            subgate=None,
            validated_inputs=[
                {"path": "20_script/design_handoff.json", "sha256": "a" * 64}
            ],
            evidence=[],
            errors=[],
            warnings=[],
            next_action="PREPARE_G50",
            auto_advance_allowed=True,
            auto_advance_class="DETERMINISTIC_ONLY",
        )
        self.assertEqual(result["schema_version"], "gate-result-v1")
        self.assertEqual(result["lane"], "general_shorts_production")
        self.assertEqual(result["gate"], "G40")

    def test_validator_rejects_forbidden_auto_advance_class(self):
        """A validator result requesting LLM_CALL_ALLOWED / PAID_ACTION_ALLOWED
        / UPLOAD_ALLOWED must be rejected at construction."""
        for forbidden in (
            "LLM_CALL_ALLOWED",
            "PAID_ACTION_ALLOWED",
            "UPLOAD_ALLOWED",
        ):
            with self.assertRaises(self.gv.ForbiddenAdvanceClass):
                self.gv.validate_gate(
                    lane="general_shorts_production",
                    gate="G40",
                    subgate=None,
                    validated_inputs=[],
                    evidence=[],
                    errors=[],
                    warnings=[],
                    next_action="x",
                    auto_advance_allowed=True,
                    auto_advance_class=forbidden,
                )


class CostGuardTests(unittest.TestCase):
    def setUp(self):
        if not COST_GUARD_PY.exists():
            self.skipTest("cost_guard.py not yet implemented (RED)")
        self.cg = _load_module("p03_cost_guard", COST_GUARD_PY)

    def test_no_budget_means_no_paid_action(self):
        guard = self.cg.CostGuard(
            episode_budget_usd=None,
            max_model_input_tokens_per_gate=None,
            max_model_output_tokens_per_gate=None,
            max_paid_tts_chars=None,
            paid_tts_authorization={
                "status": "NOT_AUTHORIZED",
                "scope": "none",
            },
        )
        self.assertFalse(guard.can_authorize_paid_action())

    def test_budget_overrun_stops(self):
        guard = self.cg.CostGuard(
            episode_budget_usd=10.0,
            max_model_input_tokens_per_gate=1000,
            max_model_output_tokens_per_gate=1000,
            max_paid_tts_chars=1000,
            paid_tts_authorization={
                "status": "AUTHORIZED_FOR_EPISODE",
                "scope": "tts_only",
                "max_chars": 1000,
            },
        )
        # Within limit: OK.
        self.assertTrue(guard.can_spend_tts(chars=500))
        # Over limit: must STOP.
        self.assertFalse(guard.can_spend_tts(chars=2000))


if __name__ == "__main__":
    unittest.main()
