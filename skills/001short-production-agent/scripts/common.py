from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_sha256(manifest: dict[str, str]) -> str:
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def result(errors: list[dict], evidence: dict | None = None) -> dict:
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "evidence": evidence or {},
    }


def resolved_declared_path(base_file: Path, declared: str) -> Path:
    candidate = Path(declared)
    if not candidate.is_absolute():
        candidate = base_file.parent / candidate
    return candidate.resolve()


def _is_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def path_contains_alias(path: Path) -> bool:
    path = Path(path).absolute()
    anchor = Path(path.anchor)
    current = anchor
    try:
        parts = path.relative_to(anchor).parts
    except ValueError:
        return True
    for part in parts:
        current = current / part
        if not os.path.lexists(current):
            continue
        if current.is_symlink() or _is_reparse_point(current):
            return True
    return False


def tree_contains_alias(root: Path) -> bool:
    """Reject any symlink, junction, reparse point, or hardlinked file below root."""
    root = Path(root).absolute()
    if path_contains_alias(root) or not root.is_dir():
        return True
    try:
        for current, directories, files in os.walk(root, followlinks=False):
            base = Path(current)
            for name in [*directories, *files]:
                candidate = base / name
                if candidate.is_symlink() or _is_reparse_point(candidate):
                    return True
                if candidate.is_file() and os.stat(candidate).st_nlink > 1:
                    return True
    except OSError:
        return True
    return False


def inspect_write_target(
    root: Path, target: Path, *, require_new: bool = False
) -> str | None:
    root = Path(root).absolute()
    target = Path(target).absolute()
    if not root.is_dir() or path_contains_alias(root):
        return "PATH_UNSAFE"
    try:
        relative = target.relative_to(root)
    except ValueError:
        return "PATH_UNSAFE"
    current = root
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            continue
        if current.is_symlink() or _is_reparse_point(current):
            return "PATH_UNSAFE"
    try:
        resolved_root = root.resolve(strict=True)
        target.resolve(strict=False).relative_to(resolved_root)
    except (OSError, ValueError):
        return "PATH_UNSAFE"
    if require_new and os.path.lexists(target):
        return "PATH_EXISTS"
    try:
        if target.is_file() and os.stat(target).st_nlink > 1:
            return "PATH_UNSAFE"
    except OSError:
        return "PATH_UNSAFE"
    return None
