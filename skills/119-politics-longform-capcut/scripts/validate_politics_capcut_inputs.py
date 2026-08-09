#!/usr/bin/env python3
"""Fail-closed preflight for a politics-longform CapCut Stage 2 assembly.

This check only reads the episode and writes one report.  It deliberately
does not create a CapCut project, copy media, or normalize a draft input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = (
    "20_script/design_blueprint_approved.json",
    "20_script/design_blueprint_approved.md",
    "10_analysis/timeline_design_approved.json",
    "90_reports/external_review_gate.json",
    "10_analysis/speech_boundary_lock.json",
    "10_analysis/roughcut_edl_locked.json",
    "10_analysis/source_labels_locked.json",
    "20_locked_clips/locked_clips_manifest.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"INVALID_JSON:{path.as_posix()}:{error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.as_posix()}")
    return value


def status_of(value: dict[str, Any]) -> str:
    for key in ("status", "gate_status", "verdict"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return "STATUS_MISSING"


def check_file(episode: Path, relative: str) -> dict[str, Any]:
    path = episode / relative
    result: dict[str, Any] = {"path": relative, "exists": path.is_file()}
    if not path.is_file():
        result.update({"status": "MISSING", "sha256": None})
        return result
    result["sha256"] = sha256(path)
    if path.suffix.lower() != ".json":
        result["status"] = "PRESENT"
        return result
    try:
        document = load_json(path)
    except RuntimeError as error:
        result.update({"status": "INVALID", "error": str(error)})
        return result
    result["status"] = status_of(document)
    return result


def validate_lock_shape(episode: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    speech = episode / "10_analysis/speech_boundary_lock.json"
    roughcut = episode / "10_analysis/roughcut_edl_locked.json"
    clips = episode / "20_locked_clips/locked_clips_manifest.json"
    if not (speech.is_file() and roughcut.is_file() and clips.is_file()):
        return findings
    try:
        speech_doc = load_json(speech)
        roughcut_doc = load_json(roughcut)
        clips_doc = load_json(clips)
    except RuntimeError as error:
        return [{"name": "lock_shape", "status": "FAIL", "reason": str(error)}]
    rows = speech_doc.get("clips")
    if not isinstance(rows, list) or not rows:
        findings.append({"name": "speech_boundary_clips", "status": "FAIL", "reason": "NONEMPTY_CLIPS_REQUIRED"})
    else:
        missing = [index for index, row in enumerate(rows) if not isinstance(row, dict) or not {"clip_id", "source_id", "source_in_sec", "source_out_sec"}.issubset(row)]
        findings.append({"name": "speech_boundary_clips", "status": "PASS" if not missing else "FAIL", "missing_rows": missing})
    declared = speech_doc.get("roughcut_edl_sha256")
    actual = sha256(roughcut)
    findings.append({"name": "roughcut_sha_binding", "status": "PASS" if declared == actual else "FAIL", "declared": declared, "actual": actual})
    locked = clips_doc.get("clips") or clips_doc.get("locked_clips")
    findings.append({"name": "locked_clip_entries", "status": "PASS" if isinstance(locked, list) and locked else "FAIL"})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Stage 2 CapCut input preflight")
    parser.add_argument("--episode-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--active-writer-machine", default="unknown")
    parser.add_argument("--lock-owner", default="unknown")
    args = parser.parse_args()

    episode = args.episode_dir.resolve()
    if not episode.is_dir():
        raise RuntimeError(f"EPISODE_DIR_MISSING:{episode}")
    report_path = args.report.resolve()
    if report_path.parent != episode / "90_reports":
        raise RuntimeError("REPORT_MUST_BE_IN_EPISODE_90_REPORTS")

    files = [check_file(episode, relative) for relative in REQUIRED_FILES]
    lock_shape = validate_lock_shape(episode)
    missing_or_unapproved = [item["path"] for item in files if item["status"] != "PASS"]
    shape_failures = [item["name"] for item in lock_shape if item["status"] != "PASS"]
    owner_declared = args.active_writer_machine != "unknown" and args.lock_owner != "unknown"
    report: dict[str, Any] = {
        "schema": "politics-longform-capcut-stage2-preflight.v1",
        "episode_id": episode.name,
        "operation": "READ_ONLY_PREFLIGHT",
        "capcut_project_created": False,
        "active_writer": {
            "machine": args.active_writer_machine,
            "lock_owner": args.lock_owner,
            "status": "DECLARED" if owner_declared else "WAIT_ACTIVE_WRITER_LOCK",
        },
        "required_inputs": files,
        "lock_shape": lock_shape,
        "status": "PASS" if not missing_or_unapproved and not shape_failures and owner_declared else "WAIT_STAGE2_INPUTS",
        "blockers": [],
        "next": "Run the CapCut builder only after this report is PASS.",
    }
    if missing_or_unapproved:
        report["blockers"].append({"code": "WAIT_APPROVED_STAGE2_INPUTS", "paths": missing_or_unapproved})
    if shape_failures:
        report["blockers"].append({"code": "WAIT_LOCK_SHAPE", "checks": shape_failures})
    if not owner_declared:
        report["blockers"].append({"code": "WAIT_ACTIVE_WRITER_LOCK"})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
