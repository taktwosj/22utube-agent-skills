from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


REQUIRED_ROOT_JSON = ("draft_content.json", "draft_meta_info.json")


def load_json_file(path: Path, *, required: bool = True) -> Any | None:
    try:
        raw = path.read_bytes()
    except OSError:
        if required:
            raise
        return None
    stripped = raw.lstrip()
    if not stripped.startswith((b"{", b"[")):
        if required:
            raise ValueError(f"required JSON is not JSON: {path}")
        return None
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        if required:
            raise
        return None


def iter_timeline_json(project_path: Path) -> Iterator[tuple[Path, Any]]:
    timeline_root = project_path / "Timelines"
    if not timeline_root.is_dir():
        return
    for path in sorted(timeline_root.rglob("*")):
        if not path.is_file():
            continue
        payload = load_json_file(path, required=False)
        if payload is not None:
            yield path, payload


def iter_primary_draft_documents(project_path: Path) -> Iterator[tuple[Path, Any]]:
    """Yield only root and direct Timelines/<id> editable draft documents."""
    project_path = Path(project_path)
    root = project_path / "draft_content.json"
    yield root, load_json_file(root, required=True)
    timelines = project_path / "Timelines"
    if not timelines.is_dir():
        return
    for path in sorted(timelines.glob("*/draft_content.json")):
        payload = load_json_file(path, required=False)
        if payload is not None:
            yield path, payload


def required_json(project_path: Path) -> dict[str, Any]:
    payloads = {
        name: load_json_file(project_path / name, required=True)
        for name in REQUIRED_ROOT_JSON
    }
    timeline_project = project_path / "Timelines" / "project.json"
    payloads["Timelines/project.json"] = load_json_file(timeline_project, required=True)
    return payloads
