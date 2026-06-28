#!/usr/bin/env bash
set -euo pipefail

TARGET="repo"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

case "$TARGET" in
  repo|all|codex|claude|hermes) ;;
  *)
    echo "Invalid target: $TARGET" >&2
    exit 2
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$REPO_ROOT" "$TARGET" <<'PY'
import hashlib
import json
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
target_arg = sys.argv[2]
errors: list[str] = []
warnings: list[str] = []

def fail(message: str) -> None:
    errors.append(message)
    print(f"FAIL {message}")

def warn(message: str) -> None:
    warnings.append(message)
    print(f"WARN {message}")

def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        fail(f"Invalid JSON: {path}")
        return None

def expand_managed_path(value: str) -> Path:
    if value.startswith("$HERMES_HOME"):
        hermes_home = os.environ.get("HERMES_HOME")
        if not hermes_home:
            raise SystemExit(f"HERMES_HOME is not set for path: {value}")
        suffix = value[12:].lstrip("/\\")
        return (Path(hermes_home) / suffix).resolve()
    if value.startswith("$LOCALAPPDATA"):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise SystemExit(f"LOCALAPPDATA is not set for path: {value}")
        suffix = value[13:].lstrip("/\\")
        return (Path(local_app_data) / suffix).resolve()
    if value.startswith("$HOME"):
        suffix = value[5:].lstrip("/\\")
        return (Path.home() / suffix).resolve()
    return Path(value).expanduser().resolve()

def target_root(config: dict) -> Path:
    return expand_managed_path(config["path"])

def selected_targets() -> list[str]:
    if target_arg == "all":
        return ["codex", "claude", "hermes"]
    if target_arg == "repo":
        return []
    return [target_arg]

def frontmatter(skill_file: Path):
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"(?s)^---\r?\n(.*?)\r?\n---", text)
    if not match:
        return None
    data = {}
    for line in re.split(r"\r?\n", match.group(1)):
        m = re.match(r"\s*([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$", line)
        if m:
            data[m.group(1)] = m.group(2).strip().strip('"')
    return data

