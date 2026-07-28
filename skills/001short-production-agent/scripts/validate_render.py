from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from capcut_io import iter_timeline_json
from clone_and_sync import hash_project_core, template_fingerprint_sha256
from common import (
    inspect_write_target,
    manifest_sha256,
    read_json,
    result,
    sha256_file,
    write_json,
)
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_EVIDENCE_SCHEMA = SKILL_ROOT / "schemas" / "capcut_project_evidence.schema.json"
STAGE09_REVIEW_EVIDENCE_SCHEMA = (
    SKILL_ROOT / "schemas" / "stage09_review_evidence.schema.json"
)
RENDER_EVIDENCE_SCHEMA = SKILL_ROOT / "schemas" / "render_evidence.schema.json"
STAGE09_EVENT_ORDER = [
    "USER_VISUAL_CHECKED",
    "CAPCUT_POST_OPEN_REVALIDATED",
    "USER_APPROVED",
]


def _event_sha(event: dict) -> str:
    encoded = json.dumps(
        event, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_stage09_review(
    review: dict,
    project_evidence: dict,
    project_evidence_path: Path,
    project_evidence_sha256: str,
) -> list[dict]:
    errors: list[dict] = []
    episode_id = project_evidence["episode_id"]
    if review["episode_id"] != episode_id:
        errors.append({"code": "STAGE09_EPISODE_MISMATCH"})
    if (
        Path(review["capcut_project_evidence_path"]).resolve()
        != project_evidence_path
        or review["capcut_project_evidence_sha256"].lower()
        != project_evidence_sha256.lower()
    ):
        errors.append({"code": "STAGE09_CAPCUT_EVIDENCE_MISMATCH"})

    events = review["events"]
    if [event["status"] for event in events] != STAGE09_EVENT_ORDER:
        errors.append({"code": "STAGE09_EVENT_ORDER_INVALID"})
    if any(event["episode_id"] != episode_id for event in events):
        errors.append({"code": "STAGE09_EPISODE_MISMATCH"})
    if any(
        event["capcut_project_evidence_sha256"].lower()
        != project_evidence_sha256.lower()
        for event in events
    ):
        errors.append({"code": "STAGE09_CAPCUT_EVIDENCE_MISMATCH"})

    expected_previous_sha = project_evidence_sha256.lower()
    for event in events:
        if event["previous_event_sha256"].lower() != expected_previous_sha:
            errors.append({"code": "STAGE09_EVENT_CHAIN_INVALID"})
            break
        expected_previous_sha = _event_sha(event)
    return errors


def _probe_video(path: Path) -> tuple[bool, int | None]:
    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_type:format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return False, None
        payload = json.loads(completed.stdout)
        has_video = any(
            isinstance(stream, dict) and stream.get("codec_type") == "video"
            for stream in payload.get("streams", [])
        )
        duration_us = round(float(payload["format"]["duration"]) * 1_000_000)
        return has_video and duration_us > 0, duration_us
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False, None


def _revalidate_project(evidence: dict) -> list[dict]:
    errors: list[dict] = []
    project = Path(evidence["actual_project_path"]).resolve()
    if not project.is_dir():
        return [{"code": "CAPCUT_PROJECT_MISSING"}]
    for relative, expected_sha in evidence["validated_files"].items():
        path = (project / relative).resolve()
        try:
            path.relative_to(project)
        except ValueError:
            errors.append({"code": "CAPCUT_PROJECT_FILE_CHANGED", "path": relative})
            continue
        if not path.is_file() or sha256_file(path).lower() != str(expected_sha).lower():
            errors.append({"code": "CAPCUT_PROJECT_FILE_CHANGED", "path": relative})
    observed_timelines = sorted(
        path.relative_to(project).as_posix() for path, _ in iter_timeline_json(project)
    )
    if observed_timelines != sorted(evidence["timeline_json_files"]):
        errors.append({"code": "CAPCUT_PROJECT_TIMELINE_SET_CHANGED"})
    for path_key, sha_key in (
        ("build_contract_path", "build_contract_sha256"),
        ("structure_snapshot_path", "structure_snapshot_sha256"),
        ("design_lock_evidence_path", "design_lock_evidence_sha256"),
    ):
        path = Path(evidence[path_key]).resolve()
        if not path.is_file() or sha256_file(path).lower() != str(evidence[sha_key]).lower():
            errors.append({"code": "SUPPORTING_FILE_CHANGED", "path": path_key})
    source = Path(evidence["source_project_path"]).resolve()
    try:
        source_core = hash_project_core(source)
    except (OSError, ValueError):
        source_core = {}
    try:
        template_sha256 = template_fingerprint_sha256(source)
    except OSError:
        template_sha256 = None
    if (
        source_core != evidence["source_core_sha256"]
        or manifest_sha256(source_core) != evidence["source_root_sha256"]
        or template_sha256 != evidence["template_sha256"]
    ):
        errors.append({"code": "SOURCE_AUTHORITY_CHANGED"})
    return errors


def validate_render(
    capcut_project_evidence_path: Path,
    expected_capcut_project_sha256: str,
    stage09_review_evidence_path: Path,
    expected_stage09_review_sha256: str,
    render_path: Path,
    expected_render_sha256: str,
    evidence_path: Path | None = None,
    approved_evidence_root_path: Path | None = None,
) -> dict:
    project_evidence_path = Path(capcut_project_evidence_path).resolve()
    review_evidence_path = Path(stage09_review_evidence_path).resolve()
    render_path = Path(render_path).resolve()
    if not project_evidence_path.is_file():
        return result([{"code": "CAPCUT_PROJECT_EVIDENCE_MISSING"}])
    actual_project_sha = sha256_file(project_evidence_path)
    if actual_project_sha.lower() != str(expected_capcut_project_sha256).lower():
        return result([{"code": "CAPCUT_PROJECT_EVIDENCE_SHA_MISMATCH"}])
    try:
        project_evidence = read_json(project_evidence_path)
        schema_errors = validate_schema(project_evidence, read_json(PROJECT_EVIDENCE_SCHEMA))
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "CAPCUT_PROJECT_EVIDENCE_SCHEMA", "detail": str(exc)}])
    if schema_errors:
        return result([{"code": "CAPCUT_PROJECT_EVIDENCE_SCHEMA", "detail": schema_errors}])

    if not review_evidence_path.is_file():
        return result([{"code": "STAGE09_REVIEW_EVIDENCE_MISSING"}])
    actual_review_sha = sha256_file(review_evidence_path)
    if actual_review_sha.lower() != str(expected_stage09_review_sha256).lower():
        return result([{"code": "STAGE09_REVIEW_EVIDENCE_SHA_MISMATCH"}])
    try:
        review_evidence = read_json(review_evidence_path)
        review_schema_errors = validate_schema(
            review_evidence, read_json(STAGE09_REVIEW_EVIDENCE_SCHEMA)
        )
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "STAGE09_REVIEW_EVIDENCE_SCHEMA", "detail": str(exc)}])
    if review_schema_errors:
        return result(
            [{"code": "STAGE09_REVIEW_EVIDENCE_SCHEMA", "detail": review_schema_errors}]
        )
    review_errors = _validate_stage09_review(
        review_evidence,
        project_evidence,
        project_evidence_path,
        actual_project_sha,
    )
    if review_errors:
        return result(review_errors)

    evidence_target: Path | None = None
    if evidence_path is not None:
        if approved_evidence_root_path is None:
            return result([{"code": "EVIDENCE_ROOT_REQUIRED"}])
        approved_evidence_root = Path(approved_evidence_root_path).absolute()
        evidence_target = Path(evidence_path).absolute()
        guard = inspect_write_target(
            approved_evidence_root, evidence_target, require_new=True
        )
        if guard == "PATH_EXISTS":
            return result([{"code": "EVIDENCE_PATH_EXISTS"}])
        if guard is not None:
            return result([{"code": "EVIDENCE_PATH_UNSAFE"}])

    errors = _revalidate_project(project_evidence)
    if not render_path.is_file() or render_path.stat().st_size <= 0:
        errors.append({"code": "RENDER_FILE_INVALID"})
        actual_render_sha = ""
        duration_us = None
    else:
        actual_render_sha = sha256_file(render_path)
        if actual_render_sha.lower() != str(expected_render_sha256).lower():
            errors.append({"code": "RENDER_SHA_MISMATCH"})
        decoded, duration_us = _probe_video(render_path)
        if not decoded:
            errors.append({"code": "RENDER_VIDEO_STREAM_INVALID"})
    if errors:
        return result(errors)
    evidence = {
        "schema_version": "001short-render-evidence-v2",
        "status": "PASS",
        "episode_id": project_evidence["episode_id"],
        "capcut_project_evidence_path": str(project_evidence_path),
        "capcut_project_evidence_sha256": actual_project_sha,
        "stage09_review_evidence_path": str(review_evidence_path),
        "stage09_review_evidence_sha256": actual_review_sha,
        "stage09_events": STAGE09_EVENT_ORDER,
        "post_open_project_revalidated": True,
        "render_path": str(render_path),
        "render_sha256": actual_render_sha,
        "measured_duration_us": duration_us,
        "video_stream_verified": True,
        "decode_verified": True,
    }
    schema_errors = validate_schema(evidence, read_json(RENDER_EVIDENCE_SCHEMA))
    if schema_errors:
        return result([{"code": "RENDER_EVIDENCE_SCHEMA", "detail": schema_errors}])
    if evidence_target is not None:
        write_json(evidence_target, evidence)
        evidence["render_evidence_path"] = str(evidence_target)
        evidence["render_evidence_sha256"] = sha256_file(evidence_target)
    return result([], evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capcut-project-evidence", type=Path, required=True)
    parser.add_argument("--capcut-project-sha256", required=True)
    parser.add_argument("--stage09-review-evidence", type=Path, required=True)
    parser.add_argument("--stage09-review-sha256", required=True)
    parser.add_argument("--render", type=Path, required=True)
    parser.add_argument("--render-sha256", required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--approved-evidence-root", type=Path)
    args = parser.parse_args()
    payload = validate_render(
        args.capcut_project_evidence,
        args.capcut_project_sha256,
        args.stage09_review_evidence,
        args.stage09_review_sha256,
        args.render,
        args.render_sha256,
        args.evidence,
        args.approved_evidence_root,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
