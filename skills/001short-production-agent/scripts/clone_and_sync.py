from __future__ import annotations

import re
import shutil
from pathlib import Path

from capcut_io import iter_timeline_json, load_json_file
from common import (
    inspect_write_target,
    path_contains_alias,
    result,
    sha256_file,
    tree_contains_alias,
    write_json,
)


SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _conflicting_paths(source: Path, working: Path) -> bool:
    return source == working or _inside(source, working) or _inside(working, source)


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and SAFE_IDENTIFIER.fullmatch(value) is not None


def _write_targets_are_safe(root: Path, targets: list[Path]) -> bool:
    expanded = []
    for target in targets:
        expanded.extend((target, target.with_name(target.name + ".tmp")))
    return not any(inspect_write_target(root, target) for target in expanded)


def _restore_documents(
    originals: dict[Path, bytes], old_mirror_dir: Path, new_mirror_dir: Path
) -> bool:
    try:
        if old_mirror_dir != new_mirror_dir and new_mirror_dir.exists():
            if old_mirror_dir.exists():
                return False
            new_mirror_dir.rename(old_mirror_dir)
        for path, data in originals.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    except OSError:
        return False
    return True


def hash_project_core(project_path: Path) -> dict[str, str]:
    project_path = Path(project_path).resolve()
    paths = [project_path / name for name in ("draft_content.json", "draft_meta_info.json")]
    paths.extend(path for path, _ in iter_timeline_json(project_path))
    hashes: dict[str, str] = {}
    for path in sorted(set(paths)):
        if not path.is_file():
            raise FileNotFoundError(path)
        hashes[path.relative_to(project_path).as_posix()] = sha256_file(path)
    return hashes


def template_fingerprint_path(project_path: Path) -> Path:
    """Return the canonical CapCut timeline-project authority file."""
    project_path = Path(project_path).resolve()
    return project_path / "Timelines" / "project.json"


def template_fingerprint_sha256(project_path: Path) -> str:
    return sha256_file(template_fingerprint_path(project_path))


def verify_source_unchanged(source: Path, expected_hashes: dict[str, str]) -> dict:
    try:
        actual = hash_project_core(source)
    except (OSError, ValueError) as exc:
        return result([{"code": "SOURCE_SHA_CHANGED", "detail": str(exc)}])
    errors = [] if actual == expected_hashes else [{"code": "SOURCE_SHA_CHANGED"}]
    return result(errors, {"source_core_sha256": actual})


def clone_project(source: Path, working: Path) -> dict:
    raw_source = Path(source).absolute()
    raw_working = Path(working).absolute()
    if (
        path_contains_alias(raw_source)
        or path_contains_alias(raw_working)
        or (raw_source.is_dir() and tree_contains_alias(raw_source))
    ):
        return result([{"code": "SOURCE_WORKING_PATH_UNSAFE"}])
    source = raw_source.resolve()
    working = raw_working.resolve()
    if _conflicting_paths(source, working):
        return result([{"code": "SOURCE_WORKING_CONFLICT"}])
    if not source.is_dir():
        return result([{"code": "SOURCE_PROJECT_MISSING"}])
    if working.exists():
        return result([{"code": "WORKING_PROJECT_EXISTS"}])
    try:
        before = hash_project_core(source)
        shutil.copytree(source, working)
        after = hash_project_core(source)
        copied = hash_project_core(working)
    except (OSError, ValueError) as exc:
        if working.exists():
            shutil.rmtree(working)
        return result([{"code": "PROJECT_CLONE_FAILED", "detail": str(exc)}])
    if before != after:
        shutil.rmtree(working)
        return result([{"code": "SOURCE_SHA_CHANGED"}])
    if copied != before:
        shutil.rmtree(working)
        return result([{"code": "WORKING_COPY_HASH_MISMATCH"}])
    return result([], {"source_core_sha256": before, "working_core_sha256": copied})


def _observed_ids(project_path: Path) -> tuple[dict, dict, dict, str, Path, dict]:
    root = load_json_file(project_path / "draft_content.json", required=True)
    meta = load_json_file(project_path / "draft_meta_info.json", required=True)
    timeline_project = load_json_file(project_path / "Timelines" / "project.json", required=True)
    if not all(isinstance(value, dict) for value in (root, meta, timeline_project)):
        raise ValueError("required project roots must be JSON objects")
    timeline_id = root.get("main_timeline_id") or root.get("id")
    mirror_path = project_path / "Timelines" / str(timeline_id) / "draft_content.json"
    mirror = load_json_file(mirror_path, required=True)
    return root, meta, timeline_project, str(timeline_id), mirror_path, mirror


