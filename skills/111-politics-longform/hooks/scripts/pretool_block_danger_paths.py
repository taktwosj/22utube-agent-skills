#!/usr/bin/env python3
"""Claude hook wrapper: block dangerous paths before tool execution."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ONEDRIVE_ROOT = "c:/users/arajun/onedrive/22utube"
CAPCUT_ROOT = "c:/users/arajun/appdata/local/capcut/user data/projects/com.lveditor.draft"
JUNGCHILONG = f"{CAPCUT_ROOT}/jungchilong"

WRITE_VERBS = re.compile(
    r"\b(copy-item|move-item|remove-item|set-content|add-content|out-file|new-item|"
    r"rename-item|del|erase|rm|mv|cp|mkdir|touch|write|edit|apply_patch)\b",
    re.IGNORECASE,
)

DIRECT_JUNGCHILONG_WRITE = re.compile(
    r"\b(remove-item|set-content|add-content|out-file|new-item|rename-item|"
    r"del|erase|rm|mv|mkdir|touch)\b[\s\S]{0,240}jungchilong",
    re.IGNORECASE,
)


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


def norm(text: str) -> str:
    return text.replace("\\", "/").lower()


def looks_pathish(text: str) -> bool:
    s = norm(text)
    return (":/" in s) or ("/" in s) or ("\\" in text)


def pathish_strings(value: Any) -> list[str]:
    return [norm(s) for s in flatten_strings(value) if looks_pathish(s)]


def touched_file_paths(tool_input: dict[str, Any]) -> list[str]:
    keys = (
        "file_path", "path", "target_file", "target_path", "destination",
        "dest", "output", "workdir",
    )
    out: list[str] = []
    for key in keys:
        value = tool_input.get(key)
        if isinstance(value, str):
            out.append(norm(value))
    return out


def deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    return 2


def main() -> int:
    data = read_input()
    tool_input = data.get("tool_input", {}) if isinstance(data.get("tool_input"), dict) else {}
    command = norm(str(tool_input.get("command", "")))
    path_haystack = "\n".join(pathish_strings(data))
    touched_paths = touched_file_paths(tool_input)
    is_writeish = bool(WRITE_VERBS.search(command)) or data.get("tool_name") in {"Edit", "Write", "MultiEdit"}

    if not is_writeish:
        return 0

    dangerous_onedrive_parts = [
        "/.codex",
        "/.claude",
        "/.agents",
        "/codex_skills",
        "/agent-skills",
        "/skills/",
    ]
    if ONEDRIVE_ROOT in path_haystack and any(part in path_haystack for part in dangerous_onedrive_parts):
        return deny("OneDrive production tree must not contain runtime folders, .codex, .claude, .agents, or Git-source mirrors.")

    if any(path.startswith(JUNGCHILONG) for path in touched_paths) or DIRECT_JUNGCHILONG_WRITE.search(command):
        return deny("jungchilong is a locked visual skeleton. Copy it first; do not patch the base directly.")

    if CAPCUT_ROOT in path_haystack and "/yp007" in path_haystack:
        return deny("Legacy YP007 drafts are not allowed as the politics-longform base.")

    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
