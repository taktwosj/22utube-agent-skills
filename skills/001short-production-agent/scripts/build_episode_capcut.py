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
import uuid
import zipfile
from pathlib import Path
from typing import Any, Iterator


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import capcut_model
import capcut_materialization
import clone_and_sync
import apply_capcut_polish_profile
import validate_audio_caption
import validate_build_inputs
import validate_capcut_project
import validate_capcut_polish_profile
import validate_postbuild
import validate_prebuild
import validate_clean_visual
import validate_design_lock
from capcut_io import iter_timeline_json
from common import manifest_sha256, resolved_declared_path


ROLE_BY_TRACK = [
    "VIDEO", "SCREEN_EFFECT", "SCREEN_WHITE", "STATE", "A10_TEXT", "A9_TEXT",
    "T2", "T1", "A9", "A10", "A11", "A12",
]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _materials(value: Any) -> Iterator[dict]:
    yield from capcut_model.iter_materials(value)


def _ensure_media_tools() -> None:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return
    local = Path.home() / "AppData" / "Local"
    candidates = [local / "Pixeling"]
    if (local / "CapCut" / "Apps").is_dir():
        candidates.extend(sorted((local / "CapCut" / "Apps").glob("*"), reverse=True))
    ffmpeg_dir = next((path for path in candidates if (path / "ffmpeg.exe").is_file()), None)
    ffprobe_dir = next((path for path in candidates if (path / "ffprobe.exe").is_file()), None)
    if ffmpeg_dir is None or ffprobe_dir is None:
        raise RuntimeError("MEDIA_TOOL_MISSING:ffmpeg/ffprobe")
    os.environ["PATH"] = os.pathsep.join(
        [str(ffmpeg_dir), str(ffprobe_dir), os.environ.get("PATH", "")]
    )


def _extract_template(template_zip: Path, destination: Path) -> Path:
    if not template_zip.is_file():
        raise FileNotFoundError(template_zip)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(template_zip) as archive:
        archive.extractall(destination)
    candidates = [
        path.parent for path in destination.rglob("draft_content.json")
        if path.parent.parent.name != "Timelines" and "subdraft" not in path.parts
        and (path.parent / "draft_meta_info.json").is_file()
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"PINNED_TEMPLATE_ROOT_AMBIGUOUS:{len(candidates)}")
    white = candidates[0] / "Resources/media/transparent_center_white_1080x1920.png"
    if not white.is_file():
        raise RuntimeError("PINNED_WHITE_ASSET_MISSING")
    return candidates[0]


def _scrub_remote(value: Any) -> None:
    if isinstance(value, dict):
        value.pop("online_id", None)
        value.pop("request_id", None)
        for child in value.values():
            _scrub_remote(child)
    elif isinstance(value, list):
        for child in value:
            _scrub_remote(child)


def _draft_path_prefix(project: Path) -> str:
    content = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
    pattern = re.compile(r"^(##_draftpath_placeholder_[^#]+_##/)Resources/")
    for material in _materials(content.get("materials", {})):
        for key in ("path", "media_path"):
            value = material.get(key)
            match = pattern.match(value) if isinstance(value, str) else None
            if match:
                return match.group(1)
    raise RuntimeError("DRAFT_PATH_PLACEHOLDER_MISSING")


def _portable_resource_path(prefix: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if not normalized.startswith("Resources/"):
        raise RuntimeError(f"CAPCUT_RESOURCE_PATH_INVALID:{relative_path}")
    return prefix + normalized


def _normalize_paths(value: Any, project: Path, draft_prefix: str) -> None:
    if isinstance(value, dict):
        for key, child in list(value.items()):
            if key in {"path", "media_path"} and isinstance(child, str) and child:
                normalized = child.replace("\\", "/")
                marker = normalized.find("Resources/")
                candidate = normalized[marker:] if marker >= 0 else normalized
                local = project / Path(candidate)
                value[key] = (
                    _portable_resource_path(draft_prefix, candidate)
                    if not Path(candidate).is_absolute() and local.is_file()
                    else ""
                )
            else:
                _normalize_paths(child, project, draft_prefix)
    elif isinstance(value, list):
        for child in value:
            _normalize_paths(child, project, draft_prefix)


def _validate_config(config: dict) -> None:
    required = (
        "episode_id", "duration_us", "T1", "T2", "state_cues",
        "project_name", "template_zip", "episode_root", "work_root", "local_capcut_root",
        "source_identity_path", "approved_timeline_path", "design_handoff_path",
        "design_lock_evidence_path", "build_manifest_path",
    )
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"CONFIG_MISSING:{','.join(missing)}")
    mode = config.get("visual_asset_mode", "CLEAN_VISUAL_READY")
    if mode not in {"CLEAN_VISUAL_READY", "SOURCE_VIDEO_PROVISIONAL"}:
        raise ValueError("VISUAL_ASSET_MODE_INVALID")
    visual_key = "source_video" if mode == "SOURCE_VIDEO_PROVISIONAL" else "clean_video"
    if visual_key not in config:
        raise ValueError(f"CONFIG_MISSING:{visual_key}")
    if config.get("audio_role", "A10") not in {"A10", "A12"}:
        raise ValueError("AUDIO_ROLE_INVALID")
    duration = config["duration_us"]
    if not isinstance(duration, int) or duration <= 0:
        raise ValueError("DURATION_INVALID")
    cues = config["state_cues"]
    if not isinstance(cues, list) or not cues:
        raise ValueError("STATE_CUES_INVALID")
    previous_end = 0
    for cue in cues:
        if (
            not isinstance(cue, dict)
            or not isinstance(cue.get("text"), str)
            or not cue["text"].strip()
            or not isinstance(cue.get("start_us"), int)
            or not isinstance(cue.get("end_us"), int)
            or cue["start_us"] < previous_end
            or cue["end_us"] <= cue["start_us"]
            or cue["end_us"] > duration
            or ("cue_id" in cue and (not isinstance(cue["cue_id"], str) or not cue["cue_id"]))
        ):
            raise ValueError("STATE_CUES_INVALID")
        # STATE is a punchy, present-scene cue, not a sentence-sized edit outline.
        # Spaces and punctuation do not consume the eight Korean-character budget.
        meaningful = "".join(char for char in cue["text"] if char.isalnum())
        if len(meaningful) > 8:
            raise ValueError("STATE_CUE_TOO_LONG")
        previous_end = cue["end_us"]


