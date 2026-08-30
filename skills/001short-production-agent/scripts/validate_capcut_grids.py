from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import user_provided_media_overlay
import validate_original_source_evidence

from common import times_match, meaningful_text_length
from track_contract import HUMAN_GRID_ROWS


# Human-facing table rows, top-down; single-sourced from the physical track
# order in track_contract (visual tracks reversed, audio tail appended).
REQUIRED_ROWS = HUMAN_GRID_ROWS
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
DECLARED_EMPTY_VALUES = {"없음", "비움"}
LINE_LIMITS = {
    ("original", "A9_TEXT"): (2, 15),
    ("urakkai", "A9_TEXT"): (2, 15),
    ("original", "STATE_LASER"): (2, 15),
    ("urakkai", "STATE_LASER"): (2, 15),
}
PLACEHOLDER_TOKEN = re.compile(
    r"(?:^|[\s_:/-])(?:placeholder|todo|tbd|tbc|n/a)(?:$|[\s_:/-])",
    re.IGNORECASE,
)
BRACKET_PLACEHOLDER = re.compile(r"^(?:<[^<>]+>|\[[^\[\]]+\]|\{[^{}]+\})$")
SOURCE_TRANSCRIPT_HEADING = re.compile(
    r"^###\s+(?P<segment>B\d{2})\s+(?P<start>\d+(?:\.\d+)?)[–-](?P<end>\d+(?:\.\d+)?)$"
)
SOURCE_TRANSCRIPT_FIELDS = (
    "(상황설명)",
    '"화자발언"',
    "<나레이션>",
    "TTS화자발언",
    "TTS나레이션",
)


@dataclass(frozen=True)
class SourceTranscriptBlock:
    segment_id: str
    start_text: str
    end_text: str
    values: tuple[str, ...]

    def markdown(self) -> str:
        lines = [f"### {self.segment_id} {self.start_text}–{self.end_text}"]
        lines.extend(
            f"{label} {value}"
            for label, value in zip(SOURCE_TRANSCRIPT_FIELDS, self.values)
        )
        return "\n".join(lines)


@dataclass(frozen=True)
class Grid:
    kind: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    source_transcript: tuple[SourceTranscriptBlock, ...] = ()

    @property
    def column_count(self) -> int:
        return len(self.headers)

    def markdown(self) -> str:
        table_lines = [
            "| " + " | ".join((HEADER_LABELS[self.kind], *self.headers)) + " |",
            "|" + "|".join("---" for _ in range(self.column_count + 1)) + "|",
        ]
        table_lines.extend("| " + " | ".join(row) + " |" for row in self.rows)
        if self.kind != "original" or not self.source_transcript:
            return "\n".join(table_lines)
        transcript = "\n\n".join(block.markdown() for block in self.source_transcript)
        return "## 원본 5분류 대본\n\n" + transcript + "\n\n" + "\n".join(table_lines)


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _error(code: str, table: str, **details: object) -> dict:
    return {"code": code, "table": table, **details}


