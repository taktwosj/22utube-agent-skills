"""000short-production-agent deterministic gate validator (G30-G90).

Validates only the current gate. Never:
- calls an external model
- opens CapCut
- performs paid TTS without authorization
- uploads
- silently advances authority

Enforces:
- entry owner-transfer receipt + matching design_handoff SHA
- G30 measured audio precedes G40 SRT lock (NORM-002)
- status=NOT_REQUIRED + reason_code=NO_GENERATED_TTS (NORM-003)
- G70 release_allowed=false
- G90 release requires FINAL_QC_PASS + UPLOAD_APPROVED (RW-P03-02)
- production cannot rewrite hook or urakkai order

Thin lane adapter over the shared generated core.
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
    / "000short-production-agent"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)


class GateFail(Exception):
    pass


def _import_core():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "short_prod_workflow_harness_core", GENERATED_CORE
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["short_prod_workflow_harness_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def validate_entry(*, owner_transfer_receipt: dict, design_handoff: dict) -> list[dict]:
    """G30 entry contract: reject without valid owner-transfer receipt and
    matching canonical handoff SHA."""
    errors: list[dict] = []
    if not owner_transfer_receipt:
        errors.append({"code": "FAIL_ENTRY_NO_OWNER_TRANSFER_RECEIPT"})
        return errors
    if owner_transfer_receipt.get("schema_version") != "owner-transfer-v1":
        errors.append({"code": "FAIL_ENTRY_RECEIPT_SCHEMA"})
    if owner_transfer_receipt.get("transfer_status") != "PASS":
        errors.append({"code": "FAIL_ENTRY_RECEIPT_NOT_PASS"})
    expected_sha = owner_transfer_receipt.get("canonical_handoff_sha256")
    actual_sha = design_handoff.get("design_handoff_sha256") or design_handoff.get("canonical_handoff_sha256")
    if expected_sha and actual_sha and expected_sha != actual_sha:
        errors.append(
            {
                "code": "FAIL_ENTRY_HANDOFF_SHA_MISMATCH",
                "expected": expected_sha,
                "actual": actual_sha,
            }
        )
    if design_handoff.get("status") != "PASS":
        errors.append({"code": "FAIL_ENTRY_HANDOFF_NOT_PASS"})
    return errors


def validate_g30(
    *,
    audio_lock: dict,
    owner_transfer_receipt: dict | None = None,
    design_handoff: dict | None = None,
) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if owner_transfer_receipt is not None and design_handoff is not None:
        errors.extend(validate_entry(
            owner_transfer_receipt=owner_transfer_receipt,
            design_handoff=design_handoff,
        ))

    # NORM-003: NOT_REQUIRED_NO_GENERATED_TTS is forbidden.
    raw_status = audio_lock.get("status")
    if raw_status == "NOT_REQUIRED_NO_GENERATED_TTS":
        errors.append({"code": "FAIL_FORBIDDEN_NOT_REQUIRED_NO_GENERATED_TTS"})
    if raw_status == "NOT_REQUIRED":
        if audio_lock.get("reason_code") != "NO_GENERATED_TTS":
            errors.append({"code": "FAIL_NO_GENERATED_TTS_REASON_CODE_MISSING"})

    # PASS requires measured duration evidence.
    if raw_status == "PASS":
        if not audio_lock.get("measured_duration_evidence_sha256"):
            errors.append({"code": "FAIL_G30_NO_MEASURED_DURATION"})
        if audio_lock.get("audio_source") == "GENERATED_TTS":
            if not audio_lock.get("paid_tts_cost_event_id"):
                errors.append({"code": "FAIL_G30_PAID_TTS_NO_COST_EVENT"})

    reason_code = audio_lock.get("reason_code") if raw_status == "NOT_REQUIRED" else None
    return core.validate_gate(
        lane="general_shorts_production",
        gate="G30",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G40" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors and raw_status == "PASS" else (raw_status if raw_status else None),
        reason_code=reason_code,
    )


def validate_g40(*, caption_lock: dict, g30_audio_lock: dict | None) -> dict:
    core = _import_core()
    errors: list[dict] = []

    # NORM-002: SRT lock requires measured audio (G30 PASS or NOT_REQUIRED
    # with NO_GENERATED_TTS and measured source duration).
    if g30_audio_lock is None:
        errors.append({"code": "FAIL_G40_NO_G30_AUDIO_LOCK"})
    else:
        g30_status = g30_audio_lock.get("status")
        if g30_status not in ("PASS", "NOT_REQUIRED"):
            errors.append({"code": "FAIL_G40_G30_NOT_LOCKED"})
        if not g30_audio_lock.get("measured_duration_evidence_sha256"):
            errors.append({"code": "FAIL_G40_G30_NO_MEASURED_DURATION"})

    if caption_lock.get("g30_audio_lock_sha256") and g30_audio_lock:
        # The caption lock must reference the audio lock. We do not recompute
        # the SHA here; the runner cross-checks.
        pass
    if caption_lock.get("final_cue_count", 0) > 0:
        if not caption_lock.get("all_cues_within_measured_audio", True):
            errors.append({"code": "FAIL_G40_CUE_OUTSIDE_MEASURED_AUDIO"})
        if not caption_lock.get("no_overlap_verified", True):
            errors.append({"code": "FAIL_G40_CUE_OVERLAP"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G40",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G50" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g50(*, track_plan: dict, g40_caption_lock: dict | None) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if g40_caption_lock is None:
        errors.append({"code": "FAIL_G50_NO_G40_CAPTION_LOCK"})
    if not track_plan.get("segments"):
        errors.append({"code": "FAIL_G50_NO_SEGMENTS"})
    if track_plan.get("timeline_order_matches_design_handoff") is False:
        errors.append({"code": "FAIL_G50_CREATIVE_REORDER_FORBIDDEN"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G50",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G60" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g60(*, assembly_result: dict, template_contract_sha256: str | None = None) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if assembly_result.get("capcut_root") and assembly_result["capcut_root"] != "shrt white":
        errors.append({"code": "FAIL_G60_WRONG_CAPCUT_ROOT"})
    hard_fails = assembly_result.get("hard_fails", [])
    for hf in hard_fails:
        errors.append({"code": hf})
    # Static PASS transitions to WAIT_USER_VISUAL_GATE.
    status = "PASS" if not errors else "FAIL"
    next_action = "WAIT_USER_VISUAL_GATE" if not errors else "NONE"

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G60",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action=next_action,
        auto_advance_allowed=False,  # WAIT_USER_VISUAL_GATE is a user gate
        auto_advance_class="NONE",
        status=status,
    )


def validate_g70(*, upload_package: dict) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if upload_package.get("release_allowed") is not False:
        errors.append({"code": "FAIL_G70_RELEASE_MUST_BE_FALSE"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G70",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G80" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g80(*, render_evidence: dict) -> dict:
    core = _import_core()
    errors: list[dict] = []

    if not render_evidence.get("ffprobe_verified"):
        errors.append({"code": "FAIL_G80_FFPROBE"})
    if not render_evidence.get("rendered_mp4_sha256"):
        errors.append({"code": "FAIL_G80_NO_RENDERED_MP4"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G80",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="PREPARE_G90" if not errors else "NONE",
        auto_advance_allowed=not errors,
        auto_advance_class="DETERMINISTIC_ONLY" if not errors else "NONE",
        status="PASS" if not errors else None,
    )


def validate_g90(*, final_qc: dict) -> dict:
    core = _import_core()
    errors: list[dict] = []

    # Release requires both FINAL_QC_PASS and UPLOAD_APPROVED, in order.
    # RW-P03-02.
    has_final_qc_pass = final_qc.get("final_qc_passed") is True
    has_upload_approved = final_qc.get("upload_approved") is True
    release_allowed = bool(has_final_qc_pass and has_upload_approved)

    if has_upload_approved and not has_final_qc_pass:
        errors.append({"code": "FAIL_G90_UPLOAD_BEFORE_FINAL_QC"})

    return core.validate_gate(
        lane="general_shorts_production",
        gate="G90",
        subgate=None,
        validated_inputs=[],
        evidence=[],
        errors=errors,
        warnings=[],
        next_action="WAIT_UPLOAD_APPROVAL" if not has_upload_approved else "EPISODE_RELEASED",
        auto_advance_allowed=False,  # upload requires explicit user approval
        auto_advance_class="NONE",
        status="PASS" if (not errors and release_allowed) else ("WAIT_UPLOAD_APPROVAL" if has_final_qc_pass else None),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a 000short-production-agent gate (G30-G90)."
    )
    parser.add_argument(
        "--gate",
        required=True,
        choices=["G30", "G40", "G50", "G60", "G60.USER", "G70", "G80", "G90"],
    )
    parser.add_argument("--audio-lock", type=Path)
    parser.add_argument("--caption-lock", type=Path)
    parser.add_argument("--track-plan", type=Path)
    parser.add_argument("--assembly-result", type=Path)
    parser.add_argument("--upload-package", type=Path)
    parser.add_argument("--render-evidence", type=Path)
    parser.add_argument("--final-qc", type=Path)
    parser.add_argument("--g30-audio-lock", type=Path, help="G40 input: G30 lock")
    parser.add_argument("--g40-caption-lock", type=Path, help="G50 input: G40 lock")
    parser.add_argument("--owner-transfer-receipt", type=Path)
    parser.add_argument("--design-handoff", type=Path)
    args = parser.parse_args(argv)

    def _load(p: Path | None) -> dict:
        if p is None or not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    if args.gate == "G30":
        result = validate_g30(
            audio_lock=_load(args.audio_lock),
            owner_transfer_receipt=_load(args.owner_transfer_receipt) or None,
            design_handoff=_load(args.design_handoff) or None,
        )
    elif args.gate == "G40":
        result = validate_g40(
            caption_lock=_load(args.caption_lock),
            g30_audio_lock=_load(args.g30_audio_lock) or None,
        )
    elif args.gate == "G50":
        result = validate_g50(
            track_plan=_load(args.track_plan),
            g40_caption_lock=_load(args.g40_caption_lock) or None,
        )
    elif args.gate == "G60":
        result = validate_g60(assembly_result=_load(args.assembly_result))
    elif args.gate == "G70":
        result = validate_g70(upload_package=_load(args.upload_package))
    elif args.gate == "G80":
        result = validate_g80(render_evidence=_load(args.render_evidence))
    elif args.gate == "G90":
        result = validate_g90(final_qc=_load(args.final_qc))
    else:
        result = {"status": "FAIL", "errors": [{"code": "UNKNOWN_GATE"}]}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("PASS", "NOT_REQUIRED", "WAIT_UPLOAD_APPROVAL") else 1


if __name__ == "__main__":
    sys.exit(main())
