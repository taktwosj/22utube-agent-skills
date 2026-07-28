from __future__ import annotations

import copy
import json
import os
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from capcut_io import iter_timeline_json, load_json_file
from capcut_model import (
    ProjectModel,
    collect_material_references,
    iter_materials,
    load_project,
    validate_materials,
)
from clone_and_sync import verify_source_unchanged
from common import inspect_write_target, path_contains_alias, result, tree_contains_alias


def _segments(payload: dict) -> Iterator[dict]:
    for track in payload.get("tracks", []):
        if not isinstance(track, dict):
            continue
        for segment in track.get("segments", []):
            if isinstance(segment, dict):
                yield segment


def _material_locations(value: Any, parent: Any = None, key: Any = None):
    if isinstance(value, dict):
        if isinstance(value.get("id"), str) and any(
            field in value for field in ("type", "role", "path", "media_path", "content", "text")
        ):
            yield parent, key, value
            return
        for child_key, child in list(value.items()):
            yield from _material_locations(child, value, child_key)
    elif isinstance(value, list):
        for index, child in enumerate(list(value)):
            yield from _material_locations(child, value, index)


def _find_material(materials: Any, material_id: str):
    for parent, key, material in _material_locations(materials):
        if material.get("id") == material_id:
            return parent, key, material
    return None


def _append_sibling(parent: Any, new_id: str, material: dict) -> None:
    if isinstance(parent, list):
        parent.append(material)
    elif isinstance(parent, dict):
        parent[new_id] = material
    else:
        raise ValueError("material container cannot accept replacement")


def _scrub_remote_ids(value: Any) -> None:
    if isinstance(value, dict):
        value.pop("online_id", None)
        value.pop("request_id", None)
        for child in value.values():
            _scrub_remote_ids(child)
    elif isinstance(value, list):
        for child in value:
            _scrub_remote_ids(child)


def _remove_material_ids(value: Any, removable: set[str]) -> None:
    if isinstance(value, list):
        value[:] = [
            child
            for child in value
            if not (
                isinstance(child, dict)
                and isinstance(child.get("id"), str)
                and any(field in child for field in ("type", "role", "path", "content", "text"))
                and child["id"] in removable
            )
        ]
        for child in value:
            _remove_material_ids(child, removable)
    elif isinstance(value, dict):
        for child_key in list(value):
            child = value[child_key]
            if (
                isinstance(child, dict)
                and isinstance(child.get("id"), str)
                and any(field in child for field in ("type", "role", "path", "content", "text"))
                and child["id"] in removable
            ):
                del value[child_key]
            else:
                _remove_material_ids(child, removable)


def _paths_conflict(first: Path, second: Path) -> bool:
    try:
        first.relative_to(second)
        return True
    except ValueError:
        try:
            second.relative_to(first)
            return True
        except ValueError:
            return False


def _validate_documents(project_path: Path, documents: list[tuple[Path, dict]]) -> list[dict]:
    base = load_project(project_path)
    errors: list[dict] = []
    for path, payload in documents:
        if not isinstance(payload.get("tracks"), list) or not isinstance(
            payload.get("materials"), (dict, list)
        ):
            continue
        staged = ProjectModel(
            project_path,
            payload,
            base.meta,
            base.template,
            base.timeline_project,
            base.timeline_mirror,
            {document_path: document for document_path, document in documents},
        )
        for error in validate_materials(staged, project_path):
            errors.append(
                {**error, "document": path.relative_to(project_path).as_posix()}
            )
    return errors


def _commit_documents(
    project_path: Path, documents: list[tuple[Path, dict]]
) -> str | None:
    staged_paths: dict[Path, Path] = {}
    originals: dict[Path, bytes] = {}
    try:
        for path, payload in documents:
            stage = path.with_name(path.name + ".replacement-stage")
            if inspect_write_target(project_path, path) or inspect_write_target(
                project_path, stage, require_new=True
            ):
                return "REPLACEMENT_PATH_UNSAFE"
            originals[path] = path.read_bytes()
            stage.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            staged_paths[path] = stage
        for path, stage in staged_paths.items():
            os.replace(stage, path)
    except OSError:
        for path, original in originals.items():
            try:
                path.write_bytes(original)
            except OSError:
                pass
        return "REPLACEMENT_WRITE_FAILED"
    finally:
        for stage in staged_paths.values():
            try:
                stage.unlink(missing_ok=True)
            except OSError:
                pass
    return None


def _restore_documents(originals: dict[Path, bytes]) -> bool:
    try:
        for path, data in originals.items():
            path.write_bytes(data)
    except OSError:
        return False
    return True


