#!/usr/bin/env python3
"""Validate the reusable politics longform HyperFrames template contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = (
    "index.html",
    "hyperframes.json",
    "package.json",
    "style_tokens.json",
    "design.md",
    "validation_report.json",
    "tests/test_template_contract.py",
    "src/styles.css",
    "src/template.js",
    "compositions/narration-explainer.html",
    "compositions/source-video.html",
    "compositions/chapter-transition.html",
    "compositions/timeline_manifest.json",
    "assets/media/source-placeholder.mp4",
    "assets/audio/source-placeholder.wav",
)
REQUIRED_COMPOSITIONS = (
    "narration-explainer",
    "source-video",
    "chapter-transition",
)
REQUIRED_TOKENS = (
    "canvas",
    "safeArea",
    "frame",
    "focusLines",
    "chapter",
    "source",
    "comment",
    "subscribe",
    "captionBand",
    "captionText",
    "animation",
    "zIndex",
)
REQUIRED_ROLES = (
    "top-frame",
    "bottom-frame",
    "focus-lines",
    "chapter-number",
    "chapter-title",
    "source-label",
    "source-date",
    "comment-label",
    "subscribe-label",
    "lower-caption-band",
    "caption-text",
)


def read_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"INVALID_JSON:{path.name}:{exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON_ROOT_NOT_OBJECT:{path.name}")
        return {}
    return value


def duplicates(values: list[str]) -> set[str]:
    return {value for value in values if values.count(value) > 1}


def validate_project(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"MISSING_FILE:{relative}")
        elif path.stat().st_size == 0:
            errors.append(f"EMPTY_FILE:{relative}")

    tokens_path = root / "style_tokens.json"
    if tokens_path.is_file():
        tokens = read_json(tokens_path, errors)
        for group in REQUIRED_TOKENS:
            if group not in tokens:
                errors.append(f"MISSING_TOKEN_GROUP:{group}")

    manifest_path = root / "compositions/timeline_manifest.json"
    if manifest_path.is_file():
        manifest = read_json(manifest_path, errors)
        entries = manifest.get("compositions", [])
        manifest_ids = [entry.get("id") for entry in entries if isinstance(entry, dict)]
        manifest_names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
        for composition_id in REQUIRED_COMPOSITIONS:
            if composition_id not in manifest_ids:
                errors.append(f"MISSING_MANIFEST_COMPOSITION:{composition_id}")
            if composition_id not in manifest_names:
                errors.append(f"MISSING_MANIFEST_NAME:{composition_id}")

    authored = ""
    for relative in (
        "index.html",
        "src/styles.css",
        "src/template.js",
        "compositions/narration-explainer.html",
        "compositions/source-video.html",
        "compositions/chapter-transition.html",
    ):
        path = root / relative
        if path.is_file():
            authored += "\n" + path.read_text(encoding="utf-8")

    for composition_id in REQUIRED_COMPOSITIONS:
        if f'data-composition-id="{composition_id}"' not in authored:
            errors.append(f"MISSING_COMPOSITION_ID:{composition_id}")
    for role in REQUIRED_ROLES:
        if role not in authored:
            errors.append(f"MISSING_DOM_ROLE:{role}")

    for path in (root / "compositions").glob("*.html") if (root / "compositions").is_dir() else ():
        text = path.read_text(encoding="utf-8")
        ids = re.findall(r'(?<!-)\bid=["\']([^"\']+)["\']', text)
        hf_ids = re.findall(r'\bdata-hf-id=["\']([^"\']+)["\']', text)
        for value in sorted(duplicates(ids)):
            errors.append(f"DUPLICATE_DOM_ID:{path.name}:{value}")
        for value in sorted(duplicates(hf_ids)):
            errors.append(f"DUPLICATE_HF_ID:{path.name}:{value}")

    scan_extensions = {".html", ".css", ".js", ".svg"}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in scan_extensions:
            text = path.read_text(encoding="utf-8")
            for match in re.findall(r"https?://[^\s'\"<>]+", text, flags=re.I):
                if not re.match(r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?", match, re.I):
                    errors.append(f"REMOTE_ASSET:{path.relative_to(root)}:{match}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = validate_project(args.project)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