def _visual_asset_path(config: dict) -> Path:
    key = "source_video" if config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL" else "clean_video"
    return Path(config[key]).resolve()


def _visual_asset_filename(config: dict) -> str:
    return "source_video.mp4" if config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL" else "clean_video.mp4"


def _episode_work_root(config: dict) -> Path:
    episode_id = str(config["episode_id"])
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", episode_id).strip("._-")[:48] or "episode"
    digest = hashlib.sha256(episode_id.encode("utf-8")).hexdigest()[:12]
    return Path(config["work_root"]).resolve() / f"{slug}-{digest}"


def _approved_rows(config: dict) -> list[dict]:
    timeline = json.loads(Path(config["approved_timeline_path"]).read_text(encoding="utf-8"))
    rows = sorted(timeline["segments"], key=lambda row: row["timeline_order"])
    if timeline.get("episode_id") != config["episode_id"]:
        raise RuntimeError("APPROVED_TIMELINE_EPISODE_MISMATCH")
    return rows


def _approved_id(config: dict, rows: list[dict], role: str, occurrence: int = 0) -> str:
    configured = config.get("segment_ids", {}).get(role)
    if isinstance(configured, str) and occurrence == 0:
        candidate = configured
    elif isinstance(configured, list) and occurrence < len(configured):
        candidate = configured[occurrence]
    else:
        matches = [row["segment_id"] for row in rows if row.get("role") == role]
        if occurrence >= len(matches):
            raise RuntimeError(f"APPROVED_SEGMENT_ROLE_MISSING:{role}:{occurrence}")
        candidate = matches[occurrence]
    if candidate not in {row["segment_id"] for row in rows if row.get("role") == role}:
        raise RuntimeError(f"APPROVED_SEGMENT_ID_MISMATCH:{role}:{candidate}")
    return candidate


def _material_parent(value: Any, material_id: str) -> list[dict] | None:
    if isinstance(value, list):
        if any(isinstance(row, dict) and row.get("id") == material_id for row in value):
            return value
        for child in value:
            found = _material_parent(child, material_id)
            if found is not None:
                return found
    elif isinstance(value, dict):
        for child in value.values():
            found = _material_parent(child, material_id)
            if found is not None:
                return found
    return None


def _documents(project: Path) -> Iterator[tuple[Path, dict]]:
    seen: set[Path] = set()
    root = project / "draft_content.json"
    payload = json.loads(root.read_text(encoding="utf-8"))
    seen.add(root.resolve())
    yield root, payload
    for path, payload in iter_timeline_json(project):
        if path.resolve() in seen:
            continue
        if isinstance(payload, dict) and isinstance(payload.get("tracks"), list):
            seen.add(path.resolve())
            yield path, payload


def _set_media(
    material: dict, *, media_type: str, portable_path: str, role: str, duration_us: int
) -> None:
    if media_type == "video":
        material["type"] = "video"
        material["media_path"] = ""
    elif material.get("type") not in {"music", "extract_music"}:
        material["type"] = "music"
    material["role"] = role
    material["desc"] = f"001short production {role}"
    material["path"] = portable_path
    material["duration"] = duration_us


def _populate_full_duration_audio(
    track: dict,
    template_segment: dict,
    material: dict,
    *,
    portable_path: str,
    duration_us: int,
    role: str,
    segment_id: str,
) -> None:
    _set_media(
        material,
        media_type="audio",
        portable_path=portable_path,
        role=role,
        duration_us=duration_us,
    )
    segment = copy.deepcopy(template_segment)
    segment["id"] = segment_id
    segment["role"] = role
    segment["target_timerange"] = {"start": 0, "duration": duration_us}
    segment["source_timerange"] = {"start": 0, "duration": duration_us}
    track["segments"] = [segment]


def _scrub_windows_cache_paths(value: object) -> int:
    changed = 0
    windows_path = re.compile(r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]")
    if isinstance(value, dict):
        for key, child in list(value.items()):
            if key in {"icon_url", "preview_cover_url"} and isinstance(child, str) and child.startswith(("http://", "https://")):
                value[key] = ""
                changed += 1
                continue
            if isinstance(child, str) and windows_path.search(child):
                if child.lstrip().startswith(("{", "[")):
                    try:
                        nested = json.loads(child)
                    except (TypeError, json.JSONDecodeError):
                        nested = None
                    if nested is not None:
                        nested_changed = _scrub_windows_cache_paths(nested)
                        value[key] = json.dumps(nested, ensure_ascii=False, separators=(",", ":"))
                        changed += max(1, nested_changed)
                        continue
                value[key] = ""
                changed += 1
                continue
            changed += _scrub_windows_cache_paths(child)
    elif isinstance(value, list):
        for index, child in enumerate(list(value)):
            if isinstance(child, str) and windows_path.search(child):
                value[index] = ""
                changed += 1
            else:
                changed += _scrub_windows_cache_paths(child)
    return changed


