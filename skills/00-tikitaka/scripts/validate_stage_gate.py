"""00-tikitaka deterministic gate validator.

Validates only the current gate (G00 / G10 / G20 subgate). Never:
- calls an external model
- opens CapCut
- performs paid TTS
- uploads
- silently advances authority

On PASS the validator returns a gate_result with
auto_advance_class=DETERMINISTIC_ONLY. The runner consumes the result.

This is a thin lane adapter over the shared core
(workflow_harness_core.gate_validation).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_CORE = (
    REPO_ROOT
    / "skills"
    / "00-tikitaka"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)


class GateFail(Exception):
    """Raised when a deterministic check fails."""


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "tikitaka_workflow_harness_core", GENERATED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tikitaka_workflow_harness_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def validate_g00(*, intake_lock: dict, cost_guard: dict) -> dict:
    """Validate the G00 lock."""
    core = _import_core()
    errors: list[dict] = []
    warnings: list[dict] = []

    required_lock_fields = (
        "source_sha256",
        "content_profile",
        "production_mode",
        "requested_target",
        "source_fingerprint",
    )
    for field in required_lock_fields:
        if field not in intake_lock:
            errors.append(
                {"code": "FAIL_G00_MISSING_FIELD", "field": field}
            )

    if intake_lock.get("content_profile") != "general_shorts":
        errors.append(
            {
                "code": "FAIL_G00_CONTENT_PROFILE",
                "message": "00-tikitaka lane requires content_profile=general_shorts",
            }
        )

    if intake_lock.get("requested_target") not in (
        "design_only",
        "editorial_locked",
        "capcut_ready",
        "upload_package",
        "rendered",
    ):
        errors.append(
            {"code": "FAIL_G00_REQUESTED_TARGET", "field": "requested_target"}
        )

    # Cost guard must exist. No budget => no paid action.
    if cost_guard.get("schema_version") != "cost-guard-v1":
        errors.append({"code": "FAIL_G00_COST_GUARD_MISSING"})

    return core.validate_gate(
        lane="general_shorts_design",
        gate="G00",
        subgate=None,
        validated_inputs=[{"path": "20_script/intake_lock.json",
                            "sha256": _sha256_file(Path("20_script/intake_lock.json"))}
                          if Path("20_script/intake_lock.json").exists()
                          else {"path": "20_script/intake_lock.json", "sha256": ""}],
        evidence=[],
        errors=errors,
        warnings=warnings,
        next_action="PREPARE_G10" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
    )


def validate_g10(*, design_blueprint: dict, timeline_design: dict) -> dict:
    core = _import_core()
    errors: list[dict] = []

    required_roles = {
        "speaker_speech",
        "narration_candidate",
        "situation_description_candidate",
        "screen_action",
        "audio_event",
        "source_order",
    }
    roles_present = {r.get("role") for r in design_blueprint.get("roles", [])}
    missing = required_roles - roles_present
    if missing:
        errors.append(
            {
                "code": "FAIL_G10_MISSING_ROLE",
                "missing": sorted(missing),
            }
        )

    # Every timeline segment must carry an assembly_role.
    for seg in timeline_design.get("segments", []):
        if "assembly_role" not in seg:
            errors.append(
                {
                    "code": "FAIL_G10_TIMELINE_MISSING_ASSEMBLY_ROLE",
                    "segment_id": seg.get("id"),
                }
            )

    return core.validate_gate(
        lane="general_shorts_design",
        gate="G10",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G20" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
    )


def validate_g20(*, handoff: dict, receipt: dict, design_lock: dict | None) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if handoff.get("schema_version") != "shorts-design-handoff-v1":
        errors.append({"code": "FAIL_G20_HANDOFF_SCHEMA"})
    if handoff.get("status") != "PASS":
        errors.append({"code": "FAIL_G20_HANDOFF_NOT_PASS"})

    # External review receipt: two rounds, no forbidden claims.
    rounds = receipt.get("rounds", [])
    if len(rounds) != 2:
        errors.append({"code": "FAIL_G20_RECEIPT_ROUNDS", "rounds": len(rounds)})
    for r in rounds:
        if r.get("grade") not in (
            "PASS_RECOMMENDED",
            "REVISE_REQUIRED",
            "EVIDENCE_REQUIRED",
        ):
            errors.append(
                {"code": "FAIL_G20_ROUND_GRADE", "round": r.get("round")}
            )
        if r.get("forbidden_claim_detected"):
            errors.append(
                {
                    "code": "EXTERNAL_AUTHORITY_OVERREACH",
                    "round": r.get("round"),
                    "message": "external return carried a forbidden final-authority claim",
                }
            )

    if receipt.get("final_status") != "PASS":
        errors.append({"code": "FAIL_G20_RECEIPT_FINAL_STATUS"})

    # Design lock conditions (if present).
    if design_lock is not None:
        if design_lock.get("material_change_detected"):
            errors.append(
                {"code": "FAIL_G20_MATERIAL_CHANGE_REQUIRES_USER"}
            )

    return core.validate_gate(
        lane="general_shorts_design",
        gate="G20",
        subgate="DESIGN_LOCKED",
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action=(
            "PREPARE_OWNER_TRANSFER"
            if (not errors and handoff.get("requested_target") != "design_only")
            else ("STOP_AT_G20" if not errors else "NONE")
        ),
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a 00-tikitaka gate (G00/G10/G20)."
    )
    parser.add_argument("--gate", required=True, choices=["G00", "G10", "G20"])
    parser.add_argument("--intake-lock", type=Path)
    parser.add_argument("--cost-guard", type=Path)
    parser.add_argument("--design-blueprint", type=Path)
    parser.add_argument("--timeline-design", type=Path)
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--design-lock", type=Path)
    args = parser.parse_args(argv)

    def _load(p: Path | None) -> dict:
        if p is None or not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    if args.gate == "G00":
        result = validate_g00(
            intake_lock=_load(args.intake_lock),
            cost_guard=_load(args.cost_guard),
        )
    elif args.gate == "G10":
        result = validate_g10(
            design_blueprint=_load(args.design_blueprint),
            timeline_design=_load(args.timeline_design),
        )
    else:
        result = validate_g20(
            handoff=_load(args.handoff),
            receipt=_load(args.receipt),
            design_lock=_load(args.design_lock),
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
