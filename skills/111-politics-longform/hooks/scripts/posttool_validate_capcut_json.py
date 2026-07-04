#!/usr/bin/env python3
"""Claude hook wrapper: validate touched CapCut draft after tool execution."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


CAPCUT_SENTINELS = {"draft_content.json", "template-2.tmp", "draft_meta_info.json"}


def read_input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(flatten_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(flatten_strings(item))
        return out
    return []


def maybe_paths(strings: list[str]) -> list[Path]:
    paths: list[Path] = []
    for text in strings:
        for token in text.replace('"', " ").replace("'", " ").split():
            normalized = token.strip()
            if not normalized:
                continue
            if any(name in normalized for name in CAPCUT_SENTINELS) or "com.lveditor.draft" in normalized:
                paths.append(Path(normalized))
    return paths


def find_draft_root(path: Path) -> Path | None:
    current = path if path.is_dir() else path.parent
    for parent in [current, *current.parents]:
        if (parent / "draft_content.json").exists() and (parent / "template-2.tmp").exists():
            return parent
        if parent.parent == parent:
            break
    return None


def block(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "decision": "block",
            "reason": reason,
        }
    }, ensure_ascii=False))
    return 2


def main() -> int:
    data = read_input()
    tool_name = data.get("tool_name")
    if tool_name not in {"Bash", "Edit", "Write", "MultiEdit"}:
        return 0

    roots = []
    for path in maybe_paths(flatten_strings(data)):
        root = find_draft_root(path)
        if root and root not in roots and root.name.lower() != "jungchilong":
            roots.append(root)

    if not roots:
        return 0

    script = Path(__file__).resolve().parents[2] / "scripts" / "validate_politics_longform_draft.py"
    failures = []
    for root in roots:
        proc = subprocess.run(
            [sys.executable, str(script), "--draft", str(root)],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            failures.append(f"{root}: {proc.stdout or proc.stderr}")

    if failures:
        return block("CapCut draft validation failed after tool use:\n" + "\n".join(failures))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
