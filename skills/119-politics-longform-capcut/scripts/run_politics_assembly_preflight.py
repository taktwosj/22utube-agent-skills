#!/usr/bin/env python3
"""Run deterministic assembly-only checks and bind their results to current inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import generate_user_final_assembly_grid as grid
import validate_politics_caption_layout as caption
import validate_srt_text_fidelity as fidelity

SCHEMA = "politics-longform-assembly-preflight.v1"
INPUT_FIELDS = (
    "source_srt_file", "narration_srt_file", "srt_file", "display_srt_path", "raw_transcript_path"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def resolve(value: str, cards_path: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else cards_path.parent / candidate


def input_files(document: dict[str, Any], cards_path: Path) -> list[dict[str, str]]:
    seen: set[tuple[str, str, Path]] = set()
    rows: list[dict[str, str]] = []
    for card in document.get("cards", []):
        if not isinstance(card, dict):
            continue
        card_id = str(card.get("card_id", "?"))
        for field in INPUT_FIELDS:
            value = card.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            path = resolve(value, cards_path).resolve()
            key = (card_id, field, path)
            if key in seen:
                continue
            if not path.is_file():
                raise RuntimeError(f"ASSEMBLY_PREFLIGHT_INPUT_MISSING:{card_id}:{field}:{path.name}")
            seen.add(key)
            rows.append(
                {
                    "card_id": card_id,
                    "field": field,
                    "filename": path.name,
                    "sha256": sha256(path),
                }
            )
    return sorted(rows, key=lambda row: (row["card_id"], row["field"], row["filename"]))


def portable_grid_reference(cards_path: Path, grid_path: Path) -> str:
    cards_root = cards_path.parent.resolve()
    try:
        relative = grid_path.resolve().relative_to(cards_root)
    except ValueError as error:
        raise RuntimeError("ASSEMBLY_PREFLIGHT_GRID_MUST_BE_UNDER_CARDS_DIR") from error
    return relative.as_posix()


def run_preflight(cards_path: Path, report_path: Path, grid_path: Path) -> dict[str, Any]:
    document = json.loads(cards_path.read_text(encoding="utf-8"))
    if document.get("execution_mode") != "ASSEMBLY_ONLY":
        raise RuntimeError("ASSEMBLY_ONLY_EXECUTION_MODE_REQUIRED")
    caption_findings = caption.validate_cards(cards_path)
    fidelity_findings = fidelity.validate_cards(cards_path)
    findings = [
        *({"gate": "CAPTION_LAYOUT", **row} for row in caption_findings),
        *({"gate": "SRT_TEXT_FIDELITY", **row} for row in fidelity_findings),
    ]
    rows = input_files(document, cards_path)
    grid_relative = portable_grid_reference(cards_path, grid_path)
    if findings:
        result = {
            "schema": SCHEMA,
            "status": "FAIL",
            "cards_file": cards_path.name,
            "cards_sha256": sha256(cards_path),
            "inputs": rows,
            "grid": None,
            "findings": findings,
        }
        write_atomic(report_path, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return result
    rendered = grid.render(document)
    write_atomic(grid_path, rendered)
    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "cards_file": cards_path.name,
        "cards_sha256": sha256(cards_path),
        "inputs": rows,
        "caption_layout": "PASS",
        "srt_text_fidelity": "PASS",
        "grid": {"relative_path": grid_relative, "sha256": sha256(grid_path)},
        "findings": [],
    }
    write_atomic(report_path, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def verify_preflight_report(cards_path: Path, report_path: Path) -> dict[str, Any]:
    if not report_path.is_file():
        raise RuntimeError("ASSEMBLY_PREFLIGHT_REPORT_REQUIRED")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schema") != SCHEMA or report.get("status") != "PASS":
        raise RuntimeError("ASSEMBLY_PREFLIGHT_PASS_REQUIRED")
    if report.get("cards_file") != cards_path.name or report.get("cards_sha256") != sha256(cards_path):
        raise RuntimeError("ASSEMBLY_PREFLIGHT_CARDS_SHA_MISMATCH")
    document = json.loads(cards_path.read_text(encoding="utf-8"))
    current_inputs = input_files(document, cards_path)
    if report.get("inputs") != current_inputs:
        raise RuntimeError("ASSEMBLY_PREFLIGHT_INPUT_SHA_MISMATCH")
    grid_row = report.get("grid")
    if not isinstance(grid_row, dict):
        raise RuntimeError("ASSEMBLY_PREFLIGHT_GRID_REQUIRED")
    relative = str(grid_row.get("relative_path", ""))
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise RuntimeError("ASSEMBLY_PREFLIGHT_GRID_REFERENCE_INVALID")
    grid_path = cards_path.parent / relative
    if not grid_path.is_file() or sha256(grid_path) != grid_row.get("sha256"):
        raise RuntimeError("ASSEMBLY_PREFLIGHT_GRID_SHA_MISMATCH")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--grid", type=Path, required=True)
    args = parser.parse_args()
    result = run_preflight(args.cards, args.report, args.grid)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
