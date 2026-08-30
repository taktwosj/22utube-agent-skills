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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from capcut_material_paths import (
    CAPCUT_DRAFT_ROOT_BUNDLE_ROOT,
    CAPCUT_ROOT_BUNDLE_ROOT,
    enforce_document_paths,
)
from root_bundle import (
    DEFAULT_ACTIVE_POINTER,
    ResolvedRoot,
    load_json_object,
    resolve_active_root,
    resolve_candidate_root,
    sha256_file,
    workspace_relative_path,
)


MICROS = 1_000_000
UUID_RE = re.compile(
    r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b"
)
JUNK_RE = re.compile(r"(?i)(\.bak$|^\.before_|^before_|_backup_|^helper_)")
PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
VERSION_RE = re.compile(r"^v([1-9][0-9]*)$")
BUNDLE_RELATIVE = DEFAULT_ACTIVE_POINTER.parent


@dataclass(frozen=True)
class CandidateBundle:
    status: str
    root_version: str
    root_profile: str
    base_layout_profile: str
    contract_relative_path: Path
    contract_path: Path
    archive_path: Path
    manifest_path: Path
    layout_path: Path
    report_path: Path
    evidence_path: Path
    capcut_project_path: Path
    active: bool = False


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
    try:
        temporary.write_text(payload, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


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


def validate_root(
    root: Path,
    content_start_us: int,
    *,
    path_reference: Path | None = None,
    draft_root_reference: Path | None = None,
) -> dict[str, Any]:
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

    path_root = path_reference or root
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".tmp"}:
            continue
        try:
            value = json_load(path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        enforce_document_paths(
            value,
            project_root=path_root,
            rebase_legacy_resources=False,
            expected_key_paths={
                "draft_root_path": (draft_root_reference or path_root.parent).as_posix()
            },
        )
    document = json_load(root / "draft_content.json")
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
    cache = (
        Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Cache"
    ).resolve(strict=False)
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
    replacements: dict[str, str] = {}
    for suffix, target in targets.items():
        source = cache / Path(suffix)
        replacements[source.as_posix()] = target
        replacements[str(source)] = target
    return replacements


def archive_root(root: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(f".{archive.name}.{uuid.uuid4().hex}.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for path in sorted(item for item in root.rglob("*") if item.is_file()):
                package.write(path, arcname=(Path(root.name) / path.relative_to(root)).as_posix())
        os.replace(temporary, archive)
    finally:
        if temporary.exists():
            temporary.unlink()


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


def ensure_capcut_closed() -> None:
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
    )
    if "CapCut.exe" in result.stdout:
        raise RuntimeError("CAPCUT_PROCESS_MUST_BE_CLOSED")


def _version_number(value: str) -> int:
    match = VERSION_RE.fullmatch(value)
    if match is None:
        raise RuntimeError("ROOT_VERSION_INVALID")
    return int(match.group(1))


def _validate_profile(value: str, field: str) -> None:
    if not isinstance(value, str) or PROFILE_RE.fullmatch(value) is None:
        raise RuntimeError(f"{field}_INVALID")


def _relative(workspace_root: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def _atomic_copytree(source: Path, destination: Path) -> None:
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        shutil.copytree(source, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def _role_name(track_type: str, text: str | None, track_index: int, segment_index: int) -> str:
    if track_type == "video":
        return "ROOT_INTRO_BACKGROUND" if track_index == 0 else "PRIMARY_VIDEO_SLOT"
    if track_type == "text":
        if text == "__INTRO_HOOK_LINE_1__\n__INTRO_HOOK_LINE_2__":
            return "INTRO_HOOK"
        if text == "__LOWER_LINE_1__\n__LOWER_LINE_2__":
            return "LOWER_TWO_LINE_SLOT"
        if text == "__CHAPTER__":
            return "CHAPTER_TITLE"
        if text == "출처 __SOURCE__\n__DATE__":
            return "SOURCE_AND_DATE"
        if text and text.startswith("구독은 "):
            return "CTA"
    return f"TRACK_{track_index}_SEGMENT_{segment_index}"


def build_layout_contract(
    root: Path,
    *,
    root_version: str,
    root_profile: str,
    base_layout_profile: str,
    content_start_us: int,
) -> dict[str, Any]:
    draft = json_load(root / "draft_content.json")
    texts = {
        material.get("id"): content_text(material)[1].get("text", "")
        for material in draft.get("materials", {}).get("texts", [])
    }
    roles: list[dict[str, Any]] = []
    for track_index, track in enumerate(draft.get("tracks", [])):
        track_type = str(track.get("type", ""))
        for segment_index, item in enumerate(track.get("segments", [])):
            material_id = item.get("material_id")
            text = texts.get(material_id) if track_type == "text" else None
            selector = (
                {"kind": "text_exact", "value": text}
                if text is not None
                else {"kind": "material_id", "value": material_id}
            )
            item_clip = item.get("clip", {})
            roles.append(
                {
                    "role": _role_name(track_type, text, track_index, segment_index),
                    "track_index": track_index,
                    "track_id": track.get("id"),
                    "track_type": track_type,
                    "material_selector": selector,
                    "seed_target_range_us": item.get("target_timerange"),
                    "clip": {
                        field: item_clip.get(field)
                        for field in ("scale", "rotation", "transform", "alpha")
                    },
                }
            )
    if not roles:
        raise RuntimeError("ROOT_LAYOUT_ROLES_MISSING")
    canvas = draft.get("canvas_config", {})
    return {
        "schema": "politics-longform-capcut-layout.v1",
        "root_version": root_version,
        "root_profile": root_profile,
        "base_layout_profile": base_layout_profile,
        "canvas": {"width": canvas.get("width"), "height": canvas.get("height")},
        "duration_us": draft.get("duration"),
        "content_start_us": content_start_us,
        "track_count": len(draft.get("tracks", [])),
        "roles": roles,
    }


def _candidate_paths(
    workspace_root: Path,
    capcut_root: Path,
    root_version: str,
    root_profile: str,
) -> dict[str, Path]:
    bundle = workspace_root / BUNDLE_RELATIVE
    identity = f"{root_version}_{root_profile}"
    return {
        "root": capcut_root / f"P0_ROOT_{identity}",
        "archive": bundle / f"{identity}_CAPCUT.zip",
        "manifest": bundle / f"template_manifest_{identity}.json",
        "layout": bundle / "layout_contracts" / f"{identity}_layout_contract_v1.json",
        "report": bundle / "promotion_reports" / f"{identity}_promotion_report_v1.json",
        "evidence": bundle / "evidence" / f"{identity}_promotion_evidence_v1.json",
        "contract": bundle / "contracts" / f"capcut_root_contract_{identity}.json",
    }


def prepare_candidate(
    workspace_root: Path,
    source_root: Path,
    capcut_root: Path,
    root_version: str,
    root_profile: str,
    base_layout_profile: str,
    parent_contract_relative_path: Path,
    ffmpeg: str,
    content_start_sec: float,
) -> CandidateBundle:
    workspace = workspace_root.resolve()
    source = source_root.resolve()
    capcut = capcut_root.resolve()
    _validate_profile(root_profile, "ROOT_PROFILE")
    _validate_profile(base_layout_profile, "BASE_LAYOUT_PROFILE")
    if root_profile == base_layout_profile:
        raise RuntimeError("ROOT_PROFILE_RELATION_INVALID")
    version = _version_number(root_version)
    if version < 6:
        raise RuntimeError("ROOT_VERSION_V5_OR_EARLIER_FORBIDDEN")
    if content_start_sec <= 0:
        raise RuntimeError("CONTENT_START_SEC_INVALID")

    active = resolve_active_root(workspace)
    active_version = _version_number(active.root_version)
    if version != active_version + 1:
        raise RuntimeError("ROOT_VERSION_NOT_MONOTONIC")
    parent_path = workspace_relative_path(
        workspace, Path(parent_contract_relative_path).as_posix()
    )
    if parent_path != active.contract_path:
        raise RuntimeError("PARENT_CONTRACT_NOT_ACTIVE")
    if not source.is_dir() or source.parent != capcut:
        raise RuntimeError("SOURCE_ROOT_MUST_BE_A_CAPCUT_DRAFT_DIRECT_CHILD")
    meta_path = capcut / "root_meta_info.json"
    if not meta_path.is_file():
        raise RuntimeError("ROOT_META_INFO_MISSING")
    ensure_capcut_closed()

    paths = _candidate_paths(workspace, capcut, root_version, root_profile)
    if any(path.exists() for path in paths.values()):
        raise RuntimeError("CANDIDATE_BUNDLE_TARGET_EXISTS")
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    content_start_us = round(content_start_sec * MICROS)
    stage = Path(tempfile.mkdtemp(prefix="capcut-root-candidate-"))
    meta_original: bytes | None = None
    published: list[Path] = []
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True)
        for path in sorted(stage.rglob("*"), reverse=True):
            if JUNK_RE.search(path.name):
                shutil.rmtree(path) if path.is_dir() else path.unlink()

        replacements = copy_required_resources(source, stage, ffmpeg, paths["root"])
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
        old_timeline_id = json_load(source / "draft_content.json").get("id")
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
        stage_replacements = {
            source_path: posix(stage / Path(target_path).relative_to(paths["root"]))
            for source_path, target_path in replacements.items()
        }
        source_to_stage = {
            source.as_posix(): stage.as_posix(),
            str(source): str(stage),
        }
        stage_to_root = {
            stage.as_posix(): paths["root"].as_posix(),
            str(stage): str(paths["root"]),
        }
        for old_path, value in parsed.items():
            relative = old_path.relative_to(stage)
            if len(relative.parts) >= 2 and relative.parts[:2] == ("Timelines", old_timeline_id):
                relative = Path("Timelines", new_timeline_id, *relative.parts[2:])
            destination = stage / relative
            value = rewrite_value(value, id_map, source_to_stage)
            value = enforce_document_paths(
                value,
                project_root=stage,
                rebase_legacy_resources=True,
                exact_rewrites=stage_replacements,
                root_aliases=(source.name,),
                rewrite_key_paths={"draft_root_path": stage.parent.as_posix()},
            )
            value = rewrite_value(value, {}, stage_to_root)
            value = enforce_document_paths(
                value,
                project_root=paths["root"],
                rebase_legacy_resources=True,
                exact_rewrites=replacements,
                root_aliases=(stage.name,),
                rewrite_key_paths={
                    "draft_root_path": paths["root"].parent.as_posix()
                },
            )
            if isinstance(value, dict) and "tracks" in value and len(value.get("materials", {}).get("videos", [])) >= 2:
                value["name"] = paths["root"].name
                normalize_content(value, duration_us=duration_us, content_start_us=content_start_us)
            if isinstance(value, dict) and value.get("draft_name") == source.name:
                value["draft_name"] = paths["root"].name
            json_write(destination, value)

        static = validate_root(stage, content_start_us, path_reference=paths["root"])
        _atomic_copytree(stage, paths["root"])
        published.append(paths["root"])
        static = validate_root(paths["root"], content_start_us)
        meta_original = update_root_meta(
            meta_path,
            source.name,
            paths["root"],
            str(uuid.uuid4()).upper(),
            duration_us,
        )

        with tempfile.TemporaryDirectory(prefix="capcut-root-portable-") as portable_temporary:
            portable_root = Path(portable_temporary) / paths["root"].name
            shutil.copytree(paths["root"], portable_root)
            for path in portable_root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in {".json", ".tmp"}:
                    continue
                try:
                    value = json_load(path)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                value = enforce_document_paths(
                    value,
                    project_root=Path(CAPCUT_ROOT_BUNDLE_ROOT),
                    rebase_legacy_resources=True,
                    root_aliases=(paths["root"].name, CAPCUT_ROOT_BUNDLE_ROOT),
                    rewrite_key_paths={
                        "draft_root_path": CAPCUT_DRAFT_ROOT_BUNDLE_ROOT
                    },
                )
                json_write(path, value)
            static = validate_root(
                portable_root,
                content_start_us,
                path_reference=Path(CAPCUT_ROOT_BUNDLE_ROOT),
                draft_root_reference=Path(CAPCUT_DRAFT_ROOT_BUNDLE_ROOT),
            )
            archive_root(portable_root, paths["archive"])
            portable_files = file_records(portable_root)
        published.append(paths["archive"])
        manifest = {
            "status": "PASS_ARCHIVE_INTEGRITY",
            "root_version": root_version,
            "root_profile": root_profile,
            "base_layout_profile": base_layout_profile,
            "template_profile": base_layout_profile,
            "reference_project_name": paths["root"].name,
            "source_candidate": source.name,
            "promotion_mode": "clean_staging_copy",
            "root_archive": paths["archive"].name,
            "archive_root": paths["root"].name + "/",
            "archive_sha256": sha256(paths["archive"]),
            "archive_bytes": paths["archive"].stat().st_size,
            "content_start_sec": content_start_sec,
            "canvas": {"width": 1920, "height": 1080},
            "lower_two_line_slot": {
                "text": "__LOWER_LINE_1__\\n__LOWER_LINE_2__",
                "active_mode_exactly_one_of": [
                    "SOURCE_TTS", "NARRATION_TTS", "VIDEO100_EXPLAINER", "NONE"
                ],
            },
            "static_validation": static,
            "files": portable_files,
        }
        json_write(paths["manifest"], manifest)
        published.append(paths["manifest"])
        layout = build_layout_contract(
            paths["root"],
            root_version=root_version,
            root_profile=root_profile,
            base_layout_profile=base_layout_profile,
            content_start_us=content_start_us,
        )
        json_write(paths["layout"], layout)
        published.append(paths["layout"])
        report = {
            "status": "PASS_ROOT_PROMOTION_STATIC",
            "source_root": source.name,
            "source_unchanged": True,
            "final_root": paths["root"].name,
            "archive": _relative(workspace, paths["archive"]),
            "manifest": _relative(workspace, paths["manifest"]),
            "visual_gate": "WAIT_USER_VISUAL_GATE",
            "post_open_validation": "WAIT_CAPCUT_OPEN_CLOSE",
            "static_validation": static,
        }
        json_write(paths["report"], report)
        published.append(paths["report"])
        evidence = {
            "schema": "politics-longform-capcut-root-evidence.v1",
            "root_version": root_version,
            "root_profile": root_profile,
            "source_candidate": source.name,
            "source_candidate_reference_kind": "project_name_only",
            "source_candidate_local_path_is_authority": False,
            "archive": {"relative_path": _relative(workspace, paths["archive"]), "sha256": sha256(paths["archive"])},
            "manifest": {"relative_path": _relative(workspace, paths["manifest"]), "sha256": sha256(paths["manifest"])},
            "promotion_report": {"relative_path": _relative(workspace, paths["report"]), "sha256": sha256(paths["report"])},
            "static_gate": "PASS_ROOT_PROMOTION_STATIC",
            "visual_gate": "WAIT_USER_VISUAL_GATE",
            "post_open_validation": "WAIT_CAPCUT_OPEN_CLOSE",
            "episode_visual_gate_inherited": False,
        }
        json_write(paths["evidence"], evidence)
        published.append(paths["evidence"])
        contract = {
            "schema": "politics-longform-capcut-root-bundle.v1",
            "root_version": root_version,
            "root_profile": root_profile,
            "base_layout_profile": base_layout_profile,
            "immutable": True,
            "parent_root_version": active.root_version,
            "parent_contract": {
                "relative_path": _relative(workspace, active.contract_path),
                "sha256": active.contract_sha256,
            },
            "source_candidate": source.name,
            "archive": {
                "relative_path": _relative(workspace, paths["archive"]),
                "sha256": sha256(paths["archive"]),
                "archive_root": paths["root"].name + "/",
                "file_count": len(manifest["files"]),
            },
            "manifest": {
                "relative_path": _relative(workspace, paths["manifest"]),
                "sha256": sha256(paths["manifest"]),
                "required_status": "PASS_ARCHIVE_INTEGRITY",
            },
            "layout_contract": {
                "relative_path": _relative(workspace, paths["layout"]),
                "sha256": sha256(paths["layout"]),
                "required_schema": "politics-longform-capcut-layout.v1",
            },
            "promotion_evidence": {
                "relative_path": _relative(workspace, paths["evidence"]),
                "sha256": sha256(paths["evidence"]),
                "required_static_gate": "PASS_ROOT_PROMOTION_STATIC",
            },
            "activation_policy": {
                "mode": "VERIFIED_VISUAL_AND_POST_OPEN",
                "allows_historical_visual_wait": False,
                "allows_historical_post_open_wait": False,
                "episode_visual_gate_inherited": False,
            },
        }
        json_write(paths["contract"], contract)
        published.append(paths["contract"])
        contract_relative = Path(_relative(workspace, paths["contract"]))
        return CandidateBundle(
            status="CANDIDATE_ROOT_BUNDLE_PREPARED",
            root_version=root_version,
            root_profile=root_profile,
            base_layout_profile=base_layout_profile,
            contract_relative_path=contract_relative,
            contract_path=paths["contract"],
            archive_path=paths["archive"],
            manifest_path=paths["manifest"],
            layout_path=paths["layout"],
            report_path=paths["report"],
            evidence_path=paths["evidence"],
            capcut_project_path=paths["root"],
        )
    except Exception:
        if meta_original is not None:
            meta_path.write_bytes(meta_original)
        for path in reversed(published):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def activate_candidate(
    workspace_root: Path,
    contract_relative_path: Path,
) -> ResolvedRoot:
    workspace = workspace_root.resolve()
    pointer_path = workspace / DEFAULT_ACTIVE_POINTER
    original_pointer_bytes = pointer_path.read_bytes()
    active = resolve_active_root(workspace)
    contract_path = workspace_relative_path(workspace, Path(contract_relative_path).as_posix())
    contract = load_json_object(contract_path)
    active_version = _version_number(active.root_version)
    candidate_version = _version_number(str(contract.get("root_version", "")))
    if candidate_version != active_version + 1:
        raise RuntimeError("ROOT_VERSION_NOT_MONOTONIC")
    if contract.get("parent_root_version") != active.root_version:
        raise RuntimeError("PARENT_ROOT_VERSION_NOT_ACTIVE")
    parent = contract.get("parent_contract")
    if not isinstance(parent, dict):
        raise RuntimeError("PARENT_CONTRACT_NOT_ACTIVE")
    parent_path = workspace_relative_path(workspace, parent.get("relative_path"))
    if parent_path != active.contract_path or str(parent.get("sha256", "")).upper() != active.contract_sha256:
        raise RuntimeError("PARENT_CONTRACT_NOT_ACTIVE")
    candidate = resolve_candidate_root(workspace, contract_relative_path)

    pointer = {
        "schema": "politics-longform-capcut-active-root.v1",
        "active_root_version": candidate.root_version,
        "contract": {
            "relative_path": _relative(workspace, candidate.contract_path),
            "sha256": sha256_file(candidate.contract_path),
        },
        "activation_basis": {"mode": candidate.activation_mode},
    }
    payload = json.dumps(pointer, ensure_ascii=False, indent=2) + "\n"
    temporary = pointer_path.with_name(f".{pointer_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        if pointer_path.read_bytes() != original_pointer_bytes:
            raise RuntimeError("ACTIVE_POINTER_CHANGED_DURING_ACTIVATION")
        temporary.write_text(payload, encoding="utf-8", newline="\n")
        os.replace(temporary, pointer_path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--workspace-root", type=Path, required=True)
    prepare.add_argument("--source-root", type=Path, required=True)
    prepare.add_argument("--capcut-root", type=Path, required=True)
    prepare.add_argument("--root-version", required=True)
    prepare.add_argument("--root-profile", required=True)
    prepare.add_argument("--base-layout-profile", required=True)
    prepare.add_argument("--parent-contract-relative-path", type=Path, required=True)
    prepare.add_argument("--ffmpeg", required=True)
    prepare.add_argument("--content-start-sec", type=float, required=True)
    activate = commands.add_parser("activate")
    activate.add_argument("--workspace-root", type=Path, required=True)
    activate.add_argument("--contract-relative-path", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            candidate = prepare_candidate(
                workspace_root=args.workspace_root,
                source_root=args.source_root,
                capcut_root=args.capcut_root,
                root_version=args.root_version,
                root_profile=args.root_profile,
                base_layout_profile=args.base_layout_profile,
                parent_contract_relative_path=args.parent_contract_relative_path,
                ffmpeg=args.ffmpeg,
                content_start_sec=args.content_start_sec,
            )
            print(
                json.dumps(
                    {
                        "status": candidate.status,
                        "root_version": candidate.root_version,
                        "root_profile": candidate.root_profile,
                        "contract_relative_path": candidate.contract_relative_path.as_posix(),
                        "active": False,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            resolved = activate_candidate(args.workspace_root, args.contract_relative_path)
            result = resolved.to_report()
            result["status"] = "ACTIVE_ROOT_BUNDLE_ACTIVATED"
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
