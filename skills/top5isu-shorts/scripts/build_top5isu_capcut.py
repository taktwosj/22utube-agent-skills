#!/usr/bin/env python3
"""Clone and populate a verified top5isu CapCut root project."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import struct
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any


class BuildFail(Exception):
    pass


TRACKS_V1 = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]
TRACKS_V2 = ["IMAGE_EFFECT_PRESETS", "FRAME", "LOGO", "TTS_TEXT", "SOURCE_TEXT", "T2", "T1"]
HIGH_IMPACT_EFFECTS = {"불꽃 회오리", "불꽃 스와이프", "불꽃 마법"}


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def make_audio_track(name: str, material_id: str, duration_us: int, volume: float = 1.0) -> dict[str, Any]:
    return {
        "id": new_id(),
        "name": name,
        "type": "audio",
        "segments": [
            {
                "id": new_id(),
                "material_id": material_id,
                "source_timerange": {"start": 0, "duration": duration_us},
                "target_timerange": {"start": 0, "duration": duration_us},
                "speed": 1.0,
                "volume": float(volume),
                "extra_material_refs": [],
                "keyframe_refs": [],
                "common_keyframes": [],
            }
        ],
    }


def read_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise BuildFail(f"object required: {path}")
    return data


def write_object(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def replace_placeholders(value: Any, local_draft_path: str) -> Any:
    if isinstance(value, dict):
        return {key: replace_placeholders(child, local_draft_path) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_placeholders(child, local_draft_path) for child in value]
    if isinstance(value, str):
        return re.sub(r"##_draftpath_placeholder_[^#]+_##", local_draft_path, value)
    return value


def normalize_subtitle_cues(cues: list[dict[str, Any]], duration_us: int) -> list[dict[str, Any]]:
    """Accept display-cue aliases and clamp only sub-millisecond tail drift."""
    normalized: list[dict[str, Any]] = []
    for cue in cues:
        start_value = cue.get("start", cue.get("start_sec"))
        end_value = cue.get("end", cue.get("end_sec"))
        if start_value is None or end_value is None:
            raise BuildFail("subtitle cue requires start/end or start_sec/end_sec")
        start_us = int(round(float(start_value) * 1_000_000))
        end_us = int(round(float(end_value) * 1_000_000))
        if end_us > duration_us and end_us - duration_us <= 1_000:
            end_us = duration_us
        if start_us < 0 or end_us <= start_us or end_us > duration_us:
            raise BuildFail("subtitle cue range is invalid")
        normalized.append(
            {
                "start": start_us / 1_000_000,
                "end": end_us / 1_000_000,
                "text": str(cue.get("text") or "").strip(),
            }
        )
    return normalized


def sanitize_inherited_cloud_identity(meta: dict[str, Any]) -> dict[str, Any]:
    """Return local-project metadata with template cloud ownership removed."""
    cleaned = copy.deepcopy(meta)
    cleaned.update(
        {
            "cloud_draft_cover": "",
            "cloud_draft_sync": False,
            "tm_draft_cloud_completed": "0",
            "tm_draft_cloud_entry_id": 0,
            "tm_draft_cloud_modified": 0,
            "tm_draft_cloud_parent_entry_id": -1,
            "tm_draft_cloud_space_id": 0,
            "tm_draft_cloud_user_id": 0,
        }
    )
    return cleaned


def set_text(material: dict[str, Any], text: str) -> None:
    content = json.loads(str(material.get("content") or "{}"))
    content["text"] = text
    for style in content.get("styles") or []:
        if isinstance(style, dict):
            style["range"] = [0, len(text)]
    material["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    material["name"] = text[:30]


def animation_names_for_segment(segment: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for ref in segment.get("extra_material_refs") or []:
        for animation in (lookup.get(str(ref)) or {}).get("animations") or []:
            name = str(animation.get("name") or "").strip()
            if name:
                names.append(name)
    return names


def split_two_line_title(title: str) -> tuple[str, str]:
    lines = [line.strip() for line in title.splitlines() if line.strip()]
    if not lines:
        raise BuildFail("title must not be empty")
    if len(lines) == 1:
        return lines[0], ""
    return lines[0], " ".join(lines[1:])


def image_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG dimensions without adding an image-library dependency."""
    header = Path(path).read_bytes()[:24]
    if header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
        width, height = struct.unpack(">II", header[16:24])
        if width > 0 and height > 0:
            return width, height
    return 1000, 800


