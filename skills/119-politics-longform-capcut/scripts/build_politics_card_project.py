#!/usr/bin/env python3
"""Build a clean politics-longform CapCut draft from episode_cards.json.

The project is intentionally created with unique *offline* media paths.  A
single CapCut Media Relink action against the emitted Media folder reconnects
all card assets; no media path from a prior episode is reused.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path, PureWindowsPath
from typing import Any

from promote_capcut_root import JUNK_RE, MICROS, collect_uuids, json_load, json_write, rewrite_value, set_material_text, sha256
from root_bundle import ResolvedRoot, resolve_active_root


LOWER_MODES = {"SOURCE_TTS", "NARRATION_TTS", "VIDEO100_EXPLAINER", "NONE"}
PUBLIC_LOWER_MODES = {"SRT", "COMMENTARY_2LINE", "NONE"}
AUDIO_DURATION_TOLERANCE_US = 250_000
NARRATION_MOTION_PROFILES = {"NONE", "SLOW_ZOOM_IN", "SLOW_ZOOM_OUT", "SUBTLE_PAN"}
CARD_TYPES = {
    "INTRO",
    "CHAPTER_CARD",
    "SOURCE_VIDEO",
    "NARRATION_IMAGE",
    "NARRATION_VIDEO",
    "TEXT_EXPLAINER",
    "ENDING",
}
V5_ADAPTER_CONFIG = "runtime_adapters/v5_legacy_profile_adapter_v1.json"


def uid() -> str:
    return str(uuid.uuid4()).upper()


def text_of(material: dict[str, Any]) -> str:
    return json.loads(material["content"])["text"]


def _presentation_row(
    document: dict[str, Any], material: dict[str, Any], segment: dict[str, Any]
) -> dict[str, Any]:
    track_index, track = next(
        (index, track)
        for index, track in enumerate(document["tracks"])
        if segment in track.get("segments", [])
    )
    return {
        "material_id": material["id"],
        "segment_id": segment["id"],
        "text": text_of(material),
        "target_timerange": copy.deepcopy(segment.get("target_timerange", {})),
        "track_type": track.get("type"),
        "track_index": track_index,
        "track_id": track.get("id"),
        "clip_geometry": copy.deepcopy(segment.get("clip", {})),
    }


def capture_presentation_contract(
    document: dict[str, Any], cards: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Freeze the editable HUD/lower track identity and clip coordinates."""
    text_by_id = {item["id"]: item for item in document["materials"]["texts"]}
    rows: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for track in document["tracks"]:
        if track.get("type") != "text":
            continue
        for segment in track.get("segments", []):
            material = text_by_id.get(segment.get("material_id"))
            if material is not None:
                rows.append((text_of(material), material, segment))

    source_texts: set[str] | None = None
    lower_texts: set[str] | None = None
    if cards is not None:
        source_texts = {
            f"출처 {str(card.get('source_channel', '')).strip()}\n{str(card.get('source_date', '')).strip()}"
            for card in cards
            if card.get("card_type") == "SOURCE_VIDEO"
        }
        lower_texts = set()
        for card in cards:
            mode = card.get("lower_mode", "NONE")
            if mode == "VIDEO100_EXPLAINER":
                lower_texts.add(str(card.get("lower_text", "")))
            elif mode in {"SOURCE_TTS", "NARRATION_TTS"}:
                field = "source_srt_file" if mode == "SOURCE_TTS" else "narration_srt_file"
                lower_texts.update(cue_text for _, _, cue_text in _srt_cues(Path(card[field])))

    sources = [
        _presentation_row(document, material, segment)
        for text, material, segment in rows
        if text.startswith("출처 ") and (source_texts is None or text in source_texts)
    ]
    ctas = [
        _presentation_row(document, material, segment)
        for text, material, segment in rows
        if text.startswith("구독은 ")
    ]
    lowers = [
        _presentation_row(document, material, segment)
        for text, material, segment in rows
        if (
            (lower_texts is not None and text in lower_texts)
            or (
                lower_texts is None
                and text.count("\n") == 1
                and not text.startswith(("출처 ", "구독은 ", "챕터 "))
            )
        )
    ]
    if len(ctas) != 1:
        raise RuntimeError(f"CTA_PRESENTATION_CONTRACT_INVALID:{len(ctas)}")
    return {
        "source_date_hud": sources,
        "cta_hud": ctas[0],
        "lower_slots": lowers,
    }


def set_range(segment: dict[str, Any], start: int, duration: int) -> None:
    segment["target_timerange"] = {"start": start, "duration": duration}


def require_capcut_closed() -> None:
    tasklist = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
    )
    if "CapCut.exe" in tasklist.stdout:
        raise RuntimeError("CAPCUT_PROCESS_MUST_BE_CLOSED")


