#!/usr/bin/env python3
"""Assemble cards into the user-authored V8 manual overlay root.

V8 keeps source video and inset image cards on different tracks, and keeps
source-SRT and narration-TTS captions on separate (time-exclusive) tracks.
It is deliberately a root-path override: it never changes the active v7 root.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from build_politics_card_project import (
    MICROS,
    _srt_cues,
    clone_media,
    clone_sequential_single_line_text,
    clone_text,
    copy_card_media,
    embed_design_images,
    json_load,
    json_write,
    mirror,
    normalize_cards,
    register_project,
    remap_ids,
    require_capcut_closed,
    set_range,
    text_of,
    trim_all_tracks_to_duration,
    uid,
    validate_build,
)

V8_TRACK_TYPES = {
    0: "video", 1: "video", 2: "sticker", 3: "sticker", 4: "video",
    5: "video", 6: "text", 7: "text", 8: "text", 9: "text",
    10: "text", 11: "audio",
}
V8_MEDIA_SPECS = {
    0: {"type": "video", "width": 1920, "height": 1080, "scale": 1.0, "x": 0.0, "y": 0.0},
    1: {"type": "photo", "width": 1920, "height": 1080, "scale": 1.0, "x": 0.0, "y": 0.0},
    4: {"type": "photo", "width": 1920, "height": 1080, "scale": 0.65, "x": 0.0, "y": 0.0},
    5: {"type": "photo", "width": 1920, "height": 1080, "scale": 1.0, "x": 0.0, "y": 0.0},
}
V8_SHAPE_SPECS = {
    2: {"shape_size": (785.874800827492, 71.74011405607625), "x": -0.031981586359368985, "y": 0.8227045804762438},
    3: {"shape_size": (785.874800827492, 70.1742432712043), "x": 0.0, "y": -0.826574458206872},
}
V8_TEXT_SPECS = {
    6: {"text": "구독은 큰 힘이 됩니다.\n댓글로 의견 부탁드려요!", "font_size": 5.0, "fixed_width": 193.68038177490234, "alignment": 0, "line_spacing": 0.04, "scale": 0.9, "rotation": 0.0, "x": 0.7578995227813721, "y": -0.5537952246973885, "fill": (1.0, 1.0, 1.0), "stroke": 0.06},
    7: {"text": "SRT", "font_size": 8.0, "fixed_width": 679.2648410797119, "alignment": 1, "line_spacing": 0.04, "scale": 1.0, "rotation": 0.030146881484351257, "x": 0.0, "y": -0.8333333333333334, "fill": (0.941176474094391, 1.0, 0.0), "stroke": 0.08},
    8: {"text": "TTS", "font_size": 8.0, "fixed_width": 679.2648410797119, "alignment": 1, "line_spacing": 0.04, "scale": 1.0, "rotation": 0.030146881484351257, "x": 0.0, "y": -0.8333333333333334, "fill": (0.941176474094391, 1.0, 0.0), "stroke": 0.08},
    9: {"text": "출처 __SOURCE__", "font_size": 5.0, "fixed_width": 334.8208165168762, "alignment": 1, "line_spacing": -0.01, "scale": 1.0, "rotation": 0.0, "x": 0.0, "y": 0.6944444444444444, "fill": (1.0, 1.0, 1.0), "stroke": 0.06},
    10: {"text": "__CHAPTER__", "font_size": 7.0, "fixed_width": 504.2707247336902, "alignment": 1, "line_spacing": 0.04, "scale": 1.0, "rotation": 0.0, "x": 0.0, "y": 0.8333333333333334, "fill": (1.0, 1.0, 1.0), "stroke": 0.06},
}
PATH_VALUE_KEYS = {"path", "source_path", "file_path", "res_path", "media_path"}
# copy_card_media writes this placeholder for every relink-mode asset. The v7
# builder allows it explicitly; the V8 tree check must allow the same token or it
# rejects the paths its own media helper just produced.
RELINK_PLACEHOLDER_ROOT = "C:/__CAPCUT_RELINK_REQUIRED__"


def material_map(document: dict[str, Any], group: str) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in document["materials"].get(group, []) if isinstance(item, dict)}


def _close(actual: Any, expected: float, tolerance: float = 1e-6) -> bool:
    try:
        return abs(float(actual) - expected) <= tolerance
    except (TypeError, ValueError):
        return False


def _assert_clip(segment: dict[str, Any], index: int, spec: dict[str, Any]) -> None:
    clip = segment.get("clip")
    if not isinstance(clip, dict):
        raise RuntimeError(f"V8_ROOT_CLIP_REQUIRED:{index}")
    scale = clip.get("scale", {})
    transform = clip.get("transform", {})
    values = (
        (scale.get("x"), spec["scale"]), (scale.get("y"), spec["scale"]),
        (transform.get("x"), spec["x"]), (transform.get("y"), spec["y"]),
        (clip.get("rotation"), spec.get("rotation", 0.0)), (clip.get("alpha"), 1.0),
    )
    if any(not _close(actual, expected) for actual, expected in values):
        raise RuntimeError(f"V8_ROOT_CLIP_GEOMETRY_INVALID:{index}")


def _style_values(material: dict[str, Any]) -> tuple[tuple[float, ...], float]:
    try:
        content = json.loads(material["content"])
        style = content["styles"][0]
        fill = tuple(float(value) for value in style["fill"]["content"]["solid"]["color"])
        stroke = float(style["strokes"][0]["width"])
        return fill, stroke
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError("V8_ROOT_TEXT_STYLE_INVALID") from error


def assert_v8_root_layout(document: dict[str, Any]) -> None:
    """Fail closed when a root no longer matches the user-authored V8 lanes."""
    tracks = document.get("tracks", [])
    if len(tracks) != len(V8_TRACK_TYPES):
        raise RuntimeError(f"V8_ROOT_TRACK_COUNT_INVALID:{len(tracks)}")
    for index, expected_type in V8_TRACK_TYPES.items():
        if tracks[index].get("type") != expected_type:
            raise RuntimeError(f"V8_ROOT_TRACK_ROLE_INVALID:{index}:{tracks[index].get('type')}:{expected_type}")
    videos = material_map(document, "videos")
    shapes = material_map(document, "shapes")
    texts = material_map(document, "texts")
    audios = material_map(document, "audios")
    for index, spec in V8_MEDIA_SPECS.items():
        segments = tracks[index].get("segments", [])
        if not segments or (index in (1, 5) and len(segments) != 1):
            raise RuntimeError(f"V8_ROOT_MEDIA_SEGMENT_INVALID:{index}")
        for segment in segments:
            material = videos.get(str(segment.get("material_id", "")))
            if material is None or material.get("type") != spec["type"] or int(material.get("width", -1)) != spec["width"] or int(material.get("height", -1)) != spec["height"]:
                raise RuntimeError(f"V8_ROOT_MEDIA_MATERIAL_INVALID:{index}")
            _assert_clip(segment, index, spec)
    for index, spec in V8_SHAPE_SPECS.items():
        segments = tracks[index].get("segments", [])
        if len(segments) != 1:
            raise RuntimeError(f"V8_ROOT_BAND_SEGMENT_INVALID:{index}")
        material = shapes.get(str(segments[0].get("material_id", "")))
        size = material.get("shape_size", []) if material else []
        if material is None or len(size) != 2 or any(not _close(size[position], expected) for position, expected in enumerate(spec["shape_size"])) or not _close(material.get("global_alpha"), 0.5) or not _close(material.get("border_width"), 4.0) or str(material.get("border_color", "")).upper() != "#CCCCCC":
            raise RuntimeError(f"V8_ROOT_BAND_MATERIAL_INVALID:{index}")
        _assert_clip(segments[0], index, {**spec, "scale": 1.0, "rotation": 0.0})
    for index, spec in V8_TEXT_SPECS.items():
        segments = tracks[index].get("segments", [])
        if not segments or (index in (6, 9, 10) and len(segments) != 1):
            raise RuntimeError(f"V8_ROOT_TEXT_SEGMENT_INVALID:{index}")
        for segment in segments:
            material = texts.get(str(segment.get("material_id", "")))
            if material is None or text_of(material) != spec["text"]:
                raise RuntimeError(f"V8_ROOT_TEXT_PLACEHOLDER_INVALID:{index}")
            numeric = (("font_size", spec["font_size"]), ("fixed_width", spec["fixed_width"]), ("line_spacing", spec["line_spacing"]))
            if any(not _close(material.get(field), expected) for field, expected in numeric) or int(material.get("alignment", -1)) != spec["alignment"]:
                raise RuntimeError(f"V8_ROOT_TEXT_GEOMETRY_INVALID:{index}")
            fill, stroke = _style_values(material)
            if len(fill) != 3 or any(not _close(fill[position], expected) for position, expected in enumerate(spec["fill"])) or not _close(stroke, spec["stroke"]):
                raise RuntimeError(f"V8_ROOT_TEXT_STYLE_INVALID:{index}")
            _assert_clip(segment, index, spec)
    audio_segments = tracks[11].get("segments", [])
    if not audio_segments or any(str(segment.get("material_id", "")) not in audios for segment in audio_segments):
        raise RuntimeError("V8_ROOT_AUDIO_TEMPLATE_REQUIRED")


def _absolute_path(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", value)) or value.startswith("/")


def _relink_placeholder(value: str) -> bool:
    normalized = value.replace("\\", "/").casefold()
    root = RELINK_PLACEHOLDER_ROOT.casefold()
    return normalized == root or normalized.startswith(root + "/")


def _within(value: str, directory: Path) -> bool:
    normalized = value.replace("\\", "/").rstrip("/").casefold()
    parent = directory.as_posix().rstrip("/").casefold()
    return normalized == parent or normalized.startswith(parent + "/")


def root_artifact_hits(
    root: Path,
    *,
    project_path: Path | None = None,
    allowed_external: tuple[Path, ...] = (),
) -> list[str]:
    hits: list[str] = []
    project_path = project_path or root

    def walk(value: Any, location: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_normalized = str(key).casefold()
                path = f"{location}.{key}"
                if key_normalized in PATH_VALUE_KEYS and isinstance(item, str):
                    if (
                        _absolute_path(item)
                        and not _relink_placeholder(item)
                        and not _within(item, project_path)
                        and not any(_within(item, allowed) for allowed in allowed_external)
                    ):
                        hits.append(f"{location}:{key}")
                walk(item, path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{location}[{index}]")

    for path in root.rglob("*"):
        if path.name.lower().endswith(".bak"):
            hits.append(path.relative_to(root).as_posix())
        if not path.is_file() or path.suffix.lower() not in {".json", ".tmp"}:
            continue
        try:
            walk(json_load(path), path.relative_to(root).as_posix())
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return hits


def assert_v8_clean_tree(
    root: Path,
    *,
    project_path: Path | None = None,
    allowed_external: tuple[Path, ...] = (),
) -> None:
    hits = root_artifact_hits(root, project_path=project_path, allowed_external=allowed_external)
    if hits:
        raise RuntimeError(f"V8_ROOT_ARTIFACT_LEAK:{'|'.join(hits[:5])}")


def embed_root_cache_assets(stage: Path, final_root: Path) -> None:
    """Make root-owned CapCut cache assets portable in the clone only."""
    destination = stage / "Resources" / "v8_root_assets"
    copied: dict[str, str] = {}

    def rewrite(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: rewrite_path(key, item) for key, item in value.items()}
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        return value

    def rewrite_path(key: str, value: Any) -> Any:
        normalized = value.replace("\\", "/") if isinstance(value, str) else ""
        if key.casefold() not in PATH_VALUE_KEYS or not isinstance(value, str) or not _absolute_path(normalized):
            return rewrite(value)
        if _within(normalized, final_root):
            return rewrite(value)
        source = Path(value)
        if not source.is_file():
            candidates = list((stage / "Resources").rglob(source.name))
            if len(candidates) != 1:
                raise RuntimeError(f"V8_ROOT_CACHE_ASSET_MISSING:{source}")
            source = candidates[0]
        if value not in copied:
            destination.mkdir(parents=True, exist_ok=True)
            target = destination / source.name
            if not target.exists():
                shutil.copy2(source, target)
            copied[value] = (final_root / "Resources" / "v8_root_assets" / source.name).as_posix()
        return copied[value]

    for path in stage.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".tmp"}:
            continue
        try:
            document = json_load(path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        json_write(path, rewrite(document))


def text_template(
    document: dict[str, Any], value: str, occurrence: int | None = None
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    materials = material_map(document, "texts")
    matches = [
        (track, segment, materials[str(segment["material_id"])])
        for track in document["tracks"]
        for segment in track.get("segments", [])
        if str(segment.get("material_id", "")) in materials and text_of(materials[str(segment["material_id"])]) == value
    ]
    if occurrence is not None:
        if len(matches) <= occurrence:
            raise RuntimeError(f"V8_TEXT_TEMPLATE_MISSING:{value}:{occurrence}")
        return matches[occurrence]
    if len(matches) != 1:
        raise RuntimeError(f"V8_TEXT_TEMPLATE_NOT_UNIQUE:{value}:{len(matches)}")
    return matches[0]


def media_template(
    document: dict[str, Any], *, track_index: int, material_type: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    materials = material_map(document, "videos")
    track = document["tracks"][track_index]
    segments = track.get("segments", [])
    if track.get("type") != "video" or not segments:
        raise RuntimeError(f"V8_MEDIA_TEMPLATE_TRACK_INVALID:{track_index}")
    material = materials.get(str(segments[0].get("material_id", "")))
    if material is None or material.get("type") != material_type:
        raise RuntimeError(f"V8_MEDIA_TEMPLATE_MATERIAL_INVALID:{track_index}:{material_type}")
    return track, segments[0], material


def remove_material_refs(document: dict[str, Any], group: str, ids: set[str]) -> None:
    document["materials"][group] = [item for item in document["materials"].get(group, []) if str(item.get("id")) not in ids]


def attach_normalization(document: dict[str, Any], segment: dict[str, Any], file_id: str, duration: int) -> None:
    old_loudness = {str(item.get("id")) for item in document["materials"].get("loudnesses", [])}
    segment["extra_material_refs"] = [
        value for value in segment.get("extra_material_refs", []) if str(value) not in old_loudness
    ]
    loudness_id = uid()
    document["materials"].setdefault("loudnesses", []).append({
        "id": loudness_id,
        "enable": True,
        "time_range": {"start": 0, "duration": int(duration)},
        "file_id": file_id,
        "target_loudness": -14.0,
        "loudness_param": None,
    })
    segment.setdefault("extra_material_refs", []).append(loudness_id)


def clone_v8_audio(
    document: dict[str, Any],
    template_track: dict[str, Any],
    template_segment: dict[str, Any],
    template_material: dict[str, Any],
    record: dict[str, Any],
    target_start: int,
    target_duration: int,
) -> None:
    audio = record["narration_audio"]
    material = copy.deepcopy(template_material)
    material_id = uid()
    file_id = uid().lower()
    material.update({
        "id": material_id,
        "music_id": uid(),
        "unique_id": file_id,
        "local_material_id": uid().lower(),
        "name": audio["filename"],
        "material_name": audio["filename"],
        "duration": int(audio["duration_us"]),
        "path": audio["offline_path"],
        "wave_points": [],
    })
    segment = copy.deepcopy(template_segment)
    segment.update({
        "id": uid(),
        "material_id": material_id,
        "source_timerange": {"start": int(audio["source_start"]), "duration": int(audio["source_duration"])},
        "target_timerange": {"start": int(target_start), "duration": int(target_duration)},
        "volume": 1.0,
        "last_nonzero_volume": 1.0,
    })
    attach_normalization(document, segment, file_id, int(audio["source_duration"]))
    document["materials"].setdefault("audios", []).append(material)
    template_track["segments"].append(segment)


def prune_unreferenced_media(document: dict[str, Any]) -> None:
    referenced = {
        str(segment.get("material_id"))
        for track in document["tracks"]
        for segment in track.get("segments", [])
    }
    for group in ("videos", "audios", "texts"):
        document["materials"][group] = [
            item for item in document["materials"].get(group, []) if str(item.get("id")) in referenced
        ]
    refs = {
        str(reference)
        for track in document["tracks"]
        for segment in track.get("segments", [])
        for reference in segment.get("extra_material_refs", [])
    }
    document["materials"]["loudnesses"] = [
        item for item in document["materials"].get("loudnesses", []) if str(item.get("id")) in refs
    ]


def extend_v8_static_overlays(document: dict[str, Any], total: int) -> None:
    """Keep the user-authored top/bottom bands and transparent focus lines alive."""
    for index in (1, 2, 3, 5):
        segments = document["tracks"][index].get("segments", [])
        if len(segments) != 1:
            raise RuntimeError(f"V8_STATIC_OVERLAY_SEGMENT_INVALID:{index}")
        set_range(segments[0], 0, total)


def delivery_report(cards_doc: dict[str, Any], project_name: str, project_path: Path, media_path: Path) -> dict[str, Any]:
    publication = cards_doc.get("publication_report")
    if not isinstance(publication, dict):
        raise RuntimeError("PUBLICATION_REPORT_REQUIRED")
    thumbnail = publication.get("thumbnail")
    content = publication.get("content")
    if not isinstance(thumbnail, dict) or not isinstance(content, dict):
        raise RuntimeError("PUBLICATION_REPORT_INVALID")
    return {
        "project_name": project_name,
        "project_path": str(project_path),
        "media_path": str(media_path),
        "title": publication.get("title"),
        "content": {
            "simple_summary": content.get("simple_summary"),
            "timeline": content.get("timeline"),
            "sources": content.get("sources"),
        },
        "thumbnail": {
            "words": thumbnail.get("words"),
            "sentences_ranked": [
                {"rank": index, "text": text}
                for index, text in enumerate(thumbnail.get("sentences", []), start=1)
            ],
        },
    }


def build_v8_document(document: dict[str, Any], cards: list[dict[str, Any]], total: int, media: dict[str, dict[str, Any]], project_name: str) -> dict[str, Any]:
    chapter_track, chapter_seed, chapter_text = text_template(document, "__CHAPTER__")
    source_track, source_seed, source_text = text_template(document, "출처 __SOURCE__")
    srt_track, srt_seed, srt_text = text_template(document, "SRT", occurrence=0)
    tts_track, tts_seed, tts_text = text_template(document, "TTS", occurrence=0)
    cta_track, cta_seed, _ = next(
        (track, segment, material)
        for track in document["tracks"]
        for segment in track.get("segments", [])
        for material in document["materials"].get("texts", [])
        if str(segment.get("material_id")) == str(material.get("id")) and text_of(material).startswith("구독은 ")
    )
    source_video_track, source_video_seed, source_video_material = media_template(
        document, track_index=0, material_type="video"
    )
    image_track, image_seed, image_material = media_template(
        document, track_index=4, material_type="photo"
    )
    audio_tracks = [track for track in document["tracks"] if track.get("type") == "audio"]
    if len(audio_tracks) != 1 or not audio_tracks[0].get("segments"):
        raise RuntimeError("V8_AUDIO_TEMPLATE_REQUIRED")
    audio_track = audio_tracks[0]
    audio_seed = audio_track["segments"][0]
    audio_materials = material_map(document, "audios")
    audio_material = audio_materials.get(str(audio_seed.get("material_id")))
    if audio_material is None:
        raise RuntimeError("V8_AUDIO_MATERIAL_REQUIRED")

    for track in (chapter_track, source_track, srt_track, tts_track, source_video_track, image_track, audio_track):
        track["segments"] = []
    if cards[0].get("cta_like_subscribe", "OFF") == "ON":
        set_range(cta_seed, 0, total)
    else:
        cta_track["segments"] = []

    labels = []
    current = None
    for card in cards:
        label = str(card.get("chapter_label", "")).strip()
        if label != current:
            labels.append((int(card["target_start_us"]), label))
            current = label
    for index, (start, label) in enumerate(labels):
        end = labels[index + 1][0] if index + 1 < len(labels) else total
        clone_text(document, chapter_text, chapter_seed, chapter_track, label, start, end - start)

    for card in cards:
        start, duration = int(card["target_start_us"]), int(card["target_duration_us"])
        kind = str(card["card_type"])
        record = media.get(str(card["card_id"]))
        if kind == "SOURCE_VIDEO":
            if record is None:
                raise RuntimeError(f"V8_SOURCE_REQUIRED:{card['card_id']}")
            clone_media(document, source_video_material, source_video_seed, None, target_track=source_video_track, kind="video", offline_path=record["offline_path"], filename=record["filename"], width=int(record["width"]), height=int(record["height"]), source_start=int(record["source_start"]), source_duration=int(record["source_duration"]), media_duration=int(record["duration_us"]), target_start=start, target_duration=duration, has_audio=True)
            source_segment = source_video_track["segments"][-1]
            source_material = document["materials"]["videos"][-1]
            attach_normalization(document, source_segment, str(source_material["local_material_id"]), int(record["source_duration"]))
            label = str(card.get("source_display_label", "")).strip()
            if not label:
                raise RuntimeError(f"V8_SOURCE_LABEL_REQUIRED:{card['card_id']}")
            clone_text(document, source_text, source_seed, source_track, f"출처 {label}", start, duration)
        elif kind in {"CHAPTER_CARD", "NARRATION_IMAGE"}:
            if record is None:
                raise RuntimeError(f"V8_IMAGE_REQUIRED:{card['card_id']}")
            clone_media(document, image_material, image_seed, None, target_track=image_track, kind="photo", offline_path=record["offline_path"], filename=record["filename"], width=int(record["width"]), height=int(record["height"]), source_start=0, source_duration=duration, media_duration=int(record["duration_us"]), target_start=start, target_duration=duration, has_audio=False)
        else:
            raise RuntimeError(f"V8_CARD_TYPE_UNSUPPORTED:{card['card_id']}:{kind}")
        if kind == "NARRATION_IMAGE":
            clone_v8_audio(document, audio_track, audio_seed, audio_material, record, start, duration)
        lower = str(card.get("lower_mode", "NONE"))
        if lower in {"SOURCE_TTS", "NARRATION_TTS"}:
            field = "source_srt_file" if lower == "SOURCE_TTS" else "narration_srt_file"
            template_track, template_segment, template_material = (srt_track, srt_seed, srt_text) if lower == "SOURCE_TTS" else (tts_track, tts_seed, tts_text)
            for cue_start, cue_end, cue_text in _srt_cues(Path(card[field])):
                clone_text(document, template_material, template_segment, template_track, cue_text, cue_start, cue_end - cue_start)
        elif lower == "VIDEO100_EXPLAINER":
            clone_sequential_single_line_text(document, tts_text, tts_seed, tts_track, str(card["lower_text"]), start, duration)

    trim_all_tracks_to_duration(document, total)
    extend_v8_static_overlays(document, total)
    for index, track in enumerate(document["tracks"]):
        for segment in track.get("segments", []):
            segment["track_render_index"] = index
    prune_unreferenced_media(document)
    document["duration"] = total
    document["name"] = project_name
    return document


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--root-project", type=Path, required=True)
    parser.add_argument("--capcut-root", type=Path, required=True)
    parser.add_argument("--media-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--project-name")
    args = parser.parse_args()
    require_capcut_closed()
    cards_doc = json_load(args.cards)
    cards, total = normalize_cards(cards_doc)
    project_name = args.project_name or str(cards_doc["project_name"])
    final_root = args.capcut_root / project_name
    meta_path = args.capcut_root / "root_meta_info.json"
    if final_root.exists() or args.media_dir.exists():
        raise RuntimeError("PROJECT_TARGET_OR_MEDIA_DIR_EXISTS")
    if not args.root_project.is_dir() or not meta_path.is_file():
        raise RuntimeError("V8_ROOT_OR_META_REQUIRED")
    staging_parent = Path(os.environ["LOCALAPPDATA"]) / "CodexCapCutStaging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    original_meta: bytes | None = None
    published = False
    with tempfile.TemporaryDirectory(prefix="politics-v8-", dir=staging_parent) as temporary:
        try:
            stage = Path(temporary) / project_name
            shutil.copytree(args.root_project, stage)
            for stale_copy in sorted(stage.rglob("*.bak"), reverse=True):
                stale_copy.unlink()
            assert_v8_root_layout(json_load(stage / "draft_content.json"))
            media = copy_card_media(cards, args.media_dir, str(cards_doc["episode_id"]))
            embed_design_images(stage, final_root, media)
            embed_root_cache_assets(stage, final_root)
            staged_document = build_v8_document(
                json_load(stage / "draft_content.json"), cards, total, media, project_name
            )
            mirror(stage, stage / "Timelines" / str(staged_document["id"]), staged_document)
            document, timeline = remap_ids(stage, final_root, project_name, args.root_project.name)
            mirror(stage, timeline, document)
            assert_v8_clean_tree(stage, project_path=final_root, allowed_external=(args.media_dir,))
            static = validate_build(stage, media, total, path_reference=final_root, cards=cards)
            shutil.copytree(stage, final_root)
            published = True
            static = validate_build(final_root, media, total, cards=cards)
            assert_v8_clean_tree(final_root, allowed_external=(args.media_dir,))
            original_meta = register_project(meta_path, args.root_project.name, project_name, final_root, total)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            json_write(args.report, {
                "status": "PROJECT_CREATED_WAIT_MEDIA_RELINK",
                **delivery_report(cards_doc, project_name, final_root, args.media_dir),
                "cards": len(cards),
                "duration_us": total,
                "root": str(args.root_project),
                "static_validation": static,
                "AUDIO_NORMALIZE_TARGET_LUFS": -14.0,
            })
            print(json.dumps({"status": "PASS", "project": str(final_root), "media_dir": str(args.media_dir), "cards": len(cards)}, ensure_ascii=False))
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