def media_kind(path: Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "photo"
    if suffix in {".mp4", ".mov", ".m4v", ".webm"}:
        return "video"
    raise BuildFail(f"unsupported visual media: {path}")


def media_dimensions(path: Path) -> tuple[int, int]:
    path = Path(path)
    if media_kind(path) == "photo":
        return image_dimensions(path)
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", str(path),
        ],
        text=True,
    )
    streams = json.loads(raw).get("streams") or []
    if not streams:
        raise BuildFail(f"video stream missing: {path}")
    width = int(streams[0].get("width") or 0)
    height = int(streams[0].get("height") or 0)
    if width <= 0 or height <= 0:
        raise BuildFail(f"invalid video dimensions: {path}")
    return width, height


def collect_visual_media(media_dir: Path) -> list[Path]:
    media_dir = Path(media_dir)
    supported = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".m4v", ".webm"}
    assets = sorted(path for path in media_dir.glob("asset_*") if path.suffix.lower() in supported)
    if assets:
        return assets
    return sorted(path for path in media_dir.glob("scene_*") if path.suffix.lower() in supported)


def visual_asset_spec(source: Path, index: int) -> dict[str, Any]:
    kind = media_kind(source)
    return {
        "filename": f"asset_{index:02}{Path(source).suffix.lower()}",
        "type": kind,
        "has_audio": False,
    }


def media_duration_us(path: Path) -> int:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        text=True,
    )
    seconds = float(json.loads(raw)["format"]["duration"])
    return int(round(seconds * 1_000_000))


