#!/usr/bin/env python3
"""Promote a closed CapCut draft into a clean, portable root template.

The source draft is never changed.  This script only deletes backup/helper files
from a uniquely named staging copy and publishes the resulting clean root.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any


MICROS = 1_000_000
UUID_RE = re.compile(
    r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b"
)
JUNK_RE = re.compile(r"(?i)(\.bak$|^\.before_|^before_|_backup_|^helper_)")
LEGACY_FONT_RE = re.compile(
    r"C:(?:/|\\\\)Users(?:/|\\\\)[^/\\\\]+(?:/|\\\\)AppData(?:/|\\\\)Local"
    r"(?:/|\\\\)CapCut(?:/|\\\\)User Data(?:/|\\\\)Projects(?:/|\\\\)com\.lveditor\.draft"
    r"(?:/|\\\\)[^/\\\\]+(?:/|\\\\)Resources(?:/|\\\\)fonts(?:/|\\\\)lower-panel-font\.ttf"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_write(path: Path, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(payload, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def posix(path: Path) -> str:
    return path.as_posix()


def file_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return records


def collect_uuids(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for item in value.values():
            collect_uuids(item, found)
    elif isinstance(value, list):
        for item in value:
            collect_uuids(item, found)
    elif isinstance(value, str):
        found.update(match.group(0) for match in UUID_RE.finditer(value))


def rewrite_value(value: Any, id_map: dict[str, str], replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"online_id", "request_id"}:
                result[key] = ""
            else:
                result[key] = rewrite_value(item, id_map, replacements)
        return result
    if isinstance(value, list):
        return [rewrite_value(item, id_map, replacements) for item in value]
    if isinstance(value, str):
        for old, new in replacements.items():
            value = value.replace(old, new)
        return UUID_RE.sub(lambda match: id_map.get(match.group(0), match.group(0)), value)
    return value


def rewrite_legacy_font_paths(value: Any, final_root: Path) -> Any:
    """Keep every text material self-contained after a draft was cloned."""
    if isinstance(value, dict):
        return {key: rewrite_legacy_font_paths(item, final_root) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_legacy_font_paths(item, final_root) for item in value]
    if isinstance(value, str):
        return LEGACY_FONT_RE.sub(
            posix(final_root / "Resources" / "fonts" / "lower-panel-font.ttf"), value
        )
    return value


def strip_external_video_materials(document: dict[str, Any], final_root: Path) -> None:
    """A relink probe's test media must never leak into a reusable root."""
    root_prefix = posix(final_root).lower().rstrip("/") + "/"
    videos = document.get("materials", {}).get("videos", [])
    removed_ids = {
        item.get("id")
        for item in videos
        if item.get("path")
        and not item["path"].replace("\\", "/").lower().startswith(root_prefix)
    }
    if not removed_ids:
        return
    document["materials"]["videos"] = [item for item in videos if item.get("id") not in removed_ids]
    cleaned_tracks: list[dict[str, Any]] = []
    for track in document.get("tracks", []):
        segments = [
            segment for segment in track.get("segments", []) if segment.get("material_id") not in removed_ids
        ]
        if segments or track.get("type") != "video":
            track["segments"] = segments
            cleaned_tracks.append(track)
    document["tracks"] = cleaned_tracks