def _timeline_id_mismatch(value: object, expected: dict[str, str]) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in expected and isinstance(child, str) and child != expected[key]:
                return True
            if key == "timelines" and isinstance(child, list):
                observed = [
                    item.get("id") if isinstance(item, dict) else item
                    for item in child
                ]
                if observed != [expected["timeline_id"]]:
                    return True
            if _timeline_id_mismatch(child, expected):
                return True
    elif isinstance(value, list):
        return any(_timeline_id_mismatch(child, expected) for child in value)
    return False


def _is_full_content_timeline_mirror(payload: object) -> bool:
    """A JSON-confirmed full-content timeline mirror is a dict that carries the
    CapCut timeline identity (a top-level ``id``) together with the editable
    ``tracks``/``materials`` surface. Such mirrors must mirror the canonical
    timeline id in their bare ``id`` field, distinct from ``project.json``
    whose top-level ``id`` is the project id."""
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("id"), str)
        and isinstance(payload.get("tracks"), list)
        and isinstance(payload.get("materials"), (dict, list))
    )


def _mirror_bare_id_mismatch(payload: object, timeline_id: str) -> bool:
    if _is_full_content_timeline_mirror(payload):
        return payload["id"] != timeline_id
    return False


def _sync_mirror_bare_id(payload: object, timeline_id: str) -> int:
    if _is_full_content_timeline_mirror(payload) and payload["id"] != timeline_id:
        payload["id"] = timeline_id
        return 1
    return 0


def _sync_timeline_ids(value: object, expected: dict[str, str]) -> int:
    updated = 0
    if isinstance(value, dict):
        for key, child in list(value.items()):
            if key in expected and isinstance(child, str):
                if child != expected[key]:
                    value[key] = expected[key]
                    updated += 1
            elif key == "timelines" and isinstance(child, list):
                if child and all(isinstance(item, dict) for item in child):
                    for item in child:
                        updated += _set(item, "id", expected["timeline_id"])
                elif child != [expected["timeline_id"]]:
                    value[key] = [expected["timeline_id"]]
                    updated += 1
            else:
                updated += _sync_timeline_ids(child, expected)
    elif isinstance(value, list):
        for child in value:
            updated += _sync_timeline_ids(child, expected)
    return updated


def validate_id_mirrors(project_path: Path) -> dict:
    project_path = Path(project_path).resolve()
    try:
        root, meta, timeline_project, timeline_id, mirror_path, mirror = _observed_ids(project_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "ID_MIRROR_MISSING", "detail": str(exc)}])
    project_id = timeline_project.get("project_id") or timeline_project.get("id")
    draft_id = meta.get("draft_id")
    checks = [
        root.get("id") == timeline_id,
        timeline_project.get("id") == project_id,
        timeline_project.get("main_timeline_id") == timeline_id,
        mirror.get("id") == timeline_id,
        mirror_path.parent.name == timeline_id,
    ]
    for payload, key, expected_value in (
        (root, "draft_id", draft_id),
        (root, "main_timeline_id", timeline_id),
        (timeline_project, "project_id", project_id),
        (timeline_project, "draft_id", draft_id),
        (mirror, "draft_id", draft_id),
        (mirror, "main_timeline_id", timeline_id),
    ):
        if key in payload:
            checks.append(payload.get(key) == expected_value)
    expected = {
        "project_id": project_id,
        "draft_id": draft_id,
        "main_timeline_id": timeline_id,
        "timeline_id": timeline_id,
    }
    timeline_mismatch = any(
        _timeline_id_mismatch(payload, expected)
        or _mirror_bare_id_mismatch(payload, timeline_id)
        for _, payload in iter_timeline_json(project_path)
    )
    errors = [] if all(checks) and not timeline_mismatch else [{"code": "ID_MIRROR_MISMATCH"}]
    return result(
        errors,
        {"project_id": project_id, "draft_id": draft_id, "main_timeline_id": timeline_id},
    )


def _set(payload: dict, key: str, value: str) -> int:
    if payload.get(key) == value:
        return 0
    payload[key] = value
    return 1


