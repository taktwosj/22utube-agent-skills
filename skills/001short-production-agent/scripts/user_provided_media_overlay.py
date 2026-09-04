from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from capcut_model import iter_materials
from track_template_matrix import CANONICAL_TRACKS


SCHEMA_VERSION = "001short-user-provided-media-overlay-v1"
LAYOUT_SCHEMA_VERSION = "001short-user-provided-media-overlay-layout-v1"
MANUAL_STATUS = "WAIT_USER_CAPCUT_AUDIO_ADJUSTMENT"
BASE_TRACK_COUNT = len(CANONICAL_TRACKS)
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_TRACK_INDEX = {role: index for index, role in enumerate(CANONICAL_TRACKS)}
_FALLBACK_RENDER_INDEX = {
    "VIDEO": 0,
    "SCREEN_EFFECT": 11000,
    "SCREEN_WHITE": 1,
    "SOURCE_CREDIT": 14003,
    "STATE_GLITCH": 14003,
    "STATE_LASER": 14003,
    "A10_TEXT_WHITE": 14003,
    "A10_TEXT_YELLOW": 14003,
    "A9_TEXT": 14002,
    "T2": 14001,
    "T1": 14000,
}


def visual_overlay_render_indices(tracks: list[dict], count: int) -> list[int] | None:
    """Place visual extensions above screen media/effects and below every text lane."""
    if count <= 0:
        return []
    if len(tracks) < BASE_TRACK_COUNT:
        return None

    def render_index(role: str) -> int | None:
        track = tracks[_TRACK_INDEX[role]]
        segments = track.get("segments") if isinstance(track, dict) else None
        if isinstance(segments, list) and segments and isinstance(segments[0], dict):
            value = segments[0].get("render_index")
            if isinstance(value, int) and not isinstance(value, bool):
                return value
        return _FALLBACK_RENDER_INDEX.get(role)

    base = [render_index(role) for role in ("VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE")]
    text = [
        render_index(role) for role in CANONICAL_TRACKS[:11]
        if role not in {"VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE"}
    ]
    if any(value is None for value in base + text):
        return None
    first = max(base) + 1
    if first + count - 1 >= min(text):
        return None
    return list(range(first, first + count))


def build_track_layout_extension(items: list[dict]) -> dict:
    """Freeze the declared tracks added after the canonical 15-track base."""
    fields = (
        "overlay_id", "media_kind", "track_index", "segment_id", "role",
        "source_sha256", "source_range_us", "target_range_us", "dimensions",
    )
    return {
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "base_track_count": BASE_TRACK_COUNT,
        "items": [
            {field: item[field] for field in fields}
            for item in items
        ],
    }


def declared_track_layout_extension(value: object) -> tuple[list[dict], list[dict]]:
    if value is None:
        return [], []
    if not isinstance(value, dict):
        return [], [_error("USER_MEDIA_OVERLAY_LAYOUT_INVALID")]
    items = value.get("items")
    if (
        value.get("schema_version") != LAYOUT_SCHEMA_VERSION
        or value.get("base_track_count") != BASE_TRACK_COUNT
        or not isinstance(items, list)
    ):
        return [], [_error("USER_MEDIA_OVERLAY_LAYOUT_INVALID")]
    expected_indices = list(range(BASE_TRACK_COUNT, BASE_TRACK_COUNT + len(items)))
    if [row.get("track_index") for row in items if isinstance(row, dict)] != expected_indices:
        return [], [_error("USER_MEDIA_OVERLAY_LAYOUT_INVALID")]
    return items, []


def _error(code: str, **detail: Any) -> dict:
    return {"code": code, **detail}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _range(value: object, *, allow_zero: bool = False) -> tuple[int, int] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    start, end = value
    if any(not isinstance(item, int) or isinstance(item, bool) for item in (start, end)):
        return None
    if start < 0 or end < start or (not allow_zero and end == start):
        return None
    return start, end


