#!/usr/bin/env python3
"""Apply the fixed two-line political-longform source label to a closed draft."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from promote_capcut_root import json_load, json_write, set_material_text


def require_capcut_closed() -> None:
    running = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    if "CapCut.exe" in running.stdout:
        raise RuntimeError("CAPCUT_PROCESS_MUST_BE_CLOSED")


def text_value(material: dict[str, Any]) -> str:
    return json.loads(material["content"])["text"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    require_capcut_closed()
    root = args.project.resolve()
    mirrors = [root / "draft_content.json", root / "template-2.tmp"]
    mirrors += sorted((root / "Timelines").glob("*/draft_content.json"))
    mirrors += sorted((root / "Timelines").glob("*/template-2.tmp"))
    if len(mirrors) != 4 or any(not path.is_file() for path in mirrors):
        raise RuntimeError("DRAFT_MIRROR_SET_INVALID")
    before_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in mirrors}
    if len(before_hashes) != 1:
        raise RuntimeError("DRAFT_MIRRORS_NOT_IN_SYNC")

    document = json_load(root / "draft_content.json")
    matches = [item for item in document["materials"]["texts"] if text_value(item).startswith("출처 ")]
    if len(matches) != 1:
        raise RuntimeError("SOURCE_LABEL_ANCHOR_NOT_UNIQUE")
    label = f"출처 {args.channel.strip()}\n{args.date.strip()}"
    set_material_text(matches[0], label)
    for path in mirrors:
        json_write(path, document)

    after_hashes = {hashlib.sha256(path.read_bytes()).hexdigest() for path in mirrors}
    if len(after_hashes) != 1:
        raise RuntimeError("DRAFT_MIRROR_UPDATE_FAILED")
    print(json.dumps({"status": "PASS", "label": label, "mirror_sha256": after_hashes.pop()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
