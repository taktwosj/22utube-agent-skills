#!/usr/bin/env python3
"""Claude hook wrapper: block false FINAL/PASS/upload_ready claims."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


COMPLETION_TERMS = re.compile(
    r"(FINAL|upload_ready|production PASS|검증 통과|최종 ?완료|작업 ?완료|완료했습니다)",
    re.IGNORECASE,
)
PASS_TERMS = re.compile(r"\bPASS\b", re.IGNORECASE)
POLITICS_CONTEXT = re.compile(
    r"(정치롱폼|CapCut|캣컷|캣컵|final_harness|production|upload_ready|Stage ?2)",
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


def find_episode_dir(candidates: list[str]) -> Path | None:
    for text in candidates:
        p = Path(text)
        if not p.exists():
            continue
        current = p if p.is_dir() else p.parent
        for parent in [current, *current.parents]:
            if (parent / "90_reports").exists() and (parent / "episode_manifest.json").exists():
                return parent
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "90_reports").exists() and (parent / "episode_manifest.json").exists():
            return parent
    return None


def block(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "decision": "block",
            "reason": reason,
        }
    }, ensure_ascii=False))
    return 2


def completion_claim_detected(text: str) -> bool:
    if COMPLETION_TERMS.search(text):
        return True
    return bool(PASS_TERMS.search(text) and POLITICS_CONTEXT.search(text))


def main() -> int:
    data = read_input()
    strings = flatten_strings(data)
    text = "\n".join(strings)
    if not completion_claim_detected(text):
        return 0

    episode_dir = find_episode_dir(strings)
    if not episode_dir:
        return block("Completion claim detected, but no episode folder with final harness was found.")

    harness = episode_dir / "90_reports" / "final_harness_report.json"
    if not harness.exists():
        return block(f"Completion claim blocked: missing {harness}.")

    try:
        report = json.loads(harness.read_text(encoding="utf-8"))
    except Exception as exc:
        return block(f"Completion claim blocked: final_harness_report.json is unreadable: {exc}")

    if str(report.get("status", "")).upper() != "PASS":
        return block(f"Completion claim blocked: final harness status is {report.get('status')!r}, not PASS.")

    report_text = json.dumps(report, ensure_ascii=False)
    if "preview_visual" not in report_text and "frame" not in report_text.lower():
        return block("Completion claim blocked: final harness lacks frame/preview evidence.")

    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
