from __future__ import annotations

import argparse
import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import read_json, sha256_file
from schema_runtime import validate_schema

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflow.json"
SCHEMAS = ROOT / "schemas"


def _contracts():
    flow = read_json(WORKFLOW)
    checks = {}
    for stage, route in flow["validation"]["checks"].items():
        validators = route.get("validators") or [route["validator"]]
        checks[stage] = tuple(Path(v).stem.removeprefix("validate_") for v in validators)
    stages = flow["production_stages"]
    entry = {}
    for i, row in enumerate(stages):
        if not i or row["id"] not in checks:
            continue
        entry[row["id"]] = row.get("requires_by_mode", stages[i - 1]["pass"])
    return checks, entry


STAGE_CHECKS, STAGE_ENTRY_STATUS = _contracts()
ALL_CHECKS = tuple(dict.fromkeys(c for values in STAGE_CHECKS.values() for c in values))
RECEIPTS = {
    "external_review": ("external_review_evidence_path", "external_review_evidence_sha256", "external_review_evidence.schema.json"),
    "design_lock": ("design_lock_evidence_path", "design_lock_evidence_sha256", "design_lock_evidence.schema.json"),
    "clean_visual": ("clean_visual_receipt_path", "clean_visual_receipt_sha256", "clean_visual_receipt.schema.json"),
    "audio_lock": ("audio_lock_path", "audio_lock_sha256", "audio_lock.schema.json"),
    "caption_lock": ("caption_lock_path", "caption_lock_sha256", "caption_lock.schema.json"),
    "build_inputs": ("build_inputs_receipt_path", "build_inputs_receipt_sha256", None),
    "capcut_project": ("capcut_project_evidence_path", "capcut_project_evidence_sha256", "capcut_project_evidence.schema.json"),
}
PREREQUISITES = {
    "05": ("external_review",),
    "06": ("design_lock",),
    "07": ("design_lock",),
    "08": ("design_lock", "clean_visual", "audio_lock", "caption_lock"),
    "09": ("design_lock", "audio_lock", "caption_lock", "build_inputs", "capcut_project"),
}


def prerequisites_for_stage(stage: str, state: dict) -> tuple[str, ...]:
    required = PREREQUISITES[stage]
    if stage == "08" and state.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL":
        return tuple(receipt for receipt in required if receipt != "clean_visual")
    return required


def expected_entry_status(stage: str, state: dict) -> str:
    contract = STAGE_ENTRY_STATUS[stage]
    if isinstance(contract, dict):
        mode = str(state.get("approval_mode", "normal"))
        expected = contract.get(mode)
        if not isinstance(expected, str):
            raise ValueError(f"APPROVAL_MODE_INVALID:{mode}")
        return expected
    return contract


def resolve_stage(state: dict) -> str:
    raw = str(state.get("current_stage", state.get("stage", ""))).strip()
    stage = raw.zfill(2) if raw.isdigit() else raw[:2]
    if stage not in STAGE_CHECKS:
        raise ValueError(f"STAGE_NOT_VALIDATABLE:{raw}")
    return stage


def _receipt_error(state, state_path, name):
    path_key, sha_key, schema = RECEIPTS[name]
    raw, expected = state.get(path_key), state.get(sha_key)
    if not isinstance(raw, str) or not raw or not isinstance(expected, str):
        return "WAIT", {"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": name}
    path = Path(raw) if Path(raw).is_absolute() else state_path.parent / raw
    try:
        if not path.is_file() or sha256_file(path).lower() != expected.lower():
            raise ValueError("path or sha256 mismatch")
        data = read_json(path)
        if schema and (errors := validate_schema(data, read_json(SCHEMAS / schema))):
            raise ValueError(str(errors))
        if data.get("status") != "PASS" or data.get("episode_id") not in (None, state.get("episode_id")):
            raise ValueError("status or episode mismatch")
        if schema is None and (data.get("errors") != [] or not isinstance(data.get("evidence"), dict)):
            raise ValueError("result shape mismatch")
    except (OSError, ValueError, TypeError) as exc:
        return "FAIL", {"code": "PREREQUISITE_EVIDENCE_INVALID", "receipt": name, "detail": str(exc)}


def _external_review_mode_error(state: dict, state_path: Path):
    if state.get("approval_mode", "normal") != "exact_paperclip_p0_automatic":
        return None
    raw = state.get("external_review_evidence_path")
    if not isinstance(raw, str) or not raw:
        return "WAIT", {"code": "EXTERNAL_REVIEW_APPROVAL_EVIDENCE_MISSING"}
    path = Path(raw) if Path(raw).is_absolute() else state_path.parent / raw
    try:
        evidence = read_json(path)
    except (OSError, ValueError, TypeError) as exc:
        return "FAIL", {"code": "EXTERNAL_REVIEW_APPROVAL_EVIDENCE_INVALID", "detail": str(exc)}
    expected = "HERMES_DELEGATED_ROUTINE_APPROVAL_AFTER_EVIDENCE"
    if evidence.get("approval_status") != expected:
        return "FAIL", {
            "code": "EXTERNAL_REVIEW_APPROVAL_MODE_MISMATCH",
            "expected": expected,
            "actual": evidence.get("approval_status"),
        }
    return None


