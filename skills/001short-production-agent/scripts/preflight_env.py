#!/usr/bin/env python3
"""One-time environment preflight for 001short episodes.

Verifies required media tools exist AND actually execute (freeze detection),
then writes a receipt that episodes read instead of re-discovering tools.
This script never installs anything: installs happen in the user's own
terminal only (agent-shell installs get macOS quarantine-tagged and freeze
at _dyld_start; see references/environment-preflight.md).
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import platform
import shutil
import subprocess
import sys

RECEIPT_PATH = os.path.expanduser("~/.cache/22utube/001short_env_receipt.json")
RECEIPT_MAX_AGE_DAYS = 7
EXTRA_PATHS = ("/opt/homebrew/bin", "/usr/local/bin")
EXEC_TIMEOUT_SEC = 10

REQUIRED_TOOLS = {
    "yt-dlp": ["--version"],
    "ffmpeg": ["-version"],
    "ffprobe": ["-version"],
}
# Optional: absence is recorded, never fatal. Demucs only matters for the
# type 3/4/5 stem paths; OCR/STT engines may be replaced by direct review.
OPTIONAL_TOOLS = {
    "tesseract": ["--version"],
    "whisper": ["--help"],
    "demucs": ["--help"],
}


def _which(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for base in EXTRA_PATHS:
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _quarantine_agent(path: str) -> str | None:
    try:
        out = subprocess.run(
            ["xattr", "-p", "com.apple.quarantine", os.path.realpath(path)],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    parts = out.stdout.strip().split(";")
    return parts[2] if len(parts) > 2 and parts[2] else "unknown"


def _check(name: str, args: list[str]) -> dict:
    path = _which(name)
    if not path:
        return {"status": "MISSING", "path": None, "version": None}
    try:
        run = subprocess.run(
            [path, *args], capture_output=True, text=True, timeout=EXEC_TIMEOUT_SEC
        )
        first_line = (run.stdout or run.stderr).strip().splitlines()
        return {
            "status": "PASS",
            "path": path,
            "version": first_line[0][:120] if first_line else "",
        }
    except subprocess.TimeoutExpired:
        agent = _quarantine_agent(path)
        return {
            "status": "FROZEN",
            "path": path,
            "version": None,
            "quarantine_agent": agent,
        }
    except Exception as exc:  # noqa: BLE001 - report, never crash preflight
        return {"status": "ERROR", "path": path, "version": None, "error": str(exc)[:200]}


def receipt_is_fresh() -> bool:
    try:
        with open(RECEIPT_PATH, "r", encoding="utf-8") as fh:
            receipt = json.load(fh)
        if receipt.get("overall_status") != "PASS":
            return False
        checked = _dt.datetime.fromisoformat(receipt["checked_at"])
        age = _dt.datetime.now(_dt.timezone.utc) - checked
        return age.days < RECEIPT_MAX_AGE_DAYS
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    if "--require-fresh" in sys.argv:
        if receipt_is_fresh():
            print(f"PREFLIGHT PASS (cached receipt) {RECEIPT_PATH}")
            return 0
        print("PREFLIGHT STALE: rerun without --require-fresh to refresh")
        return 1

    tools: dict[str, dict] = {}
    for name, args in REQUIRED_TOOLS.items():
        tools[name] = {**_check(name, args), "required": True}
    for name, args in OPTIONAL_TOOLS.items():
        tools[name] = {**_check(name, args), "required": False}

    problems = [n for n, t in tools.items() if t["required"] and t["status"] != "PASS"]
    overall = "PASS" if not problems else "FAIL"

    receipt = {
        "schema_version": "001short-env-receipt-v1",
        "checked_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "host": platform.node(),
        "platform": platform.platform(),
        "overall_status": overall,
        "tools": tools,
    }
    os.makedirs(os.path.dirname(RECEIPT_PATH), exist_ok=True)
    with open(RECEIPT_PATH, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, ensure_ascii=False, indent=2)

    for name, tool in tools.items():
        marker = "" if tool["required"] else " (optional)"
        print(f"{tool['status']:7s} {name}{marker}: {tool.get('path') or '-'}")

    if overall == "PASS":
        print(f"PREFLIGHT PASS → {RECEIPT_PATH}")
        return 0

    print("PREFLIGHT FAIL — fix in the USER'S OWN TERMINAL (never the agent shell):")
    for name in problems:
        tool = tools[name]
        if tool["status"] == "MISSING":
            print(f"  {name}: brew install {'yt-dlp' if name == 'yt-dlp' else 'ffmpeg'}")
        elif tool["status"] == "FROZEN":
            agent = tool.get("quarantine_agent")
            print(
                f"  {name}: execution frozen"
                + (f" (quarantined by {agent})" if agent else "")
                + " → run: sudo xattr -dr com.apple.quarantine /opt/homebrew/Cellar"
                + "  then REBOOT (xattr removal alone does not clear the kernel queue)"
            )
    return 1


if __name__ == "__main__":
    sys.exit(main())