def _parse_source_transcript(
    lines: list[str],
    header_index: int,
    headers: list[str],
) -> tuple[tuple[SourceTranscriptBlock, ...], list[dict]]:
    errors: list[dict] = []
    headings: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines[:header_index]):
        match = SOURCE_TRANSCRIPT_HEADING.fullmatch(line.strip())
        if match is not None:
            headings.append((index, match))
    if not headings:
        return (), [_error("ORIGINAL_TRANSCRIPT_REQUIRED", "original")]

    expected_segments: list[tuple[str, Decimal, Decimal]] = []
    for header in headers:
        match = HEADER_PATTERNS["original"].fullmatch(header)
        if match is None:
            continue
        expected_segments.append(
            (
                f"B{int(match.group('index')):02d}",
                Decimal(match.group("start")),
                Decimal(match.group("end")),
            )
        )

    blocks: list[SourceTranscriptBlock] = []
    observed_segments: list[tuple[str, Decimal, Decimal]] = []
    for position, (line_index, match) in enumerate(headings):
        end_index = headings[position + 1][0] if position + 1 < len(headings) else header_index
        field_lines = [line.strip() for line in lines[line_index + 1 : end_index] if line.strip()]
        segment_id = match.group("segment")
        observed_segments.append(
            (segment_id, Decimal(match.group("start")), Decimal(match.group("end")))
        )
        if len(field_lines) != len(SOURCE_TRANSCRIPT_FIELDS):
            errors.append(
                _error(
                    "ORIGINAL_TRANSCRIPT_FIELD_ORDER_INVALID",
                    "original",
                    segment=segment_id,
                    expected=list(SOURCE_TRANSCRIPT_FIELDS),
                    observed=field_lines,
                )
            )
            continue

        values: list[str] = []
        field_order_invalid = False
        for field_index, (label, line) in enumerate(zip(SOURCE_TRANSCRIPT_FIELDS, field_lines), start=1):
            prefix = label + " "
            if not line.startswith(prefix):
                field_order_invalid = True
                errors.append(
                    _error(
                        "ORIGINAL_TRANSCRIPT_FIELD_ORDER_INVALID",
                        "original",
                        segment=segment_id,
                        field=field_index,
                        expected=label,
                        observed=line,
                    )
                )
                values.append("")
                continue
            value = line[len(prefix) :].strip()
            values.append(value)
            if not value:
                errors.append(
                    _error(
                        "ORIGINAL_TRANSCRIPT_EMPTY_FIELD",
                        "original",
                        segment=segment_id,
                        field=label,
                    )
                )
            if value == "비움" or value in EMPTY_MARKERS:
                errors.append(
                    _error(
                        "ORIGINAL_TRANSCRIPT_ABSENCE_VALUE_INVALID",
                        "original",
                        segment=segment_id,
                        field=label,
                        value=value,
                    )
                )
            if label == "(상황설명)":
                situation_value, marker, ocr_value = value.partition("화면 OCR:")
                if any(token in situation_value for token in ("미확인", "확인 필요")):
                    errors.append(
                        _error(
                            "ORIGINAL_TRANSCRIPT_UNVERIFIED",
                            "original",
                            segment=segment_id,
                            field=label,
                            value=value,
                        )
                    )
                ocr_value = ocr_value.strip() if marker else ""
                if not ocr_value or any(token in ocr_value for token in ("미확인", "확인 필요")):
                    errors.append(
                        _error(
                            "WAIT_OCR_UNRESOLVED",
                            "original",
                            segment=segment_id,
                            value=value,
                        )
                    )
            elif any(token in value for token in ("미확인", "확인 필요")):
                errors.append(
                    _error(
                        "ORIGINAL_TRANSCRIPT_UNVERIFIED",
                        "original",
                        segment=segment_id,
                        field=label,
                        value=value,
                    )
                )
            if label in {"TTS화자발언", "TTS나레이션"} and value != "없음":
                errors.append(
                    _error(
                        "ORIGINAL_TRANSCRIPT_TTS_FORBIDDEN",
                        "original",
                        segment=segment_id,
                        field=label,
                        value=value,
                    )
                )
        if not field_order_invalid:
            blocks.append(
                SourceTranscriptBlock(
                    segment_id=segment_id,
                    start_text=match.group("start"),
                    end_text=match.group("end"),
                    values=tuple(values),
                )
            )

    if observed_segments != expected_segments:
        errors.append(
            _error(
                "ORIGINAL_TRANSCRIPT_SEGMENT_MISMATCH",
                "original",
                expected=[f"{segment} {start}–{end}" for segment, start, end in expected_segments],
                observed=[f"{segment} {start}–{end}" for segment, start, end in observed_segments],
            )
        )
    return tuple(blocks), errors


def validate_grid(
    path: Path,
    kind: str,
    *,
    require_source_transcript: bool = False,
) -> tuple[Grid | None, list[dict]]:
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

    source_transcript: tuple[SourceTranscriptBlock, ...] = ()
    if kind == "original":
        has_transcript = any(
            SOURCE_TRANSCRIPT_HEADING.fullmatch(line.strip())
            for line in lines[:header_index]
        )
        if require_source_transcript or has_transcript:
            source_transcript, transcript_errors = _parse_source_transcript(lines, header_index, headers)
            errors.extend(transcript_errors)

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
    values_by_role = {
        row[0]: row[1:]
        for row in body
        if len(row) == expected_width and row
    }
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
            line_limit = LINE_LIMITS.get((kind, role))
            if kind == "urakkai" and role == "A9_TEXT":
                a9_values = values_by_role.get("A9", ())
                a9_present = (
                    column <= len(a9_values)
                    and a9_values[column - 1].strip() not in DECLARED_EMPTY_VALUES
                    and a9_values[column - 1].strip() not in EMPTY_MARKERS
                )
                text_present = (
                    stripped not in DECLARED_EMPTY_VALUES
                    and stripped not in EMPTY_MARKERS
                )
                if text_present and not a9_present:
                    errors.append(
                        _error(
                            "A9_TEXT_TTS_PAIR_REQUIRED",
                            kind,
                            row=role,
                            column=column,
                        )
                    )
                if a9_present and not text_present:
                    errors.append(
                        _error(
                            "A9_TTS_TEXT_PAIR_REQUIRED",
                            kind,
                            row=role,
                            column=column,
                        )
                    )
            if line_limit is not None:
                max_lines, max_chars = line_limit
                display_lines = re.split(r"\s*<br\s*/?>\s*|\r?\n", stripped, flags=re.IGNORECASE)
                if len(display_lines) > max_lines:
                    errors.append(
                        _error(
                            "TABLE_TEXT_TOO_MANY_LINES",
                            kind,
                            row=role,
                            column=column,
                            observed=len(display_lines),
                            limit=max_lines,
                        )
                    )
                for display_line in display_lines:
                    if meaningful_text_length(display_line) > max_chars:
                        errors.append(
                            _error(
                                "TABLE_TEXT_LINE_TOO_LONG",
                                kind,
                                row=role,
                                column=column,
                                value=display_line,
                                limit=max_chars,
                            )
                        )

    grid = Grid(
        kind=kind,
        headers=tuple(headers),
        rows=tuple(body),
        source_transcript=source_transcript,
    )
    return grid, errors


