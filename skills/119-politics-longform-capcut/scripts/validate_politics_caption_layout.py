#!/usr/bin/env python3
"""Validate politics-longform lower captions without using an AI reviewer."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

TARGET_CHARS_PER_LINE = 15
MAX_LINES = 1
TARGET_CHARS_PER_CUE = 15
HARD_MAX_LINE_CHARS = 15
LOWER_MODES = {"SOURCE_TTS", "NARRATION_TTS", "VIDEO100_EXPLAINER", "NONE"}
LEGACY_LOWER_MODE_ALIASES = {
    "SRT": "SRT",
    "COMMENTARY_2LINE": "VIDEO100_EXPLAINER",
}
SRT_MODES = {"SRT", "SOURCE_TTS", "NARRATION_TTS"}
WORK_NOTE_PATTERNS = (
    "주시면 되지 않을까요",
    "다음 영상을 보겠습니다",
    "이렇게 넣어주세요",
    "먼저 들려주시면 됩니다",
)


def display_length(line: str) -> int:
    return len(re.sub(r"\s+", "", line))


def caption_rows(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").strip()
    return [] if not normalized else normalized.split("\n")


def nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in caption_rows(text) if line.strip()]


def validate_caption(text: str, *, label: str, exact_two_lines: bool = False) -> list[dict[str, Any]]:
    raw_rows = caption_rows(text)
    lines = nonempty_lines(text)
    findings: list[dict[str, Any]] = []
    if any(not row.strip() for row in raw_rows):
        findings.append({"code": "CAPTION_EMPTY_LINE", "label": label})
    if not lines:
        return [{"code": "CAPTION_TEXT_EMPTY", "label": label}]
    if exact_two_lines:
        if len(lines) != 2:
            return [{"code": "COMMENTARY_REQUIRES_EXACTLY_2_LINES", "label": label, "actual": len(lines)}]
        findings: list[dict[str, Any]] = []
        for index, line in enumerate(lines, start=1):
            findings.extend(validate_caption(line, label=f"{label}:sequence={index}"))
        return findings
    if len(lines) > MAX_LINES:
        findings.append(
            {"code": "CAPTION_MAX_LINES_EXCEEDED", "label": label, "actual": len(lines), "max": MAX_LINES}
        )
    lengths = [display_length(line) for line in lines]
    if lengths and max(lengths) > HARD_MAX_LINE_CHARS:
        findings.append(
            {
                "code": "CAPTION_LINE_HARD_LIMIT_EXCEEDED",
                "label": label,
                "line_lengths": lengths,
                "hard_max": HARD_MAX_LINE_CHARS,
            }
        )
    if lengths and math.ceil(sum(lengths) / len(lengths)) > TARGET_CHARS_PER_LINE:
        findings.append(
            {
                "code": "CAPTION_AVERAGE_LINE_LENGTH_EXCEEDED",
                "label": label,
                "line_lengths": lengths,
                "average": sum(lengths) / len(lengths),
                "target": TARGET_CHARS_PER_LINE,
            }
        )
    if sum(lengths) > TARGET_CHARS_PER_CUE:
        findings.append(
            {
                "code": "CAPTION_TOTAL_CHARS_EXCEEDED",
                "label": label,
                "actual": sum(lengths),
                "target": TARGET_CHARS_PER_CUE,
            }
        )
    normalized = "\n".join(lines)
    for pattern in WORK_NOTE_PATTERNS:
        if pattern in normalized:
            findings.append({"code": "CAPTION_WORK_NOTE_EXPOSED", "label": label, "pattern": pattern})
    return findings


def parse_srt(path: Path) -> list[tuple[str, str]]:
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    if not raw:
        return []
    cues: list[tuple[str, str]] = []
    for block in re.split(r"\n{2,}", raw):
        rows = block.splitlines()
        timestamp_index = next((index for index, row in enumerate(rows) if "-->" in row), None)
        if timestamp_index is None:
            continue
        cue_id = rows[0].strip() if timestamp_index > 0 else str(len(cues) + 1)
        text = "\n".join(rows[timestamp_index + 1 :]).strip()
        cues.append((cue_id, text))
    return cues


def validate_srt(path: Path) -> list[dict[str, Any]]:
    cues = parse_srt(path)
    if not cues:
        return [{"code": "SRT_CUES_REQUIRED", "label": str(path)}]
    findings: list[dict[str, Any]] = []
    for cue_id, text in cues:
        findings.extend(validate_caption(text, label=f"{path.name}:cue={cue_id}"))
    return findings


def resolve_card_path(value: str, cards_path: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else cards_path.parent / candidate


def card_srt_paths(card: dict[str, Any], cards_path: Path, mode: str) -> list[Path]:
    if mode == "SOURCE_TTS":
        fields = ("source_srt_file", "display_srt_path", "srt_file")
    elif mode == "NARRATION_TTS":
        fields = ("narration_srt_file", "srt_file")
    else:
        fields = ("source_srt_file", "narration_srt_file", "display_srt_path", "srt_file")
    paths: list[Path] = []
    for field in fields:
        value = card.get(field)
        if not isinstance(value, str) or not value.strip():
            continue
        candidate = resolve_card_path(value, cards_path)
        if candidate not in paths:
            paths.append(candidate)
    return paths


def validate_cards(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    cards = document.get("cards")
    if not isinstance(cards, list):
        return [{"code": "CARDS_REQUIRED", "label": str(path)}]
    findings: list[dict[str, Any]] = []
    for card in cards:
        if not isinstance(card, dict):
            findings.append({"code": "CARD_OBJECT_REQUIRED", "label": str(path)})
            continue
        raw_mode = str(card.get("lower_mode", "NONE"))
        mode = LEGACY_LOWER_MODE_ALIASES.get(raw_mode, raw_mode)
        card_id = str(card.get("card_id", "?"))
        label = f"{path.name}:{card_id}"
        if mode not in LOWER_MODES and mode != "SRT":
            findings.append({"code": "CAPTION_INVALID_LOWER_MODE", "label": card_id, "mode": raw_mode})
            continue
        if mode == "NONE":
            continue
        if mode in SRT_MODES:
            references = card_srt_paths(card, path, mode)
            if not references:
                findings.append({"code": "CAPTION_SRT_REFERENCE_REQUIRED", "label": label})
                continue
            for srt in references:
                if not srt.is_file():
                    findings.append({"code": "SRT_FILE_MISSING", "label": label, "path": str(srt)})
                else:
                    findings.extend(validate_srt(srt))
            continue
        findings.extend(
            validate_caption(
                str(card.get("lower_text", "")),
                label=label,
                exact_two_lines=mode == "VIDEO100_EXPLAINER",
            )
        )
    return findings


def build_report(checked: list[str], findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "politics-longform-caption-layout.v1",
        "policy": {
            "target_chars_per_line": TARGET_CHARS_PER_LINE,
            "max_lines": MAX_LINES,
            "target_chars_per_cue": TARGET_CHARS_PER_CUE,
            "hard_max_line_chars": HARD_MAX_LINE_CHARS,
        },
        "checked": checked,
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path)
    parser.add_argument("--srt", type=Path, action="append", default=[])
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.cards is None and not args.srt:
        raise RuntimeError("CAPTION_INPUT_REQUIRED")
    findings: list[dict[str, Any]] = []
    checked: list[str] = []
    if args.cards is not None:
        if not args.cards.is_file():
            raise RuntimeError(f"CARDS_FILE_MISSING:{args.cards}")
        checked.append(str(args.cards))
        findings.extend(validate_cards(args.cards))
    for srt in args.srt:
        if not srt.is_file():
            raise RuntimeError(f"SRT_FILE_MISSING:{srt}")
        checked.append(str(srt))
        findings.extend(validate_srt(srt))
    report = build_report(checked, findings)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