def extract_root(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as package:
        members = [Path(row.filename) for row in package.infolist() if not row.is_dir()]
        roots = {row.parts[0] for row in members if row.parts}
        if len(roots) != 1 or any(row.is_absolute() or ".." in row.parts for row in members):
            raise RuntimeError("ROOT_ARCHIVE_SHAPE_INVALID")
        package.extractall(destination)
    root = destination / next(iter(roots))
    if not (root / "draft_content.json").is_file():
        raise RuntimeError("ROOT_DRAFT_MISSING")
    return root


def require_non_stock_builder_for_adapter_root(resolved_root: ResolvedRoot) -> None:
    expected = f"{resolved_root.archive_root.rstrip('/')}/{V5_ADAPTER_CONFIG}"
    with zipfile.ZipFile(resolved_root.archive_path) as package:
        has_adapter = expected in {row.filename.replace("\\", "/") for row in package.infolist()}
    if not has_adapter:
        return
    bundled = Path(__file__).with_name("build_politics_v5_legacy_adapter.py")
    if not bundled.is_file():
        raise RuntimeError("WAIT_V5_ADAPTER_SOURCE_REQUIRED")
    raise RuntimeError("USE_V5_LEGACY_ADAPTER_BUILDER_REQUIRED")


def remap_ids(stage: Path, final_root: Path, project_name: str, archive_root_name: str) -> tuple[dict[str, Any], Path]:
    old_timeline = json_load(stage / "draft_content.json")["id"]
    parsed: dict[Path, Any] = {}
    ids: set[str] = set()
    for path in stage.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".tmp"}:
            try:
                parsed[path] = json_load(path)
                collect_uuids(parsed[path], ids)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    id_map = {old: uid() for old in ids}
    new_timeline = id_map.get(old_timeline)
    if not new_timeline:
        raise RuntimeError("TIMELINE_ID_REMAP_FAILED")
    old_dir = stage / "Timelines" / old_timeline
    timeline = stage / "Timelines" / new_timeline
    if not old_dir.is_dir():
        raise RuntimeError("ROOT_TIMELINE_DIR_MISSING")
    old_dir.rename(timeline)
    replacements = {
        str(stage).replace("\\", "/"): str(final_root).replace("\\", "/"),
        str(stage): str(final_root),
        str(final_root.parent / archive_root_name).replace("\\", "/"): str(final_root).replace("\\", "/"),
        str(final_root.parent / archive_root_name): str(final_root),
        stage.name: project_name,
    }
    for old_path, value in parsed.items():
        relative = old_path.relative_to(stage)
        if len(relative.parts) > 1 and relative.parts[0] == "Timelines" and relative.parts[1] == old_timeline:
            relative = Path("Timelines", new_timeline, *relative.parts[2:])
        value = rewrite_value(value, id_map, replacements)
        if isinstance(value, dict) and value.get("draft_name") == stage.name:
            value["draft_name"] = project_name
        json_write(stage / relative, value)
    return json_load(stage / "draft_content.json"), timeline


def mirror(root: Path, timeline: Path, document: dict[str, Any]) -> None:
    for path in (root / "draft_content.json", root / "template-2.tmp", timeline / "draft_content.json", timeline / "template-2.tmp"):
        json_write(path, document)


