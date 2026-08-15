#!/usr/bin/env python3
"""Publish, activate, and verify immutable managed-skill releases."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any


TEST_OVERRIDE_ENV = "AGENT_SKILLS_TEST_ROOT_OVERRIDE"
PROTECTED_SKILL_NAMES = {
    "imagegen",
    "openai-docs",
    "plugin-creator",
    "skill-creator",
    "skill-installer",
}
PROTECTED_PATH_SEGMENTS = {".system", ".plugins", "plugins", "plugin-cache"}
SUPPORTED_TARGET_NAMES = {"codex", "claude", "hermes"}
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ReleaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class LinkPlan:
    target_name: str
    skill_name: str
    destination: Path
    source: Path
    backup_root: Path


@dataclass(frozen=True)
class LinkChange:
    destination: Path
    backup: Path | None
    changed: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseError(f"invalid or missing JSON: {path}: {error}") from error


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def require_test_guard_if_overridden(overridden: bool) -> None:
    if overridden and os.environ.get(TEST_OVERRIDE_ENV) != "1":
        raise ReleaseError(f"test-only root overrides require {TEST_OVERRIDE_ENV}=1")


def git_output(repo_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *arguments], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if completed.returncode != 0:
        raise ReleaseError(f"git {' '.join(arguments)} failed: {(completed.stderr or completed.stdout).strip()}")
    return completed.stdout.strip()


def git_bytes(repo_root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(["git", "-C", str(repo_root), *arguments], capture_output=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", errors="replace").strip()
        raise ReleaseError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout


def validate_skill_name(name: str) -> None:
    if not SKILL_NAME_PATTERN.fullmatch(name):
        raise ReleaseError(f"invalid managed skill name: {name}")
    if name in PROTECTED_SKILL_NAMES:
        raise ReleaseError(f"refusing protected system/plugin skill name: {name}")


def enabled_skills(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    skill_set = read_json(repo_root / "manifests" / "skill-set.json")
    targets = read_json(repo_root / "manifests" / "targets.json")
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in skill_set.get("skills", []):
        if raw.get("enabled") is not True:
            continue
        name = raw.get("name")
        if not isinstance(name, str):
            raise ReleaseError("enabled skill has no valid name")
        validate_skill_name(name)
        if name in seen:
            raise ReleaseError(f"duplicate enabled skill: {name}")
        seen.add(name)
        source = repo_root / "skills" / name
        if not (source / "SKILL.md").is_file():
            raise ReleaseError(f"managed skill is missing SKILL.md: {name}")
        target_names = raw.get("targets")
        if not isinstance(target_names, list) or not target_names:
            raise ReleaseError(f"managed skill has no targets: {name}")
        selected.append(
            {
                "name": name,
                "category": raw.get("category", "22utube"),
                "targets": list(target_names),
            }
        )
    selected.sort(key=lambda value: value["name"])
    if not selected:
        raise ReleaseError("no enabled managed skills")
    return selected, targets.get("targets", {})


def payload_entries(root: Path, skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for skill in skills:
        skill_root = root / "skills" / skill["name"]
        for path in sorted((item for item in skill_root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
            relative = path.relative_to(root).as_posix()
            entries.append({"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)})
    return entries


def copy_head_skill_snapshot(repo_root: Path, staging: Path, skills: list[dict[str, Any]]) -> None:
    for skill in skills:
        prefix = f"skills/{skill['name']}"
        raw_tree = git_bytes(repo_root, "ls-tree", "-r", "-z", "--full-tree", "HEAD", "--", prefix)
        records = [record for record in raw_tree.split(b"\0") if record]
        tracked_paths: set[str] = set()
        for record in records:
            metadata, separator, raw_path = record.partition(b"\t")
            if not separator:
                raise ReleaseError(f"invalid git tree record for skill: {skill['name']}")
            fields = metadata.decode("ascii").split()
            if len(fields) != 3:
                raise ReleaseError(f"invalid git tree metadata for skill: {skill['name']}")
            mode, object_type, object_id = fields
            relative = raw_path.decode("utf-8")
            relative_path = Path(relative)
            if relative.startswith(("/", "\\")) or ".." in relative_path.parts:
                raise ReleaseError(f"unsafe tracked skill path: {relative}")
            if object_type != "blob" or mode == "120000":
                raise ReleaseError(f"unsupported tracked skill entry: mode={mode} type={object_type} path={relative}")
            if not relative.startswith(prefix + "/"):
                raise ReleaseError(f"tracked skill path escaped manifest owner: {relative}")
            destination = staging / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(git_bytes(repo_root, "cat-file", "blob", object_id))
            if os.name != "nt":
                destination.chmod(0o755 if mode == "100755" else 0o644)
            tracked_paths.add(relative)
        if f"{prefix}/SKILL.md" not in tracked_paths:
            raise ReleaseError(f"managed skill HEAD snapshot is missing SKILL.md: {skill['name']}")


def verify_release_directory(
    release: Path, expected_manifest_sha: str | None = None, require_immutable: bool = False
) -> dict[str, Any]:
    manifest_path = release / "manifest.json"
    ready_path = release / "READY"
    if not manifest_path.is_file() or not ready_path.is_file():
        raise ReleaseError(f"partial release: {release}")
    manifest_data = manifest_path.read_bytes()
    manifest_sha = sha256_bytes(manifest_data)
    ready_sha = ready_path.read_text(encoding="utf-8").strip()
    if ready_sha != manifest_sha:
        raise ReleaseError(f"READY manifest SHA mismatch: {release}")
    if expected_manifest_sha is not None and expected_manifest_sha != manifest_sha:
        raise ReleaseError(f"active manifest SHA mismatch: {release}")
    manifest = json.loads(manifest_data)
    if not isinstance(manifest, dict):
        raise ReleaseError(f"manifest must be an object: {release}")
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("file_count") != len(files):
        raise ReleaseError(f"manifest file_count mismatch: {release}")
    if any(not isinstance(entry, dict) for entry in files):
        raise ReleaseError(f"manifest file entry must be an object: {release}")
    listed_paths = {entry.get("path") for entry in files}
    control_paths = {"manifest.json", "READY"}
    if require_immutable:
        immutable_path = release / "IMMUTABLE"
        if not immutable_path.is_file() or immutable_path.read_text(encoding="utf-8").strip() != manifest_sha:
            raise ReleaseError(f"local immutable seal mismatch: {release}")
        control_paths.add("IMMUTABLE")
    actual_paths = {
        path.relative_to(release).as_posix()
        for path in release.rglob("*")
        if path.is_file() and path.relative_to(release).as_posix() not in control_paths
    }
    if listed_paths != actual_paths:
        extra = sorted(actual_paths - listed_paths)
        missing = sorted(listed_paths - actual_paths)
        raise ReleaseError(f"unlisted release files or missing manifest files: extra={extra} missing={missing}")
    for entry in files:
        relative = entry.get("path")
        if not isinstance(relative, str) or relative.startswith(("/", "\\")) or ".." in Path(relative).parts:
            raise ReleaseError(f"unsafe manifest path: {relative}")
        path = release / Path(relative)
        if not path.is_file():
            raise ReleaseError(f"release file missing: {relative}")
        if path.stat().st_size != entry.get("size") or sha256_file(path) != entry.get("sha256"):
            raise ReleaseError(f"release file hash mismatch: {relative}")
    return manifest


def make_local_release_immutable(release: Path, manifest_sha: str) -> None:
    (release / "IMMUTABLE").write_text(manifest_sha + "\n", encoding="utf-8")
    files = sorted((path for path in release.rglob("*") if path.is_file()), key=lambda path: len(path.parts), reverse=True)
    directories = sorted((path for path in release.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True)
    for path in files:
        if os.name == "nt":
            path.chmod(stat.S_IREAD)
        else:
            path.chmod(path.stat().st_mode & ~0o222)
    if os.name != "nt":
        for path in directories + [release]:
            path.chmod(path.stat().st_mode & ~0o222)


def make_tree_writable_for_cleanup(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            continue
        try:
            path.chmod(path.stat().st_mode | stat.S_IWRITE | stat.S_IWUSR)
        except OSError:
            pass
    try:
        root.chmod(root.stat().st_mode | stat.S_IWRITE | stat.S_IWUSR)
    except OSError:
        pass


def read_active(root: Path) -> tuple[str, str]:
    active = read_json(root / "active.json")
    release_id = active.get("release_id")
    manifest_sha = active.get("manifest_sha256")
    if not isinstance(release_id, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", release_id):
        raise ReleaseError(f"invalid active release_id: {release_id}")
    if not isinstance(manifest_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", manifest_sha):
        raise ReleaseError("invalid active manifest_sha256")
    return release_id, manifest_sha


def parse_root_overrides(values: list[str] | None) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values or []:
        target, separator, raw_path = value.partition("=")
        if not separator or target not in {"codex", "claude", "hermes"} or not raw_path:
            raise ReleaseError(f"root override must be target=path: {value}")
        if target in result:
            raise ReleaseError(f"duplicate root override: {target}")
        result[target] = Path(raw_path).resolve()
    return result


def ensure_unprotected_path(path: Path) -> None:
    lowered = {part.lower() for part in path.parts}
    if lowered.intersection(PROTECTED_PATH_SEGMENTS):
        raise ReleaseError(f"refusing protected system/plugin path: {path}")


def ensure_unprotected_config_path(value: str, target_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ReleaseError(f"target path is missing: {target_name}")
    segments = {segment.lower() for segment in value.replace("\\", "/").split("/") if segment}
    if segments.intersection(PROTECTED_PATH_SEGMENTS):
        raise ReleaseError(f"protected target path: {target_name}={value}")


def semantic_preflight(skills: list[dict[str, Any]], target_configs: dict[str, Any]) -> None:
    if not isinstance(target_configs, dict):
        raise ReleaseError("targets config must be an object")
    used_targets: set[str] = set()
    for skill in skills:
        category = skill.get("category")
        if category is not None and (not isinstance(category, str) or not SKILL_NAME_PATTERN.fullmatch(category)):
            raise ReleaseError(f"invalid skill category: {skill.get('name')}={category}")
        for target_name in skill.get("targets", []):
            if target_name not in SUPPORTED_TARGET_NAMES:
                raise ReleaseError(f"unsupported target for enabled skill {skill.get('name')}: {target_name}")
            if target_name not in target_configs:
                raise ReleaseError(f"unknown target for enabled skill {skill.get('name')}: {target_name}")
            used_targets.add(target_name)
    for target_name in sorted(used_targets):
        config = target_configs[target_name]
        if not isinstance(config, dict):
            raise ReleaseError(f"target config must be an object: {target_name}")
        universal_path = config.get("path")
        if not isinstance(universal_path, str) or not universal_path:
            if config.get("windows_path"):
                raise ReleaseError(f"windows path cannot replace universal path: {target_name}")
            raise ReleaseError(f"universal path is missing: {target_name}")
        ensure_unprotected_config_path(universal_path, target_name)
        layout = config.get("layout")
        if layout not in {"flat", "category"}:
            raise ReleaseError(f"invalid layout: {target_name}={layout}")
        if layout == "category":
            default_category = config.get("default_category")
            if not isinstance(default_category, str) or not SKILL_NAME_PATTERN.fullmatch(default_category):
                raise ReleaseError(f"missing default_category for category target: {target_name}")
        for path_key in ("path", "windows_path", "backup_path", "windows_backup_path"):
            if path_key in config:
                ensure_unprotected_config_path(config[path_key], target_name)


def expand_config_path(value: str) -> Path:
    home = Path.home()
    local_app_data = os.environ.get("LOCALAPPDATA")
    replacements = {"$HOME": str(home)}
    if local_app_data:
        replacements["$LOCALAPPDATA"] = local_app_data
    for prefix, replacement in replacements.items():
        if value == prefix or value.startswith(prefix + "/") or value.startswith(prefix + "\\"):
            return Path(replacement + value[len(prefix) :]).resolve()
    if value.startswith("$"):
        raise ReleaseError(f"runtime path variable is unavailable: {value}")
    return Path(value).expanduser().resolve()


def default_cache_root() -> Path:
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise ReleaseError("LOCALAPPDATA is not set")
        return Path(local_app_data) / "22utube" / "agent-skills-runtime"
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "22utube" / "agent-skills-runtime"


def selected_targets(value: str) -> list[str]:
    if value == "all":
        return ["codex", "claude", "hermes"]
    return [value]


def target_paths(
    manifest: dict[str, Any], target_name: str, runtime_overrides: dict[str, Path], backup_overrides: dict[str, Path]
) -> tuple[Path, Path, str]:
    config = manifest.get("targets", {}).get(target_name)
    if not isinstance(config, dict):
        raise ReleaseError(f"release manifest is missing target config: {target_name}")
    if target_name in runtime_overrides:
        runtime_root = runtime_overrides[target_name]
    else:
        path_key = "windows_path" if os.name == "nt" and config.get("windows_path") else "path"
        raw_runtime = config.get(path_key)
        if not isinstance(raw_runtime, str):
            raise ReleaseError(f"target config is missing {path_key}: {target_name}")
        runtime_root = expand_config_path(raw_runtime)
    if target_name in backup_overrides:
        backup_root = backup_overrides[target_name]
    elif target_name in runtime_overrides:
        backup_root = runtime_root.with_name(runtime_root.name + "_backups")
    else:
        backup_key = "windows_backup_path" if os.name == "nt" and config.get("windows_backup_path") else "backup_path"
        raw_backup = config.get(backup_key)
        if not isinstance(raw_backup, str):
            backup_root = runtime_root.with_name(runtime_root.name + "_backups")
        else:
            backup_root = expand_config_path(raw_backup)
    layout = config.get("layout")
    if layout not in {"flat", "category"}:
        raise ReleaseError(f"invalid target layout: {target_name}={layout}")
    ensure_unprotected_path(runtime_root)
    ensure_unprotected_path(backup_root)
    return runtime_root, backup_root, layout


def destination_for(runtime_root: Path, layout: str, target_config: dict[str, Any], skill: dict[str, Any]) -> Path:
    if layout == "flat":
        destination = runtime_root / skill["name"]
    else:
        category = skill.get("category") or target_config.get("default_category")
        if not isinstance(category, str) or not SKILL_NAME_PATTERN.fullmatch(category):
            raise ReleaseError(f"invalid skill category: {category}")
        destination = runtime_root / category / skill["name"]
    ensure_unprotected_path(destination)
    return destination


def remove_link_or_directory(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink():
        path.unlink()
        return
    if os.name == "nt" and path.is_dir() and path.resolve() != path.absolute():
        completed = subprocess.run(["cmd", "/c", "rmdir", str(path)], capture_output=True, text=True)
        if completed.returncode != 0:
            raise ReleaseError(f"failed to remove junction: {path}: {completed.stderr.strip()}")
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def create_directory_link(destination: Path, target: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(destination), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise ReleaseError(f"directory link unavailable: {destination}: {completed.stdout}{completed.stderr}")
    else:
        os.symlink(target, destination, target_is_directory=True)


def paths_equal(first: Path, second: Path) -> bool:
    first_value = os.path.normcase(str(first.resolve()))
    second_value = os.path.normcase(str(second.resolve()))
    return first_value == second_value


def is_directory_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = path.stat(follow_symlinks=False).st_file_attributes
    except (FileNotFoundError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def path_entry_is_within(path: Path, root: Path) -> bool:
    physical_path = path.parent.resolve() / path.name
    try:
        physical_path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def install_runtime_link(destination: Path, target: Path, backup_root: Path) -> LinkChange:
    if (destination.exists() or destination.is_symlink()) and paths_equal(destination, target):
        return LinkChange(destination, None, False)
    backup: Path | None = None
    if destination.exists() or destination.is_symlink():
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = backup_root / f"{destination.name}_{stamp}_{uuid.uuid4().hex[:8]}"
        os.replace(destination, backup)
        print(f"BACKUP {destination} -> {backup}")
    try:
        create_directory_link(destination, target)
        if not paths_equal(destination, target):
            raise ReleaseError(f"runtime link target mismatch: {destination}")
        if not (destination / "SKILL.md").is_file():
            raise ReleaseError(f"runtime link is missing SKILL.md: {destination}")
        print(f"LINKED {destination} -> {target}")
        return LinkChange(destination, backup, True)
    except Exception:
        remove_link_or_directory(destination)
        if backup is not None and backup.exists():
            os.replace(backup, destination)
            print(f"ROLLBACK {backup} -> {destination}")
        raise


def backup_existing(destination: Path, backup_root: Path, skill_name: str) -> LinkChange:
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = backup_root / f"{skill_name}_{stamp}_{uuid.uuid4().hex[:8]}"
    os.replace(destination, backup)
    print(f"BACKUP {destination} -> {backup}")
    return LinkChange(destination, backup, True)


def rollback_link_changes(changes: list[LinkChange]) -> None:
    for change in reversed(changes):
        if not change.changed:
            continue
        remove_link_or_directory(change.destination)
        if change.backup is not None and change.backup.exists():
            os.replace(change.backup, change.destination)
            print(f"ROLLBACK {change.backup} -> {change.destination}")


def build_link_plans(
    manifest: dict[str, Any],
    target_names: list[str],
    runtime_overrides: dict[str, Path],
    backup_overrides: dict[str, Path],
    local_release: Path,
) -> list[LinkPlan]:
    plans: list[LinkPlan] = []
    destinations: set[str] = set()
    for target_name in target_names:
        runtime_root, backup_root, layout = target_paths(manifest, target_name, runtime_overrides, backup_overrides)
        target_config = manifest["targets"][target_name]
        for skill in manifest.get("skills", []):
            validate_skill_name(skill.get("name", ""))
            if target_name not in skill.get("targets", []):
                continue
            source = local_release / "skills" / skill["name"]
            if not (source / "SKILL.md").is_file():
                raise ReleaseError(f"local release skill is missing SKILL.md: {skill['name']}")
            destination = destination_for(runtime_root, layout, target_config, skill)
            destination_key = os.path.normcase(str(destination.absolute()))
            if destination_key in destinations:
                raise ReleaseError(f"duplicate runtime destination: {destination}")
            destinations.add(destination_key)
            plans.append(LinkPlan(target_name, skill["name"], destination, source, backup_root))
    return plans


def reconcile_omitted_managed_links(
    previous_manifest: dict[str, Any],
    new_manifest: dict[str, Any],
    target_names: list[str],
    previous_plans: list[LinkPlan],
) -> list[LinkChange]:
    previous_names = {
        (target_name, skill["name"])
        for target_name in target_names
        for skill in previous_manifest.get("skills", [])
        if target_name in skill.get("targets", [])
    }
    expected_names = {
        (target_name, skill["name"])
        for target_name in target_names
        for skill in new_manifest.get("skills", [])
        if target_name in skill.get("targets", [])
    }
    plans = {(plan.target_name, plan.skill_name): plan for plan in previous_plans}
    changes: list[LinkChange] = []
    try:
        for key in sorted(previous_names - expected_names):
            plan = plans[key]
            previous_release = plan.source.parent.parent
            if (
                is_directory_link(plan.destination)
                and not path_entry_is_within(plan.destination, previous_release)
                and paths_equal(plan.destination, plan.source)
            ):
                changes.append(backup_existing(plan.destination, plan.backup_root, plan.skill_name))
    except Exception:
        rollback_link_changes(changes)
        raise
    return changes


def verify_link_plans(plans: list[LinkPlan]) -> None:
    for plan in plans:
        if not (plan.destination.exists() or plan.destination.is_symlink()):
            raise ReleaseError(f"runtime skill link is missing: {plan.target_name}/{plan.skill_name}")
        if not paths_equal(plan.destination, plan.source):
            raise ReleaseError(
                f"runtime target is not the local verified release: {plan.target_name}/{plan.skill_name} "
                f"actual={plan.destination.resolve()}"
            )
        if not (plan.destination / "SKILL.md").is_file():
            raise ReleaseError(f"runtime skill is missing SKILL.md: {plan.target_name}/{plan.skill_name}")


def activation_options(args: argparse.Namespace) -> tuple[Path, dict[str, Path], dict[str, Path]]:
    cache_root = Path(args.cache_root).resolve() if args.cache_root else default_cache_root().resolve()
    runtime_overrides = parse_root_overrides(args.runtime_root)
    backup_overrides = parse_root_overrides(args.backup_root)
    require_test_guard_if_overridden(bool(args.cache_root or runtime_overrides or backup_overrides or getattr(args, "release_root", None)))
    ensure_unprotected_path(cache_root)
    return cache_root, runtime_overrides, backup_overrides


def activate(args: argparse.Namespace) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    release_root = Path(args.release_root).resolve() if args.release_root else repo_root.parent / "agent-skills-runtime"
    cache_root, runtime_overrides, backup_overrides = activation_options(args)
    ensure_unprotected_path(release_root)
    release_id, manifest_sha = read_active(release_root)
    source_release = release_root / "releases" / release_id
    manifest = verify_release_directory(source_release, manifest_sha)
    if manifest.get("release_id") != release_id or manifest.get("source_commit") != release_id:
        raise ReleaseError("active release identity mismatch")
    semantic_preflight(manifest.get("skills", []), manifest.get("targets", {}))
    if args.dry_run:
        print(f"DRYRUN ACTIVATE release_id={release_id} cache_root={cache_root}")
        return

    staging = cache_root / ".staging" / f"{release_id}-{uuid.uuid4().hex}"
    local_release = cache_root / "releases" / release_id
    local_active_path = cache_root / "active.json"
    previous_active = local_active_path.read_bytes() if local_active_path.is_file() else None
    previous_manifest: dict[str, Any] | None = None
    previous_release: Path | None = None
    if previous_active is not None:
        previous_release_id, previous_manifest_sha = read_active(cache_root)
        previous_release = cache_root / "releases" / previous_release_id
        previous_manifest = verify_release_directory(previous_release, previous_manifest_sha, require_immutable=True)
        if (
            previous_manifest.get("release_id") != previous_release_id
            or previous_manifest.get("source_commit") != previous_release_id
        ):
            raise ReleaseError("previous local active release identity mismatch")
    staging.parent.mkdir(parents=True, exist_ok=True)
    promoted_local_release = False
    try:
        shutil.copytree(source_release, staging)
        verify_release_directory(staging, manifest_sha)
        local_release.parent.mkdir(parents=True, exist_ok=True)
        if local_release.exists():
            verify_release_directory(local_release, manifest_sha, require_immutable=True)
            if (local_release / "manifest.json").read_bytes() != (source_release / "manifest.json").read_bytes():
                raise ReleaseError(f"immutable local release differs: {release_id}")
        else:
            os.replace(staging, local_release)
            promoted_local_release = True
            make_local_release_immutable(local_release, manifest_sha)
        verify_release_directory(local_release, manifest_sha, require_immutable=True)
    except Exception:
        if promoted_local_release and local_release.exists():
            make_tree_writable_for_cleanup(local_release)
            shutil.rmtree(local_release)
        raise
    finally:
        if staging.exists():
            make_tree_writable_for_cleanup(staging)
            shutil.rmtree(staging)

    target_names = selected_targets(args.target)
    plans = build_link_plans(manifest, target_names, runtime_overrides, backup_overrides, local_release)
    previous_plans = (
        build_link_plans(previous_manifest, target_names, runtime_overrides, backup_overrides, previous_release)
        if previous_manifest is not None and previous_release is not None
        else []
    )
    fail_after_raw = os.environ.get("AGENT_SKILLS_TEST_FAIL_LINK_AFTER")
    fail_after: int | None = None
    if fail_after_raw is not None:
        if os.environ.get(TEST_OVERRIDE_ENV) != "1":
            raise ReleaseError(f"induced link failure requires {TEST_OVERRIDE_ENV}=1")
        try:
            fail_after = int(fail_after_raw)
        except ValueError as error:
            raise ReleaseError("AGENT_SKILLS_TEST_FAIL_LINK_AFTER must be an integer") from error
        if fail_after < 0:
            raise ReleaseError("AGENT_SKILLS_TEST_FAIL_LINK_AFTER must be non-negative")

    changes: list[LinkChange] = []
    try:
        if previous_manifest is not None:
            changes.extend(reconcile_omitted_managed_links(previous_manifest, manifest, target_names, previous_plans))
        for index, plan in enumerate(plans):
            if fail_after is not None and index == fail_after:
                raise ReleaseError("induced runtime link failure")
            changes.append(install_runtime_link(plan.destination, plan.source, plan.backup_root))
        verify_release_directory(local_release, manifest_sha, require_immutable=True)
        verify_link_plans(plans)
        atomic_write(
            local_active_path,
            json_bytes({"schema_version": 1, "release_id": release_id, "manifest_sha256": manifest_sha}),
        )
    except Exception:
        rollback_link_changes(changes)
        if previous_active is None:
            if local_active_path.exists():
                local_active_path.unlink()
        elif not local_active_path.is_file() or local_active_path.read_bytes() != previous_active:
            atomic_write(local_active_path, previous_active)
        raise
    print(f"ACTIVATE PASS release_id={release_id} cache={local_release} target={args.target}")


def run_self_check(skill_root: Path) -> None:
    scripts_root = skill_root / "scripts"
    candidate_suffixes = [".ps1", ".sh"] if os.name == "nt" else [".sh", ".ps1"]
    available_executables = {
        ".ps1": shutil.which("pwsh") or shutil.which("powershell"),
        ".sh": shutil.which("bash"),
    }
    found_check = False
    for suffix in candidate_suffixes:
        candidate = scripts_root / f"self-check{suffix}"
        if not candidate.is_file():
            continue
        found_check = True
        executable = available_executables[suffix]
        if not executable:
            continue
        if suffix == ".ps1":
            command = [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(candidate)]
        else:
            command = [executable, str(candidate)]
        completed = subprocess.run(command, cwd=skill_root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if completed.returncode != 0:
            raise ReleaseError(f"self-check failed: {skill_root.name}: {completed.stdout}{completed.stderr}")
        print(f"SELF_CHECK PASS skill={skill_root.name} path={candidate.relative_to(skill_root).as_posix()}")
        return
    if found_check:
        raise ReleaseError(f"no compatible self-check executable: {skill_root}")
    print(f"SELF_CHECK SKIP skill={skill_root.name}")


def verify(args: argparse.Namespace) -> None:
    cache_root, runtime_overrides, backup_overrides = activation_options(args)
    release_id, manifest_sha = read_active(cache_root)
    local_release = cache_root / "releases" / release_id
    manifest = verify_release_directory(local_release, manifest_sha, require_immutable=True)
    if manifest.get("release_id") != release_id or manifest.get("source_commit") != release_id:
        raise ReleaseError("local active release identity mismatch")
    for target_name in selected_targets(args.target):
        runtime_root, _, layout = target_paths(manifest, target_name, runtime_overrides, backup_overrides)
        target_config = manifest["targets"][target_name]
        for skill in manifest.get("skills", []):
            validate_skill_name(skill.get("name", ""))
            if target_name not in skill.get("targets", []):
                continue
            expected = local_release / "skills" / skill["name"]
            destination = destination_for(runtime_root, layout, target_config, skill)
            if not (destination.exists() or destination.is_symlink()):
                raise ReleaseError(f"runtime skill link is missing: {target_name}/{skill['name']}")
            if not paths_equal(destination, expected):
                raise ReleaseError(
                    f"runtime target is not the local verified release: {target_name}/{skill['name']} actual={destination.resolve()}"
                )
            if not (destination / "SKILL.md").is_file():
                raise ReleaseError(f"runtime skill is missing SKILL.md: {target_name}/{skill['name']}")
            if args.self_check:
                run_self_check(destination)
    print(f"VERIFY PASS release_id={release_id} target={args.target}")


def publish(args: argparse.Namespace) -> None:
    script_repo = Path(__file__).resolve().parents[1]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_repo
    release_root = Path(args.release_root).resolve() if args.release_root else repo_root.parent / "agent-skills-runtime"
    require_test_guard_if_overridden(bool(args.repo_root or args.release_root))
    ensure_unprotected_path(release_root)

    source_commit = git_output(repo_root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", source_commit):
        raise ReleaseError(f"source commit is not a full Git commit: {source_commit}")
    if git_output(repo_root, "status", "--porcelain", "--untracked-files=all"):
        raise ReleaseError("refusing to publish dirty repository")
    skills, target_configs = enabled_skills(repo_root)
    semantic_preflight(skills, target_configs)
    if args.dry_run:
        print(f"DRYRUN PUBLISH release_id={source_commit} release_root={release_root}")
        return

    staging = release_root / ".staging" / f"{source_commit}-{uuid.uuid4().hex}"
    final_release = release_root / "releases" / source_commit
    staging.mkdir(parents=True)
    try:
        copy_head_skill_snapshot(repo_root, staging, skills)
        files = payload_entries(staging, skills)
        manifest = {
            "schema_version": 1,
            "release_id": source_commit,
            "source_commit": source_commit,
            "skills": skills,
            "targets": target_configs,
            "files": files,
            "file_count": len(files),
        }
        manifest_data = json_bytes(manifest)
        (staging / "manifest.json").write_bytes(manifest_data)
        (staging / "READY").write_text(sha256_bytes(manifest_data) + "\n", encoding="utf-8")
        verify_release_directory(staging)

        final_release.parent.mkdir(parents=True, exist_ok=True)
        if final_release.exists():
            verify_release_directory(final_release)
            if (final_release / "manifest.json").read_bytes() != manifest_data:
                raise ReleaseError(f"immutable release already exists with different content: {source_commit}")
        else:
            os.replace(staging, final_release)
        manifest_sha = sha256_bytes(manifest_data)
        atomic_write(
            release_root / "active.json",
            json_bytes({"schema_version": 1, "release_id": source_commit, "manifest_sha256": manifest_sha}),
        )
        print(f"PUBLISH PASS release_id={source_commit} files={len(files)} root={final_release}")
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subcommands = result.add_subparsers(dest="command", required=True)
    publish_parser = subcommands.add_parser("publish")
    publish_parser.add_argument("--repo-root")
    publish_parser.add_argument("--release-root")
    publish_parser.add_argument("--dry-run", action="store_true")
    publish_parser.set_defaults(handler=publish)

    activate_parser = subcommands.add_parser("activate")
    activate_parser.add_argument("--release-root")
    activate_parser.add_argument("--cache-root")
    activate_parser.add_argument("--target", choices=("all", "codex", "claude", "hermes"), default="all")
    activate_parser.add_argument("--runtime-root", action="append")
    activate_parser.add_argument("--backup-root", action="append")
    activate_parser.add_argument("--dry-run", action="store_true")
    activate_parser.set_defaults(handler=activate)

    verify_parser = subcommands.add_parser("verify")
    verify_parser.add_argument("--cache-root")
    verify_parser.add_argument("--target", choices=("all", "codex", "claude", "hermes"), default="all")
    verify_parser.add_argument("--runtime-root", action="append")
    verify_parser.add_argument("--backup-root", action="append")
    verify_parser.add_argument("--self-check", action="store_true")
    verify_parser.set_defaults(handler=verify)
    return result


def main() -> int:
    try:
        arguments = parser().parse_args()
        arguments.handler(arguments)
        return 0
    except (ReleaseError, OSError, ValueError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