def directory_hash(path: Path, exclude_file_name: str = "") -> str:
    rows = []
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        if exclude_file_name and file_path.name == exclude_file_name:
            continue
        relative = file_path.relative_to(path).as_posix()
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().upper()
        rows.append(f"{relative}\t{file_hash}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest().upper()

def forbidden_patterns() -> list[str]:
    return [
        "C:" + "\\Users\\",
        "C:" + "/" + "Users/",
        "/" + "Users/",
        "/" + "home/",
        "/" + "Volumes/",
    ]

def test_forbidden_content(relative_root: str, error_on_hit: bool) -> None:
    root = repo_root / relative_root
    if not root.exists():
        return
    for file_path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in forbidden_patterns():
            if pattern in text:
                rel = file_path.relative_to(repo_root).as_posix()
                if error_on_hit:
                    fail(f"blocked absolute path in {rel} pattern={pattern}")
                else:
                    warn(f"absolute path example in {rel} pattern={pattern}")
                break

def test_forbidden_names() -> None:
    forbidden_extensions = {".mp4", ".mov", ".mkv", ".avi", ".wav", ".mp3", ".m4a", ".aac", ".zip", ".7z", ".rar", ".tar", ".gz"}
    forbidden_dirs = {"node_modules", "skills_backups", ".DS_Store"}
    secret_re = re.compile(r"(?i)(^\.env$|(^|[._-])(env|key|token|cookie|session|secret|credential)([._-]|$))")
    for item in sorted(repo_root.rglob("*")):
        if ".git" in item.parts:
            continue
        rel = item.relative_to(repo_root).as_posix()
        if item.is_dir():
            if item.name.startswith("_backup") or "_backup" in item.name or item.name in forbidden_dirs:
                fail(f"forbidden directory: {rel}")
        elif item.is_file():
            if item.suffix.lower() in forbidden_extensions:
                fail(f"forbidden binary/archive file: {rel}")
            if secret_re.search(item.name):
                fail(f"secret-like file name: {rel}")

def test_repo(skill_set: dict, targets: dict) -> None:
    if skill_set.get("repo_name") != "22utube-agent-skills":
        fail("repo_name must be 22utube-agent-skills")
    skills_root = repo_root / "skills"
    for skill in [s for s in skill_set["skills"] if s.get("enabled") is True]:
        skill_dir = skills_root / skill["name"]
        skill_file = skill_dir / "SKILL.md"
        if not skill_dir.exists():
            fail(f"missing skill folder: {skill['name']}")
            continue
        if not skill_file.exists():
            fail(f"missing SKILL.md: {skill['name']}")
            continue
        fm = frontmatter(skill_file)
        if not fm:
            fail(f"missing YAML frontmatter: {skill['name']}")
        else:
            if "name" not in fm:
                fail(f"missing frontmatter name: {skill['name']}")
            if "description" not in fm:
                fail(f"missing frontmatter description: {skill['name']}")
            if fm.get("name") and fm["name"] != skill["name"]:
                fail(f"frontmatter name mismatch: folder={skill['name']} name={fm['name']}")
        count = len(list(skill_dir.rglob("SKILL.md")))
        if count != 1:
            fail(f"nested or missing SKILL.md count={count} skill={skill['name']}")
    test_forbidden_names()
    test_forbidden_content("scripts", True)
    test_forbidden_content("skills", True)
    test_forbidden_content("docs", False)
    readme = repo_root / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for pattern in forbidden_patterns():
            if pattern in text:
                warn(f"absolute path example in README.md pattern={pattern}")

def target_skill_path(config: dict, skill_name: str) -> Path:
    root = target_root(config)
    if config.get("layout") == "category":
        return root / config["default_category"] / skill_name
    return root / skill_name

def test_target(skill_set: dict, targets: dict, target_name: str) -> None:
    config = targets.get(target_name)
    if not config:
        fail(f"missing target config: {target_name}")
        return
    root = target_root(config)
    if not root.exists():
        fail(f"missing target root: {target_name} path={root}")
        return
    for skill in [s for s in skill_set["skills"] if s.get("enabled") is True and target_name in s["targets"]]:
        dest = target_skill_path(config, skill["name"])
        skill_file = dest / "SKILL.md"
        marker_path = dest / config["state_file"]
        if not skill_file.exists():
            fail(f"missing target SKILL.md target={target_name} skill={skill['name']}")
            continue
        if not marker_path.exists():
            fail(f"missing managed marker target={target_name} skill={skill['name']}")
            continue
        marker = read_json(marker_path)
        if marker:
            if marker.get("repo") != skill_set["repo_name"]:
                fail(f"marker repo mismatch target={target_name} skill={skill['name']}")
            if marker.get("skill") != skill["name"]:
                fail(f"marker skill mismatch target={target_name} skill={skill['name']}")
            if marker.get("target") != target_name:
                fail(f"marker target mismatch target={target_name} skill={skill['name']}")
        source_hash = directory_hash(repo_root / "skills" / skill["name"])
        target_hash = directory_hash(dest, config["state_file"])
        if source_hash != target_hash:
            fail(f"target hash mismatch target={target_name} skill={skill['name']} source={source_hash} target={target_hash}")
        if marker and marker.get("source_sha256") != source_hash:
            fail(f"marker source_sha256 mismatch target={target_name} skill={skill['name']}")
        print(f"SHA256 target={target_name} skill={skill['name']} source={source_hash} target={target_hash}")

skill_set = read_json(repo_root / "manifests" / "skill-set.json")
targets_file = read_json(repo_root / "manifests" / "targets.json")
targets = targets_file["targets"] if targets_file else {}

if skill_set:
    test_repo(skill_set, targets)
    for target_name in selected_targets():
        test_target(skill_set, targets, target_name)

if errors:
    print(f"VERIFY FAIL errors={len(errors)} warnings={len(warnings)}")
    raise SystemExit(1)

print(f"VERIFY PASS warnings={len(warnings)}")
PY
