"""Helpers for the canonical codec regression tests.

These helpers manipulate record lines in rendered MD. They are written
against the round-5 record format which encodes each record as a single
JSON array of two elements: [path_segments_json, value_json]. The exact
serialization is owned by canonical_render; these helpers parse records
back into (segments, value) pairs so the tests can construct precise
mutations (bool<->string, number<->string, duplicate, value rewrite).
"""

from __future__ import annotations

import json
from typing import Any


RECORD_PREFIX = "R "  # canonical_render uses this prefix on each record line.


def _iter_record_lines(md: str):
    """Yield (line_index, parsed_record_or_None) for each line."""
    for i, raw in enumerate(md.splitlines()):
        line = raw.rstrip("\n")
        if line.startswith(RECORD_PREFIX):
            payload = line[len(RECORD_PREFIX):].strip()
            try:
                rec = json.loads(payload)
                if isinstance(rec, list) and len(rec) == 2:
                    yield i, rec
                else:
                    yield i, None
            except json.JSONDecodeError:
                yield i, None
        else:
            yield i, None


def _find_record_line_for_path(md_lines: list[str], leaf_or_path: str):
    """Find the first record line whose path encodes the given path tail
    OR whose path equals the given dotted path."""
    for i, rec in _iter_record_lines("\n".join(md_lines)):
        if rec is None:
            continue
        segments, _value = rec
        # segments is a list. Match if the leaf equals the given string OR
        # the dotted-path reconstruction equals it.
        if isinstance(segments, list):
            if segments and segments[-1] == leaf_or_path:
                return i, rec
            dotted = ".".join(str(s) for s in segments)
            if dotted == leaf_or_path:
                return i, rec
    return None, None


def _rewrite_record_line(rec: list, new_value: Any) -> str:
    segments, _old = rec
    return RECORD_PREFIX + json.dumps([segments, new_value], ensure_ascii=False)


def flip_bool_to_string_record(md: str, path_tail: str) -> str:
    """Rewrite the record at the given path so its value becomes the JSON
    STRING "true" instead of the JSON BOOL true."""
    lines = md.splitlines()
    idx, rec = _find_record_line_for_path(lines, path_tail)
    if idx is None:
        raise ValueError(f"no record line found for path {path_tail!r}")
    segments, value = rec
    if value is not True:
        raise ValueError(f"value at {path_tail!r} is not bool true: {value!r}")
    lines[idx] = _rewrite_record_line([segments, value], "true")
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")


def flip_number_to_string_record(md: str, path_tail: str) -> str:
    lines = md.splitlines()
    idx, rec = _find_record_line_for_path(lines, path_tail)
    if idx is None:
        raise ValueError(f"no record line found for path {path_tail!r}")
    segments, value = rec
    if value != 1 or isinstance(value, bool):
        raise ValueError(f"value at {path_tail!r} is not number 1: {value!r}")
    lines[idx] = _rewrite_record_line([segments, value], "1")
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")


def duplicate_record_line(md: str, path_tail: str) -> str:
    """Duplicate the record line at the given path."""
    lines = md.splitlines()
    idx, rec = _find_record_line_for_path(lines, path_tail)
    if idx is None:
        raise ValueError(f"no record line found for path {path_tail!r}")
    lines.insert(idx + 1, lines[idx])
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")


def rewrite_record_value(md: str, path_tail: str, new_value: Any) -> str:
    lines = md.splitlines()
    idx, rec = _find_record_line_for_path(lines, path_tail)
    if idx is None:
        raise ValueError(f"no record line found for path {path_tail!r}")
    segments, _old = rec
    lines[idx] = _rewrite_record_line([segments, _old], new_value)
    return "\n".join(lines) + ("\n" if md.endswith("\n") else "")
