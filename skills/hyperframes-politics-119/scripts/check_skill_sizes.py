"""Read-only UTF-8 byte size audit. Oversized files WARN, never fail the run."""
import argparse
import json
from pathlib import Path

SKILLS = ("spine-script-119", "119-politics-longform-capcut",
          "hyperframes-politics-119", "togun-politics-pre119-writer")
LIMITS = {"skill": 8 * 1024, "reference": 6 * 1024, "python": 15 * 1024}


def audit(root, skills=SKILLS):
    records = []
    for name in skills:
        folder = Path(root) / name
        if not (folder / "SKILL.md").is_file():
            raise FileNotFoundError(f"SKILL_MISSING: {folder / 'SKILL.md'}")
        for path in sorted(folder.rglob("*")):
            relative = path.relative_to(folder)
            if any(part.startswith('.') or part in ('tests', '__pycache__')
                   for part in relative.parts):
                continue
            kind = None
            if relative.as_posix() == "SKILL.md":
                kind = "skill"
            elif relative.parts[0] == "references" and path.suffix == ".md":
                kind = "reference"
            elif relative.parts[0] == "scripts" and path.suffix == ".py" and not path.name.startswith("test_"):
                kind = "python"
            if kind and path.is_file():
                size = len(path.read_bytes())
                records.append({"file": f"{name}/{relative.as_posix()}",
                                "bytes": size, "limit_bytes": LIMITS[kind],
                                "status": "WARN" if size > LIMITS[kind] else "PASS"})
    return {"size_metric": "UTF8_BYTES", "status": "WARN" if any(
        row["status"] == "WARN" for row in records) else "PASS", "files": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--skills", nargs="+", default=SKILLS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(args.skills_root, args.skills)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"SIZE_AUDIT_ERROR: {exc}\n")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        warnings = [r for r in result["files"] if r["status"] == "WARN"]
        for row in warnings:
            print(f"WARN {row['file']}: {row['bytes']}B > {row['limit_bytes']}B")
        print(f"SIZE_AUDIT {result['status']}: {len(result['files'])} files, {len(warnings)} warnings; exit=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
