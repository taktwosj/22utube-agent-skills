#!/usr/bin/env python3
"""Offline structural check for the thin 001short router."""
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "SKILL.md"
REQUIRED_STAGES = {f"0{number}" for number in range(1, 10)}
REQUIRED_SELF_CHECK = "Run `python -B scripts/validate_executable_protocol.py --self-check` before every routing run."


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    raw = ROUTER.read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if len(raw) > 8192:
        fail(f"router_bytes={len(raw)} exceeds 8192")
    if len(lines) > 80:
        fail(f"router_lines={len(lines)} exceeds 80")
    frontmatter = "---\nname: 001short-production-agent\ndescription: Use when an original Shorts video, user review, and Gemini analysis must become an OCR-verified original blueprint, first recommendation, VMake-clean CapCut assembly, and evidence-backed production validation.\n---"
    if not text.startswith(frontmatter):
        fail("frontmatter_changed")
    for token in ("workflow.json", "steps/<current_stage>.md", "validate_executable_protocol.py --self-check"):
        if token not in text:
            fail(f"required_router_token_missing={token}")
    if REQUIRED_SELF_CHECK not in text:
        fail("unconditional_self_check_missing")
    routes = re.findall(r"\| (0[1-9]) \| `([^`]+)` \|", text)
    if {stage for stage, _ in routes} != REQUIRED_STAGES:
        fail("default_stage_routes_are_not_01_to_09")
    paths = set(re.findall(r"`((?:references|scripts)/[^`]+)`", text))
    missing = sorted(path for path in paths if not (ROOT / path).is_file())
    if missing:
        fail("missing_routing_paths=" + ",".join(missing))
    print(f"PASS: router_bytes={len(raw)} router_lines={len(lines)} routing_paths={len(paths)}")


if __name__ == "__main__":
    main()