def content_text(material: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    content = json.loads(material.get("content", "{}"))
    return material, content


def set_material_text(material: dict[str, Any], text: str) -> None:
    outer, content = content_text(material)
    content["text"] = text
    styles = content.get("styles", [])
    for style in styles:
        style["range"] = [0, len(text)]
    outer["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))


def set_segment_range(segment: dict[str, Any], start_us: int, duration_us: int) -> None:
    segment["target_timerange"] = {"start": start_us, "duration": duration_us}


def normalize_content(
    document: dict[str, Any], *, duration_us: int, content_start_us: int
) -> None:
    materials = document.get("materials", {})
    text_by_id = {item.get("id"): item for item in materials.get("texts", [])}
    videos = materials.get("videos", [])
    if len(videos) < 2:
        raise RuntimeError("ROOT_REQUIRES_INTRO_AND_MAIN_VIDEO_MATERIALS")

    text_ranges: dict[str, list[dict[str, Any]]] = {}
    for track in document.get("tracks", []):
        if track.get("type") != "text":
            continue
        for segment in track.get("segments", []):
            text_ranges.setdefault(segment.get("material_id", ""), []).append(
                segment.get("target_timerange", {})
            )

    lower_duration = duration_us - content_start_us
    if lower_duration <= 0:
        raise RuntimeError("INVALID_ROOT_DURATION")

    for material in materials.get("texts", []):
        _, content = content_text(material)
        text = content.get("text", "")
        ranges = text_ranges.get(material.get("id", ""), [])
        only_range = ranges[0] if len(ranges) == 1 else {}
        start = only_range.get("start")
        duration = only_range.get("duration")
        is_intro = start == 0 and duration == content_start_us
        is_lower_slot = (
            start is not None
            and duration is not None
            and start >= content_start_us
            and start + duration == duration_us
            and "\n" in text
            and not text.startswith("구독은 ")
            and not text.startswith("출처 ")
        )
        if text == "TTS" or is_lower_slot:
            set_material_text(material, "__LOWER_LINE_1__\n__LOWER_LINE_2__")
        elif text == "intro" or is_intro:
            set_material_text(material, "__INTRO_HOOK_LINE_1__\n__INTRO_HOOK_LINE_2__")
        elif (text == "챕터 ") or (text.startswith("챕터 ") and "\n" not in text):
            set_material_text(material, "__CHAPTER__")
        elif text == "출처 " or text.startswith("출처 "):
            set_material_text(material, "출처 __SOURCE__\n__DATE__")

    for track in materials and document.get("tracks", []):
        track_type = track.get("type")
        for segment in track.get("segments", []):
            material_id = segment.get("material_id")
            if track_type == "video":
                if material_id == videos[0].get("id"):
                    set_segment_range(segment, 0, content_start_us)
                    segment["source_timerange"] = {"start": 0, "duration": content_start_us}
                elif material_id == videos[1].get("id"):
                    set_segment_range(segment, content_start_us, lower_duration)
            elif track_type == "text":
                material = text_by_id.get(material_id)
                if material is None:
                    continue
                _, content = content_text(material)
                if content.get("text", "").startswith("__INTRO_HOOK_"):
                    set_segment_range(segment, 0, content_start_us)
                else:
                    set_segment_range(segment, content_start_us, lower_duration)
            elif track_type == "sticker":
                set_segment_range(segment, content_start_us, lower_duration)

    videos[0]["duration"] = content_start_us
    document["duration"] = duration_us


def walk_strings(value: Any, hits: list[str]) -> None:
    if isinstance(value, dict):
        for item in value.values():
            walk_strings(item, hits)
    elif isinstance(value, list):
        for item in value:
            walk_strings(item, hits)
    elif isinstance(value, str):
        if "Cache/" in value or "Cache\\" in value:
            hits.append(value)


def material_ids(document: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for values in document.get("materials", {}).values():
        if isinstance(values, list):
            for item in values:
                if isinstance(item, dict) and item.get("id"):
                    result.add(item["id"])
    return result


def validate_root(root: Path, content_start_us: int, *, path_reference: Path | None = None) -> dict[str, Any]:
    banned = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if JUNK_RE.search(path.name)
    ]
    if banned:
        raise RuntimeError("ROOT_JUNK_PRESENT:" + ",".join(sorted(banned)))

    timelines = sorted((root / "Timelines").glob("*/draft_content.json"))
    if len(timelines) != 1:
        raise RuntimeError("ROOT_REQUIRES_EXACTLY_ONE_TIMELINE")
    mirror_paths = [
        root / "draft_content.json",
        root / "template-2.tmp",
        timelines[0],
        timelines[0].with_name("template-2.tmp"),
    ]
    mirror_hashes = [sha256(path) for path in mirror_paths]
    if len(set(mirror_hashes)) != 1:
        raise RuntimeError("JSON_MIRROR_MISMATCH")

    document = json_load(root / "draft_content.json")
    root_prefix = posix(path_reference or root).lower().rstrip("/") + "/"
    foreign_video_paths = [
        item.get("path", "")
        for item in document.get("materials", {}).get("videos", [])
        if item.get("path")
        and not item["path"].replace("\\", "/").lower().startswith(root_prefix)
    ]
    if foreign_video_paths:
        raise RuntimeError("FOREIGN_VIDEO_PATH_PRESENT:" + " | ".join(foreign_video_paths[:3]))
    duration_us = int(document["duration"])
    text_by_id = {item.get("id"): item for item in document["materials"].get("texts", [])}
    ids = material_ids(document)
    invalid_segments: list[str] = []
    lower_segments: list[dict[str, Any]] = []
    intro_segments: list[dict[str, Any]] = []
    for track in document.get("tracks", []):
        for segment in track.get("segments", []):
            if segment.get("material_id") not in ids:
                invalid_segments.append(str(segment.get("material_id")))
            material = text_by_id.get(segment.get("material_id"))
            if material:
                _, content = content_text(material)
                text = content.get("text", "")
                if text == "__LOWER_LINE_1__\n__LOWER_LINE_2__":
                    lower_segments.append(segment)
                if text == "__INTRO_HOOK_LINE_1__\n__INTRO_HOOK_LINE_2__":
                    intro_segments.append(segment)
    if invalid_segments:
        raise RuntimeError("SEGMENT_MATERIAL_MISSING")
    if len(lower_segments) != 1:
        raise RuntimeError("LOWER_TWO_LINE_SLOT_COUNT_INVALID")
    if len(intro_segments) != 1:
        raise RuntimeError("INTRO_TEXT_SLOT_COUNT_INVALID")
    if lower_segments[0]["target_timerange"] != {
        "start": content_start_us,
        "duration": duration_us - content_start_us,
    }:
        raise RuntimeError("LOWER_TWO_LINE_SLOT_TIMING_INVALID")
    if intro_segments[0]["target_timerange"] != {"start": 0, "duration": content_start_us}:
        raise RuntimeError("INTRO_TEXT_SLOT_TIMING_INVALID")

    external_hits: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".tmp"}:
            try:
                walk_strings(json_load(path), external_hits)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    if external_hits:
        raise RuntimeError("FOREIGN_CACHE_PATH_PRESENT:" + " | ".join(sorted(set(external_hits))[:5]))

    return {
        "status": "PASS",
        "content_start_sec": content_start_us / MICROS,
        "duration_sec": duration_us / MICROS,
        "mirror_sha256": mirror_hashes[0],
        "track_count": len(document.get("tracks", [])),
        "text_material_count": len(document["materials"].get("texts", [])),
        "lower_slot_count": len(lower_segments),
        "intro_slot_count": len(intro_segments),
    }


def copy_required_resources(source_root: Path, stage: Path, ffmpeg: str, final_root: Path) -> dict[str, str]:
    cache = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Cache"
    intro_source = cache / "onlineMaterial" / "ef5698ccb230899728b7a842abf9ec39.mp4"
    main_slot_source = cache / "onlineMaterial" / "1e65543d3133b8129357b0b0b4c1211e.png"
    texture_source = cache / "onlineMaterial" / "74ce29b9d8294a2c88c345a10249e987"
    font_source = cache / "effect" / "7528305055972199681" / "0e4893968fe2d82714917f69c69826aa" / "font.ttf"
    for path in (intro_source, main_slot_source, texture_source, font_source):
        if not path.is_file():
            raise RuntimeError(f"REQUIRED_ROOT_RESOURCE_MISSING:{path}")

    media = stage / "Resources" / "media"
    textures = stage / "Resources" / "textures"
    fonts = stage / "Resources" / "fonts"
    media.mkdir(parents=True, exist_ok=True)
    textures.mkdir(parents=True, exist_ok=True)
    fonts.mkdir(parents=True, exist_ok=True)
    intro_target = media / "123123.mp4"
    main_slot_target = media / "main-video-slot.png"
    texture_target = textures / "lower-panel-texture.bin"
    font_target = fonts / "lower-panel-font.ttf"
    subprocess.run(
        [ffmpeg, "-y", "-ss", "0", "-t", "10", "-i", str(intro_source), "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(intro_target)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    shutil.copy2(main_slot_source, main_slot_target)
    shutil.copy2(texture_source, texture_target)
    shutil.copy2(font_source, font_target)
    targets = {
        "onlineMaterial/ef5698ccb230899728b7a842abf9ec39.mp4": posix(final_root / "Resources" / "media" / "123123.mp4"),
        "onlineMaterial/1e65543d3133b8129357b0b0b4c1211e.png": posix(final_root / "Resources" / "media" / "main-video-slot.png"),
        "onlineMaterial/74ce29b9d8294a2c88c345a10249e987": posix(final_root / "Resources" / "textures" / "lower-panel-texture.bin"),
        "effect/7528305055972199681/0e4893968fe2d82714917f69c69826aa/font.ttf": posix(final_root / "Resources" / "fonts" / "lower-panel-font.ttf"),
    }
    return {
        f"C:/Users/{user}/AppData/Local/CapCut/User Data/Cache/{suffix}": target
        for user in ("arajun", "정상준")
        for suffix, target in targets.items()
    }


def archive_root(root: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(f".{archive.name}.{uuid.uuid4().hex}.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            package.write(path, arcname=(Path(root.name) / path.relative_to(root)).as_posix())
    os.replace(temporary, archive)


def update_root_meta(meta_path: Path, source_name: str, final_root: Path, project_id: str, duration_us: int) -> bytes:
    original = meta_path.read_bytes()
    meta = json.loads(original.decode("utf-8"))
    stores = meta.get("all_draft_store", [])
    if any(item.get("draft_name") == final_root.name for item in stores):
        raise RuntimeError("ROOT_META_TARGET_ALREADY_REGISTERED")
    source = next((item for item in stores if item.get("draft_name") == source_name), None)
    if source is None:
        raise RuntimeError("ROOT_META_SOURCE_NOT_FOUND")
    entry = copy.deepcopy(source)
    root_posix = posix(final_root)
    entry.update(
        {
            "draft_name": final_root.name,
            "draft_id": project_id,
            "draft_fold_path": root_posix,
            "draft_json_file": root_posix + "/draft_content.json",
            "draft_cover": root_posix + "/draft_cover.jpg",
            "draft_root_path": posix(final_root.parent),
            "draft_cloud_last_action_download": False,
            "draft_cloud_sync": False,
            "draft_cloud_template_id": "",
            "tm_draft_cloud_completed": "0",
            "tm_draft_cloud_entry_id": 0,
            "tm_draft_cloud_modified": 0,
            "tm_draft_cloud_parent_entry_id": -1,
            "tm_draft_cloud_space_id": 0,
            "tm_draft_cloud_user_id": 0,
            "tm_duration": duration_us,
        }
    )
    stores.append(entry)
    json_write(meta_path, meta)
    return original


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--capcut-root", type=Path, required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--content-start-sec", type=float, default=10.0)
    parser.add_argument("--replace-invalid-target", action="store_true")
    args = parser.parse_args()

    if args.content_start_sec <= 0:
        raise SystemExit("content-start-sec must be positive")
    tasklist = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
    )
    if "CapCut.exe" in tasklist.stdout:
        raise SystemExit("CAPCUT_PROCESS_MUST_BE_CLOSED")
    source_root = args.source_root.resolve()
    capcut_root = args.capcut_root.resolve()
    final_root = capcut_root / args.project_name
    if not source_root.is_dir() or source_root.parent != capcut_root:
        raise SystemExit("SOURCE_ROOT_MUST_BE_A_CAPCUT_DRAFT_DIRECT_CHILD")
    if not (capcut_root / "root_meta_info.json").is_file():
        raise SystemExit("ROOT_META_INFO_MISSING")

    if final_root.exists():
        if not args.replace_invalid_target:
            raise SystemExit("TARGET_ROOT_ALREADY_EXISTS")
        try:
            validate_root(final_root, round(args.content_start_sec * MICROS))
        except RuntimeError:
            meta_path = capcut_root / "root_meta_info.json"
            meta = json_load(meta_path)
            meta["all_draft_store"] = [
                item for item in meta.get("all_draft_store", []) if item.get("draft_name") != args.project_name
            ]
            json_write(meta_path, meta)
            shutil.rmtree(final_root)
            for output in (args.archive, args.manifest, args.report):
                if output.exists():
                    output.unlink()
        else:
            raise SystemExit("TARGET_ROOT_ALREADY_VALID")

    content_start_us = round(args.content_start_sec * MICROS)
    staging_parent = Path(os.environ["LOCALAPPDATA"]) / "CodexCapCutStaging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    stage = staging_parent / f"._b-{uuid.uuid4().hex[:12]}"
    meta_original: bytes | None = None
    published_root = False
    archive_written = False
    try:
        shutil.copytree(source_root, stage)
        for path in sorted(stage.rglob("*"), reverse=True):
            if JUNK_RE.search(path.name):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

        replacements = copy_required_resources(source_root, stage, args.ffmpeg, final_root)
        source_root_posix = posix(source_root)
        replacements[source_root_posix] = posix(final_root)
        replacements[source_root_posix.replace("/", "\\")] = posix(final_root)

        parsed: dict[Path, Any] = {}
        found: set[str] = set()
        for path in stage.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".json", ".tmp"}:
                try:
                    parsed[path] = json_load(path)
                    collect_uuids(parsed[path], found)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
        id_map = {old: str(uuid.uuid4()).upper() for old in found}
        old_timeline_id = json_load(source_root / "draft_content.json").get("id")
        new_timeline_id = id_map.get(old_timeline_id)
        if not new_timeline_id:
            raise RuntimeError("TIMELINE_ID_REMAP_FAILED")

        timeline_old = stage / "Timelines" / old_timeline_id
        timeline_new = stage / "Timelines" / new_timeline_id
        if not timeline_old.is_dir():
            raise RuntimeError("SOURCE_TIMELINE_DIR_MISSING")
        timeline_old.rename(timeline_new)

        duration_us = int(json_load(stage / "draft_content.json").get("duration", 0))
        if duration_us <= content_start_us:
            raise RuntimeError("ROOT_DURATION_NOT_LONGER_THAN_INTRO")
        for old_path, value in parsed.items():
            relative = old_path.relative_to(stage)
            if len(relative.parts) >= 2 and relative.parts[0] == "Timelines" and relative.parts[1] == old_timeline_id:
                relative = Path("Timelines", new_timeline_id, *relative.parts[2:])
            new_path = stage / relative
            value = rewrite_value(value, id_map, replacements)
            value = rewrite_legacy_font_paths(value, final_root)
            if (
                isinstance(value, dict)
                and "tracks" in value
                and len(value.get("materials", {}).get("videos", [])) >= 2
            ):
                value["name"] = args.project_name
                normalize_content(value, duration_us=duration_us, content_start_us=content_start_us)
                strip_external_video_materials(value, final_root)
            if isinstance(value, dict) and value.get("draft_name") == source_root.name:
                value["draft_name"] = args.project_name
            json_write(new_path, value)

        static = validate_root(stage, content_start_us, path_reference=final_root)
        final_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, final_root)
        published_root = True
        static = validate_root(final_root, content_start_us)
        project_id = str(uuid.uuid4()).upper()
        meta_original = update_root_meta(
            capcut_root / "root_meta_info.json", source_root.name, final_root, project_id, duration_us
        )
        archive_root(final_root, args.archive)
        archive_written = True
        manifest = {
            "status": "PASS_ARCHIVE_INTEGRITY",
            "template_profile": "jungchilong_base_v4_hook10_lower2",
            "reference_project_name": final_root.name,
            "source_candidate": source_root.name,
            "promotion_mode": "clean_staging_copy",
            "root_archive": args.archive.name,
            "archive_root": final_root.name + "/",
            "archive_sha256": sha256(args.archive),
            "archive_bytes": args.archive.stat().st_size,
            "content_start_sec": args.content_start_sec,
            "canvas": {"width": 1920, "height": 1080},
            "lower_two_line_slot": {
                "text": "__LOWER_LINE_1__\\n__LOWER_LINE_2__",
                "active_mode_exactly_one_of": [
                    "SOURCE_TTS",
                    "NARRATION_TTS",
                    "VIDEO100_EXPLAINER",
                    "NONE",
                ],
            },
            "static_validation": static,
            "files": file_records(final_root),
        }
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        json_write(args.manifest, manifest)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        json_write(
            args.report,
            {
                "status": "PASS_ROOT_PROMOTION_STATIC",
                "source_root": str(source_root),
                "source_unchanged": True,
                "final_root": str(final_root),
                "archive": str(args.archive),
                "manifest": str(args.manifest),
                "visual_gate": "WAIT_USER_VISUAL_GATE",
                "post_open_validation": "WAIT_CAPCUT_OPEN_CLOSE",
                "static_validation": static,
            },
        )
        print(json.dumps({"status": "PASS", "root": str(final_root), "archive": str(args.archive), "manifest": str(args.manifest), "static": static}, ensure_ascii=False))
        return 0
    except Exception:
        if meta_original is not None:
            (capcut_root / "root_meta_info.json").write_bytes(meta_original)
        if published_root and final_root.exists():
            shutil.rmtree(final_root)
        if archive_written and args.archive.exists():
            args.archive.unlink()
        if args.manifest.exists():
            args.manifest.unlink()
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == "__main__":
    sys.exit(main())