def _validate_source_evidence(grid: Grid | None, context: dict) -> list[dict]:
    errors = list(context.get("errors", []))
    if not context.get("required") or grid is None or errors:
        return errors
    evidence_segments = context.get("segments", {})
    blocks = {block.segment_id: block for block in grid.source_transcript}
    for column, header in enumerate(grid.headers, start=1):
        match = HEADER_PATTERNS["original"].fullmatch(header)
        if match is None:
            continue
        segment_id = f"B{column:02d}"
        evidence = evidence_segments.get(segment_id)
        block = blocks.get(segment_id)
        if evidence is None or block is None:
            errors.append(_error(
                "ORIGINAL_TRANSCRIPT_EVIDENCE_MISMATCH",
                "original",
                segment=segment_id,
                detail="SEGMENT_MISSING",
            ))
            continue
        expected_range = [
            int(Decimal(match.group("start")) * Decimal(1_000_000)),
            int(Decimal(match.group("end")) * Decimal(1_000_000)),
        ]
        if evidence.get("source_range_us") != expected_range:
            errors.append(_error(
                "ORIGINAL_TRANSCRIPT_EVIDENCE_MISMATCH",
                "original",
                segment=segment_id,
                detail="SOURCE_RANGE",
            ))
        fields = evidence.get("classified_fields", {})
        expected_values = (
            fields.get("situation_description"),
            fields.get("speaker_statement"),
            fields.get("narration"),
            fields.get("tts_speaker_statement"),
            fields.get("tts_narration"),
        )
        if block.values != expected_values:
            errors.append(_error(
                "ORIGINAL_TRANSCRIPT_EVIDENCE_MISMATCH",
                "original",
                segment=segment_id,
                expected=list(expected_values),
                observed=list(block.values),
            ))
    if set(evidence_segments) != set(blocks):
        errors.append(_error(
            "ORIGINAL_TRANSCRIPT_EVIDENCE_MISMATCH",
            "original",
            detail="SEGMENT_SET",
        ))
    return errors


def validate_original(
    original_path: Path,
    *,
    state_path: Path | None = None,
) -> tuple[Grid | None, list[dict], dict]:
    context = validate_original_source_evidence.resolve_contract_context(
        original_path,
        state_path=state_path,
    )
    original, errors = validate_grid(
        original_path,
        "original",
        require_source_transcript=bool(context.get("required")),
    )
    errors.extend(_validate_source_evidence(original, context))
    return original, errors, context


def validate_grids(
    original_path: Path,
    urakkai_path: Path,
    *,
    state_path: Path | None = None,
) -> dict:
    original, original_errors, _context = validate_original(
        original_path,
        state_path=state_path,
    )
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
    checked_overlay = user_provided_media_overlay.validate_bundle(
        build_manifest.get("user_provided_media_overlay"),
        episode_id=build_manifest.get("episode_id"),
        timeline_duration_us=build_manifest.get("urakkai", {}).get("target_duration_us", 0),
    )
    if checked_overlay["status"] != "PASS":
        errors.extend(checked_overlay.get("errors", []))
    else:
        errors.extend(user_provided_media_overlay.validate_a10_overlap_policy(
            build_manifest.get("source_audio"), checked_overlay.get("items", []),
        ))
    if not set(manifest_source_ranges).issubset(set(original_ranges)):
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
    empty_values = DECLARED_EMPTY_VALUES

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
                or not times_match(locked.get("start_us"), row.get("start"))
                or not times_match(locked.get("end_us"), row.get("start", 0) + row.get("duration", 0))
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
    parser.add_argument("--urakkai", type=Path)
    parser.add_argument("--original-only", action="store_true")
    parser.add_argument("--emit-report", action="store_true")
    args = parser.parse_args()

    if args.original_only:
        _grid, errors, _context = validate_original(args.original.resolve())
        payload = {"status": "FAIL" if errors else "PASS", "errors": errors}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if errors else 0
    if args.urakkai is None:
        parser.error("--urakkai is required unless --original-only is set")
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
