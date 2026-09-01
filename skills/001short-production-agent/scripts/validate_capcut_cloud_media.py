#!/usr/bin/env python3
"""Validate CapCut project media reachability before cloud upload.

Usage:
  python3 validate_capcut_cloud_media.py /path/to/project

Exit 0 only when live material references are complete, no external Windows
cache path survives in parseable project JSON/cache files, required mirrors
exist, and every retained subdraft directory is referenced by the project.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

WINDOWS_PATH = re.compile(r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]")
PARSEABLE_SUFFIXES = {".json", ".tmp"}


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def walk_strings(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)
    elif isinstance(value, str):
        yield value


def resolve_project_path(project: Path, raw: str) -> Path | None:
    normalized = raw.replace("\\", "/")
    if "Resources/" in normalized:
        return project / normalized[normalized.index("Resources/") :]
    if normalized.startswith("/"):
        return Path(normalized)
    if WINDOWS_PATH.search(raw):
        return None
    return Path(raw) if raw else None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _within(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _allowed_local_meta_path(project: Path, key: str | None, raw: str) -> bool:
    candidate = Path(raw)
    if key == "draft_fold_path":
        return candidate.resolve() == project
    if key == "draft_root_path":
        return candidate.resolve() == project.parent
    if key == "file_Path":
        return candidate.is_file() and _within(candidate, project)
    return False


def _contains_unsafe_windows_path(
    project: Path, source: Path, value: Any, key: str | None = None
) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_unsafe_windows_path(project, source, child, str(child_key))
            for child_key, child in value.items()
        )
    if isinstance(value, list):
        return any(
            _contains_unsafe_windows_path(project, source, child, key)
            for child in value
        )
    if not isinstance(value, str) or not WINDOWS_PATH.search(value):
        return False
    return not (
        source.name == "draft_meta_info.json"
        and _allowed_local_meta_path(project, key, value)
    )


def _referenced_subdraft_directories(payload: Any) -> set[str]:
    referenced: set[str] = set()
    for raw in walk_strings(payload):
        normalized = raw.replace("\\", "/")
        if "subdraft/" not in normalized:
            continue
        child = normalized.split("subdraft/", 1)[1].split("/", 1)[0]
        if child and "." not in child:
            referenced.add(child)
    return referenced


def validate_project(project: Path) -> dict[str, Any]:
    project = Path(project).expanduser().resolve()
    content_path = project / "draft_content.json"

    result: dict[str, Any] = {
        "project": str(project),
        "status": "FAIL",
        "missing_required_files": [],
        "missing_live_materials": [],
        "missing_live_paths": [],
        "windows_path_files": [],
        "unreferenced_missing_paths": [],
        "bak_files": [],
        "subdraft_files": [],
        "unreferenced_subdraft_directories": [],
        "missing_subdraft_directories": [],
        "incomplete_subdraft_directories": [],
        "unreferenced_subdraft_files": [],
    }

    required = [
        project / "draft_content.json",
        project / "draft_info.json",
        project / "template-2.tmp",
        project / "draft_meta_info.json",
    ]
    result["missing_required_files"] = [str(p) for p in required if not p.is_file()]
    if not content_path.is_file():
        return result

    payload = load_json(content_path)
    materials: dict[str, dict[str, Any]] = {}
    for item in walk(payload.get("materials", {})):
        material_id = item.get("id")
        if isinstance(material_id, str):
            materials[material_id] = item

    live_refs: set[str] = set()
    for track in payload.get("tracks", []):
        for segment in track.get("segments", []):
            material_id = segment.get("material_id")
            if isinstance(material_id, str) and material_id:
                live_refs.add(material_id)
            for extra in segment.get("extra_material_refs") or []:
                if isinstance(extra, str) and extra:
                    live_refs.add(extra)

    for material_id in sorted(live_refs):
        material = materials.get(material_id)
        if material is None:
            result["missing_live_materials"].append(material_id)
            continue
        for key in ("path", "media_path"):
            raw = material.get(key)
            if not isinstance(raw, str) or not raw:
                continue
            resolved = resolve_project_path(project, raw)
            if resolved is None or not resolved.is_file():
                result["missing_live_paths"].append(
                    {
                        "id": material_id,
                        "type": material.get("type"),
                        "name": material.get("name") or material.get("material_name"),
                        "field": key,
                        "path": raw,
                    }
                )

    for material_id, material in materials.items():
        if material_id in live_refs:
            continue
        for key in ("path", "media_path"):
            raw = material.get(key)
            if not isinstance(raw, str) or not raw:
                continue
            resolved = resolve_project_path(project, raw)
            if resolved is None or not resolved.exists():
                result["unreferenced_missing_paths"].append(
                    {
                        "id": material_id,
                        "type": material.get("type"),
                        "name": material.get("name") or material.get("material_name"),
                        "field": key,
                        "path": raw,
                    }
                )

    referenced_subdraft_directories: set[str] = set()
    for path in project.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PARSEABLE_SUFFIXES:
            continue
        try:
            parsed = load_json(path)
        except Exception:
            continue
        relative_parts = path.relative_to(project).parts
        if "subdraft" not in relative_parts:
            referenced_subdraft_directories.update(
                _referenced_subdraft_directories(parsed)
            )
        if _contains_unsafe_windows_path(project, path, parsed):
            result["windows_path_files"].append(str(path.relative_to(project)))

    result["bak_files"] = [str(p.relative_to(project)) for p in project.rglob("*.bak")]
    subdraft = project / "subdraft"
    if subdraft.is_dir():
        result["subdraft_files"] = [
            str(p.relative_to(project)) for p in subdraft.rglob("*") if p.is_file()
        ]
        actual_directories = {p.name for p in subdraft.iterdir() if p.is_dir()}
        result["unreferenced_subdraft_directories"] = sorted(
            actual_directories - referenced_subdraft_directories
        )
        result["missing_subdraft_directories"] = sorted(
            referenced_subdraft_directories - actual_directories
        )
        result["incomplete_subdraft_directories"] = sorted(
            name
            for name in actual_directories & referenced_subdraft_directories
            if not (subdraft / name / "draft_content.json").is_file()
            or not (subdraft / name / "sub_draft_config.json").is_file()
        )
        result["unreferenced_subdraft_files"] = sorted(
            str(p.relative_to(project)) for p in subdraft.iterdir() if p.is_file()
        )
        if not actual_directories and not result["unreferenced_subdraft_files"]:
            result["empty_subdraft_directory"] = True
    elif referenced_subdraft_directories:
        result["missing_subdraft_directories"] = sorted(
            referenced_subdraft_directories
        )

    cover = project / "draft_cover.jpg"
    result["draft_cover_exists"] = cover.is_file()
    result["live_reference_count"] = len(live_refs)
    result["material_count"] = len(materials)

    blockers = [
        result["missing_required_files"],
        result["missing_live_materials"],
        result["missing_live_paths"],
        result["windows_path_files"],
        result["unreferenced_missing_paths"],
        result["bak_files"],
        result["unreferenced_subdraft_directories"],
        result["missing_subdraft_directories"],
        result["incomplete_subdraft_directories"],
        result["unreferenced_subdraft_files"],
    ]
    if result.get("empty_subdraft_directory"):
        blockers.append(["empty_subdraft_directory"])
    if not result["draft_cover_exists"]:
        blockers.append(["draft_cover_missing"])

    result["status"] = "PASS" if not any(blockers) else "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    result = validate_project(args.project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
