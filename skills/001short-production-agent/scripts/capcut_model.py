from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Iterator

from capcut_io import iter_timeline_json, load_json_file


class ProjectError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


class ProjectModel:
    def __init__(
        self,
        path: Path,
        content: dict,
        meta: dict,
        template: dict,
        timeline_project: dict,
        timeline_mirror: dict,
        timeline_json: dict[Path, Any],
    ) -> None:
        self.path = path
        self.content = content
        self.meta = meta
        self.template = template
        self.timeline_project = timeline_project
        self.timeline_mirror = timeline_mirror
        self.timeline_json = timeline_json

    @property
    def tracks(self) -> list[dict]:
        return self.content["tracks"]

    @property
    def materials(self) -> Any:
        return self.content["materials"]


def _required(path: Path) -> Any:
    try:
        return load_json_file(path, required=True)
    except (OSError, ValueError, TypeError) as exc:
        raise ProjectError("REQUIRED_JSON_INVALID", f"{path}: {exc}") from exc


def load_project(project_path: Path) -> ProjectModel:
    project_path = Path(project_path).resolve()
    if not project_path.is_dir():
        raise ProjectError("PROJECT_PATH_MISSING", str(project_path))
    content = _required(project_path / "draft_content.json")
    meta = _required(project_path / "draft_meta_info.json")
    timeline_project_path = project_path / "Timelines" / "project.json"
    timeline_project = _required(timeline_project_path)
    template = timeline_project
    if not all(isinstance(value, dict) for value in (content, meta, template, timeline_project)):
        raise ProjectError("PROJECT_STRUCTURE_INVALID", "required roots must be objects")
    if not isinstance(content.get("tracks"), list) or not isinstance(content.get("materials"), (dict, list)):
        raise ProjectError("PROJECT_STRUCTURE_INVALID", "tracks/materials malformed")
    timeline_id = content.get("main_timeline_id") or content.get("id")
    if not isinstance(timeline_id, str) or not timeline_id:
        raise ProjectError("PROJECT_STRUCTURE_INVALID", "main timeline ID missing")
    mirror_path = project_path / "Timelines" / timeline_id / "draft_content.json"
    timeline_mirror = _required(mirror_path)
    if not isinstance(timeline_mirror, dict):
        raise ProjectError("PROJECT_STRUCTURE_INVALID", "timeline mirror must be object")
    timeline_json = {path: payload for path, payload in iter_timeline_json(project_path)}
    timeline_json[timeline_project_path] = timeline_project
    timeline_json[mirror_path] = timeline_mirror
    return ProjectModel(
        project_path,
        content,
        meta,
        template,
        timeline_project,
        timeline_mirror,
        timeline_json,
    )


PROTECTED_FIELDS = (
    "track_id",
    "layer_index",
    "z_order",
    "transform",
    "scale",
    "rotation",
    "crop",
    "mask",
    "opacity",
    "blend",
    "text_style",
    "effects",
    "animations",
    "transition",
    "extra_material_refs",
)


def _protected_segment(segment: dict, actual_track_id: str) -> dict:
    clip = segment.get("clip") if isinstance(segment.get("clip"), dict) else {}
    return {
        "id": segment.get("id"),
        "track_id": segment.get("track_id", actual_track_id),
        "layer_index": segment.get("layer_index"),
        "z_order": segment.get("z_order"),
        "transform": copy.deepcopy(clip.get("transform")),
        "scale": copy.deepcopy(clip.get("scale")),
        "rotation": clip.get("rotation"),
        "crop": copy.deepcopy(clip.get("crop")),
        "mask": copy.deepcopy(clip.get("mask")),
        "opacity": clip.get("opacity", clip.get("global_alpha")),
        "blend": clip.get("blend"),
        "text_style": copy.deepcopy(clip.get("text_style")),
        "effects": copy.deepcopy(segment.get("effects")),
        "animations": copy.deepcopy(segment.get("animations")),
        "transition": copy.deepcopy(segment.get("transition")),
        "extra_material_refs": copy.deepcopy(segment.get("extra_material_refs")),
    }


def capture_structure(model: ProjectModel) -> dict:
    tracks: list[dict] = []
    for index, track in enumerate(model.tracks):
        track_id = track.get("id")
        segments = track.get("segments") if isinstance(track.get("segments"), list) else []
        tracks.append(
            {
                "id": track_id,
                "index": index,
                "type": track.get("type"),
                "segment_order": [segment.get("id") for segment in segments],
                "segments": [_protected_segment(segment, track_id) for segment in segments],
            }
        )
    return {
        "schema_version": "001short-structure-snapshot-v2",
        "track_order": [track["id"] for track in tracks],
        "tracks": tracks,
    }


def is_full_content_timeline_mirror(payload: object, path: Path | None = None) -> bool:
    if path is not None and Path(path).name.casefold() != "draft_content.json":
        return False
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("tracks"), list)
        and isinstance(payload.get("materials"), (dict, list))
    )


