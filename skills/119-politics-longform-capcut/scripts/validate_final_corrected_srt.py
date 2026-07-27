#!/usr/bin/env python3
"""Validate a user-corrected final SRT without rewriting its text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


TIMING_RE = re.compile(
    r"^(?P<sh>\d{2}):(?P<sm>\d{2}):(?P<ss>\d{2}),(?P<sms>\d{3})"
    r"\s+-->\s+"
    r"(?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2}),(?P<ems>\d{3})$"
)


def parse_time_us(match: re.Match[str], prefix: str) -> int:
    hours = int(match.group(f"{prefix}h"))
    minutes = int(match.group(f"{prefix}m"))
    seconds = int(match.group(f"{prefix}s"))
    milliseconds = int(match.group(f"{prefix}ms"))
    return ((hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds) * 1000


def parse_srt(path: Path) -> list[dict[str, object]]:
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        raise ValueError("empty SRT")

    cues: list[dict[str, object]] = []
    for block in re.split(r"\r?\n\r?\n", raw):
        lines = re.split(r"\r?\n", block)
        if len(lines) < 3:
            raise ValueError(f"invalid SRT block: {block!r}")
        try:
            index = int(lines[0].strip())
        except ValueError as exc:
            raise ValueError(f"invalid cue index: {lines[0]!r}") from exc
        timing = TIMING_RE.match(lines[1].strip())
        if timing is None:
            raise ValueError(f"invalid timing line: {lines[1]!r}")
        start_us = parse_time_us(timing, "s")
        end_us = parse_time_us(timing, "e")
        text_lines = [line.rstrip() for line in lines[2:]]
        if not any(line.strip() for line in text_lines):
            raise ValueError(f"empty cue text at index {index}")
        cues.append(
            {
                "index": index,
                "start_us": start_us,
                "end_us": end_us,
                "lines": text_lines,
                "text": "\n".join(text_lines),
            }
        )
    return cues


def load_corrections(path: Path | None) -> dict[str, object]:
    if path is None:
        return {
            "replacements": [],
            "remove_tokens": ["[콧방귀]", "[웃음]", ">>"],
            "max_occurrences": {},
        }
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("corrections JSON must be an object")
    return data


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--srt", type=Path, required=True)
    parser.add_argument("--corrections-json", type=Path)
    parser.add_argument("--expected-cue-count", type=int)
    parser.add_argument("--timeline-duration-us", type=int)
    parser.add_argument("--max-end-overflow-us", type=int, default=10_000)
    args = parser.parse_args()

    failures: list[str] = []
    details: list[dict[str, object]] = []
    try:
        cues = parse_srt(args.srt)
        corrections = load_corrections(args.corrections_json)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = {
            "status": "FAIL",
            "failures": ["INVALID_INPUT"],
            "details": [{"error": str(exc)}],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    full_text = "\n".join(str(cue["text"]) for cue in cues)

    if [cue["index"] for cue in cues] != list(range(1, len(cues) + 1)):
        failures.append("NON_SEQUENTIAL_CUE_INDEX")
    if any(int(cue["end_us"]) <= int(cue["start_us"]) for cue in cues):
        failures.append("INVALID_CUE_DURATION")
    if args.expected_cue_count is not None and len(cues) != args.expected_cue_count:
        failures.append("CUE_COUNT_MISMATCH")
        details.append(
            {
                "expected_cue_count": args.expected_cue_count,
                "actual_cue_count": len(cues),
            }
        )

    for item in corrections.get("replacements", []):
        if not isinstance(item, dict) or "from" not in item or "to" not in item:
            failures.append("INVALID_REPLACEMENT_RULE")
            continue
        old = str(item["from"])
        new = str(item["to"])
        if old and old in full_text:
            failures.append("FORBIDDEN_OLD_TEXT_PRESENT")
            details.append({"from": old, "to": new, "reason": "old_text_present"})
        if new and new not in full_text:
            failures.append("REQUIRED_CORRECTED_TEXT_MISSING")
            details.append({"from": old, "to": new, "reason": "new_text_missing"})

    for token in corrections.get("remove_tokens", []):
        token = str(token)
        if token and token in full_text:
            failures.append("REMOVED_TOKEN_PRESENT")
            details.append({"token": token})

    max_occurrences = corrections.get("max_occurrences", {})
    if not isinstance(max_occurrences, dict):
        failures.append("INVALID_MAX_OCCURRENCES_RULE")
    else:
        for phrase, maximum in max_occurrences.items():
            count = full_text.count(str(phrase))
            if count > int(maximum):
                failures.append("MAX_OCCURRENCES_EXCEEDED")
                details.append(
                    {
                        "phrase": str(phrase),
                        "maximum": int(maximum),
                        "actual": count,
                    }
                )

    if args.timeline_duration_us is not None:
        overflow = int(cues[-1]["end_us"]) - args.timeline_duration_us
        if overflow > args.max_end_overflow_us:
            failures.append("TIMELINE_END_OVERFLOW")
            details.append(
                {
                    "overflow_us": overflow,
                    "maximum_us": args.max_end_overflow_us,
                }
            )

    unique_failures = list(dict.fromkeys(failures))
    report = {
        "status": "PASS" if not unique_failures else "FAIL",
        "srt": str(args.srt),
        "sha256": hashlib.sha256(args.srt.read_bytes()).hexdigest().upper(),
        "cue_count": len(cues),
        "failures": unique_failures,
        "details": details,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not unique_failures else 1


if __name__ == "__main__":
    sys.exit(main())
