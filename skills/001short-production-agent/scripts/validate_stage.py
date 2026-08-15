from __future__ import annotations

import argparse
import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from common import read_json, resolve_state_artifact, sha256_file, write_json
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
        names = [Path(v).stem.removeprefix("validate_") for v in validators]
        if route.get("protocol_validator"):
            names.append("production_plan")
        checks[stage] = tuple(names)
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
ALL_STAGES = tuple(row["id"] for row in read_json(PROTOCOL)["stages"])
AUTHORING_STAGE_ENTRY_STATUS = {
    row["id"]: row["requires_state"]
    for row in read_json(PROTOCOL)["stages"]
    if row["id"] in {"03", "04"}
}
RECEIPTS = {
    "design_lock": ("design_lock_evidence_path", "design_lock_evidence_sha256", "design_lock_evidence.schema.json"),
    "clean_visual": ("clean_visual_receipt_path", "clean_visual_receipt_sha256", "clean_visual_receipt.schema.json"),
    "audio_lock": ("audio_lock_path", "audio_lock_sha256", "audio_lock.schema.json"),
    "caption_lock": ("caption_lock_path", "caption_lock_sha256", "caption_lock.schema.json"),
    "build_inputs": ("build_inputs_receipt_path", "build_inputs_receipt_sha256", None),
    "capcut_project": ("capcut_project_evidence_path", "capcut_project_evidence_sha256", "capcut_project_evidence.schema.json"),
}
PREREQUISITES = {
    "02": (),
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
    return resolve_state_artifact(state_path, raw)


def _stage02_lock_errors(state: dict, state_path: Path) -> list[dict]:
    errors = []
    for name, relative in (
        ("original_blueprint", "20_script/original-blueprint.md"),
        ("original_capcut_grid", "20_script/original-capcut-grid.md"),
    ):
        raw = state.get(f"{name}_path")
        expected_sha = state.get(f"{name}_sha256")
        if not isinstance(raw, str) or not raw or not isinstance(expected_sha, str):
            errors.append({"code": "STAGE02_LOCK_MISSING", "artifact": name})
            continue
        expected_path = _state_declared_path(state_path, relative)
        try:
            actual_path = _state_declared_path(state_path, raw)
        except ValueError:
            actual_path = None
        if actual_path != expected_path:
            errors.append({"code": "STAGE02_LOCK_PATH_MISMATCH", "artifact": name})
        elif not actual_path.is_file() or sha256_file(actual_path).lower() != expected_sha.lower():
            errors.append({"code": "STAGE02_LOCK_SHA_MISMATCH", "artifact": name})
    return errors


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
    if check == "original_blueprint":
        from validate_original_blueprint import validate_original_blueprint
        path = _state_declared_path(a.state.resolve(), "20_script/original-blueprint.md")
        return validate_original_blueprint(path)
    if check == "capcut_grids":
        from validate_capcut_grids import validate_grid
        path = _state_declared_path(a.state.resolve(), "20_script/original-capcut-grid.md")
        grid, errors = validate_grid(path, "original")
        return {
            "status": "FAIL" if errors else "PASS",
            "errors": errors,
            "evidence": {
                "path": str(path),
                "sha256": sha256_file(path) if path.is_file() else "",
                "beat_ids": [header.split()[0] for header in grid.headers] if grid else [],
            },
        }
    if check == "production_plan":
        from validate_executable_protocol import load_protocol, validate_production_plan
        if a.production_plan is None:
            return {"status": "FAIL", "errors": [{"code": "PRODUCTION_PLAN_REQUIRED"}], "evidence": {}}
        state = read_json(a.state)
        plan_path = _state_declared_path(a.state.resolve(), str(a.production_plan))
        try:
            plan = read_json(plan_path)
            errors = validate_production_plan(plan, load_protocol())
            if plan.get("episode_id") != state.get("episode_id"):
                errors.append("PRODUCTION_PLAN_EPISODE_MISMATCH")
        except (OSError, TypeError, ValueError) as exc:
            errors = [f"PRODUCTION_PLAN_READ:{exc}"]
        return {
            "status": "FAIL" if errors else "PASS",
            "errors": [{"code": error} for error in errors],
            "evidence": {
                "episode_id": state.get("episode_id"),
                "production_plan_path": str(plan_path),
                "production_plan_sha256": sha256_file(plan_path) if plan_path.is_file() else "",
            },
        }
    module = importlib.import_module("validate_" + check)
    if check == "design_lock":
        return module.validate_handoff(a.handoff, a.source_identity, a.timeline, a.design_lock_evidence)
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


def _advance_state(state_path: Path, state: dict, stage: str, args, results: dict) -> dict:
    transition = STAGE_TRANSITIONS[stage]
    if transition["next_stage"] is None:
        raise ValueError("STAGE_HAS_NO_NEXT_STAGE")
    advanced = dict(state)
    advanced["current_stage"] = transition["next_stage"]
    advanced["status"] = transition["pass_state"]
    if stage == "02":
        validation = results.get("original_blueprint", {})
        evidence = validation.get("evidence", {})
        grid_validation = results.get("capcut_grids", {})
        grid_evidence = grid_validation.get("evidence", {})
        blueprint = _state_declared_path(state_path, "20_script/original-blueprint.md")
        original_grid = _state_declared_path(state_path, "20_script/original-capcut-grid.md")
        if (
            validation.get("status") != "PASS"
            or evidence.get("path") != str(blueprint)
            or evidence.get("sha256") != sha256_file(blueprint)
            or grid_validation.get("status") != "PASS"
            or grid_evidence.get("path") != str(original_grid)
            or grid_evidence.get("sha256") != sha256_file(original_grid)
        ):
            raise ValueError("STAGE02_ORIGINAL_ARTIFACT_BINDING_INVALID")
        advanced["original_blueprint_path"] = str(blueprint)
        advanced["original_blueprint_sha256"] = evidence["sha256"]
        advanced["original_capcut_grid_path"] = str(original_grid)
        advanced["original_capcut_grid_sha256"] = grid_evidence["sha256"]
    elif stage == "05":
        if args.design_lock_evidence is None or args.production_plan is None or args.production_plan_receipt is None:
            raise ValueError("STAGE05_BINDING_ARGUMENT_REQUIRED")
        design = resolve_state_artifact(state_path, str(args.design_lock_evidence))
        plan = resolve_state_artifact(state_path, str(args.production_plan))
        receipt = resolve_state_artifact(state_path, str(args.production_plan_receipt))
        if not design.is_file() or not plan.is_file():
            raise ValueError("STAGE05_BINDING_ARTIFACT_MISSING")
        write_json(receipt, results["production_plan"])
        for name, path in (
            ("design_lock_evidence", design),
            ("production_plan", plan),
            ("production_plan_validation_receipt", receipt),
        ):
            advanced[f"{name}_path"] = str(path)
            advanced[f"{name}_sha256"] = sha256_file(path)
    elif stage == "07":
        for name, path in (("audio_lock", args.audio_lock), ("caption_lock", args.caption_lock)):
            resolved = resolve_state_artifact(state_path, str(path))
            advanced[f"{name}_path"] = str(resolved)
            advanced[f"{name}_sha256"] = sha256_file(resolved)
    write_json(state_path, advanced)
    return advanced


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--state", type=Path, required=True); p.add_argument("--stage", choices=ALL_STAGES); p.add_argument("--check", choices=ALL_CHECKS)
    p.add_argument("--handoff", type=Path); p.add_argument("--source-identity", type=Path); p.add_argument("--timeline", type=Path)
    p.add_argument("--production-plan", type=Path); p.add_argument("--production-plan-receipt", type=Path)
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
        for field in ("episode_id", "current_stage", "status"):
            if not isinstance(state.get(field), str) or not state[field]:
                raise ValueError(f"STATE_REQUIRED_FIELD_MISSING:{field}")
        raw_stage = str(state.get("current_stage", state.get("stage", ""))).strip()
        declared_stage = raw_stage.zfill(2) if raw_stage.isdigit() else raw_stage[:2]
        if declared_stage in {"08", "09"}:
            snapshot_argument = a.snapshot or state.get("structure_snapshot_path")
            if snapshot_argument is None and declared_stage == "09":
                snapshot_argument = "50_capcut_project/structure_snapshot.json"
            if snapshot_argument is not None:
                try:
                    snapshot_payload = read_json(
                        _state_declared_path(state_path, str(snapshot_argument))
                    )
                except (OSError, TypeError, ValueError):
                    snapshot_payload = {}
                if snapshot_payload.get("schema_version") == "001short-structure-snapshot-v1":
                    return _emit({"status": "FAIL", "errors": [{"code": "STRUCTURE_SNAPSHOT_MIGRATION_REQUIRED"}], "evidence": {}, "stage": declared_stage, "stage_complete": False})
        if declared_stage in AUTHORING_STAGE_ENTRY_STATUS:
            if a.stage is not None and a.stage != declared_stage:
                return _emit({"status": "FAIL", "errors": [{"code": "CALLER_STAGE_MISMATCH", "canonical_stage": declared_stage, "caller_stage": a.stage}], "evidence": {}, "stage_complete": False})
            expected = AUTHORING_STAGE_ENTRY_STATUS[declared_stage]
            if not _entry_state_matches(state, expected):
                return _emit({"status": "FAIL", "errors": [{"code": "STATE_STATUS_MISMATCH", "stage": declared_stage, "expected": expected, "actual": state.get("status")}], "evidence": {}, "stage": declared_stage, "stage_complete": False})
            lock_errors = _stage02_lock_errors(state, state_path)
            if lock_errors:
                return _emit({"status": "FAIL", "errors": lock_errors, "evidence": {}, "stage": declared_stage, "check": "stage02_input_locks", "stage_complete": False})
            if a.advance:
                return _emit({"status": "FAIL", "errors": [{"code": "AUTHORING_STAGE_ADVANCE_UNSUPPORTED"}], "evidence": {}, "stage": declared_stage, "check": "stage02_input_locks", "stage_complete": False})
            return _emit({"status": "PASS", "errors": [], "evidence": {"stage02_input_locks": "PASS"}, "stage": declared_stage, "check": "stage02_input_locks", "stage_complete": False})
        if declared_stage == "09":
            if a.stage is not None and a.stage != declared_stage:
                return _emit({"status": "FAIL", "errors": [{"code": "CALLER_STAGE_MISMATCH", "canonical_stage": declared_stage, "caller_stage": a.stage}], "evidence": {}, "stage_complete": False})
            return _emit({"status": "WAIT", "errors": [{"code": "MANUAL_FINALIZATION_REQUIRED"}], "evidence": {}, "stage": declared_stage, "next_action": "WAIT_USER_CAPCUT_CHECK", "stage_complete": False})
        stage = resolve_stage(state)
    except (OSError, ValueError, TypeError) as exc:
        return _emit({"status": "FAIL", "errors": [{"code": "STATE_INVALID", "detail": str(exc)}], "evidence": {}, "stage_complete": False})
    if a.stage is not None and a.stage != stage:
        return _emit({"status": "FAIL", "errors": [{"code": "CALLER_STAGE_MISMATCH", "canonical_stage": stage, "caller_stage": a.stage}], "evidence": {}, "stage_complete": False})
    if a.advance and stage == "05" and a.production_plan is not None:
        try:
            plan = read_json(_state_declared_path(state_path, str(a.production_plan)))
        except (OSError, TypeError, ValueError) as exc:
            return _emit({"status": "FAIL", "errors": [{"code": "PRODUCTION_PLAN_READ", "detail": str(exc)}], "evidence": {}, "stage": stage, "stage_complete": False})
        if plan.get("schema_version") != "001short-production-plan-v2":
            return _emit({"status": "FAIL", "errors": [{"code": "PRODUCTION_PLAN_MIGRATION_REQUIRED"}], "evidence": {}, "stage": stage, "stage_complete": False})
    if a.advance and stage == "07":
        migration_errors = []
        caption_payload = None
        for path, expected, code in (
            (a.audio_lock, "001short-audio-lock-v4", "AUDIO_LOCK_MIGRATION_REQUIRED"),
            (a.caption_lock, "001short-caption-lock-v2", "CAPTION_LOCK_MIGRATION_REQUIRED"),
        ):
            try:
                payload = read_json(resolve_state_artifact(state_path, str(path)))
            except (OSError, TypeError, ValueError):
                continue
            if payload.get("schema_version") != expected:
                migration_errors.append({"code": code})
            if expected == "001short-caption-lock-v2":
                caption_payload = payload
        if caption_payload is not None and caption_payload.get("schema_version") == "001short-caption-lock-v2":
            try:
                timing = read_json(resolve_state_artifact(state_path, str(caption_payload.get("caption_timing_evidence_path"))))
            except (OSError, TypeError, ValueError):
                timing = {}
            if timing.get("schema_version") != "001short-caption-timing-evidence-v2":
                migration_errors.append({"code": "CAPTION_TIMING_EVIDENCE_MIGRATION_REQUIRED"})
        if migration_errors:
            return _emit({"status": "FAIL", "errors": migration_errors, "evidence": {}, "stage": stage, "stage_complete": False})
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
    if stage == "02" and all(
        results.get(check, {}).get("status") == "PASS"
        for check in ("original_blueprint", "capcut_grids")
    ):
        blueprint_ids = sorted(set(results["original_blueprint"]["evidence"].get("beat_ids", [])))
        grid_ids = sorted(set(results["capcut_grids"]["evidence"].get("beat_ids", [])))
        if blueprint_ids != grid_ids:
            results["capcut_grids"] = {
                **results["capcut_grids"],
                "status": "FAIL",
                "errors": [{
                    "code": "ORIGINAL_BEAT_GRID_BXX_MISMATCH",
                    "blueprint_beat_ids": blueprint_ids,
                    "grid_beat_ids": grid_ids,
                }],
            }
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
            advanced = _advance_state(state_path, state, stage, a, results)
        except (OSError, TypeError, ValueError) as exc:
            return _emit({"status": "FAIL", "errors": [{"code": "STATE_ADVANCE_FAILED", "detail": str(exc)}], "evidence": evidence, "stage": stage, "stage_complete": False})
        evidence["state_transition"] = {"from_stage": stage, "to_stage": advanced["current_stage"], "status": advanced["status"], "state_path": str(state_path)}
    return _emit({"status": status, "errors": errors, "evidence": evidence, "stage": stage, "check": a.check or "all", "required_checks": list(required), "completed_checks": completed, "missing_checks": missing, "stage_complete": status == "PASS"})


if __name__ == "__main__":
    raise SystemExit(main())