def capture_structure_from_content(content: dict) -> dict:
    tracks: list[dict] = []
    raw_tracks = content.get("tracks") if isinstance(content.get("tracks"), list) else []
    for index, track in enumerate(raw_tracks):
        if not isinstance(track, dict):
            continue
        track_id = track.get("id")
        segments = track.get("segments") if isinstance(track.get("segments"), list) else []
        tracks.append(
            {
                "id": track_id,
                "index": index,
                "type": track.get("type"),
                "segment_order": [segment.get("id") for segment in segments],
                "segments": [_protected_segment(segment, track_id) for segment in segments],
            }
        )
    return {
        "schema_version": "001short-structure-snapshot-v2",
        "track_order": [track["id"] for track in tracks],
        "tracks": tracks,
    }


FIELD_CODES = {
    "track_id": "SEGMENT_TRACK_CHANGED",
    "layer_index": "LAYER_INDEX_CHANGED",
    "z_order": "Z_ORDER_CHANGED",
    "transform": "TRANSFORM_CHANGED",
    "scale": "SCALE_CHANGED",
    "rotation": "ROTATION_CHANGED",
    "crop": "CROP_CHANGED",
    "mask": "MASK_CHANGED",
    "opacity": "OPACITY_CHANGED",
    "blend": "BLEND_CHANGED",
    "text_style": "TEXT_STYLE_CHANGED",
    "effects": "EFFECT_BINDING_CHANGED",
    "animations": "ANIMATION_BINDING_CHANGED",
    "transition": "TRANSITION_BINDING_CHANGED",
    "extra_material_refs": "EXTRA_MATERIAL_REF_CHANGED",
}


def validate_structure(model: ProjectModel, snapshot: dict) -> list[dict]:
    actual = capture_structure(model)
    errors: list[dict] = []
    if len(actual["tracks"]) != len(snapshot.get("tracks", [])):
        errors.append({"code": "TRACK_COUNT_CHANGED"})
    if actual["track_order"] != snapshot.get("track_order"):
        errors.append({"code": "TRACK_ORDER_CHANGED"})
    expected_tracks = {row.get("id"): row for row in snapshot.get("tracks", []) if isinstance(row, dict)}
    actual_tracks = {row.get("id"): row for row in actual["tracks"]}
    expected_segment_track: dict[str, str] = {}
    actual_segment_track: dict[str, str] = {}
    for track_id, row in expected_tracks.items():
        for segment_id in row.get("segment_order", []):
            expected_segment_track[segment_id] = track_id
    for track_id, row in actual_tracks.items():
        for segment_id in row.get("segment_order", []):
            actual_segment_track[segment_id] = track_id
    for segment_id in sorted(set(expected_segment_track) & set(actual_segment_track)):
        if expected_segment_track[segment_id] != actual_segment_track[segment_id]:
            errors.append({"code": "SEGMENT_TRACK_CHANGED", "segment_id": segment_id})
    for track_id in sorted(set(expected_tracks) & set(actual_tracks)):
        expected_track = expected_tracks[track_id]
        actual_track = actual_tracks[track_id]
        if expected_track.get("segment_order") != actual_track.get("segment_order"):
            errors.append({"code": "SEGMENT_ORDER_CHANGED", "track_id": track_id})
        expected_segments = {
            row.get("id"): row for row in expected_track.get("segments", []) if isinstance(row, dict)
        }
        actual_segments = {
            row.get("id"): row for row in actual_track.get("segments", []) if isinstance(row, dict)
        }
        if set(expected_segments) != set(actual_segments):
            errors.append({"code": "SEGMENT_SET_CHANGED", "track_id": track_id})
        for segment_id in sorted(set(expected_segments) & set(actual_segments)):
            for field, code in FIELD_CODES.items():
                if expected_segments[segment_id].get(field) != actual_segments[segment_id].get(field):
                    errors.append({"code": code, "segment_id": segment_id, "field": field})
    unique: list[dict] = []
    seen: set[tuple] = set()
    for row in errors:
        marker = tuple(sorted(row.items()))
        if marker not in seen:
            seen.add(marker)
            unique.append(row)
    return unique


def iter_materials(value: Any) -> Iterator[dict]:
    if isinstance(value, list):
        for item in value:
            yield from iter_materials(item)
    elif isinstance(value, dict):
        if isinstance(value.get("id"), str) and any(
            key in value for key in ("type", "role", "path", "media_path", "content", "text")
        ):
            yield value
            return
        for child in value.values():
            yield from iter_materials(child)


def _segments(model: ProjectModel) -> Iterator[dict]:
    for track in model.tracks:
        for segment in track.get("segments", []):
            if isinstance(segment, dict):
                yield segment


REFERENCE_CONTAINERS = {
    "effects",
    "effect",
    "animations",
    "animation",
    "transition",
    "transitions",
    "extra_material_refs",
    "extra_material_ids",
}


