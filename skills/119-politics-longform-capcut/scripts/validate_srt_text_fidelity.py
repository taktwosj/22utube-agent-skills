#!/usr/bin/env python3
"""Verify that display SRT preserves the locked raw transcript text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ALLOWED_TRANSFORMS = {"SPLIT", "CLAMP", "LINE_BREAK", "DIALOGUE_MARKER_REMOVAL"}
DIALOGUE_MARKER_RE = re.compile(r"(?m)^\s*(?:>{1,3}|[-–—])\s*")
TIMING_RE = re.compile(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def parse_srt_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    texts: list[str] = []
    for block in re.split(r"\n{2,}", raw):
        rows = block.splitlines()
        timing_index = next((index for index, row in enumerate(rows) if TIMING_RE.search(row)), None)
        if timing_index is None:
            continue
        text = "\n".join(rows[timing_index + 1 :]).strip()
        if text:
            texts.append(text)
    return "\n".join(texts)


def normalize_text(text: str, *, remove_dialogue_markers: bool = False) -> str:
    value = unicodedata.normalize("NFKC", text)
    if remove_dialogue_markers:
        value = DIALOGUE_MARKER_RE.sub("", value)
    return re.sub(r"\s+", " ", value).strip()


def validate_pair(raw_path: Path, display_path: Path, transforms: list[str]) -> dict[str, Any]:
    invalid = [value for value in transforms if value not in ALLOWED_TRANSFORMS]
    if invalid or len(set(transforms)) != len(transforms):
        return {"status": "FAIL", "code": "DISPLAY_TRANSFORM_INVALID", "invalid": invalid}
    raw_text = parse_srt_text(raw_path)
    display_text = parse_srt_text(display_path)
    remove_markers = "DIALOGUE_MARKER_REMOVAL" in transforms
    normalized_raw = normalize_text(raw_text, remove_dialogue_markers=remove_markers)
    normalized_display = normalize_text(display_text, remove_dialogue_markers=remove_markers)
    if not normalized_raw or not normalized_display:
        return {"status": "FAIL", "code": "SOURCE_TRANSCRIPT_TEXT_EMPTY"}
    if "CLAMP" in transforms:
        matches = normalized_display in normalized_raw
    else:
        matches = normalized_display == normalized_raw
    return {
        "status": "PASS" if matches else "FAIL",
        "code": "PASS" if matches else "SOURCE_TRANSCRIPT_TEXT_CHANGED",
        "raw_text_sha256": hashlib.sha256(normalized_raw.encode("utf-8")).hexdigest().upper(),
        "display_text_sha256": hashlib.sha256(normalized_display.encode("utf-8")).hexdigest().upper(),
        "comparison": "CONTIGUOUS_SUBSTRING" if "CLAMP" in transforms else "EXACT_NORMALIZED_TEXT",
    }


def resolve(value: Any, cards_path: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    return candidate if candidate.is_absolute() else cards_path.parent / candidate


def validate_cards(cards_path: Path) -> list[dict[str, Any]]:
    document = json.loads(cards_path.read_text(encoding="utf-8"))
    cards = document.get("cards")
    if not isinstance(cards, list):
        return [{"code": "CARDS_REQUIRED", "label": str(cards_path)}]
    findings: list[dict[str, Any]] = []
    for card in cards:
        if not isinstance(card, dict) or card.get("card_type") != "SOURCE_VIDEO":
            continue
        if str(card.get("lower_mode", "NONE")) not in {"SRT", "SOURCE_TTS"}:
            continue
        card_id = str(card.get("card_id", "?"))
        raw = resolve(card.get("raw_transcript_path"), cards_path)
        display = resolve(card.get("display_srt_path") or card.get("source_srt_file"), cards_path)
        if raw is None or display is None or not raw.is_file() or not display.is_file():
            findings.append({"code": "SOURCE_TRANSCRIPT_PROVENANCE_REQUIRED", "card_id": card_id})
            continue
        expected_raw = str(card.get("raw_transcript_sha256", "")).upper()
        expected_display = str(card.get("display_srt_sha256", card.get("source_srt_sha256", ""))).upper()
        if sha256(raw) != expected_raw:
            findings.append({"code": "RAW_TRANSCRIPT_SHA256_INVALID", "card_id": card_id})
            continue
        if sha256(display) != expected_display:
            findings.append({"code": "DISPLAY_SRT_SHA256_INVALID", "card_id": card_id})
            continue
        transforms = card.get("display_transform")
        if not isinstance(transforms, list) or any(not isinstance(value, str) for value in transforms):
            findings.append({"code": "DISPLAY_TRANSFORM_INVALID", "card_id": card_id})
            continue
        result = validate_pair(raw, display, transforms)
        if result["status"] != "PASS":
            findings.append({"code": result["code"], "card_id": card_id, **result})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not args.cards.is_file():
        raise RuntimeError(f"CARDS_FILE_MISSING:{args.cards}")
    findings = validate_cards(args.cards)
    report = {
        "schema": "politics-longform-srt-text-fidelity.v1",
        "status": "PASS" if not findings else "FAIL",
        "cards": str(args.cards),
        "findings": findings,
    }
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
