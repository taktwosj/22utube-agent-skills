#!/usr/bin/env python3
"""Compile builder cards only after validated PRE-119 A/B/C/D evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
ALLOWED_DISPLAY_TRANSFORMS = {"SPLIT", "CLAMP", "LINE_BREAK", "DIALOGUE_MARKER_REMOVAL"}
CTA_VALUES = {"ON", "OFF"}


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require_file_sha(card: dict[str, Any], path_field: str, sha_field: str, code: str) -> Path:
    value = card.get(path_field)
    expected = str(card.get(sha_field, "")).strip().upper()
    path = Path(value) if isinstance(value, str) and value.strip() else Path()
    if not value or not path.is_file() or not SHA256_RE.fullmatch(expected) or sha256(path) != expected:
        raise RuntimeError(f"{code}:{card.get('card_id', '?')}")
    return path


def requested(value: Any) -> bool:
    return value is True or str(value).strip().upper() in {"YES", "TRUE", "REQUESTED", "PASS", "ENABLED", "ON"}


def validate_lanes(plan: dict[str, Any], evidence: dict[str, Any]) -> None:
    lanes = evidence.get("lanes")
    if not isinstance(lanes, dict) or lanes.get("A") != "PASS" or lanes.get("D") != "PASS":
        raise RuntimeError("WAIT_PRE119_STAGE_A_D_REQUIRED")
    if requested(plan.get("between_narration")) and lanes.get("B") != "PASS":
        raise RuntimeError("WAIT_PRE119_STAGE_B_REQUIRED")
    if requested(plan.get("between_image")) and lanes.get("C") != "PASS":
        raise RuntimeError("WAIT_PRE119_STAGE_C_REQUIRED")


def validate_plan_bindings(plan: dict[str, Any], cards: list[dict[str, Any]]) -> None:
    narration_types = {"NARRATION_IMAGE", "NARRATION_VIDEO"}
    image_types = {"CHAPTER_CARD", "NARRATION_IMAGE"}
    card_types = {card.get("card_type") for card in cards}
    narration_requested = requested(plan.get("between_narration"))
    image_requested = requested(plan.get("between_image"))
    if narration_requested and not (card_types & narration_types):
        raise RuntimeError("PRE119_PLAN_NARRATION_CARD_REQUIRED")
    if not narration_requested and card_types & narration_types:
        raise RuntimeError("PRE119_PLAN_NARRATION_CARD_FORBIDDEN")
    if image_requested and not (card_types & image_types):
        raise RuntimeError("PRE119_PLAN_IMAGE_CARD_REQUIRED")
    if not image_requested and card_types & image_types:
        raise RuntimeError("PRE119_PLAN_IMAGE_CARD_FORBIDDEN")
    expected_lower = str(plan.get("lower_mode", "")).strip().upper()
    allowed_lower = {"SRT", "COMMENTARY_2LINE", "NONE"}
    if expected_lower not in allowed_lower | {"MIXED"}:
        raise RuntimeError("PRE119_PLAN_LOWER_MODE_INVALID")
    for card in cards:
        if card.get("card_type") not in {"SOURCE_VIDEO", "NARRATION_IMAGE", "NARRATION_VIDEO"}:
            continue
        actual = str(card.get("lower_mode", "")).strip().upper()
        if actual not in allowed_lower:
            raise RuntimeError(f"PRE119_PLAN_LOWER_MODE_INVALID:{card.get('card_id', '?')}")
        if expected_lower != "MIXED" and actual != expected_lower:
            raise RuntimeError(f"PRE119_PLAN_LOWER_MODE_MISMATCH:{card.get('card_id', '?')}")


def validate_source_provenance(card: dict[str, Any]) -> None:
    try:
        require_file_sha(card, "raw_transcript_path", "raw_transcript_sha256", "SOURCE_TRANSCRIPT_PROVENANCE_INVALID")
        display = require_file_sha(card, "display_srt_path", "display_srt_sha256", "SOURCE_TRANSCRIPT_PROVENANCE_INVALID")
    except RuntimeError as error:
        if str(error).startswith("SOURCE_TRANSCRIPT_PROVENANCE_INVALID"):
            raise RuntimeError(f"SOURCE_TRANSCRIPT_PROVENANCE_INVALID:{card.get('card_id', '?')}") from error
        raise
    transforms = card.get("display_transform")
    if (
        not isinstance(transforms, list)
        or any(not isinstance(value, str) or value not in ALLOWED_DISPLAY_TRANSFORMS for value in transforms)
        or len(set(transforms)) != len(transforms)
    ):
        raise RuntimeError(f"SOURCE_TRANSCRIPT_PROVENANCE_INVALID:{card.get('card_id', '?')}")
    card["source_srt_file"] = str(display)
    card["source_srt_sha256"] = str(card["display_srt_sha256"]).upper()


def normalize_lower_text(card: dict[str, Any]) -> None:
    if card.get("lower_mode") != "COMMENTARY_2LINE":
        return
    line1 = card.get("lower_line1")
    line2 = card.get("lower_line2")
    existing = card.get("lower_text")
    if isinstance(existing, str) and existing.strip():
        return
    if not isinstance(line1, str) or not line1.strip() or not isinstance(line2, str) or not line2.strip():
        raise RuntimeError(f"COMMENTARY_2LINE_FIELDS_REQUIRED:{card.get('card_id', '?')}")
    if "\n" in line1 or "\n" in line2:
        raise RuntimeError(f"COMMENTARY_2LINE_EMBEDDED_NEWLINE:{card.get('card_id', '?')}")
    card["lower_text"] = f"{line1.strip()}\n{line2.strip()}"


def validate_card(card: dict[str, Any]) -> None:
    card_id = str(card.get("card_id", "?"))
    kind = card.get("card_type")
    normalize_lower_text(card)
    try:
        target_duration = int(card.get("target_duration_us", 0))
        target_start = int(card.get("target_start_us", -1))
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"CARD_TIMELINE_EVIDENCE_INVALID:{card_id}") from error
    if target_start < 0 or target_duration <= 0:
        raise RuntimeError(f"CARD_TIMELINE_EVIDENCE_INVALID:{card_id}")
    if kind == "SOURCE_VIDEO":
        require_file_sha(card, "source_file", "source_sha256", "SOURCE_ASSET_EVIDENCE_INVALID")
        try:
            source_duration = int(card.get("source_duration_us", 0))
        except (TypeError, ValueError) as error:
            raise RuntimeError(f"SOURCE_ASSET_EVIDENCE_INVALID:{card_id}") from error
        if source_duration <= 0 or target_duration != source_duration:
            raise RuntimeError(f"SOURCE_ASSET_EVIDENCE_INVALID:{card_id}")
        if card.get("lower_mode") == "SRT":
            validate_source_provenance(card)
    elif kind == "NARRATION_VIDEO":
        require_file_sha(card, "video_file", "video_sha256", "NARRATION_VIDEO_ASSET_EVIDENCE_INVALID")
        require_file_sha(card, "narration_audio_file", "narration_audio_sha256", "NARRATION_AUDIO_ASSET_EVIDENCE_INVALID")
        if int(card.get("video_duration_us", 0)) <= 0 or int(card.get("audio_duration_us", 0)) <= 0:
            raise RuntimeError(f"NARRATION_ASSET_DURATION_INVALID:{card_id}")
    elif kind == "NARRATION_IMAGE":
        require_file_sha(card, "image_file", "image_sha256", "IMAGE_ASSET_EVIDENCE_INVALID")
        require_file_sha(card, "narration_audio_file", "narration_audio_sha256", "NARRATION_AUDIO_ASSET_EVIDENCE_INVALID")
        if int(card.get("audio_duration_us", 0)) <= 0:
            raise RuntimeError(f"NARRATION_ASSET_DURATION_INVALID:{card_id}")
    elif kind == "CHAPTER_CARD":
        require_file_sha(card, "image_file", "image_sha256", "IMAGE_ASSET_EVIDENCE_INVALID")
    elif kind not in {"INTRO", "TEXT_EXPLAINER", "ENDING"}:
        raise RuntimeError(f"CARD_TYPE_INVALID:{card_id}")


def normalize_cta_policy(cards: list[dict[str, Any]], plan: dict[str, Any]) -> str:
    default = str(plan.get("cta_like_subscribe", "ON")).strip().upper()
    if default not in CTA_VALUES:
        raise RuntimeError("CTA_POLICY_INVALID")
    values: set[str] = set()
    for card in cards:
        value = str(card.get("cta_like_subscribe", default)).strip().upper()
        if value not in CTA_VALUES:
            raise RuntimeError(f"CTA_POLICY_INVALID:{card.get('card_id', '?')}")
        card["cta_like_subscribe"] = value
        values.add(value)
    if len(values) != 1:
        raise RuntimeError("CTA_POLICY_MIXED_UNSUPPORTED")
    return values.pop()


def compile_cards(validation: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    if validation.get("status") != "PASS" or validation.get("route") != "PRE119":
        raise RuntimeError("WAIT_PRE119_VALIDATION_PASS_REQUIRED")
    plan = validation.get("validated_plan")
    if not isinstance(plan, dict):
        raise RuntimeError("WAIT_PRE119_VALIDATED_PLAN_REQUIRED")
    if evidence.get("status") != "PASS":
        raise RuntimeError("WAIT_PRE119_ASSET_EVIDENCE_PASS_REQUIRED")
    validate_lanes(plan, evidence)
    cards = evidence.get("cards")
    if not isinstance(cards, list) or not cards or any(not isinstance(card, dict) for card in cards):
        raise RuntimeError("PRE119_CARDS_EVIDENCE_REQUIRED")
    compiled = copy.deepcopy(cards)
    for card in compiled:
        validate_card(card)
    validate_plan_bindings(plan, compiled)
    cta_policy = normalize_cta_policy(compiled, plan)
    cursor = 0
    ordered = sorted(compiled, key=lambda item: int(item["target_start_us"]))
    for card in ordered:
        if int(card["target_start_us"]) != cursor:
            raise RuntimeError(f"CARD_TIMELINE_EVIDENCE_INVALID:{card.get('card_id', '?')}")
        cursor += int(card["target_duration_us"])
    return {
        "schema": "politics-longform-episode-cards.v1",
        "execution_mode": "ASSEMBLY_ONLY",
        "episode_id": plan["episode_id"],
        "project_name": plan["project_name"],
        "cta_like_subscribe": cta_policy,
        "canvas": {"width": 1920, "height": 1080, "fps": 30},
        "pre119_validation_sha256": validation.get("handoff_sha256", "TEST_FIXTURE"),
        "cards": ordered,
    }


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--asset-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compile_cards(load_object(args.validation_report), load_object(args.asset_evidence))
        write_atomic(args.output, result)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({"status": "PASS", "output": str(args.output), "card_count": len(result["cards"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
