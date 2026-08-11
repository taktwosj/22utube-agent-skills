from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from common import meaningful_text_length


REQUIRED_ROWS = (
    "T1",
    "T2",
    "A9_TEXT",
    "A10_TEXT_YELLOW",
    "A10_TEXT_WHITE",
    "STATE_LASER",
    "STATE_GLITCH",
    "STATE_FLICKER",
    "SCREEN_WHITE",
    "SCREEN_EFFECT",
    "VIDEO",
    "A9",
    "A10",
    "A11",
    "A12_RESERVED_EMPTY",
)
HEADER_LABELS = {
    "original": "레이어 \\ 원본 시간",
    "urakkai": "레이어 \\ 목표 시간",
}
HEADER_PATTERNS = {
    "original": re.compile(
        r"^B(?P<index>\d{2})\s+(?P<start>\d+(?:\.\d+)?)[–-](?P<end>\d+(?:\.\d+)?)$"
    ),
    "urakkai": re.compile(
        r"^V(?P<index>\d{2})\s+(?P<start>\d+(?:\.\d+)?)[–-](?P<end>\d+(?:\.\d+)?)\s+(?P<source>B\d{2})$"
    ),
}
EMPTY_MARKERS = {"", "-", "–", "—"}
LINE_LIMIT_ROLES = {"A9_TEXT", "STATE_LASER"}
PLACEHOLDER_TOKEN = re.compile(
    r"(?:^|[\s_:/-])(?:placeholder|todo|tbd|tbc|n/a)(?:$|[\s_:/-])",
    re.IGNORECASE,
)
BRACKET_PLACEHOLDER = re.compile(r"^(?:<[^<>]+>|\[[^\[\]]+\]|\{[^{}]+\})$")


@dataclass(frozen=True)
class Grid:
    kind: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    @property
    def column_count(self) -> int:
        return len(self.headers)

    def markdown(self) -> str:
        lines = [
            "| " + " | ".join((HEADER_LABELS[self.kind], *self.headers)) + " |",
            "|" + "|".join("---" for _ in range(self.column_count + 1)) + "|",
        ]
        lines.extend("| " + " | ".join(row) + " |" for row in self.rows)
        return "\n".join(lines)


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _error(code: str, table: str, **details: object) -> dict:
    return {"code": code, "table": table, **details}


def validate_grid(path: Path, kind: str) -> tuple[Grid | None, list[dict]]:
    errors: list[dict] = []
    if kind not in HEADER_LABELS:
        raise ValueError(f"GRID_KIND_INVALID:{kind}")
    if not path.is_file():
        return None, [_error("TABLE_FILE_MISSING", kind, path=str(path))]

    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = -1
    header_cells: list[str] = []
    for index, line in enumerate(lines):
        candidate = _cells(line)
        if candidate and candidate[0] == HEADER_LABELS[kind]:
            header_index = index
            header_cells = candidate
            break
    if header_index < 0:
        return None, [_error("TABLE_HEADER_INVALID", kind, expected=HEADER_LABELS[kind])]
    if len(header_cells) < 2:
        return None, [_error("TABLE_HEADER_INVALID", kind, detail="NO_TIME_COLUMNS")]

    headers = header_cells[1:]
    pattern = HEADER_PATTERNS[kind]
    for column, header in enumerate(headers, start=1):
        match = pattern.fullmatch(header)
        if match is None or int(match.group("index")) != column:
            errors.append(
                _error(
                    "TABLE_HEADER_INVALID",
                    kind,
                    column=column,
                    value=header,
                )
            )

    body: list[tuple[str, ...]] = []
    for line in lines[header_index + 2 :]:
        row = _cells(line)
        if not row:
            if body:
                break
            continue
        body.append(tuple(row))

    observed_roles = tuple(row[0] if row else "" for row in body)
    if len(body) < len(REQUIRED_ROWS):
        errors.append(
            _error(
                "TABLE_ROW_MISSING",
                kind,
                expected_count=len(REQUIRED_ROWS),
                observed_count=len(body),
            )
        )
    elif len(body) > len(REQUIRED_ROWS):
        errors.append(
            _error(
                "TABLE_ROW_COUNT_INVALID",
                kind,
                expected_count=len(REQUIRED_ROWS),
                observed_count=len(body),
            )
        )
    if observed_roles != REQUIRED_ROWS:
        errors.append(
            _error(
                "TABLE_ROW_ORDER_INVALID",
                kind,
                expected=list(REQUIRED_ROWS),
                observed=list(observed_roles),
            )
        )

    expected_width = len(headers) + 1
    for row_index, row in enumerate(body, start=1):
        role = row[0] if row else ""
        if len(row) != expected_width:
            errors.append(
                _error(
                    "TABLE_COLUMN_COUNT_MISMATCH",
                    kind,
                    row=role or row_index,
                    expected=expected_width,
                    observed=len(row),
                )
            )
            continue
        for column, value in enumerate(row[1:], start=1):
            stripped = value.strip()
            if stripped in EMPTY_MARKERS:
                errors.append(
                    _error(
                        "TABLE_EMPTY_CELL_FORBIDDEN",
                        kind,
                        row=role,
                        column=column,
                    )
                )
                continue
            if "미확인" in stripped:
                errors.append(
                    _error(
                        "TABLE_UNVERIFIED_CELL",
                        kind,
                        row=role,
                        column=column,
                        value=stripped,
                    )
                )
            if PLACEHOLDER_TOKEN.search(stripped) or BRACKET_PLACEHOLDER.fullmatch(stripped):
                errors.append(
                    _error(
                        "TABLE_PLACEHOLDER_FORBIDDEN",
                        kind,
                        row=role,
                        column=column,
                        value=stripped,
                    )
                )
            if role == "A12_RESERVED_EMPTY" and stripped != "비움":
                errors.append(
                    _error(
                        "A12_RESERVED_EMPTY",
                        kind,
                        row=role,
                        column=column,
                        value=stripped,
                    )
                )
            if role in LINE_LIMIT_ROLES:
                display_lines = re.split(r"\s*<br\s*/?>\s*|\r?\n", stripped, flags=re.IGNORECASE)
                if len(display_lines) > 2:
                    errors.append(
                        _error(
                            "TABLE_TEXT_TOO_MANY_LINES",
                            kind,
                            row=role,
                            column=column,
                            observed=len(display_lines),
                            limit=2,
                        )
                    )
                for display_line in display_lines:
                    if meaningful_text_length(display_line) > 15:
                        errors.append(
                            _error(
                                "TABLE_TEXT_LINE_TOO_LONG",
                                kind,
                                row=role,
                                column=column,
                                value=display_line,
                                limit=15,
                            )
                        )

    grid = Grid(kind=kind, headers=tuple(headers), rows=tuple(body))
    return grid, errors


