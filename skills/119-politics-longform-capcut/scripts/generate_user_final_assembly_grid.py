#!/usr/bin/env python3
"""Generate a read-only horizontal user assembly grid from episode_cards.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROWS = (
    "SEGMENT_ID", "CHAPTER_TITLE", "CARD_TYPE", "SCREEN", "VISUAL_DESIGN",
    "RENDERED_ASSET", "VIDEO_SOURCE", "SOURCE_RANGE", "SOURCE_AUDIO",
    "NARRATION_AUDIO", "NARRATION_TEXT", "SOURCE_CHANNEL", "SOURCE_DATE",
    "LOWER_MODE", "LOWER_TEXT", "CTA_LIKE_SUBSCRIBE", "WHY_THIS_SEGMENT", "STATUS",
)


def clock(microseconds: int) -> str:
    seconds = max(0, round(microseconds / 1_000_000))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def safe(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value).replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def screen_of(card_type: str) -> str:
    if card_type in {"SOURCE_VIDEO", "NARRATION_VIDEO"}:
        return "VIDEO"
    if card_type in {"CHAPTER_CARD", "NARRATION_IMAGE"}:
        return "IMAGE"
    if card_type == "INTRO":
        return "INTRO"
    if card_type == "TEXT_EXPLAINER":
        return "TEXT"
    return "ENDING"


def audio_flags(card_type: str, card: dict[str, Any]) -> tuple[str, str]:
    source = card.get("source_audio")
    narration = card.get("narration_audio")
    if source is None:
        source = "ON" if card_type == "SOURCE_VIDEO" else "OFF"
    if narration is None:
        narration = "ON" if card_type in {"NARRATION_IMAGE", "NARRATION_VIDEO"} else "OFF"
    return str(source), str(narration)


def normalize(document: dict[str, Any]) -> list[dict[str, Any]]:
    cards = document.get("cards")
    if not isinstance(cards, list) or not cards:
        raise RuntimeError("CARDS_REQUIRED")
    ordered = sorted(cards, key=lambda card: int(card["target_start_us"]))
    cursor = 0
    for card in ordered:
        start = int(card["target_start_us"])
        duration = int(card["target_duration_us"])
        if start != cursor or duration <= 0:
            raise RuntimeError(f"GRID_TIMELINE_INVALID:{card.get('card_id', '?')}")
        cursor += duration
    return ordered


def row_data(card: dict[str, Any], global_cta: Any) -> dict[str, str]:
    card_type = str(card.get("card_type", ""))
    source_audio, narration_audio = audio_flags(card_type, card)
    source_start = int(card.get("source_start_us", 0))
    source_duration = int(card.get("source_duration_us", 0))
    source_range = f"{clock(source_start)}–{clock(source_start + source_duration)}" if source_duration > 0 else "N/A"
    return {
        "SEGMENT_ID": safe(card.get("card_id")),
        "CHAPTER_TITLE": safe(card.get("chapter_title", card.get("chapter_label"))),
        "CARD_TYPE": safe(card_type),
        "SCREEN": screen_of(card_type),
        "VISUAL_DESIGN": safe(card.get("visual_design", card.get("style_profile"))),
        "RENDERED_ASSET": safe(Path(str(card["image_file"])).name if card.get("image_file") else None),
        "VIDEO_SOURCE": safe(card.get("source_id") or (Path(str(card["source_file"])).name if card.get("source_file") else None)),
        "SOURCE_RANGE": source_range,
        "SOURCE_AUDIO": safe(source_audio),
        "NARRATION_AUDIO": safe(narration_audio),
        "NARRATION_TEXT": safe(card.get("narration_text")),
        "SOURCE_CHANNEL": safe(card.get("source_channel")),
        "SOURCE_DATE": safe(card.get("source_date")),
        "LOWER_MODE": safe(card.get("lower_mode", "NONE")),
        "LOWER_TEXT": safe(card.get("lower_text")),
        "CTA_LIKE_SUBSCRIBE": safe(card.get("cta_like_subscribe", global_cta)),
        "WHY_THIS_SEGMENT": safe(card.get("why_this_segment")),
        "STATUS": "JOINED",
    }


def render(document: dict[str, Any]) -> str:
    cards = normalize(document)
    labels = [
        f"{clock(int(card['target_start_us']))}–{clock(int(card['target_start_us']) + int(card['target_duration_us']))}"
        for card in cards
    ]
    global_cta = document.get("cta_like_subscribe", "N/A")
    mapped = [row_data(card, global_cta) for card in cards]
    lines = [
        "# 119 USER FINAL ASSEMBLY GRID", "",
        "> READ-ONLY VIEW — `episode_cards.json`이 유일한 조립 정본이다.", "",
        "| 레이어 \\ 최종 시간 | " + " | ".join(labels) + " |",
        "|---|" + "|".join(["---"] * len(labels)) + "|",
    ]
    for row in ROWS:
        lines.append("| " + row + " | " + " | ".join(item[row] for item in mapped) + " |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.cards.read_text(encoding="utf-8"))
    output = render(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
