"""Validate the required Paperclip task receipt before a 001 episode starts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = {
    "company": "쇼츠팩토리 P0", "active_writer_machine": "macmini",
    "coordinator": "P0-총괄", "producer": "P0-제작", "verifier": "P0-검증",
}


def validate(entry_path: Path, episode_id: str, skill_root: Path) -> dict:
    try:
        entry = json.loads(entry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "WAIT", "errors": [{"code": "PAPERCLIP_ENTRY_MISSING", "detail": str(exc)}]}
    errors = []
    if entry.get("episode_id") != episode_id:
        errors.append({"code": "PAPERCLIP_ENTRY_EPISODE_MISMATCH"})
    for field, expected in REQUIRED.items():
        if entry.get(field) != expected:
            errors.append({"code": "PAPERCLIP_ENTRY_FIELD_INVALID", "field": field, "expected": expected})
    if not isinstance(entry.get("paperclip_issue_id"), str) or not entry["paperclip_issue_id"].strip():
        errors.append({"code": "PAPERCLIP_ISSUE_MISSING"})
    expected_sha = hashlib.sha256((skill_root / "SKILL.md").read_bytes()).hexdigest()
    if entry.get("source_skill_md_sha256", "").lower() != expected_sha.lower():
        errors.append({"code": "PAPERCLIP_SKILL_SHA_MISMATCH"})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "paperclip_issue_id": entry.get("paperclip_issue_id")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", type=Path, required=True)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = validate(args.entry, args.episode_id, args.skill_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else (3 if result["status"] == "WAIT" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
