#!/usr/bin/env python3
"""Scan a CapCut draft tree for dirty files, old references, and mojibake."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


DIRTY_NAME_PATTERNS = [
    re.compile(r".*\.bak(?:$|[_\-.].*)", re.IGNORECASE),
    re.compile(r"^before_", re.IGNORECASE),
    re.compile(r".*_backup_.*", re.IGNORECASE),
    re.compile(r"^\.before_", re.IGNORECASE),
    re.compile(r"^bottom_topic_comments_.*\.json$", re.IGNORECASE),
    re.compile(r"^t1_topic_texts\.json$", re.IGNORECASE),
    re.compile(r"^crypto_key_store\.dat\.bak$", re.IGNORECASE),
]

OLD_REF_PATTERNS = [
    re.compile(r"YP007", re.IGNORECASE),
    re.compile(r"YP005", re.IGNORECASE),
    re.compile(r"YM007", re.IGNORECASE),
    re.compile(r"YP_ROH_YSM_.*정치롱폼기본", re.IGNORECASE),
    re.compile(r"정치롱폼기준(?:[_\\/\-]|$)", re.IGNORECASE),
    re.compile(r"capcut_drafts[\\/]+YP_", re.IGNORECASE),
    re.compile(r"old[_\- ]?locked", re.IGNORECASE),
]

MOJIBAKE_PATTERNS = [
    re.compile("\ufffd"),
    re.compile(r"\?뺤"),
    re.compile(r"濡깊"),
    re.compile(r"罹"),
    re.compile(r"�"),
]

TEXT_SUFFIXES = {
    ".json",
    ".tmp",
    ".txt",
    ".md",
    ".srt",
    ".csv",
    ".xml",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def add(result: dict[str, Any], level: str, code: str, path: Path | str, detail: str) -> None:
    result[level].append({"code": code, "path": str(path), "detail": detail})


def scan_tree(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "PASS",
        "root": str(root),
        "errors": [],
        "warnings": [],
        "checked_files": 0,
    }

    if not root.exists():
        add(result, "errors", "MISSING_ROOT", root, "scan root does not exist")
        result["status"] = "FAIL"
        return result

    for path in root.rglob("*"):
        name = path.name
        rel = path.relative_to(root)
        for pattern in DIRTY_NAME_PATTERNS:
            if pattern.match(name):
                add(result, "errors", "DIRTY_FILE", rel, "backup/work memo file must not remain in active draft")
                break

        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            result["checked_files"] += 1
            try:
                text = read_text(path)
            except OSError as exc:
                add(result, "errors", "READ_FAILED", rel, str(exc))
                continue
            for pattern in MOJIBAKE_PATTERNS:
                if pattern.search(text):
                    add(result, "errors", "WAIT_ENCODING_UNSAFE", rel, "Korean mojibake or replacement character detected")
                    break
            normalized = str(rel).replace("\\", "/") + "\n" + text.replace("\\", "/")
            for pattern in OLD_REF_PATTERNS:
                if pattern.search(normalized):
                    add(result, "errors", "OLD_FORBIDDEN_REF", rel, f"matched {pattern.pattern}")
                    break

    if result["errors"]:
        result["status"] = "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="CapCut draft or episode tree to scan")
    args = parser.parse_args()

    result = scan_tree(Path(args.root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
