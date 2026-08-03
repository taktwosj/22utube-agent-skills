#!/usr/bin/env python3
"""Read a closed CapCut relink probe and write a portable implementation contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from promote_capcut_root import json_load, json_write, sha256


def require_capcut_closed() -> None:
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    if "CapCut.exe" in result.stdout:
        raise RuntimeError("CAPCUT_PROCESS_MUST_BE_CLOSED")


def text_value(material: dict[str, Any]) -> str:
    return json.loads(material["content"])["text"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--build-report", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    require_capcut_closed()

    root = args.project.resolve()
    build = json_load(args.build_report)
    mirrors = [root / "draft_content.json", root / "template-2.tmp"]
    mirrors += sorted((root / "Timelines").glob("*/draft_content.json"))
    mirrors += sorted((root / "Timelines").glob("*/template-2.tmp"))
    if len(mirrors) != 4 or any(not path.is_file() for path in mirrors):
        raise RuntimeError("DRAFT_MIRROR_SET_INVALID")
    hashes = {sha256(path) for path in mirrors}
    if len(hashes) != 1:
        raise RuntimeError("DRAFT_MIRRORS_NOT_IN_SYNC")

    document = json_load(root / "draft_content.json")
    source_basename = build.get("media_filename", "C003_S03_chapter_video.mp4")
    materials = [item for item in document["materials"]["videos"] if Path(item.get("path", "")).name == source_basename]
    material = materials[0] if len(materials) == 1 else None
    actual_path = Path(material["path"]) if material else None
    media_persisted = bool(
        actual_path
        and actual_path.is_file()
        and sha256(actual_path).upper() == build["media_sha256"].upper()
        and "__CAPCUT_RELINK_REQUIRED__" not in material["path"]
    )
    expected_media_dir = Path(build["media_folder_to_select"]).resolve()
    selected_folder_matches = bool(actual_path and actual_path.resolve().parent == expected_media_dir)

    chapter_materials = [
        item for item in document["materials"]["texts"]
        if text_value(item).startswith("챕터 ") and "\n" not in text_value(item)
    ]
    if len(chapter_materials) != 1:
        raise RuntimeError("CHAPTER_TEXT_NOT_UNIQUE")
    chapter_id = chapter_materials[0]["id"]
    chapter_segments = [segment for track in document["tracks"] for segment in track.get("segments", []) if segment.get("material_id") == chapter_id]
    if len(chapter_segments) != 1:
        raise RuntimeError("CHAPTER_SEGMENT_NOT_UNIQUE")
    chapter_range = chapter_segments[0]["target_timerange"]

    cta_materials = [
        item for item in document["materials"]["texts"]
        if text_value(item) == "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!"
    ]
    if len(cta_materials) != 1:
        raise RuntimeError("CTA_TEXT_NOT_UNIQUE")
    cta_id = cta_materials[0]["id"]
    cta_segments = [segment for track in document["tracks"] for segment in track.get("segments", []) if segment.get("material_id") == cta_id]
    if len(cta_segments) != 1:
        raise RuntimeError("CTA_SEGMENT_NOT_UNIQUE")
    cta_range = cta_segments[0]["target_timerange"]

    source_labels = [text_value(item) for item in document["materials"]["texts"] if text_value(item).startswith("출처 ")]
    if len(source_labels) != 1 or source_labels[0].count("\n") != 1:
        raise RuntimeError("SOURCE_LABEL_NOT_TWO_LINES")

    report = {
        "schema": "politics-longform-capcut-relink-readback.v1",
        "status": (
            "MEDIA_RELINKED" if media_persisted and selected_folder_matches
            else "WARN_MEDIA_RELINK_PATH_REUSED" if media_persisted
            else "FAIL_MEDIA_RELINK_PERSISTENCE"
        ),
        "kind": build["kind"],
        "project": str(root),
        "draft_mirror_sha256": hashes.pop(),
        "media_relink": {
            "before_path": build["requested_offline_path"],
            "after_path": str(actual_path) if actual_path else None,
            "media_sha256": build["media_sha256"],
            "capcut_material_name_after": material.get("material_name", "") if material else None,
            "capcut_duration_us_after": material.get("duration") if material else None,
            "persisted": media_persisted,
            "expected_media_folder": str(expected_media_dir),
            "selected_folder_matches": selected_folder_matches,
        },
        "presentation_contract": {
            "chapter_hud": {
                "text": text_value(chapter_materials[0]),
                "start_us": chapter_range["start"],
                "duration_us": chapter_range["duration"],
            },
            "cta_hud": {
                "text": text_value(cta_materials[0]),
                "start_us": cta_range["start"],
                "duration_us": cta_range["duration"],
            },
            "source_label_lines": source_labels[0].split("\n"),
        },
    }
    json_write(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
