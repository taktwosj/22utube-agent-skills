#!/usr/bin/env python3
"""Compile a minimal politics-longform card test into an offline CapCut draft.

This deliberately supports only the first relink experiment:
INTRO -> TEXT_EXPLAINER -> SOURCE_VIDEO.  It is an adapter over the existing
CapCut staging/mirror conventions, not a replacement production exporter.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

from promote_capcut_root import (
    JUNK_RE, MICROS, collect_uuids, json_load, json_write, rewrite_value,
    set_material_text, sha256,
)


def uid() -> str:
    return str(uuid.uuid4()).upper()


def rich_text(material: dict[str, Any]) -> str:
    return json.loads(material["content"])["text"]


def find_text(document: dict[str, Any], expected: str) -> dict[str, Any]:
    rows = [item for item in document["materials"]["texts"] if rich_text(item) == expected]
    if len(rows) != 1:
        raise RuntimeError(f"TEXT_ANCHOR_NOT_UNIQUE:{expected}")
    return rows[0]


def find_segment(document: dict[str, Any], material_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = [(track, segment) for track in document["tracks"] for segment in track.get("segments", []) if segment.get("material_id") == material_id]
    if len(rows) != 1:
        raise RuntimeError("SEGMENT_ANCHOR_NOT_UNIQUE")
    return rows[0]


def set_range(segment: dict[str, Any], start: int, duration: int) -> None:
    segment["target_timerange"] = {"start": start, "duration": duration}


def require_capcut_closed() -> None:
    running = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False)
    if "CapCut.exe" in running.stdout:
        raise RuntimeError("CAPCUT_PROCESS_MUST_BE_CLOSED")


def probe(path: Path) -> dict[str, int]:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    video = next((stream for stream in data["streams"] if stream.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError("SOURCE_VIDEO_STREAM_MISSING")
    return {"duration": round(float(data["format"]["duration"]) * MICROS), "width": int(video["width"]), "height": int(video["height"])}


def extract(archive: Path, parent: Path) -> Path:
    with zipfile.ZipFile(archive) as package:
        files = [Path(entry.filename) for entry in package.infolist() if not entry.is_dir()]
        roots = {entry.parts[0] for entry in files if entry.parts}
        if len(roots) != 1 or any(entry.is_absolute() or ".." in entry.parts for entry in files):
            raise RuntimeError("ARCHIVE_SHAPE_INVALID")
        package.extractall(parent)
    root = parent / next(iter(roots))
    if not (root / "draft_content.json").is_file():
        raise RuntimeError("ROOT_DRAFT_MISSING")
    return root


def remap(stage: Path, final_root: Path, project_name: str) -> tuple[dict[str, Any], Path]:
    old_timeline = json_load(stage / "draft_content.json")["id"]
    parsed: dict[Path, Any] = {}
    found: set[str] = set()
    for path in stage.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".tmp"}:
            try:
                parsed[path] = json_load(path)
                collect_uuids(parsed[path], found)
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
    mapping = {old: uid() for old in found}
    new_timeline = mapping.get(old_timeline)
    if not new_timeline:
        raise RuntimeError("TIMELINE_ID_REMAP_FAILED")
    old_dir = stage / "Timelines" / old_timeline
    new_dir = stage / "Timelines" / new_timeline
    old_dir.rename(new_dir)
    replacements = {
        str(stage).replace("\\", "/"): str(final_root).replace("\\", "/"),
        str(stage): str(final_root),
        stage.name: project_name,
    }
    for path, value in parsed.items():
        rel = path.relative_to(stage)
        if len(rel.parts) > 1 and rel.parts[0] == "Timelines" and rel.parts[1] == old_timeline:
            rel = Path("Timelines", new_timeline, *rel.parts[2:])
        value = rewrite_value(value, mapping, replacements)
        if isinstance(value, dict) and value.get("draft_name") == stage.name:
            value["draft_name"] = project_name
        json_write(stage / rel, value)
    return json_load(stage / "draft_content.json"), new_dir


def mirror(stage: Path, timeline: Path, document: dict[str, Any]) -> None:
    for path in (stage / "draft_content.json", stage / "template-2.tmp", timeline / "draft_content.json", timeline / "template-2.tmp"):
        json_write(path, document)


def populate(document: dict[str, Any], cards: list[dict[str, Any]], source_name: str, source_info: dict[str, int], offline_path: str, project_name: str) -> dict[str, Any]:
    intro, explainer, source = cards
    if [card["card_type"] for card in cards] != ["INTRO", "TEXT_EXPLAINER", "SOURCE_VIDEO"]:
        raise RuntimeError("PROBE_CARD_ORDER_INVALID")
    if int(intro["target_duration_us"]) != 10 * MICROS or int(explainer["target_duration_us"]) != 12 * MICROS:
        raise RuntimeError("PROBE_CARD_DURATION_INVALID")
    source_duration = int(source["source_duration_us"])
    total = 22 * MICROS + source_duration
    if total != 180 * MICROS or source_duration > source_info["duration"]:
        raise RuntimeError("PROBE_TOTAL_DURATION_INVALID")
    videos = document["materials"]["videos"]
    if len(videos) != 2:
        raise RuntimeError("ROOT_VIDEO_ANCHORS_INVALID")
    new_video = copy.deepcopy(videos[0])
    new_video.update({"id": uid(), "type": "video", "path": offline_path, "media_path": "", "duration": source_info["duration"], "width": source_info["width"], "height": source_info["height"], "has_audio": True, "material_name": source_name, "material_id": "", "material_url": "", "local_material_id": uid().lower(), "local_id": "", "category_id": "", "category_name": "local", "request_id": "", "online_id": "", "team_id": "", "source": 0, "source_platform": 0})
    videos.append(new_video)
    video_tracks = [track for track in document["tracks"] if track.get("type") == "video"]
    if len(video_tracks) != 2:
        raise RuntimeError("ROOT_VIDEO_TRACK_COUNT_INVALID")
    intro_segment = video_tracks[0]["segments"][0]
    back_segment = video_tracks[1]["segments"][0]
    intro_segment["source_timerange"] = {"start": 0, "duration": 10 * MICROS}
    set_range(intro_segment, 0, 10 * MICROS)
    videos[1]["duration"] = total
    back_segment["source_timerange"] = {"start": 0, "duration": total - 10 * MICROS}
    set_range(back_segment, 10 * MICROS, total - 10 * MICROS)
    source_segment = copy.deepcopy(intro_segment)
    source_segment.update({"id": uid(), "material_id": new_video["id"], "source_timerange": {"start": int(source.get("source_start_us", 0)), "duration": source_duration}, "target_timerange": {"start": 22 * MICROS, "duration": source_duration}, "extra_material_refs": [], "volume": 1.0, "last_nonzero_volume": 1.0, "render_index": 2})
    source_track = copy.deepcopy(video_tracks[0])
    source_track["id"] = uid()
    source_track["segments"] = [source_segment]
    document["tracks"].insert(document["tracks"].index(video_tracks[1]) + 1, source_track)
    for index, track in enumerate(document["tracks"]):
        for segment in track.get("segments", []):
            segment["track_render_index"] = index

    intro_text = find_text(document, "__INTRO_HOOK_LINE_1__\n__INTRO_HOOK_LINE_2__")
    chapter_text = find_text(document, "__CHAPTER__")
    cta_text = find_text(document, "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!")
    source_text = find_text(document, "출처 __SOURCE__")
    lower_template = find_text(document, "__LOWER_LINE_1__\n__LOWER_LINE_2__")
    set_material_text(intro_text, intro["text"])
    set_material_text(chapter_text, explainer["chapter"])
    source_channel = str(source.get("source_channel", "")).strip()
    source_date = str(source.get("source_date", "")).strip()
    if not source_channel or not source_date:
        raise RuntimeError("SOURCE_LABEL_TWO_LINE_FIELDS_REQUIRED")
    # The upper source area is deliberately a fixed two-line label.  Keeping
    # channel and date separate avoids unpredictable CapCut word wrapping.
    set_material_text(source_text, f"출처 {source_channel}\n{source_date}")
    _, chapter_segment = find_segment(document, chapter_text["id"])
    _, cta_segment = find_segment(document, cta_text["id"])
    _, source_segment_text = find_segment(document, source_text["id"])
    lower_track, lower_segment = find_segment(document, lower_template["id"])
    # The chapter is a persistent main-program HUD, not a 12-second card.
    # It begins with the explainer and stays visible through its source-video
    # section, so viewers retain the chapter context during playback.
    set_range(chapter_segment, 10 * MICROS, total - 10 * MICROS)
    # CTA shares the same persistent main-program HUD window as the chapter.
    set_range(cta_segment, 10 * MICROS, total - 10 * MICROS)
    set_range(source_segment_text, 22 * MICROS, source_duration)
    lower_track["segments"] = [segment for segment in lower_track["segments"] if segment is not lower_segment]
    document["materials"]["texts"] = [item for item in document["materials"]["texts"] if item is not lower_template]
    for card, start, duration in ((explainer, 10 * MICROS, 12 * MICROS), (source, 22 * MICROS, source_duration)):
        material = copy.deepcopy(lower_template)
        material["id"] = uid()
        set_material_text(material, card["lower_text"])
        segment = copy.deepcopy(lower_segment)
        segment.update({"id": uid(), "material_id": material["id"]})
        set_range(segment, start, duration)
        lower_track["segments"].append(segment)
        document["materials"]["texts"].append(material)
    for track in document["tracks"]:
        if track.get("type") == "sticker":
            for segment in track["segments"]:
                set_range(segment, 10 * MICROS, total - 10 * MICROS)
    document["duration"] = total
    document["name"] = project_name
    return document


def validate(root: Path, media: Path, media_sha: str) -> dict[str, Any]:
    junk = [item.relative_to(root).as_posix() for item in root.rglob("*") if JUNK_RE.search(item.name)]
    if junk:
        raise RuntimeError("PROBE_JUNK_PRESENT")
    mirrors = [root / "draft_content.json", root / "template-2.tmp"] + list((root / "Timelines").glob("*/draft_content.json")) + list((root / "Timelines").glob("*/template-2.tmp"))
    hashes = [sha256(path) for path in mirrors]
    if len(mirrors) != 4 or len(set(hashes)) != 1:
        raise RuntimeError("JSON_MIRROR_MISMATCH")
    if not media.is_file() or sha256(media) != media_sha:
        raise RuntimeError("MEDIA_PACKAGE_MISMATCH")
    document = json_load(root / "draft_content.json")
    track_ids = [track.get("id") for track in document["tracks"]]
    if len(track_ids) != len(set(track_ids)):
        raise RuntimeError("DUPLICATE_TRACK_ID")
    source = [item for item in document["materials"]["videos"] if item.get("material_name") == media.name]
    if len(source) != 1 or not source[0].get("local_material_id") or "__CAPCUT_RELINK_REQUIRED__" not in source[0].get("path", ""):
        raise RuntimeError("OFFLINE_MEDIA_DECLARATION_INVALID")
    if int(document["duration"]) != 180 * MICROS:
        raise RuntimeError("PROBE_DURATION_INVALID")
    cta = [item for item in document["materials"]["texts"] if rich_text(item) == "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!"]
    if len(cta) != 1:
        raise RuntimeError("CTA_TEXT_ANCHOR_INVALID")
    _, cta_segment = find_segment(document, cta[0]["id"])
    if cta_segment["target_timerange"] != {"start": 10 * MICROS, "duration": 170 * MICROS}:
        raise RuntimeError("CTA_HUD_RANGE_INVALID")
    return {"status": "PASS", "mirror_sha256": hashes[0], "duration_sec": 180, "offline_media_declared": True}


def register(meta_path: Path, source_name: str, project_name: str, root: Path, duration: int) -> bytes:
    original = meta_path.read_bytes()
    meta = json.loads(original.decode("utf-8"))
    source = next((item for item in meta.get("all_draft_store", []) if item.get("draft_name") == source_name), None)
    if source is None or any(item.get("draft_name") == project_name for item in meta["all_draft_store"]):
        raise RuntimeError("ROOT_META_REGISTRATION_INVALID")
    entry = copy.deepcopy(source)
    posix = str(root).replace("\\", "/")
    entry.update({"draft_name": project_name, "draft_id": uid(), "draft_fold_path": posix, "draft_json_file": posix + "/draft_content.json", "draft_cover": posix + "/draft_cover.jpg", "draft_root_path": str(root.parent).replace("\\", "/"), "tm_duration": duration, "draft_cloud_sync": False, "draft_cloud_template_id": ""})
    meta["all_draft_store"].append(entry)
    json_write(meta_path, meta)
    return original


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--capcut-root", type=Path, required=True)
    parser.add_argument("--media-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    require_capcut_closed()
    if sha256(args.archive).upper() != args.archive_sha256.upper():
        raise RuntimeError("FAIL_ARCHIVE_INTEGRITY")
    cards_doc = json_load(args.cards)
    project_name = cards_doc["project_name"]
    cards = cards_doc["cards"]
    source_file = Path(cards[2]["source_file"]).resolve()
    if args.media_dir.exists() or not source_file.is_file():
        raise RuntimeError("MEDIA_DIR_EXISTS_OR_SOURCE_MISSING")
    final_root = args.capcut_root / project_name
    meta_path = args.capcut_root / "root_meta_info.json"
    if final_root.exists() or not meta_path.is_file():
        raise RuntimeError("PROJECT_TARGET_OR_META_INVALID")
    info = probe(source_file)
    media_sha = ""
    original_meta: bytes | None = None
    published = False
    staging_parent = Path(os.environ["LOCALAPPDATA"]) / "CodexCapCutStaging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="politics-relink-", dir=staging_parent) as temp:
        try:
            stage = extract(args.archive, Path(temp))
            archive_root_name = stage.name
            staged = Path(temp) / project_name
            stage.rename(staged)
            stage = staged
            args.media_dir.mkdir(parents=True)
            # CapCut may reuse an already-known file solely by basename. Keep
            # every episode/project filename unique so a prior episode's S03
            # can never satisfy this project's relink request.
            media = args.media_dir / f"C003_{project_name}_S03_chapter_video.mp4"
            shutil.copy2(source_file, media)
            media_sha = sha256(media)
            document, timeline = remap(stage, final_root, project_name)
            offline = f"C:/__CAPCUT_RELINK_REQUIRED__/{cards_doc['episode_id']}/Media/{media.name}"
            document = populate(document, cards, media.name, info, offline, project_name)
            mirror(stage, timeline, document)
            static = validate(stage, media, media_sha)
            shutil.copytree(stage, final_root)
            published = True
            static = validate(final_root, media, media_sha)
            original_meta = register(meta_path, archive_root_name, project_name, final_root, 180 * MICROS)
            report = {"status": "PROJECT_CREATED_WAIT_MEDIA_RELINK", "kind": "TECHNICAL_RELINK_PROBE", "project": str(final_root), "media_folder_to_select": str(args.media_dir), "media_filename": media.name, "requested_offline_path": offline, "media_sha256": media_sha, "cards": cards, "static_validation": static, "next": "Open this project in CapCut, select Media Relink, choose media_folder_to_select, save, close CapCut, then run post-open readback."}
            json_write(args.report, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        except Exception:
            if original_meta is not None:
                meta_path.write_bytes(original_meta)
            if published and final_root.exists():
                shutil.rmtree(final_root)
            if args.media_dir.exists():
                shutil.rmtree(args.media_dir)
            raise


if __name__ == "__main__":
    raise SystemExit(main())
