"""Validate and safely rewrite path-bearing CapCut material fields."""

from __future__ import annotations

import copy
import json
import ntpath
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


_DRIVE_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:/")
_DRIVE_RELATIVE_RE = re.compile(r"^[A-Za-z]:(?:$|[^/])")
_WRAPPER_KEYS = {"content", "metadata"}
_MAX_WRAPPER_DECODE_DEPTH = 2


def _error(code: str, location: str, original: Any) -> RuntimeError:
    return RuntimeError(f"MATERIAL_PATH_{code}:{location}:original={original!r}")


def _is_path_key(key: Any) -> bool:
    return isinstance(key, str) and (key == "path" or key.endswith("_path"))


def _parts(value: str) -> list[str]:
    normalized = value.replace("\\", "/")
    if _DRIVE_ABSOLUTE_RE.match(normalized):
        normalized = normalized[3:]
    return [part for part in normalized.split("/") if part]


def _is_absolute(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return bool(_DRIVE_ABSOLUTE_RE.match(normalized)) or normalized.startswith("/")


def _normalized_windows(value: str) -> str:
    return ntpath.normcase(ntpath.normpath(value.replace("/", "\\")))


def _is_within(value: str, root: str) -> bool:
    candidate = _normalized_windows(value)
    normalized_root = _normalized_windows(root)
    try:
        return ntpath.commonpath((candidate, normalized_root)) == normalized_root
    except ValueError:
        return False


def _validate_lexical_path(value: str, location: str, original: Any) -> None:
    if "\0" in value:
        raise _error("NUL", location, original)
    normalized = value.replace("\\", "/")
    if _DRIVE_RELATIVE_RE.match(normalized):
        raise _error("DRIVE_RELATIVE", location, original)
    parts = _parts(normalized)
    if any(part in {".", ".."} for part in parts):
        raise _error("TRAVERSAL", location, original)
    if any(":" in part for part in parts):
        raise _error("COLON", location, original)


def _legacy_resources_suffix(value: str) -> list[str] | None:
    if not _is_absolute(value):
        return None
    parts = _parts(value)
    resource_indexes = [index for index, part in enumerate(parts) if part.casefold() == "resources"]
    if not resource_indexes:
        return None
    suffix = parts[resource_indexes[-1] + 1 :]
    return suffix or None


def _enforce_path_value(
    value: Any,
    *,
    location: str,
    project_root: Path,
    rebase_legacy_resources: bool,
    exact_rewrites: Mapping[str, str],
    allowed_roots: Sequence[str],
) -> Any:
    original = value
    if not isinstance(value, str):
        raise _error("NON_STRING", location, original)
    if not value:
        return value
    _validate_lexical_path(value, location, original)

    if value in exact_rewrites:
        replacement = exact_rewrites[value]
        if not isinstance(replacement, str):
            raise _error("NON_STRING", location, original)
        value = replacement
        _validate_lexical_path(value, location, original)

    suffix = _legacy_resources_suffix(value) if rebase_legacy_resources else None
    if suffix is not None:
        value = (project_root / "Resources" / Path(*suffix)).as_posix()

    if not _is_absolute(value):
        return value

    project_root_text = project_root.resolve(strict=False).as_posix()
    if _is_within(value, project_root_text):
        return value
    if any(_is_within(value, allowed_root) for allowed_root in allowed_roots):
        return value
    raise _error("FOREIGN", location, original)


def _looks_json_encoded(value: str) -> bool:
    return value.lstrip().startswith(("{", "[", '"'))


def _decode_container(value: str, location: str, depth: int) -> tuple[Any, int]:
    original = value
    current: Any = value
    used = 0
    while isinstance(current, str):
        if not _looks_json_encoded(current):
            raise _error("JSON_INVALID", location, original)
        if depth + used >= _MAX_WRAPPER_DECODE_DEPTH:
            raise _error("DEPTH_EXCEEDED", location, original)
        try:
            current = json.loads(current)
        except json.JSONDecodeError as exc:
            raise _error("JSON_INVALID", location, original) from exc
        used += 1
    if not isinstance(current, (dict, list)):
        raise _error("JSON_INVALID", location, original)
    return current, used


def _encode_container(value: Any, layers: int) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    for _ in range(layers - 1):
        encoded = json.dumps(encoded, ensure_ascii=False, separators=(",", ":"))
    return encoded


def _walk(
    value: Any,
    *,
    location: str,
    wrapper_depth: int,
    project_root: Path,
    rebase_legacy_resources: bool,
    exact_rewrites: Mapping[str, str],
    allowed_roots: Sequence[str],
) -> tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        result: dict[Any, Any] = {}
        for key, item in value.items():
            child_location = f"{location}.{key}"
            if _is_path_key(key):
                rewritten = _enforce_path_value(
                    item,
                    location=child_location,
                    project_root=project_root,
                    rebase_legacy_resources=rebase_legacy_resources,
                    exact_rewrites=exact_rewrites,
                    allowed_roots=allowed_roots,
                )
                result[key] = rewritten
                changed = changed or rewritten != item
                continue
            if key in _WRAPPER_KEYS and isinstance(item, str) and _looks_json_encoded(item):
                decoded, layers = _decode_container(item, child_location, wrapper_depth)
                rewritten, inner_changed = _walk(
                    decoded,
                    location=f"{child_location}::<json>",
                    wrapper_depth=wrapper_depth + layers,
                    project_root=project_root,
                    rebase_legacy_resources=rebase_legacy_resources,
                    exact_rewrites=exact_rewrites,
                    allowed_roots=allowed_roots,
                )
                result[key] = _encode_container(rewritten, layers) if inner_changed else item
                changed = changed or inner_changed
                continue
            rewritten, inner_changed = _walk(
                item,
                location=child_location,
                wrapper_depth=wrapper_depth,
                project_root=project_root,
                rebase_legacy_resources=rebase_legacy_resources,
                exact_rewrites=exact_rewrites,
                allowed_roots=allowed_roots,
            )
            result[key] = rewritten
            changed = changed or inner_changed
        return result, changed
    if isinstance(value, list):
        changed = False
        result = []
        for index, item in enumerate(value):
            rewritten, inner_changed = _walk(
                item,
                location=f"{location}[{index}]",
                wrapper_depth=wrapper_depth,
                project_root=project_root,
                rebase_legacy_resources=rebase_legacy_resources,
                exact_rewrites=exact_rewrites,
                allowed_roots=allowed_roots,
            )
            result.append(rewritten)
            changed = changed or inner_changed
        return result, changed
    return value, False


def enforce_material_paths(
    document: dict,
    *,
    project_root: Path,
    rebase_legacy_resources: bool,
    exact_rewrites: Mapping[str, str] = {},
    allowed_roots: Sequence[str] = (),
) -> dict:
    """Return an enforced copy of *document*, walking only its materials tree."""
    result = copy.deepcopy(document)
    materials = result.get("materials")
    if not isinstance(materials, (dict, list)):
        return result
    rewritten, _ = _walk(
        materials,
        location="$.materials",
        wrapper_depth=0,
        project_root=Path(project_root),
        rebase_legacy_resources=rebase_legacy_resources,
        exact_rewrites=exact_rewrites,
        allowed_roots=allowed_roots,
    )
    result["materials"] = rewritten
    return result
