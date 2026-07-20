#!/usr/bin/env python3
"""Fail visible placeholder/operator text before CapCut readiness reports."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


FORBIDDEN_EXACT_VISIBLE_TEXT = {"T1", "T2"}
FORBIDDEN_VISIBLE_FRAGMENTS = (
    "의견입력",
    "의견 입력",
    "여기 입력",
    "placeholder",
    "Default",
    "수정필요",
    "수정 필요",
    "작업자",
)
FORBIDDEN_TIMECODE_PATTERNS = (
    re.compile(r"\[\d{1,2}:\d{2}"),
    re.compile(r"\[\d+-"),
)
VISIBLE_TEXT_KEYS = {
    "text",
    "visible_text",
    "content",
    "caption",
    "display_text",
    "value",
}
NON_VISIBLE_ID_KEYS = {
    "track_id",
    "track",
    "role",
    "id",
    "edit_id",
    "source_block_id",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail("visible text json root must be object")
    return data


def check_visible_string(value: str, path: str) -> None:
    stripped = value.strip()
    if stripped in FORBIDDEN_EXACT_VISIBLE_TEXT:
        raise GateFail(f"FAIL_VISIBLE_TEXT_PLACEHOLDER: forbidden visible text {stripped!r} at {path}")
    lowered = stripped.lower()
    for fragment in FORBIDDEN_VISIBLE_FRAGMENTS:
        if fragment.lower() in lowered:
            raise GateFail(f"FAIL_VISIBLE_TEXT_PLACEHOLDER: forbidden visible text fragment {fragment!r} at {path}")
    for pattern in FORBIDDEN_TIMECODE_PATTERNS:
        if pattern.search(stripped):
            raise GateFail(f"FAIL_VISIBLE_TEXT_PLACEHOLDER: visible timecode marker at {path}")


def walk_visible_text(value: Any, path: str = "$", key: str | None = None) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            walk_visible_text(child_value, f"{path}.{child_key}", child_key)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            walk_visible_text(item, f"{path}[{index}]", key)
        return
    if isinstance(value, str):
        if key in NON_VISIBLE_ID_KEYS:
            return
        if key in VISIBLE_TEXT_KEYS or key is None:
            check_visible_string(value, path)


def validate_visible_text_clean(data: dict[str, Any]) -> dict[str, Any]:
    walk_visible_text(data)
    return {"visible_text_clean_status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path")
    args = parser.parse_args()
    try:
        result = validate_visible_text_clean(load_json(Path(args.json_path)))
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
