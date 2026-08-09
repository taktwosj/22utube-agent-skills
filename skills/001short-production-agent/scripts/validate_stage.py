from __future__ import annotations

import argparse
import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import read_json, sha256_file, write_json
from schema_runtime import validate_schema

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflow.json"
PROTOCOL = ROOT / "protocol.json"
SCHEMAS = ROOT / "schemas"


def _contracts():
    flow = read_json(WORKFLOW)
    protocol = read_json(PROTOCOL)
    checks = {}
    for stage, route in flow["validation"]["checks"].items():
        if route.get("manual_only") is True:
            continue
        validators = route.get("validators") or [route["validator"]]
        checks[stage] = tuple(Path(v).stem.removeprefix("validate_") for v in validators)
    stages = {row["id"]: row for row in protocol["stages"]}
    entry = {stage: stages[stage]["requires_state"] for stage in checks}
    ordered = [row["id"] for row in protocol["stages"]]
    transitions = {
        stage: {
            "pass_state": stages[stage]["pass_state"],
            "next_stage": ordered[ordered.index(stage) + 1]
            if ordered.index(stage) + 1 < len(ordered) else None,
        }
        for stage in checks
    }
    return checks, entry, transitions


STAGE_CHECKS, STAGE_ENTRY_STATUS, STAGE_TRANSITIONS = _contracts()
ALL_CHECKS = tuple(dict.fromkeys(c for values in STAGE_CHECKS.values() for c in values))
RECEIPTS = {
    "design_lock": ("design_lock_evidence_path", "design_lock_evidence_sha256", "design_lock_evidence.schema.json"),
    "clean_visual": ("clean_visual_receipt_path", "clean_visual_receipt_sha256", "clean_visual_receipt.schema.json"),
    "audio_lock": ("audio_lock_path", "audio_lock_sha256", "audio_lock.schema.json"),
    "caption_lock": ("caption_lock_path", "caption_lock_sha256", "caption_lock.schema.json"),
    "build_inputs": ("build_inputs_receipt_path", "build_inputs_receipt_sha256", None),
    "capcut_project": ("capcut_project_evidence_path", "capcut_project_evidence_sha256", "capcut_project_evidence.schema.json"),
}
PREREQUISITES = {
    "05": (),
    "06": ("design_lock",),
    "07": ("design_lock",),
    "08": ("design_lock", "audio_lock", "caption_lock"),
    "09": ("design_lock", "audio_lock", "caption_lock", "build_inputs", "capcut_project"),
}


def resolve_stage(state: dict) -> str:
    raw = str(state.get("current_stage", state.get("stage", ""))).strip()
    stage = raw.zfill(2) if raw.isdigit() else raw[:2]
    if stage not in STAGE_CHECKS:
        raise ValueError(f"STAGE_NOT_VALIDATABLE:{raw}")
    return stage


def _entry_state_matches(state: dict, requirement: str) -> bool:
    suffix = "_WITH_ACCEPTED_VISUAL_MODE"
    if requirement.endswith(suffix):
        return (
            state.get("status") == requirement.removesuffix(suffix)
            and state.get("visual_asset_mode")
            in {
                "CLEAN_VISUAL_READY", "SOURCE_VIDEO_PROVISIONAL",
                "USER_APPROVED_NONMATCHING_CLEAN_SOURCE",
            }
        )
    return state.get("status") in requirement.split("_OR_")


def _canonical_state_path(path: Path) -> bool:
    return path.name == "state.json" and path.parent.name == "90_workflow"


