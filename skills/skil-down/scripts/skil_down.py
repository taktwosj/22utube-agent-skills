#!/usr/bin/env python3
"""Install Git-managed Codex skills into the current user's runtime skill folder."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set


IGNORE_PATTERNS = (".git", "__pycache__", ".DS_Store")


def is_url(value: str) -> bool:
    return bool(re.match(r"^https?://", value, flags=re.IGNORECASE))


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def has_skill_md(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").is_file()


def discover_skill_dirs(source_root: Path) -> List[Path]:
    if has_skill_md(source_root):
        return [source_root]

    skills: List[Path] = []
    if not source_root.is_dir():
        return skills

    for child in sorted(source_root.iterdir(), key=lambda p: p.name.lower()):
        if child.name.startswith("_backup_"):
            continue
        if has_skill_md(child):
            skills.append(child)
    return skills


def looks_like_source_root(path: Path) -> bool:
    return bool(discover_skill_dirs(path))


def unique_paths(paths: List[Path]) -> List[Path]:
    seen: Set[str] = set()
    unique: List[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def candidate_source_paths() -> List[Path]:
    candidates: List[Path] = []

    env_source = os.environ.get("CODEX_SKILLS_SOURCE")
    if env_source:
        candidates.append(expand_path(env_source))

    home = Path.home()
    candidates.append(home / "agent-skills" / "skills")

    for start in (Path.cwd(), Path(__file__).resolve()):
        current = start if start.is_dir() else start.parent
        for parent in (current, *current.parents):
            candidates.append(parent / "agent-skills" / "skills")

    return unique_paths(candidates)


def find_default_source() -> Optional[Path]:
    for candidate in candidate_source_paths():
        try:
            if looks_like_source_root(candidate):
                return candidate.resolve()
        except OSError:
            continue
    return None


def find_skill_root(extracted_root: Path) -> Path:
    if looks_like_source_root(extracted_root):
        return extracted_root

    child_candidates = [p for p in extracted_root.iterdir() if p.is_dir()]
    for child in sorted(child_candidates, key=lambda p: p.name.lower()):
        if looks_like_source_root(child):
            return child

    raise SystemExit(f"ERROR no SKILL.md folders found in extracted source: {extracted_root}")


def materialize_source(source: Optional[str], temp_root: Path) -> Path:
    if not source:
        found = find_default_source()
        if found:
            return found
        raise SystemExit(
            "ERROR source not found. Pass --source pointing to $HOME/agent-skills/skills."
        )

    if is_url(source):
        zip_path = temp_root / "skills_source.zip"
        print(f"DOWNLOAD {source}")
        with urllib.request.urlopen(source) as response, zip_path.open("wb") as output:
            shutil.copyfileobj(response, output)
        return extract_zip(zip_path, temp_root)

    source_path = expand_path(source)
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        return extract_zip(source_path, temp_root)

    if not source_path.exists():
        raise SystemExit(f"ERROR source does not exist: {source_path}")

    if not looks_like_source_root(source_path):
        raise SystemExit(f"ERROR no SKILL.md folders found under source: {source_path}")

    return source_path


def extract_zip(zip_path: Path, temp_root: Path) -> Path:
    extract_root = temp_root / "extracted"
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_root)
    return find_skill_root(extract_root)


def default_target_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return expand_path(codex_home) / "skills"
    return Path.home() / ".codex" / "skills"


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def backup_destination(backup_root: Path, skill_name: str, stamp: str) -> Path:
    candidate = backup_root / f"{skill_name}_{stamp}"
    if not candidate.exists():
        return candidate

    index = 2
    while True:
        candidate = backup_root / f"{skill_name}_{stamp}_{index}"
        if not candidate.exists():
            return candidate
        index += 1


def parse_selected_skills(values: List[str]) -> Set[str]:
    selected: Set[str] = set()
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                selected.add(item)
    return selected


def sync_skills(
    source_root: Path,
    target_root: Path,
    selected: Set[str],
    dry_run: bool,
    list_only: bool,
) -> int:
    skill_dirs = discover_skill_dirs(source_root)
    if selected:
        available = {skill.name for skill in skill_dirs}
        missing = sorted(selected - available)
        if missing:
            raise SystemExit(f"ERROR selected skill not found in source: {', '.join(missing)}")
        skill_dirs = [skill for skill in skill_dirs if skill.name in selected]

    if not skill_dirs:
        raise SystemExit(f"ERROR no skills to sync from source: {source_root}")

    if list_only:
        for skill in skill_dirs:
            print(skill.name)
        return 0

    source_root_resolved = source_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    target_root_resolved = target_root.resolve()

    if source_root_resolved == target_root_resolved:
        raise SystemExit("ERROR source and target are the same folder")

    backup_root = target_root.parent / "skills_backups"
    if not dry_run:
        backup_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    synced: List[str] = []
    backups: List[str] = []

    for skill_dir in skill_dirs:
        destination = target_root / skill_dir.name
        skill_resolved = skill_dir.resolve()
        destination_resolved = destination.resolve() if destination.exists() else destination

        if skill_resolved == destination_resolved:
            raise SystemExit(f"ERROR source and destination are the same skill folder: {skill_dir.name}")
        if is_relative_to(destination_resolved, skill_resolved):
            raise SystemExit(f"ERROR destination would be inside source skill folder: {destination}")
        if destination.exists() and is_relative_to(skill_resolved, destination_resolved):
            raise SystemExit(f"ERROR source skill folder is inside destination: {skill_dir}")

        if dry_run:
            action = "UPDATE" if destination.exists() else "INSTALL"
            print(f"DRY-RUN {action} {skill_dir.name} -> {destination}")
            continue

        if destination.exists():
            backup = backup_destination(backup_root, skill_dir.name, stamp)
            shutil.move(str(destination), str(backup))
            backups.append(str(backup))
            print(f"BACKUP {skill_dir.name} -> {backup}")

        shutil.copytree(
            skill_dir,
            destination,
            ignore=shutil.ignore_patterns(*IGNORE_PATTERNS),
        )
        synced.append(skill_dir.name)
        print(f"SYNCED {skill_dir.name}")

    print(f"DONE source={source_root}")
    print(f"DONE target={target_root}")
    if backups:
        print(f"DONE backups={backup_root}")
    if synced:
        print("DONE synced=" + ", ".join(synced))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install Git-managed Codex skills into ~/.codex/skills."
    )
    parser.add_argument(
        "--source",
        help="Source folder, local .zip, or .zip URL. Defaults to $HOME/agent-skills/skills.",
    )
    parser.add_argument(
        "--target",
        help="Target Codex skills folder. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Skill name to sync. Repeat or pass comma-separated names. Defaults to all source skills.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without copying.")
    parser.add_argument("--list", action="store_true", help="List source skill names and exit.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    selected = parse_selected_skills(args.skill)
    target_root = expand_path(args.target) if args.target else default_target_root()

    with tempfile.TemporaryDirectory(prefix="skil-down-") as temp_dir:
        source_root = materialize_source(args.source, Path(temp_dir)).resolve()
        return sync_skills(source_root, target_root, selected, args.dry_run, args.list)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("ERROR interrupted", file=sys.stderr)
        raise SystemExit(130)
