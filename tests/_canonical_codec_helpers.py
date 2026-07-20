"""Helpers for the canonical codec regression tests.

These helpers manipulate record lines in rendered MD. They are written
against the round-6 record format which encodes each record as a single
JSON array of two elements: ``[path_segments, value]`` where each segment
in ``path_segments`` is itself a ``[kind, name]`` pair (``kind`` is
``"key"`` or ``"idx"``). The exact serialization is owned by
canonical_render; these helpers parse records back into structured forms
so the tests can construct precise mutations.
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


def _segments_to_path_strings(segments: list[list[str]]) -> list[str]:
    """Convert [[kind, name], ...] to dotted-path-friendly tokens.

    For matching convenience, key segments contribute their name and idx
    segments contribute their bracketed name (e.g. ``[0]``)."""
    out: list[str] = []
    for seg in segments:
        if not isinstance(seg, list) or len(seg) != 2:
            return []
        kind, name = seg
        if kind == "key":
            out.append(name)
        elif kind == "idx":
            out.append(name)  # already in "[i]" form
        else:
            out.append(name)
    return out


def _find_record_line_for_path(md_lines: list[str], path: str):
    """Find the first record line whose segments match the given path.

    ``path`` may be a leaf name (e.g. ``"title"``) or a dotted path
    (e.g. ``"chapter_a.title"``). For dotted paths we compare the dotted
    reconstruction of key/idx names. For leaf names we match on the last
    segment's name.
    """
    for i, rec in _iter_record_lines("\n".join(md_lines)):
        if rec is None:
            continue
        segments, _value = rec
        if not isinstance(segments, list):
            continue
        names = _segments_to_path_strings(segments)
        if not names:
            continue
        if names[-1] == path:
            return i, rec
        dotted = ".".join(names)
        if dotted == path:
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