def _prepare_cloud_project(
    project: Path,
    *,
    project_name: str,
    capcut_root: Path,
    draft_id: str,
    duration_us: int,
) -> dict:
    project = Path(project).resolve()
    subdraft = project / "subdraft"
    if subdraft.is_dir():
        shutil.rmtree(subdraft)
    shutil.copy2(project / "draft_content.json", project / "draft_info.json")
    shutil.copy2(project / "draft_content.json", project / "template-2.tmp")
    for content in (project / "Timelines").glob("*/draft_content.json"):
        shutil.copy2(content, content.with_name("draft_info.json"))
        shutil.copy2(content, content.with_name("template-2.tmp"))
    changed = 0
    for path in sorted(project.rglob("*")):
        if not path.is_file() or not (path.suffix == ".json" or path.name in {"draft_info.json", "template-2.tmp"}):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        current = _scrub_windows_cache_paths(payload)
        if current:
            _write_json(path, payload)
            changed += current
    meta_path = project / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update({
        "draft_id": draft_id,
        "draft_name": project_name,
        "draft_fold_path": str(project),
        "draft_root_path": str(Path(capcut_root).resolve()),
        "tm_duration": duration_us,
        "tm_draft_cloud_entry_id": -1,
        "tm_draft_cloud_parent_entry_id": -1,
        "tm_draft_cloud_space_id": 0,
        "tm_draft_cloud_user_id": 0,
        "tm_draft_cloud_completed": False,
        "cloud_draft_sync": False,
    })
    _write_json(meta_path, meta)
    return {"windows_paths_scrubbed": changed, "draft_meta": meta}


def _register_capcut_project(project: Path, capcut_root: Path, backup_path: Path) -> None:
    root_path = Path(capcut_root).resolve() / "root_meta_info.json"
    shutil.copy2(root_path, backup_path)
    root = json.loads(root_path.read_text(encoding="utf-8"))
    meta = json.loads((Path(project) / "draft_meta_info.json").read_text(encoding="utf-8"))
    rows = root.setdefault("all_draft_store", [])
    rows[:] = [row for row in rows if row.get("draft_name") != meta["draft_name"] and row.get("draft_id") != meta["draft_id"]]
    row = copy.deepcopy(meta)
    row["draft_json_file"] = str(Path(project) / "draft_info.json")
    row["draft_cover"] = str(Path(project) / "draft_cover.jpg")
    row["draft_timeline_materials_size"] = sum(path.stat().st_size for path in Path(project).rglob("*") if path.is_file())
    rows.append(row)
    root["root_path"] = str(Path(capcut_root).resolve())
    _write_json(root_path, root)


def _set_text(material: dict, text: str, role: str) -> None:
    try:
        rich = json.loads(material["content"])
    except (KeyError, TypeError, json.JSONDecodeError):
        raise RuntimeError(f"CAPCUT_RICH_TEXT_TEMPLATE_INVALID:{role}") from None
    styles = rich.get("styles")
    if not isinstance(styles, list) or not styles:
        raise RuntimeError(f"CAPCUT_RICH_TEXT_TEMPLATE_INVALID:{role}")
    rich["text"] = text
    for style in styles:
        if not isinstance(style, dict):
            raise RuntimeError(f"CAPCUT_RICH_TEXT_TEMPLATE_INVALID:{role}")
        style["range"] = [0, len(text)]
    material["type"] = "text"
    material["role"] = role
    material["desc"] = f"001short production {role}"
    material["content"] = json.dumps(rich, ensure_ascii=False, separators=(",", ":"))
    material.pop("text", None)


def _material_text(material: dict) -> str | None:
    content = material.get("content")
    if isinstance(content, str) and content.strip():
        try:
            rich = json.loads(content)
        except json.JSONDecodeError:
            return content.strip()
        text = rich.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    text = material.get("text")
    return text.strip() if isinstance(text, str) and text.strip() else None