def replace_materials(
    project_path: Path,
    replacements: list[dict],
    *,
    source_project_path: Path | None = None,
    expected_source_hashes: dict[str, str] | None = None,
) -> dict:
    raw_project_path = Path(project_path).absolute()
    if path_contains_alias(raw_project_path) or tree_contains_alias(raw_project_path):
        return result([{"code": "REPLACEMENT_PATH_UNSAFE"}])
    project_path = raw_project_path.resolve()
    if source_project_path is None or not isinstance(expected_source_hashes, dict) or not expected_source_hashes:
        return result([{"code": "SOURCE_PROJECT_CONTEXT_REQUIRED"}])
    raw_source_project_path = Path(source_project_path).absolute()
    if path_contains_alias(raw_source_project_path) or tree_contains_alias(raw_source_project_path):
        return result([{"code": "REPLACEMENT_PATH_UNSAFE"}])
    source_project_path = raw_source_project_path.resolve()
    if _paths_conflict(source_project_path, project_path):
        return result([{"code": "SOURCE_WORKING_CONFLICT"}])
    source_before = verify_source_unchanged(source_project_path, expected_source_hashes)
    if source_before["status"] != "PASS":
        return source_before
    content_path = project_path / "draft_content.json"
    try:
        root = load_json_file(content_path, required=True)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "REPLACEMENT_PROJECT_INVALID", "detail": str(exc)}])
    if not isinstance(replacements, list) or not replacements:
        return result([{"code": "REPLACEMENTS_REQUIRED"}])
    root_segments = {row.get("id"): row for row in _segments(root)}
    errors: list[dict] = []
    segment_ids = [
        replacement.get("segment_id")
        for replacement in replacements
        if isinstance(replacement, dict)
    ]
    duplicate_segment_ids = sorted(
        segment_id
        for segment_id, count in Counter(segment_ids).items()
        if segment_id is not None and count > 1
    )
    for segment_id in duplicate_segment_ids:
        errors.append(
            {"code": "DUPLICATE_REPLACEMENT_SEGMENT", "segment_id": segment_id}
        )
    for replacement in replacements:
        segment_id = replacement.get("segment_id") if isinstance(replacement, dict) else None
        if segment_id not in root_segments:
            errors.append({"code": "REPLACEMENT_SEGMENT_UNKNOWN", "segment_id": segment_id})
            continue
        if not replacement.get("role") or not replacement.get("desc"):
            errors.append({"code": "REPLACEMENT_METADATA_MISSING", "segment_id": segment_id})
        raw_path = replacement.get("path")
        if raw_path:
            asset = Path(raw_path)
            if not asset.is_absolute():
                asset = project_path / asset
            asset = asset.resolve()
            try:
                asset.relative_to(project_path)
            except ValueError:
                errors.append({"code": "REPLACEMENT_ASSET_OUTSIDE_PROJECT", "segment_id": segment_id})
                continue
            if not asset.is_file():
                errors.append({"code": "REPLACEMENT_ASSET_MISSING", "segment_id": segment_id})
        elif not isinstance(replacement.get("text"), str) or not replacement["text"].strip():
            errors.append({"code": "REPLACEMENT_CONTENT_MISSING", "segment_id": segment_id})
    if errors:
        return result(errors)

    replacement_ids = {
        row["segment_id"]: "material-" + uuid.uuid4().hex for row in replacements
    }
    documents: list[tuple[Path, dict]] = [(content_path, root)]
    for path, payload in iter_timeline_json(project_path):
        if path == content_path or not isinstance(payload, dict):
            continue
        if isinstance(payload.get("tracks"), list) and isinstance(payload.get("materials"), (dict, list)):
            documents.append((path, payload))

    try:
        for _, payload in documents:
            segment_map = {row.get("id"): row for row in _segments(payload)}
            replaced_old_ids: set[str] = set()
            for replacement in replacements:
                segment = segment_map.get(replacement["segment_id"])
                if segment is None:
                    continue
                old_id = segment.get("material_id")
                if isinstance(old_id, str):
                    replaced_old_ids.add(old_id)
                located = _find_material(payload.get("materials"), old_id)
                if located is None:
                    raise ValueError(f"material not found for {replacement['segment_id']}")
                parent, _, old_material = located
                new_id = replacement_ids[replacement["segment_id"]]
                new_material = copy.deepcopy(old_material)
                _scrub_remote_ids(new_material)
                new_material["id"] = new_id
                new_material["role"] = replacement["role"]
                new_material["desc"] = replacement["desc"]
                if replacement.get("path"):
                    new_material["path"] = replacement["path"]
                    new_material["media_path"] = replacement["path"]
                if replacement.get("text") is not None:
                    new_material["content"] = replacement["text"]
                    new_material["text"] = replacement["text"]
                _append_sibling(parent, new_id, new_material)
                segment["material_id"] = new_id
            defined_ids = {
                material.get("id")
                for material in iter_materials(payload.get("materials"))
                if isinstance(material.get("id"), str)
            }
            referenced = {
                row["material_id"]
                for row in collect_material_references(payload.get("tracks", []))
                if row["material_id"] in defined_ids
            }
            _remove_material_ids(payload.get("materials"), replaced_old_ids - referenced)
    except (TypeError, ValueError) as exc:
        return result([{"code": "REPLACEMENT_ASSEMBLY_FAILED", "detail": str(exc)}])

    material_errors = _validate_documents(project_path, documents)
    if material_errors:
        return result(material_errors)
    source_after = verify_source_unchanged(source_project_path, expected_source_hashes)
    if source_after["status"] != "PASS":
        return source_after
    try:
        originals = {path: path.read_bytes() for path, _ in documents}
    except OSError as exc:
        return result([{"code": "REPLACEMENT_READ_FAILED", "detail": str(exc)}])
    write_error = _commit_documents(project_path, documents)
    if write_error is not None:
        return result([{"code": write_error}])
    source_after = verify_source_unchanged(source_project_path, expected_source_hashes)
    if source_after["status"] != "PASS":
        if not _restore_documents(originals):
            return result([*source_after["errors"], {"code": "REPLACEMENT_ROLLBACK_FAILED"}])
        return source_after
    return result(
        [],
        {
            "updated_segments": sorted(replacement_ids),
            "material_ids": [replacement_ids[row["segment_id"]] for row in replacements],
            "source_core_sha256": source_after["evidence"]["source_core_sha256"],
        },
    )