def _run(check, a):
    module = importlib.import_module("validate_" + check)
    if check == "design_lock":
        return module.validate_handoff(a.handoff, a.source_identity, a.timeline, a.evidence)
    if check == "clean_visual":
        return module.validate_clean_visual(
            a.clean_visual_manifest,
            a.source_identity,
            a.design_lock_evidence,
            a.clean_visual_evidence,
            a.approved_evidence_root,
        )
    if check == "audio_caption":
        return module.validate_audio_caption(a.audio_lock, a.caption_lock)
    if check == "prebuild":
        return module.validate_prebuild(
            a.build_manifest,
            allow_source_provisional=a.visual_asset_mode == "SOURCE_VIDEO_PROVISIONAL",
        )
    if check == "build_inputs":
        return module.validate_build_inputs(a.caption_lock, a.srt, a.build_contract, a.timeline)
    if check == "capcut_project":
        return module.validate_capcut_project(a.project, a.snapshot, a.build_contract, a.evidence, a.evidence_root)
    if check == "postbuild":
        return module.validate_postbuild(
            a.build_manifest, a.project, visual_asset_mode=a.visual_asset_mode
        )
    return module.validate_render(
        a.capcut_project_evidence,
        a.capcut_project_sha256,
        a.stage09_review_evidence,
        a.stage09_review_sha256,
        a.render,
        a.render_sha256,
        a.evidence,
        a.approved_evidence_root,
    )


def _emit(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else (3 if payload["status"] == "WAIT" else 1)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--state", type=Path, required=True); p.add_argument("--stage", choices=tuple(STAGE_CHECKS)); p.add_argument("--check", choices=ALL_CHECKS)
    p.add_argument("--handoff", type=Path); p.add_argument("--source-identity", type=Path); p.add_argument("--timeline", type=Path)
    p.add_argument("--clean-visual-manifest", type=Path); p.add_argument("--design-lock-evidence", type=Path)
    p.add_argument("--clean-visual-evidence", type=Path); p.add_argument("--approved-evidence-root", type=Path)
    p.add_argument("--audio-lock", type=Path); p.add_argument("--caption-lock", type=Path); p.add_argument("--srt", type=Path); p.add_argument("--build-contract", type=Path); p.add_argument("--build-manifest", type=Path)
    p.add_argument("--project", type=Path); p.add_argument("--snapshot", type=Path); p.add_argument("--evidence", type=Path); p.add_argument("--evidence-root", type=Path)
    p.add_argument("--capcut-project-evidence", type=Path); p.add_argument("--capcut-project-sha256")
    p.add_argument("--stage09-review-evidence", type=Path); p.add_argument("--stage09-review-sha256")
    p.add_argument("--render", type=Path); p.add_argument("--render-sha256")
    p.add_argument(
        "--visual-asset-mode",
        choices=("CLEAN_VISUAL_READY", "SOURCE_VIDEO_PROVISIONAL"),
    )
    a = p.parse_args(); state_path = a.state.resolve()
    try:
        state = read_json(state_path); stage = resolve_stage(state)
    except (OSError, ValueError, TypeError) as exc:
        return _emit({"status": "FAIL", "errors": [{"code": "STATE_INVALID", "detail": str(exc)}], "evidence": {}, "stage_complete": False})
    a.visual_asset_mode = a.visual_asset_mode or state.get(
        "visual_asset_mode", "CLEAN_VISUAL_READY"
    )
    if a.stage is not None and a.stage != stage:
        return _emit({"status": "FAIL", "errors": [{"code": "CALLER_STAGE_MISMATCH", "canonical_stage": stage, "caller_stage": a.stage}], "evidence": {}, "stage_complete": False})
    try:
        expected = expected_entry_status(stage, state)
    except ValueError as exc:
        return _emit({"status": "FAIL", "errors": [{"code": "STATE_APPROVAL_MODE_INVALID", "detail": str(exc)}], "evidence": {}, "stage": stage, "stage_complete": False})
    if state.get("status") != expected:
        return _emit({"status": "FAIL", "errors": [{"code": "STATE_STATUS_MISMATCH", "stage": stage, "expected": expected, "actual": state.get("status")}], "evidence": {}, "stage": stage, "stage_complete": False})
    for receipt in prerequisites_for_stage(stage, state):
        if failure := _receipt_error(state, state_path, receipt):
            status, error = failure
            return _emit({"status": status, "errors": [error], "evidence": {}, "stage": stage, "stage_complete": False})
    if stage == "05" and (failure := _external_review_mode_error(state, state_path)):
        status, error = failure
        return _emit({"status": status, "errors": [error], "evidence": {}, "stage": stage, "stage_complete": False})
    required = STAGE_CHECKS[stage]; selected = (a.check,) if a.check else required
    if any(check not in required for check in selected):
        return _emit({"status": "FAIL", "errors": [{"code": "CHECK_STAGE_MISMATCH", "stage": stage, "check": selected[0]}], "evidence": {}, "stage": stage, "stage_complete": False})
    if stage == "08" and a.check is None and selected == required:
        # Stage 08 checks share immutable inputs and write to separate outputs.
        # Submit together, then collect in workflow order for deterministic JSON.
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {check: executor.submit(_run, check, a) for check in selected}
            results = {check: futures[check].result() for check in selected}
    else:
        results = {check: _run(check, a) for check in selected}
    failed = [c for c, result in results.items() if result.get("status") != "PASS"]
    completed = [c for c, result in results.items() if result.get("status") == "PASS"]
    missing = [c for c in required if c not in completed]
    if failed:
        status = "FAIL"
        errors = [
            {**error, "check": c}
            for c in failed
            for error in results[c].get("errors", [{"code": "STAGE_CHECK_FAILED"}])
        ]
    elif missing:
        status, errors = "WAIT", [{"code": "STAGE_CHECKS_INCOMPLETE", "required": list(required), "completed": completed}]
    else:
        status, errors = "PASS", []
    return _emit({"status": status, "errors": errors, "evidence": {"check_results": results}, "stage": stage, "check": a.check or "all", "required_checks": list(required), "completed_checks": completed, "missing_checks": missing, "stage_complete": status == "PASS"})


if __name__ == "__main__":
    raise SystemExit(main())