def _normalize_source(
    project: Path, config: dict, audio_source: Path, build_manifest: dict
) -> list[dict]:
    duration = config["duration_us"]
    approved = _approved_rows(config)
    approved_by_id = {row["segment_id"]: row for row in approved}
    media = project / "Resources" / "media"
    media.mkdir(parents=True, exist_ok=True)
    visual_asset = _visual_asset_path(config)
    visual_name = _visual_asset_filename(config)
    shutil.copy2(visual_asset, media / visual_name)
    audio_suffix = audio_source.suffix.lower() or ".wav"
    audio_name = f"source_audio{audio_suffix}"
    shutil.copy2(audio_source, media / audio_name)
    draft_prefix = _draft_path_prefix(project)

    root_rows: list[dict] = []
    for document_index, (path, payload) in enumerate(_documents(project)):
        tracks = payload["tracks"]
        if len(tracks) < 12:
            raise RuntimeError("PINNED_TRACK_LAYOUT_INVALID")
        payload["duration"] = duration
        material_map = {
            row.get("id"): row for row in _materials(payload.get("materials", {}))
            if isinstance(row.get("id"), str)
        }
        for index, track in enumerate(tracks):
            role = ROLE_BY_TRACK[index] if index < len(ROLE_BY_TRACK) else f"AUX_{index}"
            for segment in track.get("segments", []):
                segment["role"] = role
                material = material_map.get(segment.get("material_id"))
                if material is not None:
                    material["role"] = role
                    material["desc"] = f"001short production {role}"

        a12_template_segment = None
        a12_material = None
        if config.get("audio_role", "A10") == "A12":
            if not tracks[11].get("segments"):
                raise RuntimeError("PINNED_A12_TEMPLATE_SEGMENT_MISSING")
            a12_template_segment = copy.deepcopy(tracks[11]["segments"][0])
            a12_material = material_map.get(a12_template_segment.get("material_id"))
            if a12_material is None:
                raise RuntimeError("PINNED_A12_TEMPLATE_MATERIAL_MISSING")

        # Existing template lanes only: no track is added.
        for index in (4, 5, 8, 10, 11):
            tracks[index]["segments"] = []

        base_video_segment = tracks[0]["segments"][0]
        video_material = material_map[base_video_segment["material_id"]]
        _set_media(
            video_material, media_type="video",
            portable_path=_portable_resource_path(draft_prefix, f"Resources/media/{visual_name}"),
            role="VIDEO", duration_us=duration,
        )
        video_segments = []
        for clip in sorted(build_manifest["urakkai"]["video_clips"], key=lambda row: row["target_range_us"][0]):
            video_row = approved_by_id.get(clip["clip_id"])
            if (
                video_row is None or video_row.get("role") != "VIDEO"
                or video_row.get("start") != clip["target_range_us"][0]
                or video_row.get("duration") != clip["target_range_us"][1] - clip["target_range_us"][0]
            ):
                raise RuntimeError(f"VIDEO_PLAN_AUTHORITY_MISMATCH:{clip['clip_id']}")
            video_segment = copy.deepcopy(base_video_segment)
            video_segment["id"] = clip["clip_id"]
            video_segment["role"] = "VIDEO"
            video_segment["target_timerange"] = {
                "start": clip["target_range_us"][0],
                "duration": clip["target_range_us"][1] - clip["target_range_us"][0],
            }
            video_segment["source_timerange"] = {
                "start": clip["source_range_us"][0],
                "duration": clip["source_range_us"][1] - clip["source_range_us"][0],
            }
            if config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL":
                video_segment["volume"] = 0.0
            video_segments.append(video_segment)
        tracks[0]["segments"] = video_segments

        for index, role in ((1, "SCREEN_EFFECT"), (2, "SCREEN_WHITE")):
            if not any(row.get("role") == role for row in approved):
                tracks[index]["segments"] = []
                continue
            segment = tracks[index]["segments"][0]
            segment["id"] = _approved_id(config, approved, role)
            row = approved_by_id[segment["id"]]
            segment["target_timerange"] = {"start": row["start"], "duration": row["duration"]}

        for index, key in ((6, "T2"), (7, "T1")):
            segment = tracks[index]["segments"][0]
            segment["id"] = _approved_id(config, approved, key)
            _set_text(material_map[segment["material_id"]], config[key], key)
            row = approved_by_id[segment["id"]]
            segment["target_timerange"] = {"start": row["start"], "duration": row["duration"]}

        state_track = tracks[3]
        base_segment = state_track["segments"][0]
        base_material = material_map[base_segment["material_id"]]
        parent = _material_parent(payload["materials"], base_material["id"])
        if parent is None:
            raise RuntimeError("STATE_MATERIAL_CONTAINER_MISSING")
        state_segments = []
        for cue_index, cue in enumerate(config["state_cues"]):
            segment = copy.deepcopy(base_segment)
            material = copy.deepcopy(base_material)
            segment_id = cue.get("segment_id") or _approved_id(config, approved, "STATE", cue_index)
            approved_row = approved_by_id.get(segment_id)
            if (
                approved_row is None or approved_row.get("role") != "STATE"
                or approved_row.get("start") != cue["start_us"]
                or approved_row.get("duration") != cue["end_us"] - cue["start_us"]
            ):
                raise RuntimeError(f"STATE_CUE_AUTHORITY_MISMATCH:{segment_id}")
            material_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{config['episode_id']}:state-material:{cue_index}"))
            segment["id"] = segment_id
            segment["material_id"] = material_id
            segment["role"] = "STATE"
            segment["target_timerange"] = {
                "start": cue["start_us"], "duration": cue["end_us"] - cue["start_us"]
            }
            material["id"] = material_id
            _set_text(material, cue["text"], "STATE")
            parent.append(material)
            material_map[material_id] = material
            state_segments.append(segment)
        state_track["segments"] = state_segments

        base_a10_segment = tracks[9]["segments"][0]
        a10_material = material_map[base_a10_segment["material_id"]]
        _set_media(
            a10_material, media_type="audio",
            portable_path=_portable_resource_path(draft_prefix, f"Resources/media/{audio_name}"),
            role="A10", duration_us=duration,
        )
        a10_segments = []
        for audio_index, audio_plan in enumerate(build_manifest["source_audio"]):
            if audio_plan.get("mode") not in {"on", "duck"}:
                continue
            capcut_source_range = audio_plan.get("capcut_source_range_us", audio_plan["source_range_us"])
            a10_segment = copy.deepcopy(base_a10_segment)
            a10_segment["id"] = _approved_id(config, approved, "A10", audio_index)
            a10_segment["role"] = "A10"
            a10_segment["target_timerange"] = {
                "start": audio_plan["target_range_us"][0],
                "duration": audio_plan["target_range_us"][1] - audio_plan["target_range_us"][0],
            }
            a10_segment["source_timerange"] = {
                "start": capcut_source_range[0],
                "duration": capcut_source_range[1] - capcut_source_range[0],
            }
            if config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL":
                a10_segment["volume"] = 1.0
            a10_segments.append(a10_segment)
        tracks[9]["segments"] = a10_segments

        if config.get("audio_role", "A10") == "A12":
            assert a12_template_segment is not None and a12_material is not None
            _populate_full_duration_audio(
                tracks[11],
                a12_template_segment,
                a12_material,
                portable_path=_portable_resource_path(
                    draft_prefix, f"Resources/media/{audio_name}"
                ),
                duration_us=duration,
                role="A12",
                segment_id=_approved_id(config, approved, "A12"),
            )

        # Keep every retained local template material self-contained.
        retained_ids = {
            segment.get("material_id")
            for track in tracks for segment in track.get("segments", [])
        }
        for serial, material in enumerate(_materials(payload.get("materials", {})), start=1):
            material.setdefault("role", f"AUX_MATERIAL_{serial}")
            material.setdefault("desc", "001short retained template material")
            if material.get("id") not in retained_ids and material.get("type") == "text":
                material["content"] = ""
                material["text"] = ""
            _scrub_remote(material)
            _normalize_paths(material, project, draft_prefix)
        for track in tracks:
            for segment in track.get("segments", []):
                if isinstance(segment.get("extra_material_refs"), list):
                    segment["extra_material_refs"] = [
                        item for item in segment["extra_material_refs"] if item in retained_ids or item in material_map
                    ]
        _write_json(path, payload)

        if document_index == 0:
            refreshed = {
                row.get("id"): row for row in _materials(payload["materials"])
                if isinstance(row.get("id"), str)
            }
            for track in tracks:
                for segment in track.get("segments", []):
                    timerange = segment["target_timerange"]
                    material = refreshed.get(segment.get("material_id"), {})
                    root_rows.append({
                        "segment_id": segment["id"],
                        "role": segment["role"],
                        "material_type": material.get("type", "unknown"),
                        "start": timerange["start"],
                        "duration": timerange["duration"],
                        "end": timerange["start"] + timerange["duration"],
                    })
    meta_path = project / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["tm_duration"] = duration
    _write_json(meta_path, meta)

    actual = sorted(root_rows, key=lambda row: (row["start"], row["segment_id"]))
    expected = [
        {key: row[key] for key in ("segment_id", "role", "start", "duration")}
        for row in approved
    ]
    observed = [
        {key: row[key] for key in ("segment_id", "role", "start", "duration")}
        for row in actual
    ]
    if observed != expected:
        raise RuntimeError(f"APPROVED_TIMELINE_ACTUAL_MISMATCH:{observed}")
    return actual


