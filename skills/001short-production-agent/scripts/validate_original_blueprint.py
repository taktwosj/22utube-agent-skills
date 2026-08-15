from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import result, sha256_file
from validate_capcut_grids import BRACKET_PLACEHOLDER, PLACEHOLDER_TOKEN


HEADER_FIELDS = {
    "상황·행동": "situation_action",
    "주도 화자": "lead_speaker",
    "전달 방식": "delivery_mode",
    "서사 기능": "narrative_function",
    "구조 분리 근거": "split_basis",
}
BEAT_ID = re.compile(r"^B\d{2}$")
DASH_PLACEHOLDER = re.compile(r"^(?:-|–|—)$")


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _error(code: str, **details: object) -> dict:
    return {"code": code, **details}


def validate_original_blueprint(path: Path) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        return result([_error("ORIGINAL_BLUEPRINT_FILE_MISSING", path=str(path))])

    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = -1
    header: list[str] = []
    for index, line in enumerate(lines):
        candidate = _cells(line)
        if candidate and candidate[0] == "원본 구조":
            header_index = index
            header = candidate
            break
    if header_index < 0:
        return result([_error("ORIGINAL_BLUEPRINT_BEAT_TABLE_MISSING")])

    errors: list[dict] = []
    positions: dict[str, int] = {}
    for label, field in HEADER_FIELDS.items():
        if label not in header:
            errors.append(_error("ORIGINAL_BLUEPRINT_FIELD_MISSING", field=field))
        else:
            positions[field] = header.index(label)
    if errors:
        return result(errors, {"path": str(path), "sha256": sha256_file(path)})

    beats: list[str] = []
    for line in lines[header_index + 2 :]:
        row = _cells(line)
        if not row:
            if beats:
                break
            continue
        beat = row[0]
        if not BEAT_ID.fullmatch(beat):
            errors.append(_error("ORIGINAL_BLUEPRINT_BEAT_ID_INVALID", beat=beat))
            continue
        if beat in beats:
            errors.append(_error("ORIGINAL_BLUEPRINT_BEAT_DUPLICATE", beat=beat))
        beats.append(beat)
        for field, position in positions.items():
            value = row[position].strip() if position < len(row) else ""
            if not value:
                errors.append(
                    _error("ORIGINAL_BLUEPRINT_BEAT_FIELD_EMPTY", beat=beat, field=field)
                )
            elif (
                "미확인" in value
                or PLACEHOLDER_TOKEN.search(value)
                or BRACKET_PLACEHOLDER.fullmatch(value)
                or DASH_PLACEHOLDER.fullmatch(value)
            ):
                errors.append(
                    _error(
                        "ORIGINAL_BLUEPRINT_BEAT_FIELD_PLACEHOLDER",
                        beat=beat,
                        field=field,
                        value=value,
                    )
                )

    if not beats:
        errors.append(_error("ORIGINAL_BLUEPRINT_BEAT_MISSING"))
    return result(
        errors,
        {
            "path": str(path),
            "sha256": sha256_file(path),
            "beat_count": len(beats),
            "beat_ids": beats,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-blueprint", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_original_blueprint(args.original_blueprint)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