def sync_project_ids(
    project_path: Path,
    project_id: str,
    draft_id: str,
    timeline_id: str,
    *,
    source_project_path: Path | None = None,
    expected_source_hashes: dict[str, str] | None = None,
) -> dict:
    raw_project_path = Path(project_path).absolute()
    if path_contains_alias(raw_project_path) or tree_contains_alias(raw_project_path):
        return result([{"code": "ID_SYNC_PATH_UNSAFE"}])
    project_path = raw_project_path.resolve()
    if source_project_path is None or not isinstance(expected_source_hashes, dict) or not expected_source_hashes:
        return result([{"code": "SOURCE_PROJECT_CONTEXT_REQUIRED"}])
    raw_source_project_path = Path(source_project_path).absolute()
    if path_contains_alias(raw_source_project_path) or tree_contains_alias(raw_source_project_path):
        return result([{"code": "SOURCE_WORKING_PATH_UNSAFE"}])
    source_project_path = raw_source_project_path.resolve()
    if _conflicting_paths(source_project_path, project_path):
        return result([{"code": "SOURCE_WORKING_CONFLICT"}])
    source_before = verify_source_unchanged(source_project_path, expected_source_hashes)
    if source_before["status"] != "PASS":
        return source_before
    if not all(_valid_identifier(value) for value in (project_id, draft_id, timeline_id)):
        return result([{"code": "ID_SYNC_INPUT_INVALID"}])
    try:
        root, meta, timeline_project, old_timeline_id, mirror_path, mirror = _observed_ids(project_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "ID_MIRROR_MISSING", "detail": str(exc)}])

    new_mirror_dir = mirror_path.parent.parent / timeline_id
    timeline_documents = {
        path: payload
        for path, payload in iter_timeline_json(project_path)
        if isinstance(payload, dict)
    }
    timeline_documents[project_path / "Timelines" / "project.json"] = timeline_project
    timeline_documents[mirror_path] = mirror
    write_targets = [
        project_path / "draft_content.json",
        project_path / "draft_meta_info.json",
        *timeline_documents,
        new_mirror_dir,
    ]
    if not _write_targets_are_safe(project_path, write_targets):
        return result([{"code": "ID_SYNC_PATH_UNSAFE"}])
    document_paths = [
        project_path / "draft_content.json",
        project_path / "draft_meta_info.json",
        *timeline_documents,
    ]
    try:
        originals = {path: path.read_bytes() for path in set(document_paths)}
    except OSError as exc:
        return result([{"code": "ID_SYNC_READ_FAILED", "detail": str(exc)}])

    updated = 0
    updated += _set(root, "id", timeline_id)
    updated += _set(meta, "draft_id", draft_id)
    updated += _set(timeline_project, "id", project_id)
    updated += _set(timeline_project, "main_timeline_id", timeline_id)
    updated += _set(mirror, "id", timeline_id)
    for payload, mapping in (
        (root, {"draft_id": draft_id, "main_timeline_id": timeline_id}),
        (timeline_project, {"project_id": project_id, "draft_id": draft_id}),
        (mirror, {"draft_id": draft_id, "main_timeline_id": timeline_id}),
    ):
        for key, value in mapping.items():
            if key in payload:
                updated += _set(payload, key, value)
    timeline_expected = {
        "project_id": project_id,
        "draft_id": draft_id,
        "main_timeline_id": timeline_id,
        "timeline_id": timeline_id,
    }
    for payload in timeline_documents.values():
        updated += _sync_timeline_ids(payload, timeline_expected)
        updated += _sync_mirror_bare_id(payload, timeline_expected["timeline_id"])
    if updated == 0:
        return result([{"code": "ID_SYNC_NO_UPDATES"}], {"updated_fields": 0})

    if new_mirror_dir.exists() and new_mirror_dir != mirror_path.parent:
        return result([{"code": "ID_SYNC_TARGET_EXISTS"}])
    try:
        write_json(project_path / "draft_content.json", root)
        write_json(project_path / "draft_meta_info.json", meta)
        for path, payload in timeline_documents.items():
            write_json(path, payload)
        if mirror_path.parent != new_mirror_dir:
            mirror_path.parent.rename(new_mirror_dir)
    except OSError as exc:
        _restore_documents(originals, mirror_path.parent, new_mirror_dir)
        return result([{"code": "ID_SYNC_WRITE_FAILED", "detail": str(exc)}])
    verified = validate_id_mirrors(project_path)
    if verified["status"] != "PASS":
        if not _restore_documents(originals, mirror_path.parent, new_mirror_dir):
            return result([*verified["errors"], {"code": "ID_SYNC_ROLLBACK_FAILED"}], {"updated_fields": updated})
        return result(verified["errors"], {"updated_fields": updated})
    source_after = verify_source_unchanged(source_project_path, expected_source_hashes)
    if source_after["status"] != "PASS":
        if not _restore_documents(originals, mirror_path.parent, new_mirror_dir):
            return result([*source_after["errors"], {"code": "ID_SYNC_ROLLBACK_FAILED"}])
        return source_after
    return result(
        [],
        {
            **verified["evidence"],
            "updated_fields": updated,
            "source_core_sha256": source_after["evidence"]["source_core_sha256"],
        },
    )
