"""Rebuild manual_gate_state.json from the ledger.

Authority: projection only. manual_gate_state.json is always a function of
gate_ledger.jsonl. On mismatch with a hand-written state file, raise
StateLedgerMismatch and stop — never silently advance.
"""

from __future__ import annotations

from typing import Iterable


GATE_ORDER = [
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
]


class StateLedgerMismatch(Exception):
    """Raised when a candidate manual_gate_state.json disagrees with the
    projection rebuilt from the ledger."""

    def __init__(self, field_name: str, ledger_value, candidate_value):
        super().__init__(
            f"STATE_LEDGER_MISMATCH field={field_name} "
            f"ledger={ledger_value!r} candidate={candidate_value!r}"
        )
        self.field_name = field_name
        self.ledger_value = ledger_value
        self.candidate_value = candidate_value


def _gate_index(gate: str | None) -> int:
    if gate is None:
        return -1
    if gate not in GATE_ORDER:
        return -1
    return GATE_ORDER.index(gate)


def rebuild_state(events: Iterable[dict]) -> dict:
    """Project the current manual_gate_state.json from a ledger event list.

    The projection captures:
    - episode_id, lane, content_profile, production_mode, requested_target
      (locked at WORKFLOW_CREATED or the first G00 event).
    - current_gate / current_subgate / last_passed_gate derived from
      GATE_STARTED / GATE_PASSED / GATE_FAILED events.
    - projection_of_ledger_event_id = the last event id seen.
    """
    events = list(events)
    if not events:
        raise ValueError("STATE_REBUILD_EMPTY_LEDGER")

    genesis = events[0]
    state = {
        "schema_version": "manual-gate-state-v1",
        "episode_id": genesis.get("episode_id"),
        "lane": genesis.get("lane"),
        "content_profile": genesis.get("content_profile", "general_shorts"),
        "production_mode": genesis.get("production_mode", "not_applicable"),
        "requested_target": genesis.get("requested_target", "design_only"),
        "current_gate": None,
        "current_subgate": None,
        "last_passed_gate": None,
        "source_fingerprint": genesis.get("source_fingerprint", ""),
        "current_authoritative_artifact": None,
        "current_authoritative_sha256": None,
        "next_user_action": None,
        "auto_external_call": False,
        "release_allowed": False,
        "projection_of_ledger_event_id": genesis.get("event_id"),
        "contract_mode": genesis.get("contract_mode", "V2_CANONICAL"),
    }

    last_passed_idx = -1
    final_qc_passed = False
    for ev in events:
        et = ev.get("event_type")
        gate = ev.get("gate")
        actor = ev.get("actor")
        if et == "WORKFLOW_CREATED":
            # Promote any G00-scoped fields locked at creation.
            for k in (
                "content_profile",
                "production_mode",
                "requested_target",
                "source_fingerprint",
            ):
                if k in ev:
                    state[k] = ev[k]
        if et == "GATE_STARTED" and gate is not None:
            state["current_gate"] = gate
            state["current_subgate"] = ev.get("subgate")
        elif et == "GATE_PASSED" and gate is not None:
            idx = _gate_index(gate)
            if idx > last_passed_idx:
                last_passed_idx = idx
                state["last_passed_gate"] = gate
            # After a pass, the current gate stays at the passed gate until
            # the next GATE_STARTED event arrives.
            state["current_gate"] = gate
            state["current_subgate"] = ev.get("subgate")
            if ev.get("artifact_path"):
                state["current_authoritative_artifact"] = ev["artifact_path"]
            if ev.get("artifact_sha256"):
                state["current_authoritative_sha256"] = ev["artifact_sha256"]
        elif et == "GATE_FAILED" and gate is not None:
            state["current_gate"] = gate
            state["current_subgate"] = ev.get("subgate")
        elif et == "OWNER_TRANSFERRED":
            state["next_user_action"] = None
        elif et == "USER_VISUAL_PASS":
            state["next_user_action"] = None
        elif et == "FINAL_QC_PASS":
            # RW-P03-02 strict: FINAL_QC_PASS counts toward release only when
            # it occurs on gate=G90 and actor=VALIDATOR. A FINAL_QC_PASS
            # recorded against any other gate (e.g. G20) or any other actor
            # does not satisfy the release precondition.
            if gate == "G90" and actor == "VALIDATOR":
                final_qc_passed = True
        elif et == "UPLOAD_APPROVED":
            # RW-P03-02 strict: UPLOAD_APPROVED releases only when (a) a
            # valid G90 FINAL_QC_PASS preceded it, (b) this UPLOAD_APPROVED
            # is itself on gate=G90, and (c) its actor is USER (material
            # user-owned decision; never auto-released by RUNNER/VALIDATOR).
            if (
                final_qc_passed
                and gate == "G90"
                and actor == "USER"
            ):
                state["release_allowed"] = True
        state["projection_of_ledger_event_id"] = ev.get("event_id")

    return state


# Fields that must match exactly between a candidate state file and the
# ledger projection. Other fields (e.g. display timestamps) are advisory.
_MATCHED_FIELDS = (
    "episode_id",
    "lane",
    "content_profile",
    "production_mode",
    "current_gate",
    "current_subgate",
    "last_passed_gate",
    "current_authoritative_artifact",
    "current_authoritative_sha256",
    "projection_of_ledger_event_id",
    "release_allowed",
)


def compare_and_assert(ledger_projection: dict, candidate: dict) -> None:
    """Raise StateLedgerMismatch if the candidate state disagrees with the
    ledger projection on any matched field."""
    for field_name in _MATCHED_FIELDS:
        ledger_value = ledger_projection.get(field_name)
        candidate_value = candidate.get(field_name)
        if ledger_value != candidate_value:
            raise StateLedgerMismatch(field_name, ledger_value, candidate_value)