def _audio_codec(path: Path) -> str:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_name", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=False,
    )
    codec = completed.stdout.strip()
    if completed.returncode or not codec:
        raise RuntimeError("SOURCE_AUDIO_STREAM_MISSING")
    return codec


def _video_dimensions(path: Path) -> tuple[int, int]:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", str(path)],
        capture_output=True, text=True, check=False,
    )
    try:
        stream = json.loads(completed.stdout)["streams"][0]
        width, height = int(stream["width"]), int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        raise RuntimeError("CLEAN_VIDEO_STREAM_MISSING") from None
    if completed.returncode or width <= 0 or height <= 0:
        raise RuntimeError("CLEAN_VIDEO_STREAM_MISSING")
    return width, height


def _srt_time(microseconds: int) -> str:
    milliseconds = microseconds // 1000
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _clean_receipt_fields_match(stored: dict, expected: dict) -> bool:
    return stored.get("status") == "PASS" and all(
        stored.get(field) == value for field, value in expected.items()
    )


def _build_manifest_visual_matches(config: dict, build_manifest: dict, visual_asset: Path) -> bool:
    visual_asset = Path(visual_asset).resolve()
    provisional = config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL"
    section = build_manifest.get("source" if provisional else "vmake")
    if not isinstance(section, dict):
        return False
    raw_path = section.get("path" if provisional else "output_path")
    raw_sha = section.get("sha256" if provisional else "output_sha256")
    return (
        isinstance(raw_path, str)
        and isinstance(raw_sha, str)
        and len(raw_sha) == 64
        and Path(raw_path).resolve() == visual_asset
        and visual_asset.is_file()
        and _sha(visual_asset).lower() == raw_sha.lower()
    )