def _probe(path: Path) -> dict | None:
    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=codec_type,width,height", "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode:
        return None
    try:
        payload = json.loads(completed.stdout)
        streams = payload.get("streams", [])
        duration = float(payload.get("format", {}).get("duration", 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(streams, list):
        return None
    stream_types = {
        row.get("codec_type") for row in streams
        if isinstance(row, dict) and isinstance(row.get("codec_type"), str)
    }
    visual = next(
        (row for row in streams if isinstance(row, dict) and row.get("codec_type") == "video"),
        None,
    )
    width = visual.get("width") if isinstance(visual, dict) else 0
    height = visual.get("height") if isinstance(visual, dict) else 0
    if not isinstance(width, int) or not isinstance(height, int):
        return None
    return {
        "stream_types": stream_types,
        "duration_us": round(duration * 1_000_000) if duration > 0 else 0,
        "width": width,
        "height": height,
    }


def _image_decodes(path: Path) -> bool:
    try:
        completed = subprocess.run(
            [
                "ffmpeg", "-v", "error", "-xerror", "-err_detect", "explode",
                "-i", str(path), "-map", "0:v:0", "-frames:v", "1",
                "-f", "null", "-",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _normalized_item(item: object, *, ordinal: int, timeline_duration_us: int) -> tuple[dict | None, list[dict]]:
    errors: list[dict] = []
    if not isinstance(item, dict):
        return None, [_error("USER_MEDIA_OVERLAY_ITEM_INVALID", index=ordinal)]
    overlay_id = item.get("overlay_id")
    kind = item.get("media_kind")
    if not isinstance(overlay_id, str) or not overlay_id.strip() or kind not in {"audio", "image", "video"}:
        return None, [_error("USER_MEDIA_OVERLAY_ITEM_INVALID", index=ordinal)]
    track_index = item.get("track_index")
    if track_index != BASE_TRACK_COUNT + ordinal:
        errors.append(_error("USER_MEDIA_OVERLAY_TRACK_INDEX_INVALID", overlay_id=overlay_id))
    source_audio_underlay_required = item.get("source_audio_underlay_required", True)
    if not isinstance(source_audio_underlay_required, bool):
        errors.append(_error("USER_MEDIA_OVERLAY_ITEM_INVALID", index=ordinal))
    raw_path = item.get("source_path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, errors + [_error("USER_MEDIA_OVERLAY_PATH_INVALID", overlay_id=overlay_id)]
    path = Path(raw_path).resolve()
    declared_sha = item.get("source_sha256")
    if (
        not path.is_file()
        or path.is_symlink()
        or not isinstance(declared_sha, str)
        or not _SHA256.fullmatch(declared_sha)
        or _sha(path).lower() != declared_sha.lower()
    ):
        return None, errors + [_error("USER_MEDIA_OVERLAY_PATH_OR_SHA_INVALID", overlay_id=overlay_id)]
    probe = _probe(path)
    if probe is None:
        return None, errors + [_error("USER_MEDIA_OVERLAY_MEDIA_PROBE_INVALID", overlay_id=overlay_id)]
    target_range = _range(item.get("target_range_us"))
    if target_range is None or target_range[1] > timeline_duration_us:
        errors.append(_error("USER_MEDIA_OVERLAY_PLACEMENT_INVALID", overlay_id=overlay_id))
    dimensions = item.get("dimensions")
    if not isinstance(dimensions, dict):
        errors.append(_error("USER_MEDIA_OVERLAY_DIMENSIONS_INVALID", overlay_id=overlay_id))
        dimensions = {}
    declared_width, declared_height = dimensions.get("width"), dimensions.get("height")
    measured_duration = item.get("measured_duration_us")
    if not isinstance(measured_duration, int) or isinstance(measured_duration, bool) or measured_duration < 0:
        errors.append(_error("USER_MEDIA_OVERLAY_DURATION_INVALID", overlay_id=overlay_id))
    if kind == "audio":
        source_range = _range(item.get("source_range_us"))
        if (
            "audio" not in probe["stream_types"]
            or (declared_width, declared_height) != (0, 0)
            or not isinstance(measured_duration, int)
            or abs(probe["duration_us"] - measured_duration) > 50_000
            or source_range is None
            or source_range != (0, measured_duration)
            or target_range is None
            or target_range[1] - target_range[0] != measured_duration
        ):
            errors.append(_error("USER_MEDIA_OVERLAY_DURATION_OR_STREAM_INVALID", overlay_id=overlay_id))
        role = "USER_PROVIDED_AUDIO"
    elif kind == "image":
        if (
            "video" not in probe["stream_types"]
            or probe["width"] <= 0
            or probe["height"] <= 0
            or not _image_decodes(path)
            or (declared_width, declared_height) != (probe["width"], probe["height"])
            or measured_duration != 0
            or "source_range_us" in item
        ):
            errors.append(_error("USER_MEDIA_OVERLAY_DIMENSIONS_INVALID", overlay_id=overlay_id))
        role = "USER_PROVIDED_VISUAL"
    else:
        source_range = _range(item.get("source_range_us"))
        if (
            "video" not in probe["stream_types"]
            or (declared_width, declared_height) != (probe["width"], probe["height"])
            or not isinstance(measured_duration, int)
            or abs(probe["duration_us"] - measured_duration) > 50_000
            or source_range is None
            or source_range[1] > measured_duration
            or target_range is None
            or target_range[1] - target_range[0] != source_range[1] - source_range[0]
        ):
            errors.append(_error("USER_MEDIA_OVERLAY_DURATION_OR_STREAM_INVALID", overlay_id=overlay_id))
        role = "USER_PROVIDED_VISUAL"
    if errors:
        return None, errors
    return {
        "overlay_id": overlay_id,
        "media_kind": kind,
        "track_index": track_index,
        "source_path": str(path),
        "source_sha256": declared_sha.lower(),
        "measured_duration_us": measured_duration,
        "dimensions": {"width": declared_width, "height": declared_height},
        "source_range_us": item.get("source_range_us"),
        "target_range_us": list(target_range),
        "source_audio_underlay_required": source_audio_underlay_required,
        "role": role,
        "segment_id": f"USER_MEDIA::{overlay_id}",
    }, []


def validate_bundle(bundle: object, *, episode_id: str, timeline_duration_us: int) -> dict:
    if bundle is None:
        return {"status": "PASS", "items": [], "manual_status": None, "errors": []}
    if not isinstance(bundle, dict):
        return {"status": "FAIL", "items": [], "errors": [_error("USER_MEDIA_OVERLAY_BUNDLE_INVALID")]}
    authority = bundle.get("user_authority")
    errors: list[dict] = []
    if bundle.get("schema_version") != SCHEMA_VERSION or bundle.get("episode_id") != episode_id:
        errors.append(_error("USER_MEDIA_OVERLAY_BUNDLE_INVALID"))
    if bundle.get("status") != MANUAL_STATUS:
        errors.append(_error("USER_MEDIA_OVERLAY_STATUS_INVALID"))
    if (
        not isinstance(authority, dict)
        or not isinstance(authority.get("evidence"), str)
        or not authority["evidence"].strip()
        or not isinstance(authority.get("exact_text"), str)
        or not authority["exact_text"].strip()
    ):
        errors.append(_error("USER_MEDIA_OVERLAY_AUTHORITY_INVALID"))
    rows = bundle.get("items")
    if not isinstance(rows, list) or not rows:
        errors.append(_error("USER_MEDIA_OVERLAY_ITEMS_REQUIRED"))
        rows = []
    normalized: list[dict] = []
    ids: set[str] = set()
    for ordinal, row in enumerate(rows):
        item, item_errors = _normalized_item(row, ordinal=ordinal, timeline_duration_us=timeline_duration_us)
        errors.extend(item_errors)
        if item is not None:
            if item["overlay_id"] in ids:
                errors.append(_error("USER_MEDIA_OVERLAY_DUPLICATE_ID", overlay_id=item["overlay_id"]))
            ids.add(item["overlay_id"])
            normalized.append(item)
    return {
        "status": "PASS" if not errors else "FAIL",
        "items": normalized,
        "manual_status": MANUAL_STATUS if normalized else None,
        "errors": errors,
    }


def validate_a10_overlap_policy(source_audio: object, declared_items: list[dict]) -> list[dict]:
    """Keep source A10 audible beneath explicitly manual user narration."""
    audio_ranges = [
        item["target_range_us"] for item in declared_items
        if (
            item.get("media_kind") == "audio"
            and item.get("source_audio_underlay_required", True)
            and isinstance(item.get("target_range_us"), list)
        )
    ]
    if not audio_ranges or not isinstance(source_audio, list):
        return []
    errors: list[dict] = []
    for row in source_audio:
        if not isinstance(row, dict):
            continue
        target = _range(row.get("target_range_us"))
        if target is None:
            continue
        if any(target[0] < overlay_end and overlay_start < target[1] for overlay_start, overlay_end in audio_ranges):
            if row.get("mode") != "on":
                errors.append(_error(
                    "USER_MEDIA_OVERLAY_A10_ON_REQUIRED", clip_id=row.get("clip_id"),
                ))
    return errors


def validate_project_tracks(
    tracks: object,
    materials: object,
    *,
    project_root: Path,
    declared_items: list[dict],
) -> dict:
    if not isinstance(tracks, list) or len(tracks) < BASE_TRACK_COUNT:
        return {"status": "FAIL", "errors": [_error("USER_MEDIA_OVERLAY_BASE_TRACKS_INVALID")]}
    expected_count = BASE_TRACK_COUNT + len(declared_items)
    if len(tracks) != expected_count:
        code = "USER_MEDIA_OVERLAY_TRACK_UNBOUND" if len(tracks) > expected_count else "USER_MEDIA_OVERLAY_TRACK_COUNT_MISMATCH"
        return {"status": "FAIL", "errors": [_error(code, observed=len(tracks), expected=expected_count)]}
    material_map = {
        material["id"]: material
        for material in iter_materials(materials)
        if isinstance(material.get("id"), str)
    }
    visual_items = [item for item in declared_items if item.get("media_kind") != "audio"]
    visual_render_indices = visual_overlay_render_indices(tracks, len(visual_items))
    if visual_render_indices is None:
        return {"status": "FAIL", "errors": [_error("USER_VISUAL_OVERLAY_RENDER_ORDER_INVALID")]}
    visual_ordinal = 0
    errors: list[dict] = []
    for ordinal, expected in enumerate(declared_items):
        index = BASE_TRACK_COUNT + ordinal
        track = tracks[index]
        segments = track.get("segments") if isinstance(track, dict) else None
        if not isinstance(segments, list) or len(segments) != 1:
            errors.append(_error("USER_MEDIA_OVERLAY_TRACK_UNBOUND", track_index=index))
            continue
        segment = segments[0]
        expected_range = expected["target_range_us"]
        timerange = segment.get("target_timerange") if isinstance(segment, dict) else None
        expected_source_range = expected.get("source_range_us")
        source_timerange = segment.get("source_timerange") if isinstance(segment, dict) else None
        source_range_matches = (
            source_timerange is None
            if expected_source_range is None
            else isinstance(source_timerange, dict)
            and source_timerange.get("start") == expected_source_range[0]
            and source_timerange.get("duration") == expected_source_range[1] - expected_source_range[0]
        )
        if (
            not isinstance(segment, dict)
            or segment.get("id") != expected["segment_id"]
            or segment.get("role") != expected["role"]
            or not isinstance(timerange, dict)
            or timerange.get("start") != expected_range[0]
            or timerange.get("duration") != expected_range[1] - expected_range[0]
            or not source_range_matches
            or (
                expected["media_kind"] != "audio"
                and segment.get("render_index") != visual_render_indices[visual_ordinal]
            )
        ):
            errors.append(_error("USER_MEDIA_OVERLAY_TRACK_UNBOUND", track_index=index))
            if expected["media_kind"] != "audio":
                visual_ordinal += 1
            continue
        if expected["media_kind"] != "audio":
            visual_ordinal += 1
        material = material_map.get(segment.get("material_id"))
        if not isinstance(material, dict):
            errors.append(_error("USER_MEDIA_OVERLAY_MATERIAL_UNBOUND", overlay_id=expected["overlay_id"]))
            continue
        expected_types = {"audio", "music", "extract_music"} if expected["media_kind"] == "audio" else {"video"}
        raw_path = material.get("path") or material.get("media_path")
        if not isinstance(raw_path, str) or "Resources/" not in raw_path.replace("\\", "/"):
            errors.append(_error("USER_MEDIA_OVERLAY_MATERIAL_UNBOUND", overlay_id=expected["overlay_id"]))
            continue
        normalized = raw_path.replace("\\", "/")
        rel = normalized[normalized.index("Resources/"):]
        local = (Path(project_root).resolve() / rel).resolve()
        try:
            local.relative_to(Path(project_root).resolve())
        except ValueError:
            errors.append(_error("USER_MEDIA_OVERLAY_MATERIAL_UNBOUND", overlay_id=expected["overlay_id"]))
            continue
        if expected["media_kind"] != "audio" and local.is_file():
            actual_visual = _probe(local)
            if (
                actual_visual is None
                or "video" not in actual_visual["stream_types"]
                or (actual_visual["width"], actual_visual["height"])
                != (expected["dimensions"]["width"], expected["dimensions"]["height"])
            ):
                errors.append(_error(
                    "USER_MEDIA_OVERLAY_PROJECT_DIMENSIONS_INVALID",
                    overlay_id=expected["overlay_id"],
                ))
        if (
            material.get("type") not in expected_types
            or not local.is_file()
            or _sha(local).lower() != expected["source_sha256"].lower()
            or segment.get("volume") != (1.0 if expected["media_kind"] == "audio" else 0.0)
        ):
            errors.append(_error("USER_MEDIA_OVERLAY_MATERIAL_UNBOUND", overlay_id=expected["overlay_id"]))
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}
