#!/usr/bin/env bash
set -euo pipefail

TARGET="all"
PRUNE="0"
DRY_RUN="0"
ONLY=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --only)
      ONLY+=("$2")
      shift 2
      ;;
    --prune)
      PRUNE="1"
      shift
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  all|codex|claude|hermes) ;;
  *)
    echo "Invalid target: $TARGET" >&2
    exit 2
    ;;
esac

if [ "$PRUNE" = "1" ] && [ "${#ONLY[@]}" -gt 0 ]; then
  echo "--only and --prune cannot be used together." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$REPO_ROOT" "$TARGET" "$PRUNE" "$DRY_RUN" "${ONLY[@]}" <<'PY'
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
target_arg = sys.argv[2]
prune = sys.argv[3] == "1"
dry_run = sys.argv[4] == "1"
only = sys.argv[5:]

skill_set = json.loads((repo_root / "manifests" / "skill-set.json").read_text(encoding="utf-8"))
targets = json.loads((repo_root / "manifests" / "targets.json").read_text(encoding="utf-8"))["targets"]

if target_arg == "all":
    selected_targets = ["codex", "claude", "hermes"]
else:
    selected_targets = [target_arg]

skills = [s for s in skill_set["skills"] if s.get("enabled") is True]
if only:
    requested = set(only)
    skills = [s for s in skills if s["name"] in requested]
    found = {s["name"] for s in skills}
    missing = sorted(requested - found)
    if missing:
        raise SystemExit(f"Unknown or disabled skill in --only: {', '.join(missing)}")

def expand_managed_path(value: str) -> Path:
    if value.startswith("$HOME"):
        suffix = value[5:].lstrip("/\\")
        return (Path.home() / suffix).resolve()
    return Path(value).expanduser().resolve()

def source_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "uncommitted"

def directory_hash(path: Path) -> str:
    rows = []
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = file_path.relative_to(path).as_posix()
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().upper()
        rows.append(f"{relative}\t{file_hash}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest().upper()

def target_skill_path(config: dict, skill_name: str) -> Path:
    root = expand_managed_path(config["path"])
    if config.get("layout") == "category":
        return root / config["default_category"] / skill_name
    return root / skill_name

def backup_existing(existing: Path, backup_root: Path, skill_name: str, stamp: str) -> None:
    if not existing.exists():
        return
    backup = backup_root / f"{skill_name}_{stamp}"
    if dry_run:
        print(f"DRYRUN BACKUP {existing} -> {backup}")
        return
    backup_root.mkdir(parents=True, exist_ok=True)
    shutil.move(str(existing), str(backup))
    print(f"BACKUP {existing} -> {backup}")

def copy_skill(source: Path, destination: Path) -> None:
    if dry_run:
        print(f"DRYRUN COPY {source} -> {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    print(f"SYNCED {destination}")

def write_marker(config: dict, destination: Path, skill_name: str, target_name: str, commit: str, src_hash: str) -> None:
    marker_path = destination / config["state_file"]
    marker = {
        "repo": skill_set["repo_name"],
        "skill": skill_name,
        "target": target_name,
        "installed_at": datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(),
        "source_commit": commit,
        "source_sha256": src_hash,
    }
    if dry_run:
        print(f"DRYRUN MARKER {marker_path}")
        return
    marker_path.write_text(json.dumps(marker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"MARKER {marker_path}")

def prune_target(config: dict, expected_names: set[str], stamp: str) -> None:
    root = expand_managed_path(config["path"])
    scan_root = root / config["default_category"] if config.get("layout") == "category" else root
    if not scan_root.exists():
        return
    backup_root = expand_managed_path(config["backup_path"])
    marker_name = config["state_file"]
    for child in sorted(p for p in scan_root.iterdir() if p.is_dir()):
        if child.name in expected_names:
            continue
        if not (child / marker_name).exists():
            continue
        backup = backup_root / f"PRUNED_{child.name}_{stamp}"
        if dry_run:
            print(f"DRYRUN PRUNE {child} -> {backup}")
            continue
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(child), str(backup))
        print(f"PRUNED {child} -> {backup}")

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
commit = source_commit()

for target_name in selected_targets:
    if target_name not in targets:
        raise SystemExit(f"Missing target config: {target_name}")
    config = targets[target_name]
    target_skills = [s for s in skills if target_name in s["targets"]]
    for skill in target_skills:
        source = repo_root / "skills" / skill["name"]
        if not (source / "SKILL.md").exists():
            raise SystemExit(f"Missing source skill: {skill['name']}")
        destination = target_skill_path(config, skill["name"])
        backup_root = expand_managed_path(config["backup_path"])
        src_hash = directory_hash(source)
        backup_existing(destination, backup_root, skill["name"], stamp)
        copy_skill(source, destination)
        write_marker(config, destination, skill["name"], target_name, commit, src_hash)
    if prune:
        prune_target(config, {s["name"] for s in target_skills}, stamp)

print(f"DONE install target={target_arg} dry_run={dry_run}")
PY