def _stage_prerequisites(config: dict, episode: Path, source_rows: list[dict]) -> dict:
    del source_rows
    episode_id = config["episode_id"]
    visual_asset = _visual_asset_path(config)
    provisional = config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL"
    audio_source = Path(config.get("source_audio") or config.get("source_video") or visual_asset).resolve()
    duration = config["duration_us"]
    width, height = _video_dimensions(visual_asset)
    source_identity = Path(config["source_identity_path"]).resolve()
    approved_timeline = Path(config["approved_timeline_path"]).resolve()
    handoff = Path(config["design_handoff_path"]).resolve()
    design_evidence = Path(config["design_lock_evidence_path"]).resolve()
    if not all(path.is_file() for path in (source_identity, approved_timeline, handoff, design_evidence)):
        raise RuntimeError("STAGE05_AUTHORITY_MISSING")
    lock = validate_design_lock.validate_handoff(handoff, source_identity, approved_timeline)
    if lock["status"] != "PASS":
        raise RuntimeError(f"STAGE05:{lock}")
    stored_evidence = json.loads(design_evidence.read_text(encoding="utf-8"))
    verified_fields = (
        "episode_id", "handoff_path", "handoff_sha256", "source_identity_path",
        "source_identity_sha256", "source_media_path", "source_media_sha256",
        "timeline_path", "timeline_sha256", "source_fingerprint",
    )
    if stored_evidence.get("status") != "PASS" or any(
        stored_evidence.get(field) != lock["evidence"].get(field) for field in verified_fields
    ):
        raise RuntimeError("STAGE05_EVIDENCE_MISMATCH")

    # Heavy VMake media remains machine-local; the episode folder retains only
    # its manifests and pointers.  A missing override preserves legacy tests.
    clean_root = Path(config.get("clean_asset_root", episode / "40_assets_used")).resolve()
    clean_evidence_root = Path(config.get("clean_evidence_root", clean_root)).resolve()
    try:
        if not provisional:
            visual_asset.relative_to(clean_root.resolve())
    except ValueError:
        raise RuntimeError("STAGE06_CLEAN_OUTPUT_OUTSIDE_ASSET_ROOT") from None
    build_manifest_path = Path(config["build_manifest_path"]).resolve()
    prebuild = validate_prebuild.validate_prebuild(build_manifest_path, allow_source_provisional=provisional)
    if prebuild["status"] != "PASS":
        raise RuntimeError(f"STAGE08_PREBUILD:{prebuild}")
    build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    if (
        build_manifest.get("episode_id") != episode_id
        or build_manifest["source"].get("sha256", "").lower()
        != stored_evidence["source_media_sha256"].lower()
        or Path(build_manifest["template"]["root_zip_path"]).resolve()
        != Path(config["template_zip"]).resolve()
        or build_manifest["template"]["root_zip_sha256"].lower()
        != _sha(Path(config["template_zip"])).lower()
        or not _build_manifest_visual_matches(config, build_manifest, visual_asset)
    ):
        raise RuntimeError("STAGE08_BUILD_MANIFEST_AUTHORITY_MISMATCH")

    if not provisional:
        clean_manifest = clean_evidence_root / "clean_visual_manifest.json"
        clean_receipt = clean_evidence_root / "clean_visual_receipt.json"
        if not clean_manifest.is_file() or not clean_receipt.is_file():
            raise RuntimeError("STAGE06_EVIDENCE_MISSING")
        clean = validate_clean_visual.validate_clean_visual(clean_manifest, source_identity, design_evidence)
        stored_clean_receipt = json.loads(clean_receipt.read_text(encoding="utf-8"))
        expected_receipt = clean.get("evidence", {})
        if clean["status"] != "PASS" or not _clean_receipt_fields_match(
            stored_clean_receipt, expected_receipt
        ):
            raise RuntimeError("STAGE06_RECEIPT_AUTHORITY_MISMATCH")
        if clean["status"] != "PASS":
            raise RuntimeError(f"STAGE06:{clean}")

    audio_root = episode / "30_audio_srt"
    audio_lock = audio_root / "audio_lock.json"
    final_srt = audio_root / "final.srt"
    caption_lock = audio_root / "caption_lock.json"
    cues = config["state_cues"]
    if not all(path.is_file() for path in (audio_lock, final_srt, caption_lock)):
        raise RuntimeError("STAGE07_EVIDENCE_MISSING")
    audio = validate_audio_caption.validate_audio_caption(audio_lock, caption_lock)
    if audio["status"] != "PASS":
        raise RuntimeError(f"STAGE07:{audio}")
    audio_payload = json.loads(audio_lock.read_text(encoding="utf-8"))
    caption_payload = json.loads(caption_lock.read_text(encoding="utf-8"))
    expected_cues = [
        {"cue_id": cue.get("cue_id", str(index)), "start_us": cue["start_us"],
         "end_us": cue["end_us"], "text": cue["text"]}
        for index, cue in enumerate(cues, start=1)
    ]
    if (
        audio_payload.get("episode_id") != episode_id
        or resolved_declared_path(audio_lock, audio_payload["audio_path"]) != audio_source
        or audio_payload.get("audio_sha256") != _sha(audio_source)
        or audio_payload.get("measured_duration_us") != duration
        or caption_payload.get("episode_id") != episode_id
        or caption_payload.get("cues") != expected_cues
    ):
        raise RuntimeError("STAGE07_AUTHORITY_MISMATCH")
    return locals()