def build_project(
    template_root: Path,
    destination: Path,
    project_name: str,
    image_paths: list[Path],
    audio_path: Path,
    subtitles: dict[str, Any],
    title: str,
    duration_us: int,
    image_boundaries_us: list[int],
    final_draft_path: Path | None = None,
    source_audio_path: Path | None = None,
    bgm_path: Path | None = None,
    bgm_volume: float = 0.16,
    high_impact_indices: list[int] | None = None,
    source_label: str = "출처",
) -> dict[str, Any]:
    template_root = Path(template_root)
    destination = Path(destination)
    final_draft_path = Path(final_draft_path) if final_draft_path else destination
    if destination.exists():
        raise BuildFail(f"destination already exists: {destination}")
    if not template_root.is_dir():
        raise BuildFail(f"template root missing: {template_root}")
    if not project_name.strip() or "/" in project_name or "\\" in project_name:
        raise BuildFail("project_name must be a folder-safe name")
    if not image_paths or not all(Path(path).is_file() for path in image_paths):
        raise BuildFail("one or more visual media files are required")
    if not Path(audio_path).is_file():
        raise BuildFail("narration audio missing")
    if source_audio_path is not None and not Path(source_audio_path).is_file():
        raise BuildFail("source quote audio missing")
    if bgm_path is not None and not Path(bgm_path).is_file():
        raise BuildFail("BGM audio missing")
    if not 0.0 <= float(bgm_volume) <= 1.0:
        raise BuildFail("BGM volume must be between 0 and 1")
    cues = subtitles.get("cues")
    if not isinstance(cues, list) or not cues:
        raise BuildFail("subtitle cues are required")
    cues = normalize_subtitle_cues(cues, duration_us)
    if (
        len(image_boundaries_us) != len(image_paths) + 1
        or image_boundaries_us[0] != 0
        or image_boundaries_us[-1] != duration_us
    ):
        raise BuildFail("image boundaries must match image count and span the full duration")
    if any(a >= b for a, b in zip(image_boundaries_us, image_boundaries_us[1:])):
        raise BuildFail("image boundaries must be strictly increasing")
    image_sizes = [media_dimensions(Path(path)) for path in image_paths]
    visual_specs = [visual_asset_spec(Path(path), index) for index, path in enumerate(image_paths, 1)]

    shutil.copytree(template_root, destination)
    media_dir = destination / "Resources" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    for sample in media_dir.glob("leehaneul_*.png"):
        sample.unlink()
    for sample in media_dir.glob("top55_sample_image.*"):
        sample.unlink()
    for sample in media_dir.glob("top55_neutral_placeholder_*"):
        sample.unlink()
    copied_images: list[Path] = []
    for index, source in enumerate(image_paths, 1):
        target = media_dir / visual_specs[index - 1]["filename"]
        shutil.copy2(source, target)
        copied_images.append(target)
    narration_target = media_dir / "narration_final.wav"
    shutil.copy2(audio_path, narration_target)
    source_audio_target = media_dir / "source_quotes_timeline.wav"
    if source_audio_path is not None:
        shutil.copy2(source_audio_path, source_audio_target)
    bgm_target = media_dir / "bgm_final.wav"
    if bgm_path is not None:
        shutil.copy2(bgm_path, bgm_target)
    cover_source = next(
        (path for path, spec in zip(copied_images, visual_specs) if spec["type"] == "photo"),
        None,
    )
    if cover_source is not None:
        shutil.copy2(cover_source, destination / "draft_cover.jpg")
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "0", "-i", str(copied_images[0]), "-frames:v", "1", str(destination / "draft_cover.jpg")],
            check=True,
        )

    content = read_object(destination / "draft_content.json")
    materials = content.setdefault("materials", {})
    tracks = content.get("tracks") or []
    track_names = [track.get("name") for track in tracks]
    if track_names == TRACKS_V2:
        template_version = "top5isu_v2_top55"
    elif track_names == TRACKS_V1:
        template_version = "top5isu_v1"
    else:
        raise BuildFail("template track order is invalid")
    image_prototypes = tracks[0].get("segments") or []
    if template_version == "top5isu_v1" and (len(image_prototypes) != 7 or len(image_paths) != 7):
        raise BuildFail("top5isu_v1 requires seven image-effect segments and seven images")
    if template_version == "top5isu_v2_top55" and len(image_prototypes) != 4:
        raise BuildFail("top5isu_v2_top55 requires four animation prototype segments")

    timeline_id = new_id()
    project_id = new_id()
    now_us = int(time.time() * 1_000_000)
    content.update(
        {
            "id": timeline_id,
            "name": project_name,
            "duration": duration_us,
            "create_time": now_us,
            "update_time": now_us,
            "path": str(final_draft_path),
            "canvas_config": {"ratio": "9:16", "width": 1080, "height": 1920, "background": None},
        }
    )

    videos = materials.get("videos") or []
    videos_by_id = {str(item.get("id")): item for item in videos if isinstance(item, dict)}
    animation_lookup = {
        str(item.get("id")): item
        for item in materials.get("material_animations") or []
        if isinstance(item, dict)
    }
    if template_version == "top5isu_v2_top55":
        generic_prototypes: list[dict[str, Any]] = []
        strong_prototypes: list[dict[str, Any]] = []
        for prototype in image_prototypes:
            names = animation_names_for_segment(prototype, animation_lookup)
            if len(names) != 1:
                raise BuildFail("every TOP55 image prototype must contain exactly one animation")
            (strong_prototypes if names[0] in HIGH_IMPACT_EFFECTS else generic_prototypes).append(prototype)
        if not generic_prototypes or not strong_prototypes:
            raise BuildFail("TOP55 requires generic and high-impact animation prototypes")
        if high_impact_indices is None:
            high_impact_indices = [max(1, min(len(image_paths), round(len(image_paths) * 0.7)))]
        high_impact_indices = sorted(set(int(value) for value in high_impact_indices))
        if not 1 <= len(high_impact_indices) <= 2:
            raise BuildFail("one or two high-impact image indices are required")
        if any(value < 1 or value > len(image_paths) for value in high_impact_indices):
            raise BuildFail("high-impact image index is outside the image range")
        selected_prototypes: list[dict[str, Any]] = []
        generic_index = 0
        strong_index = 0
        for one_based in range(1, len(image_paths) + 1):
            if one_based in high_impact_indices:
                selected_prototypes.append(strong_prototypes[strong_index % len(strong_prototypes)])
                strong_index += 1
            else:
                selected_prototypes.append(generic_prototypes[generic_index % len(generic_prototypes)])
                generic_index += 1
    else:
        high_impact_indices = []
        selected_prototypes = image_prototypes

    prototype_material_ids = {str(segment.get("material_id")) for segment in image_prototypes}
    new_videos = [item for item in videos if str(item.get("id")) not in prototype_material_ids]
    image_segments: list[dict[str, Any]] = []
    for index, prototype in enumerate(selected_prototypes):
        prototype_material = videos_by_id.get(str(prototype.get("material_id")))
        if prototype_material is None:
            raise BuildFail(f"image material missing for prototype {index + 1}")
        segment = copy.deepcopy(prototype)
        segment["id"] = new_id()
        material = copy.deepcopy(prototype_material)
        material_id = new_id()
        material["id"] = material_id
        segment["material_id"] = material_id
        start = image_boundaries_us[index]
        segment_duration = image_boundaries_us[index + 1] - start
        spec = visual_specs[index]
        relative = f"Resources/media/{spec['filename']}"
        absolute = str(final_draft_path / relative)
        material.update(
            {
                "duration": segment_duration,
                "path": absolute,
                "media_path": absolute,
                "material_name": spec["filename"],
                "width": image_sizes[index][0],
                "height": image_sizes[index][1],
                "type": spec["type"],
                "has_audio": spec["has_audio"],
                # A cloned TOP55 prototype carries CapCut's stock-photo cache
                # identity (for example the coltsfoot-flower material).  If it
                # survives, CapCut can render that cached stock image even
                # though the file at path is the newly approved PNG.  Make
                # every imported episode image a distinct local material.
                "material_id": str(
                    7_000_000_000_000_000_000
                    + (uuid.uuid4().int % 1_000_000_000_000_000_000)
                ),
                "unique_id": new_id(),
                "local_id": new_id(),
                "local_material_id": new_id(),
                "origin_material_id": "",
                "request_id": new_id(),
                "category_id": "",
                "category_name": "",
                "material_url": "",
                "source": 0,
                "source_platform": 0,
                "check_flag": 0,
                "is_copyright": False,
            }
        )
        new_videos.append(material)
        segment["source_timerange"] = {"start": 0, "duration": segment_duration}
        segment["target_timerange"] = {"start": start, "duration": segment_duration}
        if "render_timerange" in segment:
            segment["render_timerange"] = {"start": start, "duration": segment_duration}
        if template_version == "top5isu_v1":
            transform = ((segment.setdefault("clip", {})).setdefault("transform", {}))
            transform["y"] = -0.15625
        if spec["type"] == "video":
            clip = segment.setdefault("clip", {})
            clip.setdefault("flip", {}).update({"vertical": False, "horizontal": True})
        image_segments.append(segment)
    materials["videos"] = new_videos
    # Remove prototype stock-media analytics/cache metadata as well.  This
    # file can otherwise re-associate every fresh image with the sample asset.
    (destination / "key_value.json").write_text("{}", encoding="utf-8")
    videos = new_videos
    videos_by_id = {str(item.get("id")): item for item in videos if isinstance(item, dict)}
    tracks[0]["segments"] = image_segments

    subtitle_track_name = "TTS_TEXT" if template_version == "top5isu_v2_top55" else "T2"
    subtitle_track = next(track for track in tracks if track.get("name") == subtitle_track_name)
    old_tts_material_id = str((subtitle_track.get("segments") or [{}])[0].get("material_id") or "")
    audio_id = new_id()
    materials["audios"] = [
        {
            "id": audio_id,
            "music_id": audio_id,
            "duration": duration_us,
            "path": str(final_draft_path / "Resources" / "media" / "narration_final.wav"),
            "name": "narration_final.wav",
            "material_name": "narration_final.wav",
            "type": "extract_music",
        }
    ]
    audio_segment = {
        "id": new_id(),
        "material_id": audio_id,
        "source_timerange": {"start": 0, "duration": duration_us},
        "target_timerange": {"start": 0, "duration": duration_us},
        "speed": 1.0,
        "volume": 1.0,
        "extra_material_refs": [],
        "keyframe_refs": [],
        "common_keyframes": [],
    }
    if template_version == "top5isu_v1":
        tracks[1]["type"] = "audio"
        tracks[1]["segments"] = [audio_segment]
        narration_track = tracks[1]
    else:
        narration_track = {"id": new_id(), "name": "A_TTS", "type": "audio", "segments": [audio_segment]}
        tracks.append(narration_track)

    bgm_audio_track: dict[str, Any] | None = None
    if bgm_path is not None:
        bgm_audio_id = new_id()
        materials["audios"].append(
            {
                "id": bgm_audio_id,
                "music_id": bgm_audio_id,
                "duration": duration_us,
                "path": str(final_draft_path / "Resources" / "media" / "bgm_final.wav"),
                "name": "bgm_final.wav",
                "material_name": "bgm_final.wav",
                "type": "extract_music",
            }
        )
        bgm_audio_track = make_audio_track("A_BGM", bgm_audio_id, duration_us, float(bgm_volume))
        tracks.append(bgm_audio_track)

    source_audio_track: dict[str, Any] | None = None
    if source_audio_path is not None:
        source_audio_id = new_id()
        materials["audios"].append(
            {
                "id": source_audio_id,
                "music_id": source_audio_id,
                "duration": duration_us,
                "path": str(final_draft_path / "Resources" / "media" / "source_quotes_timeline.wav"),
                "name": "source_quotes_timeline.wav",
                "material_name": "source_quotes_timeline.wav",
                "type": "extract_music",
            }
        )
        new_source_track = copy.deepcopy(narration_track)
        new_source_track.update({"id": new_id(), "name": "A_SOURCE", "type": "audio"})
        new_source_track["segments"] = [
            {
                "id": new_id(),
                "material_id": source_audio_id,
                "source_timerange": {"start": 0, "duration": duration_us},
                "target_timerange": {"start": 0, "duration": duration_us},
                "speed": 1.0,
                "volume": 1.0,
                "extra_material_refs": [],
                "keyframe_refs": [],
                "common_keyframes": [],
            }
        ]
        source_audio_track = new_source_track
        tracks.append(new_source_track)

    text_materials = materials.get("texts") or []
    text_by_id = {str(item.get("id")): item for item in text_materials if isinstance(item, dict)}

    def template_pair(track_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
        track = next((item for item in tracks if item.get("name") == track_name), None)
        if track is None:
            raise BuildFail(f"text track missing: {track_name}")
        segment = copy.deepcopy((track.get("segments") or [{}])[0])
        material = copy.deepcopy(text_by_id.get(str(segment.get("material_id"))) or {})
        if not material:
            raise BuildFail(f"text template material missing: {track_name}")
        return segment, material

    subtitle_template_segment, subtitle_template_material = template_pair(subtitle_track_name)
    new_text_materials: list[dict[str, Any]] = []
    new_subtitle_segments: list[dict[str, Any]] = []
    for cue in cues:
        start_us = int(round(float(cue["start"]) * 1_000_000))
        end_us = int(round(float(cue["end"]) * 1_000_000))
        if start_us < 0 or end_us <= start_us or end_us > duration_us:
            raise BuildFail("subtitle cue range is invalid")
        material = copy.deepcopy(subtitle_template_material)
        material_id = new_id()
        material["id"] = material_id
        set_text(material, str(cue["text"]).strip())
        segment = copy.deepcopy(subtitle_template_segment)
        segment.update(
            {
                "id": new_id(),
                "material_id": material_id,
                "target_timerange": {"start": start_us, "duration": end_us - start_us},
                "source_timerange": None,
            }
        )
        new_text_materials.append(material)
        new_subtitle_segments.append(segment)
    subtitle_track["segments"] = new_subtitle_segments

    if template_version == "top5isu_v2_top55":
        t1_text, t2_text = split_two_line_title(title)
        for track_name, value in (("SOURCE_TEXT", source_label), ("T2", t2_text), ("T1", t1_text)):
            template_segment, template_material = template_pair(track_name)
            material = copy.deepcopy(template_material)
            material_id = new_id()
            material["id"] = material_id
            set_text(material, value)
            segment = copy.deepcopy(template_segment)
            segment.update(
                {
                    "id": new_id(),
                    "material_id": material_id,
                    "target_timerange": {"start": 0, "duration": duration_us},
                    "source_timerange": None,
                }
            )
            next(track for track in tracks if track.get("name") == track_name)["segments"] = [segment]
            new_text_materials.append(material)
    else:
        t1_template_segment, t1_template_material = template_pair("T1")
        t1_material = copy.deepcopy(t1_template_material)
        t1_material_id = new_id()
        t1_material["id"] = t1_material_id
        set_text(t1_material, title)
        t1_segment = copy.deepcopy(t1_template_segment)
        t1_segment.update(
            {
                "id": new_id(),
                "material_id": t1_material_id,
                "target_timerange": {"start": 0, "duration": duration_us},
                "source_timerange": None,
            }
        )
        next(track for track in tracks if track.get("name") == "T1")["segments"] = [t1_segment]
        new_text_materials.append(t1_material)
    materials["texts"] = new_text_materials

    # Operator-locked gunlimbo colors.  Do not inherit pink/green prototype
    # colors from an older CapCut root.
    text_material_by_id = {
        str(item.get("id")): item for item in new_text_materials if isinstance(item, dict)
    }
    locked_text_colors = {
        "T1": ("#f1ff00", [0.9450980392156862, 1.0, 0.0]),
        "T2": ("#f1ff00", [0.9450980392156862, 1.0, 0.0]),
        "TTS_TEXT": ("#ffffff", [1.0, 1.0, 1.0]),
        "SOURCE_TEXT": ("#ffffff", [1.0, 1.0, 1.0]),
    }
    for track_name, (hex_color, rgb_color) in locked_text_colors.items():
        text_track = next((track for track in tracks if track.get("name") == track_name), None)
        if text_track is None:
            continue
        for segment in text_track.get("segments") or []:
            material = text_material_by_id.get(str(segment.get("material_id")))
            if material is None:
                continue
            material["text_color"] = hex_color
            try:
                payload = json.loads(str(material.get("content") or "{}"))
            except json.JSONDecodeError:
                continue
            for style in payload.get("styles") or []:
                solid = (((style.get("fill") or {}).get("content") or {}).get("solid"))
                if isinstance(solid, dict):
                    solid["color"] = list(rgb_color)
                    solid["alpha"] = 1.0
            material["content"] = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    full_duration_tracks = ["LOGO"] if template_version == "top5isu_v1" else ["FRAME", "LOGO"]
    for track_name in full_duration_tracks:
        full_track = next(track for track in tracks if track.get("name") == track_name)
        segments = full_track.get("segments") or []
        if not segments:
            raise BuildFail(f"{track_name} segment missing")
        segments[0]["source_timerange"] = {"start": 0, "duration": duration_us}
        segments[0]["target_timerange"] = {"start": 0, "duration": duration_us}
        material = videos_by_id.get(str(segments[0].get("material_id")))
        if material is not None:
            material["duration"] = duration_us

    if template_version == "top5isu_v2_top55":
        # CapCut UI: Scale 50%, X 0, Y 1500.  Draft JSON stores Y as 1500/1920.
        logo_track = next(track for track in tracks if track.get("name") == "LOGO")
        logo_segment = (logo_track.get("segments") or [{}])[0]
        logo_clip = logo_segment.setdefault("clip", {})
        logo_clip["scale"] = {"x": 0.5, "y": 0.5}
        logo_clip.setdefault("transform", {}).update({"x": 0.0, "y": 0.78125})

    content = replace_placeholders(content, str(final_draft_path))
    for filename in ("draft_content.json", "draft_info.json", "template-2.tmp"):
        write_object(destination / filename, content)
    timelines = destination / "Timelines"
    if timelines.exists():
        shutil.rmtree(timelines)
    timeline_root = timelines / timeline_id
    write_object(timeline_root / "draft_content.json", content)
    write_object(timeline_root / "template-2.tmp", content)

    subdrafts = destination / "subdraft"
    if subdrafts.exists():
        for subdraft_root in subdrafts.iterdir():
            if not subdraft_root.is_dir():
                continue
            for filename in ("draft_content.json", "template-2.tmp"):
                mirror = subdraft_root / filename
                if mirror.exists():
                    write_object(mirror, content)

    meta = sanitize_inherited_cloud_identity(read_object(destination / "draft_meta_info.json"))
    meta.update(
        {
            "draft_id": project_id,
            "draft_name": project_name,
            "draft_fold_path": str(final_draft_path),
            "draft_root_path": str(final_draft_path.parent),
            "draft_cover": str(final_draft_path / "draft_cover.jpg"),
            "tm_draft_create": now_us,
            "tm_draft_modified": now_us,
            "tm_duration": duration_us,
            "cloud_draft_sync": False,
            "draft_timeline_materials_size_": sum(
                path.stat().st_size for path in media_dir.iterdir() if path.is_file()
            ),
        }
    )
    meta["draft_materials"] = [
        {
            "type": 0,
            "value": [
                {
                    "id": new_id(),
                    "metetype": visual_specs[index]["type"],
                    "type": 0,
                    "duration": image_boundaries_us[index + 1] - image_boundaries_us[index],
                    "width": image_sizes[index][0],
                    "height": image_sizes[index][1],
                    "file_Path": str(final_draft_path / "Resources" / "media" / visual_specs[index]["filename"]),
                    "extra_info": visual_specs[index]["filename"],
                }
                for index in range(len(image_paths))
            ],
        },
        {
            "type": 1,
            "value": [
                {
                    "id": new_id(),
                    "metetype": "audio",
                    "type": 1,
                    "duration": duration_us,
                    "width": 0,
                    "height": 0,
                    "file_Path": str(final_draft_path / "Resources" / "media" / "narration_final.wav"),
                    "extra_info": "narration_final.wav",
                }
            ] + (
                [
                    {
                        "id": new_id(),
                        "metetype": "audio",
                        "type": 1,
                        "duration": duration_us,
                        "width": 0,
                        "height": 0,
                        "file_Path": str(final_draft_path / "Resources" / "media" / "bgm_final.wav"),
                        "extra_info": "bgm_final.wav",
                    }
                ]
                if bgm_path is not None
                else []
            ),
        },
    ]
    meta = replace_placeholders(meta, str(final_draft_path))
    write_object(destination / "draft_meta_info.json", meta)

    placeholder_pattern = re.compile(r"##_draftpath_placeholder_[^#]+_##")
    for control_file in destination.rglob("*"):
        if not control_file.is_file() or control_file.suffix.lower() not in {".json", ".tmp", ".md", ".txt"}:
            continue
        try:
            text = control_file.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        replaced = placeholder_pattern.sub(str(final_draft_path), text)
        if replaced != text:
            control_file.write_text(replaced, encoding="utf-8")

    if old_tts_material_id and any(str(item.get("id")) == old_tts_material_id for item in materials["texts"]):
        raise BuildFail("sample TTS text material remains active")
    serialized = json.dumps(content, ensure_ascii=False)
    if "##_draftpath_placeholder_" in serialized:
        raise BuildFail("draft path placeholder remains")
    for control_file in destination.rglob("*"):
        if control_file.is_file() and control_file.suffix.lower() in {".json", ".tmp", ".md", ".txt"}:
            try:
                if "##_draftpath_placeholder_" in control_file.read_text(encoding="utf-8-sig"):
                    raise BuildFail(f"draft path placeholder remains: {control_file.relative_to(destination)}")
            except UnicodeDecodeError:
                continue
    if any(media_dir.glob("leehaneul_*.png")) or any(media_dir.glob("top55_sample_image.*")):
        raise BuildFail("sample image remains in media folder")

    return {
        "status": "PASS_CAPCUT_STAGING_BUILD",
        "project_name": project_name,
        "project_path": str(destination),
        "final_draft_path": str(final_draft_path),
        "duration_us": duration_us,
        "template_profile": template_version,
        "image_effect_segments": len(image_segments),
        "subtitle_segments": len(new_subtitle_segments),
        "high_impact_indices": list(high_impact_indices or []),
        "source_audio_track": source_audio_track is not None,
        "bgm_audio_track": bgm_audio_track is not None,
        "bgm_volume": float(bgm_volume) if bgm_audio_track is not None else None,
        "fresh_project_id": True,
        "fresh_timeline_id": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template_root")
    parser.add_argument("destination")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--bgm", default="")
    parser.add_argument("--bgm-volume", type=float, default=0.16)
    parser.add_argument("--subtitles-json", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--boundaries-sec", required=True)
    parser.add_argument("--final-draft-path", default="")
    parser.add_argument("--high-impact-indices", default="")
    parser.add_argument("--source-label", default="출처")
    args = parser.parse_args()
    try:
        audio = Path(args.audio)
        duration_us = media_duration_us(audio)
        boundaries = [int(round(float(value.strip()) * 1_000_000)) for value in args.boundaries_sec.split(",")]
        if boundaries:
            boundaries[-1] = duration_us
        image_dir = Path(args.image_dir)
        images = collect_visual_media(image_dir)
        high_impact_indices = [
            int(value.strip())
            for value in args.high_impact_indices.split(",")
            if value.strip()
        ] or None
        subtitles = read_object(Path(args.subtitles_json))
        result = build_project(
            Path(args.template_root),
            Path(args.destination),
            args.project_name,
            images,
            audio,
            subtitles,
            args.title.replace("\\n", "\n"),
            duration_us,
            boundaries,
            Path(args.final_draft_path) if args.final_draft_path else None,
            bgm_path=Path(args.bgm) if args.bgm else None,
            bgm_volume=args.bgm_volume,
            high_impact_indices=high_impact_indices,
            source_label=args.source_label,
        )
    except (BuildFail, OSError, json.JSONDecodeError, ValueError, subprocess.CalledProcessError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