def validate_grids(original_path: Path, urakkai_path: Path) -> dict:
    original, original_errors = validate_grid(original_path, "original")
    urakkai, urakkai_errors = validate_grid(urakkai_path, "urakkai")
    errors = original_errors + urakkai_errors
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "original": original,
        "urakkai": urakkai,
    }


def _header_range_us(kind: str, header: str) -> tuple[int, int]:
    match = HEADER_PATTERNS[kind].fullmatch(header)
    if match is None:
        raise ValueError(f"TABLE_HEADER_INVALID:{kind}:{header}")
    return tuple(
        int(Decimal(match.group(name)) * Decimal(1_000_000))
        for name in ("start", "end")
    )


def _overlaps(start: int, end: int, target: tuple[int, int]) -> bool:
    return start < target[1] and end > target[0]


def _normalized_text(value: object) -> str:
    text = re.sub(r"(?i)<br\s*/?>", "\n", str(value or ""))
    return " ".join(unicodedata.normalize("NFKC", text).split())


def validate_locked_assembly(
    validation: dict,
    build_manifest: dict,
    approved_timeline: dict,
    audio_lock: dict,
    caption_lock: dict,
) -> list[dict]:
    """Bind a format-valid grid pair to the immutable assembly declarations."""
    if validation.get("status") != "PASS":
        return [_error("TABLE_VALIDATION_REQUIRED", "locked")]
    original: Grid = validation["original"]
    urakkai: Grid = validation["urakkai"]
    clips = sorted(
        build_manifest.get("urakkai", {}).get("video_clips", []),
        key=lambda row: row.get("target_range_us", [0, 0])[0],
    )
    original_ranges = [_header_range_us("original", header) for header in original.headers]
    manifest_source_ranges = sorted({tuple(row.get("source_range_us", ())) for row in clips})
    errors: list[dict] = []
    if original_ranges != manifest_source_ranges:
        errors.append(_error(
            "TABLE_VIDEO_RANGE_MISMATCH",
            "original",
            detail="SOURCE_RANGES",
            declared=[list(row) for row in original_ranges],
            actual=[list(row) for row in manifest_source_ranges],
        ))
    if len(urakkai.headers) != len(clips):
        errors.append(_error(
            "TABLE_VIDEO_RANGE_MISMATCH",
            "urakkai",
            detail="TARGET_COLUMN_COUNT",
            declared=len(urakkai.headers),
            actual=len(clips),
        ))
        return errors

    target_ranges: list[tuple[int, int]] = []
    for column, (header, clip) in enumerate(zip(urakkai.headers, clips), start=1):
        match = HEADER_PATTERNS["urakkai"].fullmatch(header)
        declared_target = _header_range_us("urakkai", header)
        actual_target = tuple(clip.get("target_range_us", ()))
        source_index = int(match.group("source")[1:]) - 1 if match else -1
        declared_source = (
            original_ranges[source_index]
            if 0 <= source_index < len(original_ranges)
            else None
        )
        actual_source = tuple(clip.get("source_range_us", ()))
        target_ranges.append(declared_target)
        if declared_target != actual_target or declared_source != actual_source:
            errors.append(_error(
                "TABLE_VIDEO_RANGE_MISMATCH",
                "urakkai",
                column=column,
                declared_target=list(declared_target),
                actual_target=list(actual_target),
                declared_source=list(declared_source) if declared_source else None,
                actual_source=list(actual_source),
            ))

    rows = {row[0]: row[1:] for row in urakkai.rows}
    segments = approved_timeline.get("segments", [])
    caption_cues = caption_lock.get("cues", [])
    empty_values = {"없음", "비움"}

    caption_rows = [row for row in segments if row.get("role") in {"A9_TEXT", "A10_TEXT", "STATE"}]
    timeline_cue_ids = [row.get("cue_id") for row in caption_rows]
    locked_cue_ids = [row.get("cue_id") for row in caption_cues]
    strict_caption_contract = caption_lock.get("schema_version") == "001short-caption-lock-v2"
    if strict_caption_contract and (
            any(not isinstance(cue_id, str) or not cue_id for cue_id in timeline_cue_ids + locked_cue_ids)
            or len(set(timeline_cue_ids)) != len(timeline_cue_ids)
            or len(set(locked_cue_ids)) != len(locked_cue_ids)
            or set(timeline_cue_ids) != set(locked_cue_ids)):
        errors.append(_error("CAPTION_LOCK_CUE_UNASSEMBLED", "urakkai", timeline_cue_ids=timeline_cue_ids, caption_lock_cue_ids=locked_cue_ids))
    elif strict_caption_contract:
        locked_by_id = {row["cue_id"]: row for row in caption_cues}
        for row in caption_rows:
            locked = locked_by_id[row["cue_id"]]
            if (
                locked.get("layer", locked.get("caption_role")) != row.get("role")
                or _normalized_text(locked.get("text")) != _normalized_text(row.get("text"))
                or locked.get("start_us") != row.get("start")
                or locked.get("end_us") != row.get("start", 0) + row.get("duration", 0)
            ):
                errors.append(_error(
                    "TABLE_CAPTION_TEXT_MISMATCH", "urakkai",
                    cue_id=row["cue_id"], expected_text=_normalized_text(row.get("text")),
                ))
                break

    def timeline_rows(role: str, target: tuple[int, int]) -> list[dict]:
        matches: list[dict] = []
        for row in segments:
            observed_role = row.get("role")
            if role == "A10_TEXT_WHITE":
                accepted = observed_role == "A10_TEXT" and row.get("color_role") == "WHITE"
            elif role == "A10_TEXT_YELLOW":
                accepted = observed_role == "A10_TEXT" and row.get("color_role") == "YELLOW"
            elif role in {"STATE_LASER", "STATE_GLITCH", "STATE_FLICKER"}:
                expected_effect = {
                    "STATE_LASER": "LASER_CUT",
                    "STATE_GLITCH": "GLITCH_SHAKE",
                    "STATE_FLICKER": "FLICKER_RAVE",
                }[role]
                accepted = observed_role == "STATE" and row.get("state_effect") == expected_effect
            else:
                accepted = observed_role == role
            start = row.get("start")
            duration = row.get("duration")
            if accepted and isinstance(start, int) and isinstance(duration, int) and _overlaps(start, start + duration, target):
                matches.append(row)
        return matches

    source_audio = build_manifest.get("source_audio", [])
    checked_roles = (
        "A9", "A9_TEXT", "A10", "A10_TEXT_WHITE", "A10_TEXT_YELLOW",
        "STATE_LASER", "STATE_GLITCH", "STATE_FLICKER",
    )
    audio_roles = {
        row.get("role") for row in audio_lock.get("role_files", []) if isinstance(row, dict)
    }
    for column, target in enumerate(target_ranges, start=1):
        for role in checked_roles:
            actual_rows = timeline_rows(role, target)
            if role == "A10":
                actual = any(
                    row.get("mode") in {"on", "duck"}
                    and isinstance(row.get("target_range_us"), list)
                    and len(row["target_range_us"]) == 2
                    and all(isinstance(value, int) for value in row["target_range_us"])
                    and _overlaps(row["target_range_us"][0], row["target_range_us"][1], target)
                    for row in source_audio
                )
            else:
                actual = bool(actual_rows)
            declared = rows[role][column - 1]
            declared_empty = declared in empty_values
            if actual and declared_empty:
                errors.append(_error(
                    "TABLE_ROLE_ACTUAL_PRESENT_DECLARED_EMPTY",
                    "urakkai",
                    row=role,
                    column=column,
                    value=declared,
                ))
            elif not actual and not declared_empty:
                errors.append(_error(
                    "TABLE_ROLE_DECLARED_POPULATED_ACTUAL_MISSING",
                    "urakkai",
                    row=role,
                    column=column,
                    value=declared,
                ))

            required_audio_role = role if role in {"A9", "A10"} else None
            if actual and required_audio_role and required_audio_role not in audio_roles:
                errors.append(_error(
                    "TABLE_AUDIO_LOCK_ROLE_MISSING",
                    "urakkai",
                    row=role,
                    column=column,
                    audio_role=required_audio_role,
                ))

            text_role = role in {
                "A9", "A9_TEXT", "A10_TEXT_WHITE", "A10_TEXT_YELLOW",
                "STATE_LASER", "STATE_GLITCH", "STATE_FLICKER",
            }
            if actual and not declared_empty and text_role:
                ordered_rows = sorted(actual_rows, key=lambda row: (row.get("start", 0), row.get("segment_id", "")))
                expected_text = _normalized_text(" ".join(str(row.get("text", "")) for row in ordered_rows))
                if _normalized_text(declared) != expected_text:
                    errors.append(_error(
                        "TABLE_CELL_TEXT_MISMATCH",
                        "urakkai",
                        row=role,
                        column=column,
                        declared=_normalized_text(declared),
                        actual=expected_text,
                    ))

            caption_layer = {
                "A9_TEXT": "A9_TEXT",
                "A10_TEXT_WHITE": "A10_TEXT",
                "A10_TEXT_YELLOW": "A10_TEXT",
                "STATE_LASER": "STATE",
            }.get(role)
            if actual and caption_layer:
                layer_cues = [
                    cue for cue in caption_cues
                    if cue.get("layer") == caption_layer
                    and isinstance(cue.get("start_us"), int)
                    and isinstance(cue.get("end_us"), int)
                    and _overlaps(cue["start_us"], cue["end_us"], target)
                ]
                if not layer_cues:
                    errors.append(_error(
                        "TABLE_CAPTION_LOCK_ROLE_MISSING",
                        "urakkai",
                        row=role,
                        column=column,
                    ))
                else:
                    for locked_row in actual_rows:
                        expected_text = _normalized_text(locked_row.get("text", ""))
                        expected_cue_id = locked_row.get("cue_id")
                        matching = [
                            cue for cue in layer_cues
                            if _normalized_text(cue.get("text", "")) == expected_text
                            and (expected_cue_id is None or cue.get("cue_id") == expected_cue_id)
                        ]
                        if not matching:
                            errors.append(_error(
                                "TABLE_CAPTION_TEXT_MISMATCH",
                                "urakkai",
                                row=role,
                                column=column,
                                cue_id=expected_cue_id,
                                expected_text=expected_text,
                            ))

        for title_role in ("T1", "T2"):
            actual_titles = timeline_rows(title_role, target)
            declared = rows[title_role][column - 1]
            if not actual_titles:
                if declared not in empty_values:
                    errors.append(_error(
                        "TABLE_ROLE_DECLARED_POPULATED_ACTUAL_MISSING",
                        "urakkai", row=title_role, column=column, value=declared,
                    ))
                continue
            locked_values = {str(row.get("text", "")) for row in actual_titles}
            if declared in empty_values:
                errors.append(_error(
                    "TABLE_ROLE_ACTUAL_PRESENT_DECLARED_EMPTY",
                    "urakkai", row=title_role, column=column, value=declared,
                ))
            elif locked_values != {declared}:
                errors.append(_error(
                    "TABLE_TITLE_TEXT_MISMATCH",
                    "urakkai", row=title_role, column=column,
                    declared=declared, actual=sorted(locked_values),
                ))
    return errors


def render_chat_report(validation: dict) -> str:
    if validation["status"] != "PASS":
        raise ValueError("TABLE_VALIDATION_REQUIRED")
    original: Grid = validation["original"]
    urakkai: Grid = validation["urakkai"]
    return (
        "원본표\n\n"
        + original.markdown()
        + "\n\n우라까이표\n\n"
        + urakkai.markdown()
        + "\n\n"
        + f"검증: 원본표 {original.column_count}개 열, "
        + f"우라까이표 {urakkai.column_count}개 열, "
        + f"{len(REQUIRED_ROWS)}개 레이어, 빈 셀 없음 — PASS"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--urakkai", type=Path, required=True)
    parser.add_argument("--emit-report", action="store_true")
    args = parser.parse_args()

    validation = validate_grids(args.original.resolve(), args.urakkai.resolve())
    if validation["status"] != "PASS":
        print(
            json.dumps(
                {"status": "FAIL", "errors": validation["errors"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    if args.emit_report:
        print(render_chat_report(validation))
    else:
        print(json.dumps({"status": "PASS", "errors": []}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
