#!/usr/bin/env python3
"""Validate the locked jungchilong visual skeleton before Stage 2 uses it."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from scan_forbidden_capcut_refs import scan_tree


ALLOWED_VISIBLE_TEXT = {
    "__SOURCE__",
    "출처 __SOURCE__",
    "__DATE__",
    "__FLOW_1__",
    "__FLOW_2__",
    "__FLOW_3__",
    "__FLOW_4__",
    "__FLOW_5__",
    "__FLOW_6__",
    "__FLOW_1__ > __FLOW_2__ > __FLOW_3__\n__FLOW_4__ > __FLOW_5__ > __FLOW_6__",
    "__LOWER_T1_A__",
    "__LOWER_T1_B__",
    "구독과 좋아요는 큰힘이 됩니다. 감사합니다.",
    "구독과 좋아요는 큰 힘이 됩니다. 감사합니다.",
    "구독은 큰힘이 됩니다.",
    "구독은 큰 힘이 됩니다.",
}

FORBIDDEN_BASE_TERMS = [
    "CBS",
    "노컷뉴스",
    "광주MBC",
    "유시민",
    "노무현",
    "이재명",
    "source_full",
    "_locked.mp4",
    "roughcut",
    "YP007",
    "YP005",
    "YM007",
    "YSM",
    "ROH",
]


def normalize_visible_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.strip().splitlines())


def text_contents(draft_json: dict[str, Any]) -> list[str]:
    contents: list[str] = []
    for item in draft_json.get("materials", {}).get("texts", []):
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        text = content
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = None
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            text = parsed["text"]
        normalized = normalize_visible_text(text)
        if normalized:
            contents.append(normalized)
    return contents


def validate_base(base: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "PASS",
        "base": str(base),
        "errors": [],
        "warnings": [],
        "visible_texts": [],
    }

    def error(code: str, detail: str, path: str | Path = "") -> None:
        result["errors"].append({"code": code, "path": str(path), "detail": detail})

    if not base.exists():
        error("WAIT_JUNGCHILONG_BASE_MISSING", "base folder does not exist", base)
        result["status"] = "FAIL"
        return result

    scan = scan_tree(base)
    result["scan"] = scan
    if scan["status"] != "PASS":
        error("FAIL_JUNGCHILONG_DIRTY_BASE", "dirty file, old reference, or mojibake detected")

    draft_path = base / "draft_content.json"
    if not draft_path.exists():
        error("MISSING_DRAFT_CONTENT", "draft_content.json is missing", draft_path)
    else:
        try:
            draft = json.loads(draft_path.read_text(encoding="utf-8"))
        except Exception as exc:
            error("JSON_PARSE_FAILED", str(exc), draft_path)
            draft = {}
        texts = text_contents(draft)
        result["visible_texts"] = texts
        for text in texts:
            if any(term in text for term in FORBIDDEN_BASE_TERMS):
                error("REAL_EPISODE_TEXT_IN_BASE", f"forbidden base text: {text}", draft_path)
            if text not in ALLOWED_VISIBLE_TEXT:
                error("UNKNOWN_VISIBLE_TEXT_IN_BASE", f"not in placeholder allowlist: {text}", draft_path)

    if result["errors"]:
        result["status"] = "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    result = validate_base(Path(args.base))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
