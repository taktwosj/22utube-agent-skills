#!/usr/bin/env python3
"""Read a closed CapCut card project and verify relink plus presentation state."""
from __future__ import annotations

import argparse
import copy
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


def find_final_placeholders(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            lower_key = key.casefold()
            if lower_key in {"online_id", "request_id"} and item:
                found.append(item_path)
            if lower_key == "onlinematerial":
                found.append(item_path)
            found.extend(find_final_placeholders(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(find_final_placeholders(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        normalized = value.replace("\\", "/").casefold()
        if "onlinematerial" in normalized or "__capcut_relink_required__" in normalized:
            found.append(path)
    return sorted(set(found))


def expected_media(build: dict[str, Any]) -> list[dict[str, Any]]:
    records = build.get("media")
    if isinstance(records, dict):
        expected: list[dict[str, Any]] = []
        for card_id, record in records.items():
            expected.append({
                "card_id": card_id,
                "asset_role": "primary_visual",
                "material_group": "videos",
                "filename": record["filename"],
                "sha256": record["sha256"],
                "requested_offline_path": record.get("offline_path"),
                "storage": record.get("storage"),
            })
            narration_audio = record.get("narration_audio")
            if isinstance(narration_audio, dict):
                expected.append({
                    "card_id": card_id,
                    "asset_role": "narration_audio",
                    "material_group": "audios",
                    "filename": narration_audio["filename"],
                    "sha256": narration_audio["sha256"],
                    "requested_offline_path": narration_audio.get("offline_path"),
                    "storage": narration_audio.get("storage"),
                })
        return expected
    return [
        {
            "card_id": None,
            "asset_role": "primary_visual",
            "material_group": "videos",
            "filename": build.get("media_filename", "C003_S03_chapter_video.mp4"),
            "sha256": build["media_sha256"],
            "requested_offline_path": build["requested_offline_path"],
            "storage": "relink",
        }
    ]


def resolve_expected_media_dir(build: dict[str, Any], media_dir: Path | None) -> Path:
    reference = build.get("media_folder_to_select")
    if not isinstance(reference, str) or not reference.strip():
        raise RuntimeError("FAIL_MEDIA_FOLDER_REFERENCE_INVALID")
    normalized = reference.replace("\\", "/")
    if normalized.startswith("LOCAL_MEDIA_FOLDER/"):
        if media_dir is None:
            raise RuntimeError("WAIT_PRIVATE_MEDIA_DIR_REQUIRED")
        resolved = media_dir.resolve()
        expected_reference = "/".join(
            ["LOCAL_MEDIA_FOLDER", resolved.parent.name, resolved.name]
        )
        if normalized != expected_reference:
            raise RuntimeError("FAIL_PRIVATE_MEDIA_DIR_MISMATCH")
        return resolved
    legacy = Path(reference)
    if legacy.is_absolute():
        return legacy.resolve()
    raise RuntimeError("FAIL_MEDIA_FOLDER_REFERENCE_INVALID")


def readback_media(
    document: dict[str, Any],
    build: dict[str, Any],
    expected_folder: Path,
    public_folder: str,
) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    for expected in expected_media(build):
        materials = document.get("materials", {}).get(expected["material_group"], [])
        matches = [
            item
            for item in materials
            if item.get("material_name") == expected["filename"]
            or item.get("name") == expected["filename"]
            or Path(item.get("path", "")).name == expected["filename"]
        ]
        material = matches[0] if len(matches) == 1 else None
        actual_path = Path(material["path"]) if material and material.get("path") else None
        persisted = bool(
            actual_path
            and actual_path.is_file()
            and sha256(actual_path).upper() == expected["sha256"].upper()
            and "__CAPCUT_RELINK_REQUIRED__" not in material["path"]
            and "onlinematerial" not in material["path"].replace("\\", "/").casefold()
        )
        folder_matches = expected["storage"] == "embedded" or bool(
            actual_path and actual_path.resolve().parent == expected_folder
        )
        results.append(
            {
                "card_id": expected["card_id"],
                "asset_role": expected["asset_role"],
                "filename": expected["filename"],
                "storage": expected["storage"],
                "before_path": f"CAPCUT_RELINK_PLACEHOLDER/{expected['filename']}",
                "after_path": f"{public_folder}/{actual_path.name}" if actual_path else None,
                "media_sha256": expected["sha256"],
                "capcut_material_name_after": material.get("material_name", "") if material else None,
                "capcut_duration_us_after": material.get("duration") if material else None,
                "persisted": persisted,
                "expected_media_folder": public_folder,
                "selected_folder_matches": folder_matches,
            }
        )
    return results, bool(results) and all(
        item["persisted"] and item["selected_folder_matches"] for item in results
    )


def readback_presentation_contract(
    document: dict[str, Any], expected: dict[str, Any] | None
) -> dict[str, Any] | None:
    if not expected:
        return None
    materials = {
        item.get("id"): item for item in document.get("materials", {}).get("texts", [])
    }

    def resolve(row: dict[str, Any]) -> dict[str, Any] | None:
        material = materials.get(row.get("material_id"))
        if material is None:
            return None
        matches = [
            (index, track, segment)
            for index, track in enumerate(document.get("tracks", []))
            for segment in track.get("segments", [])
            if segment.get("id") == row.get("segment_id")
            and segment.get("material_id") == material.get("id")
        ]
        if len(matches) != 1:
            return None
        index, track, segment = matches[0]
        return {
            "material_id": material["id"],
            "segment_id": segment["id"],
            "text": json.loads(material["content"])["text"],
            "target_timerange": copy.deepcopy(segment.get("target_timerange", {})),
            "track_type": track.get("type"),
            "track_index": index,
            "track_id": track.get("id"),
            "clip_geometry": copy.deepcopy(segment.get("clip", {})),
        }

    source_rows = [resolve(row) for row in expected.get("source_date_hud", [])]
    lower_rows = [resolve(row) for row in expected.get("lower_slots", [])]
    cta_row = resolve(expected.get("cta_hud", {}))
    if cta_row is None or any(row is None for row in source_rows + lower_rows):
        return None
    return {
        "source_date_hud": source_rows,
        "cta_hud": cta_row,
        "lower_slots": lower_rows,
    }


def unexpected_presentation_segments(
    document: dict[str, Any], expected: dict[str, Any] | None
) -> list[str]:
    if not expected:
        return []
    expected_rows = (
        list(expected.get("source_date_hud", []))
        + [expected.get("cta_hud", {})]
        + list(expected.get("lower_slots", []))
    )
    expected_pairs = {
        (row.get("material_id"), row.get("segment_id")) for row in expected_rows
    }
    lower_material_ids = {
        row.get("material_id") for row in expected.get("lower_slots", [])
    }
    lower_texts = {row.get("text") for row in expected.get("lower_slots", [])}
    role_layouts = {
        (
            row.get("track_type"),
            json.dumps(row.get("clip_geometry", {}), sort_keys=True),
        )
        for row in expected_rows
    }
    text_by_id = {
        item.get("id"): json.loads(item["content"])["text"]
        for item in document.get("materials", {}).get("texts", [])
    }
    unexpected: list[str] = []
    for track_index, track in enumerate(document.get("tracks", [])):
        for segment in track.get("segments", []):
            material_id = segment.get("material_id")
            text = text_by_id.get(material_id, "")
            is_role = (
                text.startswith(("출처 ", "구독은 "))
                or material_id in lower_material_ids
                or text in lower_texts
                or (
                    track.get("type"),
                    json.dumps(segment.get("clip", {}), sort_keys=True),
                )
                in role_layouts
            )
            if is_role and (material_id, segment.get("id")) not in expected_pairs:
                unexpected.append(f"tracks[{track_index}].segments[{segment.get('id')}]")
    return unexpected


def legacy_presentation_fields(document: dict[str, Any]) -> dict[str, Any]:
    text_by_id = {
        item.get("id"): json.loads(item["content"])["text"]
        for item in document.get("materials", {}).get("texts", [])
    }
    rows = [
        (text_by_id.get(segment.get("material_id"), ""), segment)
        for track in document.get("tracks", [])
        for segment in track.get("segments", [])
    ]

    def timed(row: tuple[str, dict[str, Any]]) -> dict[str, Any]:
        text, segment = row
        timerange = segment["target_timerange"]
        return {
            "text": text,
            "start_us": timerange["start"],
            "duration_us": timerange["duration"],
        }

    chapters = [row for row in rows if row[0].startswith("챕터 ") and "\n" not in row[0]]
    ctas = [row for row in rows if row[0] == "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!"]
    sources = [row[0] for row in rows if row[0].startswith("출처 ") and row[0].count("\n") == 1]
    return {
        "chapter_hud": timed(chapters[0]) if len(chapters) == 1 else None,
        "cta_hud": timed(ctas[0]) if len(ctas) == 1 else None,
        "source_label_lines": sources[0].split("\n") if len(sources) == 1 else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--build-report", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--media-dir", type=Path)
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
    try:
        expected_media_dir = resolve_expected_media_dir(build, args.media_dir)
    except RuntimeError as error:
        status = str(error)
        report = {
            "schema": "politics-longform-capcut-relink-readback.v1",
            "status": status,
            "kind": build.get("kind", "POLITICS_CAPCUT_CARD_PROJECT"),
            "project": f"LOCAL_CAPCUT_DRAFT/{root.name}",
            "PROJECT_BUILD": "WAIT",
            "STATIC_STRUCTURE": "WAIT",
            "MEDIA_RELINK": "WAIT" if status.startswith("WAIT_") else "FAIL",
            "MEDIA_RESOLUTION": "WAIT" if status.startswith("WAIT_") else "FAIL",
            "VISUAL_GATE": "WAIT_USER_VISUAL_GATE",
            "MP4": "NOT_RUN",
            "UPLOAD": "NOT_RUN",
            "media_relink": {
                "mapping_status": status,
                "public_media_folder_reference": build.get("media_folder_to_select"),
                "expected_media_folder": None,
            },
        }
        json_write(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    media_folder_reference = str(build["media_folder_to_select"]).replace("\\", "/")
    public_media_folder = (
        media_folder_reference
        if media_folder_reference.startswith("LOCAL_MEDIA_FOLDER/")
        else "/".join(
            ["LOCAL_MEDIA_FOLDER", expected_media_dir.parent.name, expected_media_dir.name]
        )
    )
    media_rows, media_persisted = readback_media(
        document, build, expected_media_dir, public_media_folder
    )
    placeholders = find_final_placeholders(document)
    expected_presentation = copy.deepcopy(
        build.get("static_validation", {}).get("presentation_contract")
    )
    legacy_presentation = legacy_presentation_fields(document)
    actual_presentation = readback_presentation_contract(document, expected_presentation)
    unexpected_segments = unexpected_presentation_segments(document, expected_presentation)
    if expected_presentation:
        hud_matches: bool | None = bool(actual_presentation) and all(
            actual_presentation.get(role) == expected_presentation.get(role)
            for role in ("source_date_hud", "cta_hud")
        )
        lower_matches: bool | None = bool(actual_presentation) and (
            actual_presentation.get("lower_slots") == expected_presentation.get("lower_slots")
        )
        presentation_matches = hud_matches and lower_matches and not unexpected_segments
        presentation_evidence = "SNAPSHOT"
    else:
        presentation_matches = all(legacy_presentation.values())
        hud_matches = None
        lower_matches = None
        presentation_evidence = "LEGACY_V1"
    media_resolution = media_persisted and not placeholders
    project_build = (
        build.get("status") == "PROJECT_CREATED_WAIT_MEDIA_RELINK"
        and build.get("static_validation", {}).get("status") == "PASS"
    )
    static_structure = project_build and presentation_matches
    status = (
        "FAIL_MEDIA_RELINK_PERSISTENCE"
        if not media_resolution
        else "FAIL_PROJECT_BUILD_EVIDENCE"
        if not project_build
        else "FAIL_PRESENTATION_CONTRACT"
        if not presentation_matches
        else "MEDIA_RELINKED"
    )
    media_summary: dict[str, Any] = {
        "items": media_rows,
        "persisted": media_persisted,
        "expected_media_folder": public_media_folder,
        "selected_folder_matches": bool(media_rows) and all(
            item["selected_folder_matches"] for item in media_rows
        ),
    }
    if len(media_rows) == 1:
        media_summary.update(media_rows[0])

    report = {
        "schema": "politics-longform-capcut-relink-readback.v1",
        "status": status,
        "kind": build.get("kind", "POLITICS_CAPCUT_CARD_PROJECT"),
        "project": f"LOCAL_CAPCUT_DRAFT/{root.name}",
        "draft_mirror_sha256": hashes.pop(),
        "PROJECT_BUILD": "PASS" if project_build else "FAIL",
        "STATIC_STRUCTURE": "PASS" if static_structure else "FAIL",
        "MEDIA_RELINK": "PASS" if media_resolution else "FAIL",
        "MEDIA_RESOLUTION": "PASS" if media_resolution else "FAIL",
        "FINAL_DRAFT_PLACEHOLDER_SCAN": "PASS" if not placeholders else "FAIL",
        "HUD_TRACK_GEOMETRY": (
            "WAIT_LEGACY_V1_NO_GEOMETRY_SNAPSHOT"
            if hud_matches is None
            else "PASS" if hud_matches else "FAIL"
        ),
        "LOWER_SLOT_TRACK_GEOMETRY": (
            "WAIT_LEGACY_V1_NO_GEOMETRY_SNAPSHOT"
            if lower_matches is None
            else "PASS" if lower_matches else "FAIL"
        ),
        "VISUAL_GATE": "WAIT_USER_VISUAL_GATE",
        "MP4": "NOT_RUN",
        "UPLOAD": "NOT_RUN",
        "final_draft_placeholder_scan": {
            "status": "PASS" if not placeholders else "FAIL",
            "paths": placeholders,
        },
        "media_relink": media_summary,
        "presentation_contract": {
            **legacy_presentation,
            "evidence_mode": presentation_evidence,
            "matches": presentation_matches,
            "expected": expected_presentation,
            "actual": actual_presentation,
            "unexpected_role_segments": unexpected_segments,
        },
    }
    json_write(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "MEDIA_RELINKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
