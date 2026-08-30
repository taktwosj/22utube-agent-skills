#!/usr/bin/env python3
"""Prepare an existing 119 card manifest for the user-authored V8 overlay root.

This is intentionally a non-editorial migration: card order, durations, media,
and spoken text stay untouched.  It adds only the required chapter/source
display fields and rewrites display SRT line breaks for the V8 lower-third.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def visible_length(value: str) -> int:
    return len(re.sub(r"\s+", "", value))


def split_words(text: str, limit: int = 15) -> list[str]:
    """Return exact words packed to the visible-character limit.

    A long unbroken token is split only when unavoidable; no wording is
    shortened or substituted.
    """
    words = re.findall(r"\S+", text)
    rows: list[str] = []
    current = ""
    for word in words:
        if visible_length(word) > limit:
            if current:
                rows.append(current)
                current = ""
            while visible_length(word) > limit:
                rows.append(word[:limit])
                word = word[limit:]
            if word:
                current = word
            continue
        candidate = f"{current} {word}".strip()
        if current and visible_length(candidate) > limit:
            rows.append(current)
            current = word
        else:
            current = candidate
    if current:
        rows.append(current)
    return rows


def as_us(value: str) -> int:
    hours, minutes, seconds = value.strip().replace(",", ".").split(":")
    return round((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1_000_000)


def as_timestamp(value: int) -> str:
    millis = value // 1000
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def read_srt(path: Path) -> list[tuple[int, int, str]]:
    rows: list[tuple[int, int, str]] = []
    for block in re.split(r"\n{2,}", path.read_text(encoding="utf-8").strip()):
        lines = [line.strip() for line in block.splitlines()]
        timing = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing is None:
            continue
        start, end = lines[timing].split("-->", 1)
        text = " ".join(line for line in lines[timing + 1 :] if line)
        if text:
            rows.append((as_us(start), as_us(end), text))
    if not rows:
        raise RuntimeError(f"SRT_CUES_REQUIRED:{path.name}")
    return rows


def reflow_srt(source: Path, destination: Path) -> None:
    output: list[tuple[int, int, str]] = []
    for start, end, text in read_srt(source):
        rows = split_words(text)
        cues = rows
        weights = [max(1, visible_length(cue)) for cue in cues]
        total = sum(weights)
        cursor = start
        span = end - start
        for index, (cue, weight) in enumerate(zip(cues, weights)):
            next_cursor = end if index == len(cues) - 1 else cursor + round(span * weight / total)
            output.append((cursor, max(cursor + 1, next_cursor), cue))
            cursor = next_cursor
    destination.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        f"{index}\n{as_timestamp(start)} --> {as_timestamp(end)}\n{text}"
        for index, (start, end, text) in enumerate(output, 1)
    ]
    destination.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--caption-dir", type=Path, required=True)
    parser.add_argument("--project-name", required=True)
    args = parser.parse_args()

    document = json.loads(args.cards.read_text(encoding="utf-8"))
    prepared = copy.deepcopy(document)
    prepared["project_name"] = args.project_name
    prepared["v8_root_profile"] = "V8_MANUAL_OVERLAY_65"
    prepared["caption_contract"] = {"line_visible_chars": 15, "max_lines": 1}
    for card in prepared["cards"]:
        card_id = str(card["card_id"])
        title = str(card.get("chapter_title", "")).strip()
        label = str(card.get("chapter_label", "")).strip()
        if not title or label != title:
            raise RuntimeError(f"APPROVED_CHAPTER_LABEL_REQUIRED:{card_id}")
        if card["card_type"] == "SOURCE_VIDEO":
            source_label = str(card.get("source_display_label", "")).strip()
            if not source_label:
                raise RuntimeError(f"SOURCE_DISPLAY_LABEL_REQUIRED:{card_id}")
        srt_field = "source_srt_file" if card.get("lower_mode") == "SOURCE_TTS" else "narration_srt_file"
        if card.get(srt_field):
            original = Path(card[srt_field])
            rendered = args.caption_dir / f"{card_id}_{original.name}"
            reflow_srt(original, rendered)
            card[srt_field] = str(rendered)
            sha_field = {
                "source_srt_file": "source_srt_sha256",
                "narration_srt_file": "narration_srt_sha256",
            }[srt_field]
            card[sha_field] = sha256(rendered)
            if srt_field == "source_srt_file":
                card["display_srt_path"] = str(rendered)
                card["display_srt_sha256"] = card[sha_field]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(prepared, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "cards": len(prepared["cards"]), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