def _collect_material_id_field(value: Any) -> Iterator[str]:
    """Yield only semantically named material-id fields, recursing into every
    dict/list so that material references nested inside unknown containers
    (e.g. ``effects[].binding.material_id``, ``transition.binding.material_id``)
    are still found. A bare ``id`` is the definition identifier of a container
    entry (effect/animation instance) and is never a material reference, so it
    is deliberately ignored to avoid false orphans."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized == "material_id" or normalized.endswith("_material_id"):
                if isinstance(child, str) and child:
                    yield child
                elif isinstance(child, list):
                    for item in child:
                        if isinstance(item, str) and item:
                            yield item
            else:
                yield from _collect_material_id_field(child)
    elif isinstance(value, list):
        for child in value:
            yield from _collect_material_id_field(child)


def _binding_reference_ids(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        if value:
            yield value
        return
    if isinstance(value, list):
        for child in value:
            yield from _binding_reference_ids(child)
        return
    if not isinstance(value, dict):
        return
    for key, child in value.items():
        normalized = str(key).lower()
        if normalized == "material_id" or normalized.endswith("_material_id"):
            if isinstance(child, str) and child:
                yield child
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, str) and item:
                        yield item
        elif normalized in REFERENCE_CONTAINERS or "material_ref" in normalized:
            yield from _binding_reference_ids(child)


def collect_material_references(tracks: list[dict]) -> list[dict]:
    references: list[dict] = []
    for track in tracks:
        for segment in track.get("segments", []):
            if not isinstance(segment, dict):
                continue
            segment_id = segment.get("id")
            direct = segment.get("material_id")
            if isinstance(direct, str) and direct:
                references.append(
                    {"segment_id": segment_id, "field": "material_id", "material_id": direct}
                )
            for key, value in segment.items():
                normalized = str(key).lower()
                if normalized in REFERENCE_CONTAINERS or "material_ref" in normalized:
                    if normalized in {"extra_material_refs", "extra_material_ids"} or "material_ref" in normalized:
                        id_iter = _binding_reference_ids(value)
                    else:
                        id_iter = _collect_material_id_field(value)
                    for material_id in id_iter:
                        references.append(
                            {
                                "segment_id": segment_id,
                                "field": str(key),
                                "material_id": material_id,
                            }
                        )
    return references


def _iter_named_fields(value: Any, names: set[str], location: str = "$") -> Iterator[tuple[str, str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if str(key).lower() in names:
                yield child_location, str(key), child
            yield from _iter_named_fields(child, names, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_named_fields(child, names, f"{location}[{index}]")


def validate_materials(model: ProjectModel, project_path: Path) -> list[dict]:
    project_path = Path(project_path).resolve()
    materials = list(iter_materials(model.materials))
    errors: list[dict] = []
    ids: list[str] = [row.get("id") for row in materials]
    duplicates = sorted({material_id for material_id in ids if ids.count(material_id) > 1})
    for material_id in duplicates:
        errors.append({"code": "DUPLICATE_MATERIAL_ID", "material_id": material_id})
    material_ids = set(ids)
    referenced: set[str] = set()
    for reference in collect_material_references(model.tracks):
        material_id = reference["material_id"]
        if material_id not in material_ids:
            errors.append(
                {
                    "code": "ORPHAN_MATERIAL_REFERENCE",
                    "segment_id": reference.get("segment_id"),
                    "field": reference.get("field"),
                    "material_id": material_id,
                }
            )
        else:
            referenced.add(material_id)
    for material in materials:
        material_id = material.get("id")
        if not material.get("role") or not material.get("desc"):
            errors.append({"code": "MATERIAL_METADATA_MISSING", "material_id": material_id})
        for location, field, remote_id in _iter_named_fields(
            material, {"online_id", "request_id"}
        ):
            if remote_id:
                errors.append(
                    {
                        "code": "REMOTE_MATERIAL_ID",
                        "material_id": material_id,
                        "field": field,
                        "location": location,
                    }
                )
        for location, field, raw_path in _iter_named_fields(
            material, {"path", "media_path"}
        ):
            if not isinstance(raw_path, str) or not raw_path:
                continue
            normalized = raw_path.replace("\\", "/").lower()
            if any(token in normalized for token in ("previous_episode", "example_asset", "cache/onlinematerial")) or "://" in normalized:
                errors.append({"code": "STALE_MATERIAL_PATH", "material_id": material_id, "field": field, "location": location})
                continue
            portable = re.match(
                r"^##_draftpath_placeholder_[^#]+_##/(Resources/.+)$",
                raw_path.replace("\\", "/"),
            )
            candidate = project_path / Path(portable.group(1)) if portable else Path(raw_path)
            if not candidate.is_absolute():
                candidate = project_path / candidate
            candidate = candidate.resolve()
            try:
                candidate.relative_to(project_path)
            except ValueError:
                errors.append({"code": "MATERIAL_PATH_OUTSIDE_PROJECT", "material_id": material_id, "field": field, "location": location})
                continue
            if not candidate.is_file():
                errors.append({"code": "MATERIAL_FILE_MISSING", "material_id": material_id, "field": field, "location": location})
    media_root = project_path / "Resources" / "media"
    if media_root.is_dir():
        for path in media_root.rglob("*"):
            if not path.is_file():
                continue
            normalized = path.relative_to(project_path).as_posix().lower()
            if any(token in normalized for token in ("previous_episode", "example_asset", "onlinematerial")):
                errors.append({"code": "STALE_RESOURCE_FILE", "path": normalized})
    return errors