def _build_episode_once(config: dict) -> dict:
    _ensure_media_tools()
    _validate_config(config)
    visual_asset = _visual_asset_path(config)
    audio_source = Path(config.get("source_audio") or config.get("source_video") or visual_asset).resolve()
    if not visual_asset.is_file() or not audio_source.is_file():
        raise FileNotFoundError("INPUT_MEDIA_MISSING")
    episode = Path(config["episode_root"]).resolve()
    capcut_root = Path(config["local_capcut_root"]).resolve()
    target = capcut_root / config["project_name"]
    if target.exists():
        raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
    episode.mkdir(parents=True, exist_ok=True)
    build_root = episode / "50_capcut_project"
    evidence_root = build_root / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    work_root = _episode_work_root(config)
    work_root.mkdir(parents=True, exist_ok=True)
    root_contract = capcut_materialization.stage_episode_root_authority(
        Path(config["template_zip"]), episode, config["episode_id"]
    )
    source = _extract_template(Path(root_contract["episode_root_zip_path"]), work_root / "source_authority")
    pre = _stage_prerequisites(config, episode, [])
    source_rows = _normalize_source(source, config, audio_source, pre["build_manifest"])

    working = work_root / "working_project"
    cloned = clone_and_sync.clone_project(source, working)
    if cloned["status"] != "PASS":
        raise RuntimeError(f"STAGE08_CLONE:{cloned}")
    source_manifest = clone_and_sync.hash_project_core(source)
    project_id = "project-" + uuid.uuid4().hex
    draft_id = "draft-" + uuid.uuid4().hex
    timeline_id = "timeline-" + uuid.uuid4().hex
    synced = clone_and_sync.sync_project_ids(
        working, project_id, draft_id, timeline_id,
        source_project_path=source, expected_source_hashes=source_manifest,
    )
    if synced["status"] != "PASS":
        raise RuntimeError(f"STAGE08_ID_SYNC:{synced}")

    source_root_sha = manifest_sha256(source_manifest)
    template_sha = clone_and_sync.template_fingerprint_sha256(source)
    snapshot = capcut_model.capture_structure(capcut_model.load_project(source))
    snapshot["authority"] = {
        "captured_from": "source", "source_project_path": str(source.resolve()),
        "source_root_sha256": source_root_sha, "template_sha256": template_sha,
        "design_lock_evidence_sha256": _sha(pre["design_evidence"]),
    }
    snapshot_path = build_root / "structure_snapshot.json"
    _write_json(snapshot_path, snapshot)

    staging_target = work_root / "materialized_project"
    shutil.copytree(working, staging_target)
    cloud_prepare = _prepare_cloud_project(
        staging_target,
        project_name=config["project_name"],
        capcut_root=capcut_root,
        draft_id=draft_id,
        duration_us=config["duration_us"],
    )
    polish_receipt_path = build_root / "capcut_polish_profile_receipt.json"
    polish_receipt = apply_capcut_polish_profile.apply_project(staging_target)
    _write_json(polish_receipt_path, polish_receipt)
    polish_validation = validate_capcut_polish_profile.validate_project(staging_target)
    if polish_validation["status"] != "PASS":
        raise RuntimeError(f"STAGE08_POLISH:{polish_validation}")
    model = capcut_model.load_project(staging_target)
    material_map = {row.get("id"): row for row in _materials(model.materials) if isinstance(row.get("id"), str)}
    timeline_rows = []
    approved_text: set[str] = set()
    required_assets: set[str] = set()
    for track in model.tracks:
        for segment in track.get("segments", []):
            timerange = segment["target_timerange"]
            material = material_map.get(segment.get("material_id"), {})
            timeline_rows.append({
                "segment_id": segment["id"], "role": segment["role"],
                "material_type": material.get("type", "unknown"),
                "start": timerange["start"], "duration": timerange["duration"],
                "end": timerange["start"] + timerange["duration"],
            })
            visible_text = _material_text(material)
            if visible_text:
                approved_text.add(visible_text)
            if material.get("type") in {"video", "audio", "music", "extract_music"}:
                raw = material.get("path") or material.get("media_path")
                if isinstance(raw, str) and raw:
                    required_assets.add(Path(raw).as_posix())
    ordered = sorted(timeline_rows, key=lambda row: (row["start"], row["segment_id"]))
    contract_path = build_root / "build_contract.json"
    receipt_path = build_root / "build_inputs_receipt.json"
    contract = {
        "schema_version": "001short-build-contract-v1", "episode_id": config["episode_id"],
        "visual_asset_mode": config.get("visual_asset_mode", "CLEAN_VISUAL_READY"),
        "source_video_provisional": config.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL",
        "source_project_path": str(source.resolve()), "working_project_path": str(staging_target.resolve()),
        "materialized_project_path": str(target.resolve()),
        "evidence_root_path": str(evidence_root.resolve()), "source_core_sha256": source_manifest,
        "source_root_sha256": source_root_sha, "template_sha256": template_sha,
        "design_lock_evidence_path": str(pre["design_evidence"].resolve()),
        "design_lock_evidence_sha256": _sha(pre["design_evidence"]),
        "audio_lock_path": str(pre["audio_lock"].resolve()), "audio_lock_sha256": _sha(pre["audio_lock"]),
        "caption_lock_path": str(pre["caption_lock"].resolve()), "caption_lock_sha256": _sha(pre["caption_lock"]),
        "final_srt_path": str(pre["final_srt"].resolve()), "final_srt_sha256": _sha(pre["final_srt"]),
        "approved_timeline_path": str(pre["approved_timeline"].resolve()),
        "approved_timeline_sha256": _sha(pre["approved_timeline"]),
        "build_manifest_path": str(Path(config["build_manifest_path"]).resolve()),
        "build_manifest_sha256": _sha(Path(config["build_manifest_path"]).resolve()),
        "build_inputs_receipt_path": str(receipt_path.resolve()), "build_inputs_receipt_sha256": "0" * 64,
        "capcut_polish_profile_receipt_path": str(polish_receipt_path.resolve()),
        "capcut_polish_profile_receipt_sha256": _sha(polish_receipt_path),
        "capcut_polish_profile_validation": polish_validation,
        "structure_snapshot_sha256": _sha(snapshot_path), "project_id": project_id,
        "draft_id": draft_id, "main_timeline_id": timeline_id,
        "required_asset_paths": sorted(required_assets), "approved_text": sorted(approved_text),
        "approved_actual_order": [row["segment_id"] for row in ordered], "timeline": ordered,
        "primary_timeline_roles": ["VIDEO"], "authorized_gaps": [],
        "authorized_overlaps": [], "parallel_pairs": [],
        "subtitle_roles": ["STATE"],
        "caption_bindings": [
            {
                "segment_id": cue.get("segment_id")
                or _approved_id(config, _approved_rows(config), "STATE", index - 1),
                "cue_id": cue.get("cue_id", str(index)),
            }
            for index, cue in enumerate(config["state_cues"], start=1)
        ],
    }
    _write_json(contract_path, contract)
    inputs = validate_build_inputs.validate_build_inputs(
        pre["caption_lock"], pre["final_srt"], contract_path, pre["approved_timeline"]
    )
    if inputs["status"] != "PASS":
        raise RuntimeError(f"STAGE08_INPUTS:{inputs}")
    _write_json(receipt_path, inputs)
    contract["build_inputs_receipt_sha256"] = _sha(receipt_path)
    _write_json(contract_path, contract)
    capcut_evidence = evidence_root / "capcut_project_evidence.json"
    if capcut_evidence.exists():
        if not capcut_evidence.is_file() or capcut_evidence.parent.resolve() != evidence_root.resolve():
            raise RuntimeError("UNSAFE_PREVIOUS_CAPCUT_EVIDENCE")
        capcut_evidence.unlink()
    checked = validate_capcut_project.validate_capcut_project(
        staging_target, snapshot_path, contract_path, capcut_evidence, evidence_root
    )
    if checked["status"] != "PASS":
        raise RuntimeError(f"STAGE08_VALIDATE:{checked}")
    postbuild = validate_postbuild.validate_postbuild(
        Path(config["build_manifest_path"]), staging_target,
        visual_asset_mode=config.get("visual_asset_mode", "CLEAN_VISUAL_READY"),
    )
    if postbuild["status"] != "PASS":
        raise RuntimeError(f"STAGE08_POSTBUILD:{postbuild}")
    materialized = capcut_materialization.materialize_validated_package(
        staging_target, capcut_root, config["project_name"], config["episode_id"],
        assert_closed=lambda: _assert_capcut_closed_for_target(target),
    )
    if materialized["status"] != "PASS":
        raise RuntimeError(f"STAGE08_MATERIALIZATION:{materialized}")
    capcut_evidence.unlink()
    checked = validate_capcut_project.validate_capcut_project(
        target, snapshot_path, contract_path, capcut_evidence, evidence_root
    )
    if checked["status"] != "PASS":
        raise RuntimeError(f"STAGE08_FINAL_VALIDATE:{checked}")
    postbuild = validate_postbuild.validate_postbuild(
        Path(config["build_manifest_path"]), target,
        visual_asset_mode=config.get("visual_asset_mode", "CLEAN_VISUAL_READY"),
    )
    if postbuild["status"] != "PASS":
        raise RuntimeError(f"STAGE08_FINAL_POSTBUILD:{postbuild}")
    canonical_identity = materialized["canonical_identity"]
    materialization_receipt = {"resource": "Mac_CapCut_global_root", **materialized}
    _write_json(build_root / "materialization_receipt.json", materialization_receipt)
    state = {
        "episode_id": config["episode_id"], "current_stage": "09",
        "status": "WAIT_USER_CAPCUT_CHECK", "project_name": config["project_name"],
        "local_capcut_project_path": str(target), "stage09_user_approval": "NOT_RUN",
        "cloud_prepare": cloud_prepare, "visual_asset_mode": config.get("visual_asset_mode", "CLEAN_VISUAL_READY"),
        "canonical_identity": canonical_identity,
    }
    _write_json(episode / "episode_state.json", state)
    return {
        "status": state["status"], "current_stage": "09", "stage08_validation": "PASS",
        "project_path": str(target), "capcut_evidence_path": str(capcut_evidence),
    }