def probe_media(path: Path) -> dict[str, int | bool]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    video = next((stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError(f"MEDIA_VIDEO_STREAM_MISSING:{path.name}")
    return {
        "duration_us": round(float(data["format"]["duration"]) * MICROS),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "has_audio": any(stream.get("codec_type") == "audio" for stream in data.get("streams", [])),
    }


def probe_duration(path: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(json.loads(result.stdout)["format"]["duration"]) * MICROS)


def _require_file_sha(card: dict[str, Any], file_field: str, sha_field: str, error: str) -> Path:
    value = Path(str(card.get(file_field, ""))).resolve()
    expected = str(card.get(sha_field, "")).upper()
    if not value.is_file() or not expected or sha256(value).upper() != expected:
        raise RuntimeError(error)
    return value


def _srt_timestamp(value: str) -> int:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return round((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * MICROS)


def _srt_ranges(path: Path) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if " --> " not in line:
            continue
        start, end = (part.strip() for part in line.split(" --> ", 1))
        ranges.append((_srt_timestamp(start), _srt_timestamp(end)))
    return ranges


def _srt_cues(path: Path) -> list[tuple[int, int, str]]:
    cues: list[tuple[int, int, str]] = []
    blocks = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").split("\n\n")
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((index for index, line in enumerate(lines) if " --> " in line), None)
        if timing_index is None:
            continue
        start, end = (part.strip() for part in lines[timing_index].split(" --> ", 1))
        text = "\n".join(lines[timing_index + 1 :]).strip()
        if text:
            cues.append((_srt_timestamp(start), _srt_timestamp(end), text))
    return cues


def validate_narration_contract(cards_doc: dict[str, Any]) -> dict[str, Any]:
    """Validate locked narration assets before any CapCut mutation."""
    cards = cards_doc.get("cards")
    if not isinstance(cards, list):
        raise RuntimeError("CARDS_REQUIRED")
    editorial_duration = sum(
        int(card.get("target_duration_us", 0))
        for card in cards
        if card.get("card_type") != "INTRO"
        and not (card.get("card_type") == "CHAPTER_CARD" and not card.get("narration_audio_file"))
    )
    intervals: dict[str, list[tuple[int, int]]] = {}
    for card in cards:
        kind = card.get("card_type")
        if kind not in {"NARRATION_IMAGE", "NARRATION_VIDEO"}:
            continue
        card_id = str(card.get("card_id", "?"))
        target_start = int(card.get("target_start_us", -1))
        target_duration = int(card.get("target_duration_us", 0))
        audio = _require_file_sha(card, "narration_audio_file", "narration_audio_sha256", "NARRATION_AUDIO_SHA256_INVALID")
        audio_start = int(card.get("audio_start_us", 0))
        audio_duration = int(card.get("audio_duration_us", probe_duration(audio)))
        audio_total = probe_duration(audio)
        if audio_start < 0 or audio_duration <= 0 or audio_start + audio_duration > audio_total + AUDIO_DURATION_TOLERANCE_US:
            raise RuntimeError(f"NARRATION_AUDIO_RANGE_INVALID:{card_id}")
        if abs(target_duration - audio_duration) > AUDIO_DURATION_TOLERANCE_US:
            raise RuntimeError("NARRATION_AUDIO_TARGET_DURATION_INVALID")
        srt = _require_file_sha(card, "narration_srt_file", "narration_srt_sha256", "NARRATION_SRT_SHA256_INVALID")
        srt_ranges = _srt_ranges(srt)
        if not srt_ranges:
            raise RuntimeError("SRT_CUES_REQUIRED")
        card_end = target_start + target_duration
        if any(start < target_start or end > card_end or end <= start for start, end in srt_ranges):
            raise RuntimeError("NARRATION_SRT_RANGE_INVALID")
        if kind == "NARRATION_IMAGE":
            image = _require_file_sha(card, "image_file", "image_sha256", "IMAGE_SHA256_INVALID")
            width, height = image_size(image)
            if width * 9 != height * 16:
                raise RuntimeError("NARRATION_IMAGE_16_9_REQUIRED")
            if card.get("motion_profile") not in NARRATION_MOTION_PROFILES:
                raise RuntimeError("NARRATION_IMAGE_MOTION_PROFILE_INVALID")
        else:
            video = _require_file_sha(card, "video_file", "video_sha256", "NARRATION_VIDEO_SHA256_INVALID")
            video_start = int(card.get("video_start_us", -1))
            video_duration = int(card.get("video_duration_us", 0))
            video_total = int(probe_media(video)["duration_us"])
            if video_start < 0 or video_duration <= 0 or video_start + video_duration > video_total + AUDIO_DURATION_TOLERANCE_US:
                raise RuntimeError("NARRATION_VIDEO_RANGE_INVALID")
            if abs(target_duration - video_duration) > AUDIO_DURATION_TOLERANCE_US:
                raise RuntimeError("NARRATION_VIDEO_TARGET_DURATION_INVALID")
            if card.get("source_audio_mode") != "MUTE":
                raise RuntimeError("FAIL_DUPLICATE_AUDIO")
        intervals.setdefault(str(card["narration_audio_sha256"]).upper(), []).append((audio_start, audio_start + audio_duration))
    narration_duration = 0
    for ranges in intervals.values():
        end = -1
        for start, stop in sorted(ranges):
            if start > end:
                narration_duration += stop - start
                end = stop
            elif stop > end:
                narration_duration += stop - end
                end = stop
    if editorial_duration <= 0:
        raise RuntimeError("EDITORIAL_DURATION_REQUIRED")
    ratio = narration_duration / editorial_duration
    override = bool(cards_doc.get("narration_ratio_override"))
    return {
        "status": "PASS",
        "editorial_duration_us": editorial_duration,
        "narration_duration_us": narration_duration,
        "narration_ratio": ratio,
        "override": override,
    }


def image_size(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    streams = json.loads(result.stdout).get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError(f"IMAGE_STREAM_MISSING:{path.name}")
    return int(video["width"]), int(video["height"])


def material_by_text(document: dict[str, Any], predicate: Any, label: str) -> dict[str, Any]:
    matches = [row for row in document["materials"]["texts"] if predicate(text_of(row))]
    if len(matches) != 1:
        raise RuntimeError(f"TEXT_TEMPLATE_NOT_UNIQUE:{label}:{len(matches)}")
    return matches[0]


def segment_for(document: dict[str, Any], material_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    matches = [
        (track, segment)
        for track in document["tracks"]
        for segment in track.get("segments", [])
        if segment.get("material_id") == material_id
    ]
    if len(matches) != 1:
        raise RuntimeError(f"TEMPLATE_SEGMENT_NOT_UNIQUE:{material_id}:{len(matches)}")
    return matches[0]


def remove_segment(track: dict[str, Any], segment: dict[str, Any]) -> None:
    track["segments"] = [row for row in track.get("segments", []) if row is not segment]


def prune_unreferenced_text_materials(document: dict[str, Any]) -> None:
    """Remove template-only text after the visible episode segments are made."""
    referenced = {
        segment.get("material_id")
        for track in document["tracks"]
        if track.get("type") == "text"
        for segment in track.get("segments", [])
    }
    document["materials"]["texts"] = [
        material
        for material in document["materials"]["texts"]
        if material.get("id") in referenced
    ]


def trim_all_tracks_to_duration(document: dict[str, Any], total: int) -> None:
    """CapCut derives project duration from the longest visible segment.

    The root's decorative frame is intentionally long.  A short episode must
    shorten that frame too, otherwise CapCut silently restores the old 3-minute
    tail after opening the draft.
    """
    for track in document["tracks"]:
        retained = []
        for segment in track.get("segments", []):
            timerange = segment.get("target_timerange", {})
            start = int(timerange.get("start", 0))
            duration = int(timerange.get("duration", 0))
            if duration <= 0 or start >= total:
                continue
            allowed = min(duration, total - start)
            if allowed != duration:
                timerange["duration"] = allowed
                source = segment.get("source_timerange")
                if isinstance(source, dict):
                    source["duration"] = min(int(source.get("duration", allowed)), allowed)
            retained.append(segment)
        track["segments"] = retained


def clone_text(
    document: dict[str, Any],
    template_material: dict[str, Any],
    template_segment: dict[str, Any],
    target_track: dict[str, Any],
    text: str,
    start: int,
    duration: int,
) -> None:
    material = copy.deepcopy(template_material)
    material["id"] = uid()
    set_material_text(material, text)
    segment = copy.deepcopy(template_segment)
    segment["id"] = uid()
    segment["material_id"] = material["id"]
    set_range(segment, start, duration)
    document["materials"]["texts"].append(material)
    target_track["segments"].append(segment)


def clone_media(
    document: dict[str, Any],
    template_material: dict[str, Any],
    template_segment: dict[str, Any],
    insert_after: int | None,
    *,
    target_track: dict[str, Any] | None = None,
    kind: str,
    offline_path: str,
    filename: str,
    width: int,
    height: int,
    source_start: int,
    source_duration: int,
    media_duration: int,
    target_start: int,
    target_duration: int,
    has_audio: bool,
) -> None:
    material = copy.deepcopy(template_material)
    material.update(
        {
            "id": uid(),
            "type": kind,
            "path": offline_path,
            "media_path": "",
            # CapCut uses native media duration while resolving an offline
            # asset.  The segment may be a short cut, but recording that cut
            # as the material duration makes the real source file fail relink.
            "duration": media_duration,
            "width": width,
            "height": height,
            "has_audio": has_audio,
            "material_name": filename,
            "material_id": "",
            "material_url": "",
            "local_material_id": uid().lower(),
            "local_id": "",
            "category_id": "",
            "category_name": "local",
            "request_id": "",
            "online_id": "",
            "team_id": "",
            "source": 0,
            "source_platform": 0,
        }
    )
    segment = copy.deepcopy(template_segment)
    segment.update(
        {
            "id": uid(),
            "material_id": material["id"],
            "source_timerange": {"start": source_start, "duration": source_duration},
            "target_timerange": {"start": target_start, "duration": target_duration},
            "extra_material_refs": [],
            "volume": 1.0 if has_audio else 0.0,
            "last_nonzero_volume": 1.0 if has_audio else 0.0,
        }
    )
    document["materials"]["videos"].append(material)
    if target_track is not None:
        target_track["segments"].append(segment)
        return
    if insert_after is None:
        raise RuntimeError("MEDIA_TRACK_TARGET_REQUIRED")
    track = copy.deepcopy(next(row for row in document["tracks"] if row.get("type") == "video"))
    track["id"] = uid()
    track["segments"] = [segment]
    document["tracks"].insert(insert_after, track)


def clone_narration_audio(
    document: dict[str, Any], record: dict[str, Any], target_start: int, target_duration: int
) -> None:
    audio = record["narration_audio"]
    material_id = uid()
    document["materials"].setdefault("audios", []).append({
        "id": material_id, "music_id": material_id, "unique_id": "", "type": "extract_music",
        "name": audio["filename"], "material_name": audio["filename"],
        "duration": int(audio["duration_us"]), "path": audio["offline_path"],
        "category_name": "local", "wave_points": [], "local_material_id": uid().lower(),
    })
    segment = {
        "id": uid(), "material_id": material_id,
        "source_timerange": {"start": int(audio["source_start"]), "duration": int(audio["source_duration"])},
        "target_timerange": {"start": target_start, "duration": target_duration},
        "speed": 1.0, "volume": 1.0, "last_nonzero_volume": 1.0,
        "extra_material_refs": [], "keyframe_refs": [], "common_keyframes": [], "visible": True,
    }
    track = next((row for row in document["tracks"] if row.get("type") == "audio" and row.get("name") == "A_NARRATION"), None)
    if track is None:
        track = {"id": uid(), "name": "A_NARRATION", "type": "audio", "segments": []}
        document["tracks"].append(track)
    track["segments"].append(segment)


def normalize_cards(
    cards_doc: dict[str, Any], *, content_start_us: int | None = None
) -> tuple[list[dict[str, Any]], int]:
    cards = cards_doc.get("cards")
    if not isinstance(cards, list) or not cards:
        raise RuntimeError("CARDS_REQUIRED")
    ordered = sorted(copy.deepcopy(cards), key=lambda card: int(card["target_start_us"]))
    cursor = 0
    for card in ordered:
        card_type = card.get("card_type")
        start = int(card.get("target_start_us", -1))
        duration = int(card.get("target_duration_us", 0))
        lower_mode = card.get("lower_mode", "NONE")
        if lower_mode == "SRT":
            if card_type == "SOURCE_VIDEO":
                lower_mode = "SOURCE_TTS"
            elif card_type in {"NARRATION_IMAGE", "NARRATION_VIDEO"}:
                lower_mode = "NARRATION_TTS"
            else:
                raise RuntimeError(f"SILENT_SRT_INVALID:{card.get('card_id', '?')}")
        elif lower_mode == "COMMENTARY_2LINE":
            lower_mode = "VIDEO100_EXPLAINER"
        card["lower_mode"] = lower_mode
        if card_type not in CARD_TYPES or start != cursor or duration <= 0:
            raise RuntimeError(f"CARD_TIMELINE_INVALID:{card.get('card_id', '?')}")
        if lower_mode not in LOWER_MODES:
            raise RuntimeError(f"CARD_LOWER_MODE_INVALID:{card.get('card_id', '?')}")
        if card_type == "CHAPTER_CARD" and lower_mode != "NONE":
            raise RuntimeError("CHAPTER_CARD_REQUIRES_LOWER_NONE")
        if lower_mode == "VIDEO100_EXPLAINER" and not str(card.get("lower_text", "")).strip():
            raise RuntimeError(f"LOWER_TEXT_REQUIRED:{card.get('card_id', '?')}")
        if lower_mode == "SOURCE_TTS":
            srt = _require_file_sha(card, "source_srt_file", "source_srt_sha256", "SOURCE_SRT_SHA256_INVALID")
            ranges = _srt_ranges(srt)
            if not _srt_cues(srt):
                raise RuntimeError("SRT_CUES_REQUIRED")
            if any(cue_start < start or cue_end > start + duration or cue_end <= cue_start for cue_start, cue_end in ranges):
                raise RuntimeError(f"SOURCE_SRT_RANGE_INVALID:{card.get('card_id', '?')}")
        if lower_mode == "NARRATION_TTS":
            srt = _require_file_sha(card, "narration_srt_file", "narration_srt_sha256", "NARRATION_SRT_SHA256_INVALID")
            if not _srt_cues(srt):
                raise RuntimeError("SRT_CUES_REQUIRED")
        cursor += duration
    first = ordered[0]
    if first.get("card_type") == "INTRO":
        if content_start_us is not None and (
            content_start_us <= 0
            or int(first["target_duration_us"]) != int(content_start_us)
        ):
            raise RuntimeError("INTRO_DURATION_CONTRADICTS_ROOT")
    elif first.get("card_type") != "SOURCE_VIDEO":
        raise RuntimeError("FIRST_CARD_MUST_BE_SOURCE_VIDEO_OR_INTRO")
    for card in ordered:
        if card["card_type"] == "CHAPTER_CARD" and not card.get("narration_audio") and int(card["target_duration_us"]) != 3 * MICROS:
            raise RuntimeError("SILENT_CHAPTER_MUST_BE_3_SECONDS")
    return ordered, cursor


def copy_card_media(cards: list[dict[str, Any]], media_dir: Path, episode_id: str) -> dict[str, dict[str, Any]]:
    media_dir.mkdir(parents=True)
    records: dict[str, dict[str, Any]] = {}
    for card in cards:
        kind = card["card_type"]
        field = {"SOURCE_VIDEO": "source_file", "NARRATION_VIDEO": "video_file"}.get(kind, "image_file")
        if field not in card:
            continue
        source = Path(card[field]).resolve()
        if not source.is_file():
            raise RuntimeError(f"CARD_MEDIA_MISSING:{card['card_id']}")
        filename = f"{card['card_id']}_{source.name}"
        is_image = source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        # Images are part of the project design, not user media to relink.  Put
        # them in the draft Resources directory later; only audio/video files
        # remain deliberately offline.  CapCut's folder relink accepts the
        # latter reliably (as proven by the v3 probe), but not a mixed PNG/MP4
        # batch.
        if is_image:
            width, height = image_size(source)
            info: dict[str, Any] = {"width": width, "height": height, "duration_us": int(card["target_duration_us"]), "has_audio": False, "kind": "photo"}
            target = source
            storage = "embedded"
        else:
            target = media_dir / filename
            if target.exists():
                raise RuntimeError(f"MEDIA_NAME_COLLISION:{filename}")
            shutil.copy2(source, target)
            info = dict(probe_media(target))
            info["kind"] = "video"
            storage = "relink"
        expected_sha_field = {"SOURCE_VIDEO": "source_sha256", "NARRATION_VIDEO": "video_sha256"}.get(kind, "image_sha256")
        expected_sha = str(card.get(expected_sha_field, "")).upper()
        if not expected_sha or sha256(source).upper() != expected_sha:
            raise RuntimeError(f"CARD_MEDIA_SHA256_INVALID:{card['card_id']}")
        if kind in {"SOURCE_VIDEO", "NARRATION_VIDEO"}:
            start_field = "source_start_us" if kind == "SOURCE_VIDEO" else "video_start_us"
            duration_field = "source_duration_us" if kind == "SOURCE_VIDEO" else "video_duration_us"
            start = int(card.get(start_field, 0))
            duration = int(card.get(duration_field, card["target_duration_us"]))
            if start < 0 or duration <= 0 or start + duration > int(info["duration_us"]):
                raise RuntimeError(f"SOURCE_RANGE_INVALID:{card['card_id']}")
        else:
            start, duration = 0, int(card["target_duration_us"])
        record = {
            "file": str(target),
            "filename": filename,
            "sha256": sha256(target),
            "offline_path": f"C:/__CAPCUT_RELINK_REQUIRED__/{episode_id}/Media/{filename}" if storage == "relink" else "",
            "storage": storage,
            "source_start": start,
            "source_duration": duration,
            **info,
        }
        if kind == "NARRATION_VIDEO":
            record["source_audio_mode"] = str(card.get("source_audio_mode", ""))
        if kind in {"NARRATION_IMAGE", "NARRATION_VIDEO"}:
            audio = _require_file_sha(card, "narration_audio_file", "narration_audio_sha256", "NARRATION_AUDIO_SHA256_INVALID")
            audio_filename = f"{card['card_id']}_{audio.name}"
            audio_target = media_dir / audio_filename
            if audio_target.exists():
                raise RuntimeError(f"MEDIA_NAME_COLLISION:{audio_filename}")
            shutil.copy2(audio, audio_target)
            audio_total = probe_duration(audio_target)
            audio_start = int(card.get("audio_start_us", 0))
            audio_duration = int(card.get("audio_duration_us", card["target_duration_us"]))
            if audio_start < 0 or audio_duration <= 0 or audio_start + audio_duration > audio_total + AUDIO_DURATION_TOLERANCE_US:
                raise RuntimeError(f"NARRATION_AUDIO_RANGE_INVALID:{card['card_id']}")
            record["narration_audio"] = {
                "file": str(audio_target),
                "filename": audio_filename,
                "sha256": sha256(audio_target),
                "offline_path": f"C:/__CAPCUT_RELINK_REQUIRED__/{episode_id}/Media/{audio_filename}",
                "storage": "relink",
                "source_start": audio_start,
                "source_duration": audio_duration,
                "duration_us": audio_total,
                "kind": "audio",
            }
        records[card["card_id"]] = record
    return records


def embed_design_images(stage: Path, final_root: Path, records: dict[str, dict[str, Any]]) -> None:
    """Copy design images into this project; never make them relink candidates."""
    resource_dir = stage / "Resources" / "media"
    for record in records.values():
        if record.get("storage") != "embedded":
            continue
        destination = resource_dir / record["filename"]
        if destination.exists():
            raise RuntimeError(f"EMBEDDED_IMAGE_NAME_COLLISION:{record['filename']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(record["file"]), destination)
        if sha256(destination) != record["sha256"]:
            raise RuntimeError("EMBEDDED_IMAGE_COPY_INTEGRITY_INVALID")
        record["embedded_relpath"] = destination.relative_to(stage).as_posix()
        record["offline_path"] = str(final_root / record["embedded_relpath"]).replace("\\", "/")


def build_document(document: dict[str, Any], cards: list[dict[str, Any]], total: int, media: dict[str, dict[str, Any]], project_name: str) -> dict[str, Any]:
    text_intro = material_by_text(document, lambda value: value.startswith("__INTRO_HOOK_LINE_1__"), "INTRO")
    text_chapter = material_by_text(document, lambda value: value == "__CHAPTER__", "CHAPTER")
    text_source = material_by_text(document, lambda value: value.startswith("출처 __SOURCE__"), "SOURCE")
    text_lower = material_by_text(document, lambda value: value.startswith("__LOWER_LINE_1__"), "LOWER")
    text_cta = material_by_text(document, lambda value: value.startswith("구독은 "), "CTA")
    intro_track, intro_segment = segment_for(document, text_intro["id"])
    chapter_track, chapter_segment = segment_for(document, text_chapter["id"])
    source_track, source_segment = segment_for(document, text_source["id"])
    lower_track, lower_segment = segment_for(document, text_lower["id"])
    cta_track, cta_segment = segment_for(document, text_cta["id"])
    for track, segment in ((chapter_track, chapter_segment), (source_track, source_segment), (lower_track, lower_segment)):
        remove_segment(track, segment)
    # The GUI relink probe deliberately carried one literal chapter-hook sample.
    # It is never allowed to leak into a real episode; each CHAPTER_CARD below
    # creates its own hook from the editable intro-text geometry.
    for material in document["materials"]["texts"]:
        value = text_of(material)
        if value.startswith("챕터 ") and "\n" in value:
            trial_track, trial_segment = segment_for(document, material["id"])
            remove_segment(trial_track, trial_segment)

    has_intro = cards[0]["card_type"] == "INTRO"
    intro_duration = int(cards[0]["target_duration_us"]) if has_intro else 0
    main_ui_start = next(
        int(card["target_start_us"])
        for card in cards
        if card["card_type"] != "CHAPTER_CARD"
    )
    set_range(cta_segment, main_ui_start, total - main_ui_start)
    videos = document["materials"]["videos"]
    intro_video = next(item for item in videos if item.get("type") == "video")
    photo_video = next(item for item in videos if item.get("type") == "photo")
    video_tracks = [track for track in document["tracks"] if track.get("type") == "video"]
    intro_video_track, intro_video_segment = next(
        (track, segment) for track in video_tracks for segment in track.get("segments", []) if segment.get("material_id") == intro_video["id"]
    )
    photo_track, photo_segment = next(
        (track, segment) for track in video_tracks for segment in track.get("segments", []) if segment.get("material_id") == photo_video["id"]
    )
    if has_intro:
        set_material_text(text_intro, str(cards[0].get("text", cards[0].get("intro_text", ""))))
        set_range(intro_segment, 0, intro_duration)
        set_range(intro_video_segment, 0, intro_duration)
        intro_video_segment["source_timerange"] = {"start": 0, "duration": intro_duration}
        intro_video_track["segments"] = [intro_video_segment]
    else:
        remove_segment(intro_track, intro_segment)
        intro_video_track["segments"] = []
    photo_video["duration"] = total
    set_range(photo_segment, intro_duration, total - intro_duration)
    photo_segment["source_timerange"] = {"start": 0, "duration": total - intro_duration}
    # Keep every visible card on one contiguous primary video lane.  CapCut
    # compacts a source-video lane across gaps when chapter stills live on a
    # different lane, which shifts every following source clip earlier.  The
    # intro, silent chapter images, narration images, and source clips must
    # therefore occupy this same lane in their declared card order.
    # The focus-lines photo remains a separate full-duration overlay track.
    photo_segment.setdefault("clip", {})["alpha"] = 0.8

    # The upper/lower decorative rails are static sticker assets.  Preserve
    # their authored start point, but carry them to the actual episode end.
    for track in document["tracks"]:
        if track.get("type") != "sticker":
            continue
        for segment in track.get("segments", []):
            start = int(segment.get("target_timerange", {}).get("start", 0))
            if 0 < start < total:
                set_range(segment, start, total - start)

    first_visual_index = 1 if has_intro else 0
    for card_index, card in enumerate(cards[first_visual_index:], start=first_visual_index):
        start, duration = int(card["target_start_us"]), int(card["target_duration_us"])
        kind = card["card_type"]
        lower_mode = card.get("lower_mode", "NONE")
        record = media.get(card["card_id"])
        if kind == "CHAPTER_CARD":
            if record is None:
                raise RuntimeError(f"CHAPTER_IMAGE_REQUIRED:{card['card_id']}")
            clone_media(document, photo_video, photo_segment, None, target_track=intro_video_track, kind="photo", offline_path=record["offline_path"], filename=record["filename"], width=int(record["width"]), height=int(record["height"]), source_start=0, source_duration=duration, media_duration=int(record["duration_us"]), target_start=start, target_duration=duration, has_audio=False)
            next_chapter_start = next(
                (
                    int(next_card["target_start_us"])
                    for next_card in cards[card_index + 1 :]
                    if next_card["card_type"] == "CHAPTER_CARD"
                ),
                total,
            )
            # A chapter is a state, not a 3-second flash: keep its concise
            # upper title across the following source-video block.
            clone_text(document, text_chapter, chapter_segment, chapter_track, str(card["chapter_label"]), start, next_chapter_start - start)
            clone_text(document, text_intro, intro_segment, intro_track, str(card["chapter_hook"]), start, duration)
        elif kind in {"SOURCE_VIDEO", "NARRATION_VIDEO"}:
            if record is None:
                raise RuntimeError(f"VIDEO_REQUIRED:{card['card_id']}")
            clone_media(document, intro_video, intro_video_segment, None, target_track=intro_video_track, kind="video", offline_path=record["offline_path"], filename=record["filename"], width=int(record["width"]), height=int(record["height"]), source_start=int(record["source_start"]), source_duration=int(record["source_duration"]), media_duration=int(record["duration_us"]), target_start=start, target_duration=duration, has_audio=bool(record["has_audio"]) if kind == "SOURCE_VIDEO" else False)
            if kind == "SOURCE_VIDEO":
                channel, date = str(card.get("source_channel", "")).strip(), str(card.get("source_date", "")).strip()
                if not channel or not date:
                    raise RuntimeError(f"SOURCE_LABEL_REQUIRED:{card['card_id']}")
                chapter_label = str(card.get("chapter_label", "")).strip()
                if chapter_label:
                    clone_text(document, text_chapter, chapter_segment, chapter_track, chapter_label, start, duration)
                clone_text(document, text_source, source_segment, source_track, f"출처 {channel}\n{date}", start, duration)
        elif kind == "NARRATION_IMAGE":
            if record is None:
                raise RuntimeError(f"IMAGE_REQUIRED:{card['card_id']}")
            clone_media(document, photo_video, photo_segment, None, target_track=intro_video_track, kind="photo", offline_path=record["offline_path"], filename=record["filename"], width=int(record["width"]), height=int(record["height"]), source_start=0, source_duration=duration, media_duration=int(record["duration_us"]), target_start=start, target_duration=duration, has_audio=False)
        elif kind in {"TEXT_EXPLAINER", "ENDING"}:
            pass
        else:
            raise RuntimeError(f"CARD_TYPE_UNSUPPORTED:{kind}")
        if kind in {"NARRATION_IMAGE", "NARRATION_VIDEO"}:
            clone_narration_audio(document, record, start, duration)
        if lower_mode in {"SOURCE_TTS", "NARRATION_TTS"}:
            srt_field = "source_srt_file" if lower_mode == "SOURCE_TTS" else "narration_srt_file"
            for cue_start, cue_end, cue_text in _srt_cues(Path(card[srt_field])):
                clone_text(document, text_lower, lower_segment, lower_track, cue_text, cue_start, cue_end - cue_start)
        elif lower_mode == "VIDEO100_EXPLAINER":
            clone_text(document, text_lower, lower_segment, lower_track, str(card["lower_text"]), start, duration)

    trim_all_tracks_to_duration(document, total)
    for index, track in enumerate(document["tracks"]):
        for segment in track.get("segments", []):
            segment["track_render_index"] = index
    prune_unreferenced_text_materials(document)
    document["duration"] = total
    document["name"] = project_name
    return document


def validate_build(
    root: Path,
    media_records: dict[str, dict[str, Any]],
    total: int,
    *,
    path_reference: Path | None = None,
    cards: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    junk = [path.relative_to(root).as_posix() for path in root.rglob("*") if JUNK_RE.search(path.name)]
    if junk:
        raise RuntimeError("PROJECT_JUNK_PRESENT")
    mirrors = [root / "draft_content.json", root / "template-2.tmp"] + sorted((root / "Timelines").glob("*/draft_content.json")) + sorted((root / "Timelines").glob("*/template-2.tmp"))
    if len(mirrors) != 4 or any(not path.is_file() for path in mirrors):
        raise RuntimeError("PROJECT_MIRROR_SET_INVALID")
    hashes = {sha256(path) for path in mirrors}
    if len(hashes) != 1:
        raise RuntimeError("PROJECT_MIRROR_MISMATCH")
    document = json_load(root / "draft_content.json")
    root_prefix = str(path_reference or root).replace("\\", "/").lower().rstrip("/") + "/"
    foreign_root_media = [
        item.get("path", "")
        for item in document.get("materials", {}).get("videos", [])
        if item.get("path")
        and "__CAPCUT_RELINK_REQUIRED__" not in item["path"]
        and not item["path"].replace("\\", "/").lower().startswith(root_prefix)
    ]
    if foreign_root_media:
        raise RuntimeError("FOREIGN_ROOT_MEDIA_PATH:" + " | ".join(foreign_root_media[:3]))
    if int(document["duration"]) != total:
        raise RuntimeError("PROJECT_DURATION_INVALID")
    valid_ids = {item.get("id") for group in document.get("materials", {}).values() if isinstance(group, list) for item in group if isinstance(item, dict)}
    if any(segment.get("material_id") not in valid_ids for track in document["tracks"] for segment in track.get("segments", [])):
        raise RuntimeError("PROJECT_DANGLING_SEGMENT")
    referenced_text = {
        segment.get("material_id")
        for track in document["tracks"]
        if track.get("type") == "text"
        for segment in track.get("segments", [])
    }
    if any(item.get("id") not in referenced_text for item in document["materials"]["texts"]):
        raise RuntimeError("UNREFERENCED_TEXT_MATERIAL")
    if any("3분 연결 시험" in text_of(item) for item in document["materials"]["texts"]):
        raise RuntimeError("LEGACY_TRIAL_TEXT_PRESENT")
    lower = [
        segment["target_timerange"]
        for track in document["tracks"]
        if track.get("type") == "text"
        for segment in track.get("segments", [])
        if any(item.get("id") == segment.get("material_id") and text_of(item).count("\n") == 1 and not text_of(item).startswith("출처 ") and not text_of(item).startswith("구독은 ") for item in document["materials"]["texts"])
    ]
    lower.sort(key=lambda row: row["start"])
    if any(left["start"] + left["duration"] > right["start"] for left, right in zip(lower, lower[1:])):
        raise RuntimeError("LOWER_SLOT_OVERLAP")
    for record in media_records.values():
        media_file = root / record["embedded_relpath"] if record.get("storage") == "embedded" else Path(record["file"])
        if not media_file.is_file() or sha256(media_file) != record["sha256"]:
            raise RuntimeError("MEDIA_COPY_INTEGRITY_INVALID")
    return {
        "status": "PASS",
        "duration_sec": total / MICROS,
        "mirror_sha256": next(iter(hashes)),
        "media_count": len(media_records),
        "lower_slot_overlap": False,
        "presentation_contract": capture_presentation_contract(document, cards),
    }


def register_project(meta_path: Path, source_name: str, project_name: str, project_root: Path, duration: int) -> bytes:
    original = meta_path.read_bytes()
    meta = json.loads(original.decode("utf-8"))
    source = next((item for item in meta.get("all_draft_store", []) if item.get("draft_name") == source_name), None)
    if source is None or any(item.get("draft_name") == project_name for item in meta.get("all_draft_store", [])):
        raise RuntimeError("ROOT_META_REGISTRATION_INVALID")
    entry = copy.deepcopy(source)
    root_posix = str(project_root).replace("\\", "/")
    entry.update({"draft_name": project_name, "draft_id": uid(), "draft_fold_path": root_posix, "draft_json_file": root_posix + "/draft_content.json", "draft_cover": root_posix + "/draft_cover.jpg", "draft_root_path": str(project_root.parent).replace("\\", "/"), "tm_duration": duration, "draft_cloud_sync": False, "draft_cloud_template_id": ""})
    meta["all_draft_store"].append(entry)
    json_write(meta_path, meta)
    return original


def build_report_payload(
    *,
    project: Path,
    media_dir: Path,
    cards: list[dict[str, Any]],
    media_records: dict[str, dict[str, Any]],
    static: dict[str, Any],
    resolved_root: ResolvedRoot,
) -> dict[str, Any]:
    def portable(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: portable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, str) and (
            Path(value).is_absolute() or PureWindowsPath(value).is_absolute()
        ):
            return f"LOCAL_PATH/{PureWindowsPath(value).name}"
        return value

    public_media = portable(copy.deepcopy(media_records))
    for record in public_media.values():
        filename = record.get("filename", "media")
        if "file" in record:
            record["file"] = f"LOCAL_MEDIA_FILE/{filename}"
        if record.get("offline_path"):
            record["offline_path"] = f"CAPCUT_RELINK_PLACEHOLDER/{filename}"
    media_reference = "/".join(
        ["LOCAL_MEDIA_FOLDER", media_dir.parent.name, media_dir.name]
    )
    return {
        "status": "PROJECT_CREATED_WAIT_MEDIA_RELINK",
        "project": f"LOCAL_CAPCUT_DRAFT/{project.name}",
        "media_folder_to_select": media_reference,
        "root_bundle": resolved_root.to_report(),
        "cards": portable(copy.deepcopy(cards)),
        "media": public_media,
        "static_validation": portable(copy.deepcopy(static)),
        "PROJECT_BUILD": "PASS",
        "STATIC_STRUCTURE": "PASS",
        "MEDIA_RELINK": "WAIT",
        "MEDIA_RESOLUTION": "WAIT",
        "VISUAL_GATE": "WAIT_USER_VISUAL_GATE",
        "MP4": "NOT_RUN",
        "UPLOAD": "NOT_RUN",
        "next": "Open in CapCut, select Media Relink, choose the local media folder printed by the builder CLI, save, close, then run post-open readback.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--capcut-root", type=Path, required=True)
    parser.add_argument("--media-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--replace-invalid-target", action="store_true")
    args = parser.parse_args()
    require_capcut_closed()
    resolved_root = resolve_active_root(args.workspace_root)
    require_non_stock_builder_for_adapter_root(resolved_root)
    cards_doc = json_load(args.cards)
    episode_id = str(cards_doc.get("episode_id", "")).strip()
    project_name = str(cards_doc.get("project_name", "")).strip()
    if not episode_id or not project_name or Path(project_name).name != project_name:
        raise RuntimeError("EPISODE_OR_PROJECT_NAME_INVALID")
    layout = json_load(resolved_root.layout_path)
    content_start_us = layout.get("content_start_us")
    if isinstance(content_start_us, bool) or not isinstance(content_start_us, int) or content_start_us < 0:
        raise RuntimeError("ROOT_CONTENT_START_INVALID")
    cards, total = normalize_cards(cards_doc, content_start_us=content_start_us)
    if any(card["card_type"] in {"NARRATION_IMAGE", "NARRATION_VIDEO"} for card in cards):
        narration_doc = copy.deepcopy(cards_doc)
        narration_doc["cards"] = cards
        validate_narration_contract(narration_doc)
    final_root = args.capcut_root / project_name
    meta_path = args.capcut_root / "root_meta_info.json"
    if not meta_path.is_file():
        raise RuntimeError("ROOT_META_INFO_MISSING")
    if final_root.exists() or args.media_dir.exists():
        if not args.replace_invalid_target:
            raise RuntimeError("PROJECT_TARGET_OR_MEDIA_DIR_EXISTS")
        if final_root.exists():
            try:
                validate_build(final_root, {}, int(json_load(final_root / "draft_content.json")["duration"]))
            except RuntimeError:
                meta = json_load(meta_path)
                meta["all_draft_store"] = [item for item in meta.get("all_draft_store", []) if item.get("draft_name") != project_name]
                json_write(meta_path, meta)
                shutil.rmtree(final_root)
            else:
                raise RuntimeError("PROJECT_TARGET_ALREADY_VALID")
        if args.media_dir.exists():
            shutil.rmtree(args.media_dir)
        if args.report.exists():
            args.report.unlink()
    original_meta: bytes | None = None
    published = False
    staging_parent = Path(os.environ["LOCALAPPDATA"]) / "CodexCapCutStaging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="politics-cards-", dir=staging_parent) as temporary:
        try:
            stage = extract_root(resolved_root.archive_path, Path(temporary))
            source_root_name = stage.name
            renamed = Path(temporary) / project_name
            stage.rename(renamed)
            stage = renamed
            media_records = copy_card_media(cards, args.media_dir, episode_id)
            embed_design_images(stage, final_root, media_records)
            document, timeline = remap_ids(stage, final_root, project_name, source_root_name)
            document = build_document(document, cards, total, media_records, project_name)
            mirror(stage, timeline, document)
            static = validate_build(stage, media_records, total, path_reference=final_root, cards=cards)
            shutil.copytree(stage, final_root)
            published = True
            static = validate_build(final_root, media_records, total, cards=cards)
            original_meta = register_project(meta_path, source_root_name, project_name, final_root, total)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            report = build_report_payload(
                project=final_root,
                media_dir=args.media_dir,
                cards=cards,
                media_records=media_records,
                static=static,
                resolved_root=resolved_root,
            )
            json_write(args.report, report)
            print(json.dumps({"status": "PASS", "project": str(final_root), "media_dir": str(args.media_dir), "static": static}, ensure_ascii=False))
        except Exception:
            if original_meta is not None:
                meta_path.write_bytes(original_meta)
            if published and final_root.exists():
                shutil.rmtree(final_root)
            if args.media_dir.exists():
                shutil.rmtree(args.media_dir)
            raise


if __name__ == "__main__":
    main()