def _state_declared_path(state_path: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return state_path.parent.parent / path


def _receipt_error(state, state_path, name):
    path_key, sha_key, schema = RECEIPTS[name]
    raw, expected = state.get(path_key), state.get(sha_key)
    if not isinstance(raw, str) or not raw or not isinstance(expected, str):
        return "WAIT", {"code": "PREREQUISITE_EVIDENCE_MISSING", "receipt": name}
    path = _state_declared_path(state_path, raw)
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
        return module.validate_prebuild(a.build_manifest)
    if check == "build_inputs":
        return module.validate_build_inputs(a.caption_lock, a.srt, a.build_contract, a.timeline)
    if check == "capcut_project":
        return module.validate_capcut_project(a.project, a.snapshot, a.build_contract, a.evidence, a.evidence_root)
    if check == "postbuild":
        return module.validate_postbuild(a.build_manifest, a.project)
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


def _advance_state(state_path: Path, state: dict, stage: str, args) -> dict:
    transition = STAGE_TRANSITIONS[stage]
    if transition["next_stage"] is None:
        raise ValueError("STAGE_HAS_NO_NEXT_STAGE")
    advanced = dict(state)
    advanced["current_stage"] = transition["next_stage"]
    advanced["status"] = transition["pass_state"]
    if stage == "07":
        for name, path in (("audio_lock", args.audio_lock), ("caption_lock", args.caption_lock)):
            resolved = Path(path).resolve()
            advanced[f"{name}_path"] = str(resolved)
            advanced[f"{name}_sha256"] = sha256_file(resolved)
    write_json(state_path, advanced)
    return advanced


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
    p.add_argument("--advance", action="store_true")
    a = p.parse_args(); state_path = a.state.resolve()
    try:
        if not _canonical_state_path(state_path):
            raise ValueError("CANONICAL_STATE_PATH_REQUIRED")
        state = read_json(state_path)
        raw_stage = str(state.get("current_stage", state.get("stage", ""))).strip()
        declared_stage = raw_stage.zfill(2) if raw_stage.isdigit() else raw_stage[:2]
        if declared_stage == "09":
            if a.stage is not None and a.stage != declared_stage:
                return _emit({"status": "FAIL", "errors": [{"code": "CALLER_STAGE_MISMATCH", "canonical_stage": declared_stage, "caller_stage": a.stage}], "evidence": {}, "stage_complete": False})
            return _emit({"status": "WAIT", "errors": [{"code": "MANUAL_FINALIZATION_REQUIRED"}], "evidence": {}, "stage": declared_stage, "next_action": "WAIT_USER_CAPCUT_CHECK", "stage_complete": False})
        stage = resolve_stage(state)
    except (OSError, ValueError, TypeError) as exc:
        return _emit({"status": "FAIL", "errors": [{"code": "STATE_INVALID", "detail": str(exc)}], "evidence": {}, "stage_complete": False})
    if a.stage is not None and a.stage != stage:
        return _emit({"status": "FAIL", "errors": [{"code": "CALLER_STAGE_MISMATCH", "canonical_stage": stage, "caller_stage": a.stage}], "evidence": {}, "stage_complete": False})
    expected = STAGE_ENTRY_STATUS[stage]
    if not _entry_state_matches(state, expected):
        return _emit({"status": "FAIL", "errors": [{"code": "STATE_STATUS_MISMATCH", "stage": stage, "expected": expected, "actual": state.get("status")}], "evidence": {}, "stage": stage, "stage_complete": False})
    for receipt in PREREQUISITES[stage]:
        if failure := _receipt_error(state, state_path, receipt):
            status, error = failure
            return _emit({"status": status, "errors": [error], "evidence": {}, "stage": stage, "stage_complete": False})
    if stage in {"08", "09"}:
        if a.audio_lock is None and isinstance(state.get("audio_lock_path"), str):
            a.audio_lock = _state_declared_path(state_path, state["audio_lock_path"])
        if a.caption_lock is None and isinstance(state.get("caption_lock_path"), str):
            a.caption_lock = _state_declared_path(state_path, state["caption_lock_path"])
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
    evidence = {"check_results": results}
    if a.advance:
        if status != "PASS" or a.check is not None:
            return _emit({"status": "FAIL", "errors": [{"code": "ADVANCE_REQUIRES_COMPLETE_STAGE_PASS"}], "evidence": evidence, "stage": stage, "stage_complete": False})
        try:
            advanced = _advance_state(state_path, state, stage, a)
        except (OSError, TypeError, ValueError) as exc:
            return _emit({"status": "FAIL", "errors": [{"code": "STATE_ADVANCE_FAILED", "detail": str(exc)}], "evidence": evidence, "stage": stage, "stage_complete": False})
        evidence["state_transition"] = {"from_stage": stage, "to_stage": advanced["current_stage"], "status": advanced["status"], "state_path": str(state_path)}
    return _emit({"status": status, "errors": errors, "evidence": evidence, "stage": stage, "check": a.check or "all", "required_checks": list(required), "completed_checks": completed, "missing_checks": missing, "stage_complete": status == "PASS"})


if __name__ == "__main__":
    raise SystemExit(main())