def _cleanup_generated_work(work_root: Path) -> None:
    work_root = Path(work_root).resolve()
    for name in ("normalized_source", "working_project", "materialized_project"):
        candidate = work_root / name
        if candidate.parent != work_root:
            raise RuntimeError("UNSAFE_GENERATED_WORK_PATH")
        if candidate.is_dir():
            shutil.rmtree(candidate)
        elif candidate.exists():
            candidate.unlink()


def _reset_source_authority(work_root: Path) -> None:
    work_root = Path(work_root).resolve()
    candidate = work_root / "source_authority"
    if candidate.parent != work_root:
        raise RuntimeError("UNSAFE_SOURCE_AUTHORITY_PATH")
    if candidate.is_dir():
        shutil.rmtree(candidate)
    elif candidate.exists():
        candidate.unlink()


def _assert_optional_edit_lock(config: dict) -> None:
    raw_path = config.get("edit_lock_path")
    if not raw_path:
        return
    path = Path(raw_path).resolve()
    if not path.is_file():
        raise RuntimeError("EDIT_LOCK_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("episode_id") != config["episode_id"]:
        raise RuntimeError("EDIT_LOCK_EPISODE_MISMATCH")
    expected_writer = config.get("active_writer_machine")
    if expected_writer and payload.get("active_writer_machine") != expected_writer:
        raise RuntimeError("EDIT_LOCK_WRITER_MISMATCH")


def _assert_capcut_closed_for_target(target: Path) -> None:
    if sys.platform == "darwin":
        completed = subprocess.run(
            ["pgrep", "-x", "CapCut"], capture_output=True, text=True, check=False
        )
        if completed.returncode == 0:
            raise RuntimeError("CAPCUT_PROCESS_OPEN")
        if completed.returncode != 1:
            raise RuntimeError("CAPCUT_PROCESS_CHECK_FAILED")
        return
    if os.name != "nt":
        return
    local_appdata = Path(os.environ.get("LOCALAPPDATA", "")).resolve()
    capcut_root = local_appdata / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    try:
        target.resolve(strict=False).relative_to(capcut_root.resolve(strict=False))
    except ValueError:
        return
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError("CAPCUT_PROCESS_CHECK_FAILED")
    active = completed.stdout.casefold()
    if '"capcut.exe"' in active or '"lveditor.exe"' in active:
        raise RuntimeError("CAPCUT_PROCESS_OPEN")


def build_episode(config: dict) -> dict:
    _validate_config(config)
    target = Path(config["local_capcut_root"]).resolve() / config["project_name"]
    if target.exists():
        raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
    _assert_optional_edit_lock(config)
    work_root = _episode_work_root(config)
    work_root.mkdir(parents=True, exist_ok=True)
    _cleanup_generated_work(work_root)
    _reset_source_authority(work_root)
    try:
        return _build_episode_once(config)
    finally:
        _cleanup_generated_work(work_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    payload = build_episode(json.loads(args.config.read_text(encoding="utf-8")))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
