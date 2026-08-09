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
import resolve_shorts_capcut_root
from capcut_io import iter_primary_draft_documents
from common import manifest_sha256, meaningful_text_length, read_json, resolved_declared_path
from track_contract import A10_TEXT_TRACK_BY_COLOR, A12_INDEX, CANONICAL_TRACKS, STATE_TRACK_BY_EFFECT, TRACK_INDEX, TRACK_LAYOUT


ROLE_BY_TRACK = list(CANONICAL_TRACKS)

# A9 carries the narration we generate; A10 carries the retained source speech.
# MIXED keeps both, so the source stem must still be present while A9 is built.
AUDIO_POLICIES = frozenset({
    "A10_RETAINED_SYNC", "TTS_ONLY_MUTE_SOURCE", "A9_TTS_PLUS_A10_RETAINED",
})
TTS_POLICIES = frozenset({"TTS_ONLY_MUTE_SOURCE", "A9_TTS_PLUS_A10_RETAINED"})
A10_POLICIES = frozenset({"A10_RETAINED_SYNC", "A9_TTS_PLUS_A10_RETAINED"})


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


def _bind_portable_root_contract(config: dict) -> dict | None:
    raw_contract = config.get("root_contract_path")
    if raw_contract is None:
        raise ValueError("ROOT_CONTRACT_PATH_MISSING")
    raw_workspace = config.get("workspace_root")
    profile = config.get("root_profile")
    if not isinstance(raw_workspace, str) or not raw_workspace.strip():
        raise ValueError("ROOT_CONTRACT_WORKSPACE_ROOT_MISSING")
    if not isinstance(profile, str) or not profile.strip():
        raise ValueError("ROOT_CONTRACT_PROFILE_MISSING")
    workspace_root = Path(raw_workspace).resolve()
    candidate = Path(str(raw_contract))
    if candidate.is_absolute():
        raise ValueError("ROOT_CONTRACT_PATH_MUST_BE_WORKSPACE_RELATIVE")
    contract_path = workspace_root / candidate
    resolved = resolve_shorts_capcut_root.resolve_root_contract(
        workspace_root, profile, contract_path
    )
    if resolved.get("template_profile") != "shrt_white_base_v2":
        raise ValueError("ROOT_CONTRACT_V2_PROFILE_REQUIRED")
    declared = config.get("template_zip")
    if declared is not None and Path(str(declared)).resolve() != Path(resolved["archive"]):
        raise ValueError("ROOT_CONTRACT_TEMPLATE_MISMATCH")
    config["template_zip"] = resolved["archive"]
    config["_resolved_root_contract"] = {
        "profile": resolved["profile"],
        "template_profile": resolved["template_profile"],
        "archive_sha256": resolved["archive_sha256"],
    }
    return resolved


def resolve_visual_input(config: dict) -> dict:
    mode = config.get("visual_asset_mode")
    if mode == "SOURCE_VIDEO_PROVISIONAL":
        identity_path = Path(config["source_identity_path"]).resolve()
        identity = read_json(identity_path)
        video = resolved_declared_path(identity_path, identity["media_path"])
        expected_sha = identity.get("media_sha256")
        if not video.is_file() or not isinstance(expected_sha, str) or _sha(video).lower() != expected_sha.lower():
            raise RuntimeError("SOURCE_PROVISIONAL_SHA_MISMATCH")
        return {
            "visual_asset_mode": mode,
            "video_asset_key": "source_video",
            "video_input_path": video,
            "video_input_sha256": expected_sha.lower(),
            "resource_name": "source.mp4",
            "upload_ready": False,
        }
    if mode == "CLEAN_VISUAL_READY":
        raw = config.get("clean_video")
        if not isinstance(raw, str) or not raw:
            raise ValueError("CLEAN_VIDEO_REQUIRED")
        video = Path(raw).resolve()
        if not video.is_file():
            raise FileNotFoundError("CLEAN_VIDEO_MISSING")
        return {
            "visual_asset_mode": mode,
            "video_asset_key": "clean_video",
            "video_input_path": video,
            "video_input_sha256": _sha(video),
            "resource_name": "clean_video.mp4",
            "upload_ready": False,
        }
    raise ValueError(f"VISUAL_ASSET_MODE_INVALID:{mode}")


def validate_state_cues(config: dict, timeline: dict) -> None:
    cues = config.get("state_cues")
    if not isinstance(cues, list):
        raise ValueError("STATE_CUES_INVALID")
    state_rows = sorted(
        (row for row in timeline.get("segments", []) if row.get("role") == "STATE"),
        key=lambda row: row.get("timeline_order", 0),
    )
    if len(cues) != len(state_rows):
        raise ValueError("STATE_CUES_TIMELINE_MISMATCH")
    previous_end = 0
    duration = config["duration_us"]
    for index, (cue, row) in enumerate(zip(cues, state_rows), start=1):
        if (
            not isinstance(cue, dict)
            or not isinstance(cue.get("text"), str)
            or not cue["text"].strip()
            or not isinstance(cue.get("start_us"), int)
            or not isinstance(cue.get("end_us"), int)
            or cue["start_us"] < previous_end
            or cue["end_us"] <= cue["start_us"]
            or cue["end_us"] > duration
            or any(meaningful_text_length(line) > 8 for line in cue["text"].splitlines())
            or cue.get("text") != row.get("text")
            or cue["start_us"] != row.get("start")
            or cue["end_us"] - cue["start_us"] != row.get("duration")
            or str(cue.get("cue_id", index)) != str(row.get("cue_id", index))
        ):
            raise ValueError("STATE_CUES_INVALID")
        previous_end = cue["end_us"]


def validate_tts_cues(config: dict, timeline: dict) -> None:
    if config.get("audio_policy") not in TTS_POLICIES and not config.get("tts_cues"):
        return
    cues = config.get("tts_cues")
    if not isinstance(cues, list) or not cues:
        raise ValueError("TTS_CUES_REQUIRED")
    audio_rows = {row.get("cue_id"): row for row in timeline.get("segments", []) if row.get("role") == "A9"}
    text_rows = {row.get("cue_id"): row for row in timeline.get("segments", []) if row.get("role") == "A9_TEXT"}
    if len(audio_rows) != len(cues) or set(audio_rows) != set(text_rows):
        raise ValueError("TTS_CUE_PLAN_AUTHORITY_MISMATCH")
    for cue in cues:
        cue_id = cue.get("cue_id")
        sound, caption = audio_rows.get(cue_id), text_rows.get(cue_id)
        target_range = cue.get("target_range_us")
        if (
            sound is None or caption is None
            or not isinstance(target_range, list) or len(target_range) != 2
            or cue.get("text") != sound.get("text")
            or cue.get("text") != caption.get("text")
            or (sound.get("start"), sound.get("duration"))
            != (target_range[0], target_range[1] - target_range[0])
            or (caption.get("start"), caption.get("duration"))
            != (target_range[0], target_range[1] - target_range[0])
        ):
            raise ValueError("TTS_CUE_PLAN_AUTHORITY_MISMATCH")


def build_caption_bindings(config: dict, caption_lock_path: Path) -> list[dict]:
    caption = read_json(caption_lock_path)
    cues = caption.get("cues", [])
    rows = [
        row for row in _approved_rows(config)
        if row.get("role") in {"STATE", "A10_TEXT", "A9_TEXT"}
    ]
    bindings: list[dict] = []
    used_cues: set[str] = set()
    for row in rows:
        role = row["role"]
        matches = [
            cue for cue in cues
            if cue.get("layer") == role
            and cue.get("text") == row.get("text")
            and cue.get("start_us") == row.get("start")
            and cue.get("end_us") == row.get("start") + row.get("duration")
        ]
        if len(matches) != 1:
            raise RuntimeError(f"CAPTION_BINDING_AUTHORITY_MISMATCH:{row.get('segment_id')}")
        cue_id = str(matches[0].get("cue_id"))
        if not cue_id or cue_id in used_cues:
            raise RuntimeError(f"CAPTION_BINDING_AUTHORITY_MISMATCH:{row.get('segment_id')}")
        used_cues.add(cue_id)
        bindings.append({"segment_id": row["segment_id"], "cue_id": cue_id, "role": role})
    return bindings


def assert_a12_empty(segments: list[dict]) -> None:
    if any(row.get("role") in {"A12", "A12_RESERVED_EMPTY"} for row in segments):
        raise RuntimeError("A12_RESERVED_EMPTY")


def _validate_config(config: dict) -> None:
    _bind_portable_root_contract(config)
    required = (
        "episode_id", "visual_asset_mode", "audio_policy", "duration_us", "T1", "T2", "state_cues",
        "project_name", "template_zip", "episode_root", "work_root", "local_capcut_root",
        "source_identity_path", "approved_timeline_path", "design_handoff_path",
        "design_lock_evidence_path", "build_manifest_path", "state_path",
    )
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"CONFIG_MISSING:{','.join(missing)}")
    canonical_state = Path(config["episode_root"]).resolve() / "90_workflow" / "state.json"
    if Path(config["state_path"]).resolve() != canonical_state:
        raise ValueError("CANONICAL_STATE_PATH_REQUIRED")
    if config.get("audio_role", "A10") not in {"A10", None}:
        raise ValueError("AUDIO_ROLE_INVALID")
    duration = config["duration_us"]
    if not isinstance(duration, int) or duration <= 0:
        raise ValueError("DURATION_INVALID")
    timeline = read_json(Path(config["approved_timeline_path"]).resolve())
    role_errors = validate_design_lock.validate_role_contract(timeline, expected_duration=duration)
    if role_errors:
        raise ValueError(f"APPROVED_TIMELINE_ROLE_CONTRACT:{role_errors}")
    if (
        config["audio_policy"] not in AUDIO_POLICIES
        or timeline.get("audio_policy") != config["audio_policy"]
    ):
        raise ValueError("AUDIO_POLICY_TIMELINE_MISMATCH")
    validate_state_cues(config, timeline)
    validate_tts_cues(config, timeline)
    config["_visual_input"] = resolve_visual_input(config)


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


def _remove_material_ids(value: Any, material_ids: set[str]) -> None:
    if isinstance(value, list):
        value[:] = [
            row for row in value
            if not (isinstance(row, dict) and row.get("id") in material_ids)
        ]
        for child in value:
            _remove_material_ids(child, material_ids)
    elif isinstance(value, dict):
        for child in value.values():
            _remove_material_ids(child, material_ids)


def _documents(project: Path) -> Iterator[tuple[Path, dict]]:
    for path, payload in iter_primary_draft_documents(project):
        if isinstance(payload, dict) and isinstance(payload.get("tracks"), list):
            yield path, payload


def _set_media(
    material: dict, *, media_type: str, portable_path: str, role: str, duration_us: int,
    dimensions: tuple[int, int] | None = None,
) -> None:
    if media_type == "video":
        material["type"] = "video"
        material["media_path"] = ""
        # The seed material carries the template's dimensions, not the swapped-in
        # media's.  Leaving them stale makes CapCut scale the clip against the
        # wrong intrinsic size, which shows up as a blank or mis-framed preview.
        if dimensions is not None:
            material["width"], material["height"] = dimensions
    elif material.get("type") not in {"music", "extract_music"}:
        material["type"] = "music"
    material["role"] = role
    material["desc"] = f"001short production {role}"
    material["path"] = portable_path
    material["duration"] = duration_us


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


def _ranges_overlap(left: list[int], right: list[int]) -> bool:
    return max(left[0], right[0]) < min(left[1], right[1])


def _range_fully_covered(inner: list[int], outer: list[int]) -> bool:
    return outer[0] <= inner[0] and outer[1] >= inner[1]


def _validate_mixed_audio_modes(config: dict, build_manifest: dict) -> None:
    if config.get("audio_policy") != "A9_TTS_PLUS_A10_RETAINED":
        return
    narration_ranges = [cue["target_range_us"] for cue in config.get("tts_cues", [])]
    for row in build_manifest.get("source_audio", []):
        target_range = row.get("target_range_us")
        if not isinstance(target_range, list) or len(target_range) != 2:
            continue
        overlapping_ranges = [
            cue_range for cue_range in narration_ranges
            if _ranges_overlap(target_range, cue_range)
        ]
        if any(
            not _range_fully_covered(target_range, cue_range)
            for cue_range in overlapping_ranges
        ):
            raise RuntimeError(
                f"MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED:{row.get('clip_id')}"
            )
        overlaps_narration = bool(overlapping_ranges)
        if overlaps_narration and row.get("mode") != "duck":
            raise RuntimeError(f"MIXED_A10_MUTE_REQUIRED_UNDER_A9:{row.get('clip_id')}")
        if not overlaps_narration and row.get("mode") != "on":
            raise RuntimeError(f"MIXED_A10_RESTORE_REQUIRED_OUTSIDE_A9:{row.get('clip_id')}")


def _normalize_source(
    project: Path, config: dict, audio_source: Path | None, build_manifest: dict
) -> list[dict]:
    _validate_mixed_audio_modes(config, build_manifest)
    duration = config["duration_us"]
    approved = _approved_rows(config)
    approved_by_id = {row["segment_id"]: row for row in approved}
    media = project / "Resources" / "media"
    media.mkdir(parents=True, exist_ok=True)
    visual = config["_visual_input"]
    video_input = Path(visual["video_input_path"])
    video_resource = visual["resource_name"]
    shutil.copy2(video_input, media / video_resource)
    video_dimensions = _video_dimensions(video_input)
    policy = config.get("audio_policy")
    build_a9 = policy in TTS_POLICIES
    keep_a10 = policy in A10_POLICIES
    audio_name = ""
    if keep_a10:
        if audio_source is None:
            raise RuntimeError("SOURCE_AUDIO_REQUIRED")
        audio_suffix = audio_source.suffix.lower() or ".wav"
        # This is the externally separated Demucs vocal stem, not the raw
        # source audio.  Keep that distinction visible in the portable asset.
        audio_name = f"a10_vocal_stem{audio_suffix}"
        shutil.copy2(audio_source, media / audio_name)
    draft_prefix = _draft_path_prefix(project)

    root_rows: list[dict] = []
    for document_index, (path, payload) in enumerate(_documents(project)):
        tracks = payload["tracks"]
        if len(tracks) != len(ROLE_BY_TRACK):
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
        seed_segments = {
            index: copy.deepcopy(track["segments"][0])
            for index, track in enumerate(tracks)
            if track.get("segments")
        }
        empty_audio_material_ids = {
            segment.get("material_id")
            for track_index in (TRACK_INDEX["A11"], A12_INDEX)
            for segment in tracks[track_index].get("segments", [])
            if isinstance(segment.get("material_id"), str)
        }

        a9_text_template_segment = None
        a9_text_template_material = None
        a9_text_parent = None
        a9_template_segment = None
        a9_template_material = None
        a9_parent = None
        if build_a9:
            if not tracks[TRACK_INDEX["A9_TEXT"]].get("segments") or not tracks[TRACK_INDEX["A9"]].get("segments"):
                raise RuntimeError("PINNED_A9_TEMPLATE_SEGMENT_MISSING")
            a9_text_template_segment = copy.deepcopy(tracks[TRACK_INDEX["A9_TEXT"]]["segments"][0])
            a9_template_segment = copy.deepcopy(tracks[TRACK_INDEX["A9"]]["segments"][0])
            a9_text_template_material = material_map.get(a9_text_template_segment.get("material_id"))
            a9_template_material = material_map.get(a9_template_segment.get("material_id"))
            if a9_text_template_material is None or a9_template_material is None:
                raise RuntimeError("PINNED_A9_TEMPLATE_MATERIAL_MISSING")
            a9_text_parent = _material_parent(payload["materials"], a9_text_template_material["id"])
            a9_parent = _material_parent(payload["materials"], a9_template_material["id"])
            if a9_text_parent is None or a9_parent is None:
                raise RuntimeError("PINNED_A9_MATERIAL_CONTAINER_MISSING")

        # Existing v2 lanes only: no track is added.  Every generated lane is
        # rebuilt from the approved plan; A12 is always empty.
        for index in range(3, 15):
            if index not in (9, 10):
                tracks[index]["segments"] = []

        base_video_segment = tracks[TRACK_INDEX["VIDEO"]]["segments"][0]
        video_material = material_map[base_video_segment["material_id"]]
        _set_media(
            video_material, media_type="video",
            portable_path=_portable_resource_path(draft_prefix, f"Resources/media/{video_resource}"),
            role="VIDEO", duration_us=duration, dimensions=video_dimensions,
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
            video_segment["volume"] = 0.0
            video_segment["last_nonzero_volume"] = 0.0
            video_segments.append(video_segment)
        tracks[TRACK_INDEX["VIDEO"]]["segments"] = video_segments

        for role in ("SCREEN_EFFECT", "SCREEN_WHITE"):
            index = TRACK_INDEX[role]
            matches = [row for row in approved if row.get("role") == role]
            if len(matches) != 1:
                raise RuntimeError(f"FULL_SPAN_ANCHOR_INVALID:{role}")
            segment = tracks[index]["segments"][0]
            row = matches[0]
            segment["id"] = row["segment_id"]
            segment["target_timerange"] = {"start": row["start"], "duration": row["duration"]}

        # The pinned white-frame material arrives from CapCut with an online
        # cache path.  The template archive already carries its portable copy;
        # bind that copy explicitly before generic path scrubbing can blank it.
        white_segments = tracks[TRACK_INDEX["SCREEN_WHITE"]]["segments"]
        if white_segments:
            white_resource = "transparent_center_white_1080x1920.png"
            white_asset = media / white_resource
            if not white_asset.is_file():
                raise RuntimeError("PINNED_WHITE_ASSET_MISSING")
            white_material = material_map[white_segments[0]["material_id"]]
            white_material["name"] = white_resource
            white_material["path"] = _portable_resource_path(
                draft_prefix, f"Resources/media/{white_resource}"
            )
            white_material["media_path"] = ""
            white_material["role"] = "SCREEN_WHITE"
            white_material["desc"] = "001short production SCREEN_WHITE"

        for key in ("T2", "T1"):
            index = TRACK_INDEX[key]
            segment = tracks[index]["segments"][0]
            segment["id"] = _approved_id(config, approved, key)
            row = approved_by_id[segment["id"]]
            if row.get("text") != config[key] or not config[key].strip():
                raise RuntimeError(f"TITLE_PLAN_AUTHORITY_MISMATCH:{key}")
            _set_text(material_map[segment["material_id"]], row["text"], key)
            segment["target_timerange"] = {"start": row["start"], "duration": row["duration"]}

        state_templates = {}
        for effect, index in STATE_TRACK_BY_EFFECT.items():
            if index not in seed_segments:
                raise RuntimeError("STATE_TEMPLATE_SEGMENT_MISSING")
            seed = copy.deepcopy(seed_segments[index])
            seed_material = material_map.get(seed.get("material_id"))
            if seed_material is None:
                raise RuntimeError("STATE_TEMPLATE_MATERIAL_MISSING")
            parent = _material_parent(payload["materials"], seed_material["id"])
            if parent is None:
                raise RuntimeError("STATE_MATERIAL_CONTAINER_MISSING")
            state_templates[effect] = (index, seed, seed_material, parent)
        for cue_index, cue in enumerate(config["state_cues"]):
            segment_id = cue.get("segment_id") or _approved_id(config, approved, "STATE", cue_index)
            approved_row = approved_by_id.get(segment_id)
            if (
                approved_row is None or approved_row.get("role") != "STATE"
                or approved_row.get("start") != cue["start_us"]
                or approved_row.get("duration") != cue["end_us"] - cue["start_us"]
            ):
                raise RuntimeError(f"STATE_CUE_AUTHORITY_MISMATCH:{segment_id}")
            effect = approved_row.get("state_effect")
            if effect not in state_templates:
                raise RuntimeError(f"STATE_EFFECT_INVALID:{segment_id}")
            track_index, seed, seed_material, parent = state_templates[effect]
            segment = copy.deepcopy(seed)
            material = copy.deepcopy(seed_material)
            material_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{config['episode_id']}:state-material:{cue_index}"))
            segment["id"] = segment_id
            segment["material_id"] = material_id
            segment["role"] = "STATE"
            segment["target_timerange"] = {
                "start": cue["start_us"], "duration": cue["end_us"] - cue["start_us"]
            }
            material["id"] = material_id
            _set_text(material, cue["text"], "STATE")
            material["state_effect"] = effect
            parent.append(material)
            material_map[material_id] = material
            tracks[track_index]["segments"].append(segment)

        # Speaker utterances are generated only on their approved color lane.
        for color, track_index in A10_TEXT_TRACK_BY_COLOR.items():
            rows = [row for row in approved if row.get("role") == "A10_TEXT" and row.get("color_role") == color]
            if not rows:
                continue
            original = seed_segments.get(track_index)
            if original is None:
                raise RuntimeError(f"A10_TEXT_TEMPLATE_SEGMENT_MISSING:{color}")
            original_material = material_map.get(original.get("material_id"))
            if original_material is None:
                raise RuntimeError(f"A10_TEXT_TEMPLATE_MATERIAL_MISSING:{color}")
            parent = _material_parent(payload["materials"], original_material["id"])
            if parent is None:
                raise RuntimeError(f"A10_TEXT_MATERIAL_CONTAINER_MISSING:{color}")
            generated = []
            for row_index, row in enumerate(rows):
                segment = copy.deepcopy(original)
                material = copy.deepcopy(original_material)
                material_id = str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{config['episode_id']}:a10-text:{color}:{document_index}:{row_index}",
                ))
                segment.update({
                    "id": row["segment_id"], "material_id": material_id,
                    "role": "A10_TEXT",
                    "target_timerange": {"start": row["start"], "duration": row["duration"]},
                })
                material["id"] = material_id
                _set_text(material, row["text"], "A10_TEXT")
                material["color_role"] = color
                material["speaker_id"] = row["speaker_id"]
                parent.append(material)
                material_map[material_id] = material
                generated.append(segment)
            tracks[track_index]["segments"] = generated

        if build_a9:
            assert a9_text_template_segment is not None and a9_text_template_material is not None
            assert a9_text_parent is not None and a9_template_segment is not None
            assert a9_template_material is not None and a9_parent is not None
            captions, tts_segments = [], []
            cues = config.get("tts_cues")
            if not isinstance(cues, list) or not cues:
                raise RuntimeError("TTS_CUES_REQUIRED")
            for cue_index, cue in enumerate(cues):
                cue_id = str(cue.get("cue_id") or f"TTS_{cue_index + 1:02d}")
                text = cue.get("text")
                audio_path = Path(str(cue.get("audio_path", "")))
                resource_name = str(cue.get("resource_name") or f"tts_{cue_index + 1:02d}.wav")
                start_us, end_us = cue.get("target_range_us", [None, None])
                if (
                    not isinstance(text, str) or not text.strip() or not audio_path.is_file()
                    or not isinstance(start_us, int) or not isinstance(end_us, int) or end_us <= start_us
                ):
                    raise RuntimeError(f"TTS_CUE_INVALID:{cue_id}")
                tts_row = approved_by_id.get(_approved_id(config, approved, "A9", cue_index))
                text_row = approved_by_id.get(_approved_id(config, approved, "A9_TEXT", cue_index))
                if (
                    tts_row is None or text_row is None or tts_row.get("start") != start_us
                    or text_row.get("start") != start_us or tts_row.get("duration") != end_us - start_us
                    or text_row.get("duration") != end_us - start_us
                ):
                    raise RuntimeError(f"TTS_CUE_AUTHORITY_MISMATCH:{cue_id}")
                shutil.copy2(audio_path, media / resource_name)
                text_material_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{config['episode_id']}:a9-text:{document_index}:{cue_index}"))
                audio_material_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{config['episode_id']}:a9-audio:{document_index}:{cue_index}"))
                text_material = copy.deepcopy(a9_text_template_material)
                audio_material = copy.deepcopy(a9_template_material)
                text_material["id"] = text_material_id
                audio_material["id"] = audio_material_id
                _set_text(text_material, text, "A9_TEXT")
                _set_media(
                    audio_material, media_type="audio",
                    portable_path=_portable_resource_path(draft_prefix, f"Resources/media/{resource_name}"),
                    role="A9", duration_us=end_us - start_us,
                )
                a9_text_parent.append(text_material)
                a9_parent.append(audio_material)
                material_map[text_material_id] = text_material
                material_map[audio_material_id] = audio_material
                caption = copy.deepcopy(a9_text_template_segment)
                caption["id"] = _approved_id(config, approved, "A9_TEXT", cue_index)
                caption["material_id"] = text_material_id
                caption["role"] = "A9_TEXT"
                caption["target_timerange"] = {"start": start_us, "duration": end_us - start_us}
                sound = copy.deepcopy(a9_template_segment)
                sound["id"] = _approved_id(config, approved, "A9", cue_index)
                sound["material_id"] = audio_material_id
                sound["role"] = "A9"
                sound["target_timerange"] = {"start": start_us, "duration": end_us - start_us}
                sound["source_timerange"] = {"start": 0, "duration": end_us - start_us}
                captions.append(caption)
                tts_segments.append(sound)
            tracks[TRACK_INDEX["A9_TEXT"]]["segments"] = captions
            tracks[TRACK_INDEX["A9"]]["segments"] = tts_segments
            if not keep_a10:
                tracks[TRACK_INDEX["A10"]]["segments"] = []
        if keep_a10:
            # The A10 template seed must be captured before generated lanes are
            # cleared.  v2 pins A10 at physical track 12.
            base_a10_segment = seed_segments.get(TRACK_INDEX["A10"])
            if base_a10_segment is None:
                raise RuntimeError("PINNED_A10_TEMPLATE_SEGMENT_MISSING")
            a10_material = material_map[base_a10_segment["material_id"]]
            _set_media(
                a10_material, media_type="audio",
                portable_path=_portable_resource_path(draft_prefix, f"Resources/media/{audio_name}"),
                role="A10", duration_us=duration,
            )
            a10_material["name"] = audio_name
            a10_segments = []
            for audio_index, audio_plan in enumerate(build_manifest["source_audio"]):
                if audio_plan.get("mode") not in {"on", "duck"}:
                    continue
                # A10 plays the reordered stem, whose length equals the final
                # timeline (STAGE07_AUTHORITY_MISMATCH already enforces that), so
                # its source range is the target range - not the original media's.
                capcut_source_range = audio_plan.get(
                    "capcut_source_range_us", audio_plan["target_range_us"]
                )
                a10_segment = copy.deepcopy(base_a10_segment)
                a10_segment["id"] = _approved_id(config, approved, "A10", audio_index)
                a10_segment["role"] = "A10"
                a10_segment["volume"] = 0.0 if audio_plan["mode"] == "duck" else 1.0
                a10_segment["target_timerange"] = {
                    "start": audio_plan["target_range_us"][0],
                    "duration": audio_plan["target_range_us"][1] - audio_plan["target_range_us"][0],
                }
                a10_segment["source_timerange"] = {
                    "start": capcut_source_range[0],
                    "duration": capcut_source_range[1] - capcut_source_range[0],
                }
                a10_segments.append(a10_segment)
            tracks[TRACK_INDEX["A10"]]["segments"] = a10_segments
        tracks[TRACK_INDEX["A11"]]["segments"] = []
        tracks[A12_INDEX]["segments"] = []
        _remove_material_ids(payload["materials"], empty_audio_material_ids)
        for material_id in empty_audio_material_ids:
            material_map.pop(material_id, None)

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
    assert_a12_empty(actual)
    expected = sorted([
        {key: row[key] for key in ("segment_id", "role", "start", "duration")}
        for row in approved
    ], key=lambda row: (row["start"], row["segment_id"]))
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


def _stage_prerequisites(config: dict, episode: Path, source_rows: list[dict]) -> dict:
    del source_rows
    episode_id = config["episode_id"]
    visual = config["_visual_input"]
    video_input = Path(visual["video_input_path"]).resolve()
    duration = config["duration_us"]
    width, height = _video_dimensions(video_input)
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

    build_manifest_path = Path(config["build_manifest_path"]).resolve()
    prebuild = validate_prebuild.validate_prebuild(build_manifest_path)
    if prebuild["status"] != "PASS":
        raise RuntimeError(f"STAGE08_PREBUILD:{prebuild}")
    build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    if (
        build_manifest.get("episode_id") != episode_id
        or build_manifest["source"].get("sha256", "").lower()
        != stored_evidence["source_media_sha256"].lower()
        or build_manifest.get("visual_asset_mode") != visual["visual_asset_mode"]
        or Path(build_manifest["source"]["path"]).resolve()
        != Path(stored_evidence["source_media_path"]).resolve()
        or Path(build_manifest["template"]["root_zip_path"]).resolve()
        != Path(config["template_zip"]).resolve()
        or build_manifest["template"]["root_zip_sha256"].lower()
        != _sha(Path(config["template_zip"])).lower()
    ):
        raise RuntimeError("STAGE08_BUILD_MANIFEST_AUTHORITY_MISMATCH")
    if visual["visual_asset_mode"] == "SOURCE_VIDEO_PROVISIONAL":
        if video_input != Path(stored_evidence["source_media_path"]).resolve():
            raise RuntimeError("STAGE08_SOURCE_PROVISIONAL_AUTHORITY_MISMATCH")
    else:
        clean_source = build_manifest.get("clean_source", {})
        if (
            Path(clean_source.get("output_path", "")).resolve() != video_input
            or str(clean_source.get("output_sha256", "")).lower() != _sha(video_input).lower()
        ):
            raise RuntimeError("STAGE08_BUILD_MANIFEST_AUTHORITY_MISMATCH")
        clean_root = Path(config.get("clean_asset_root", episode / "40_assets_used")).resolve()
        clean_evidence_root = Path(config.get("clean_evidence_root", clean_root)).resolve()
        try:
            video_input.relative_to(clean_root)
        except ValueError:
            raise RuntimeError("STAGE06_CLEAN_OUTPUT_OUTSIDE_ASSET_ROOT") from None
        clean_manifest = clean_evidence_root / "clean_visual_manifest.json"
        clean_receipt = clean_evidence_root / "clean_visual_receipt.json"
        if not clean_manifest.is_file() or not clean_receipt.is_file():
            raise RuntimeError("STAGE06_EVIDENCE_MISSING")
        clean = validate_clean_visual.validate_clean_visual(clean_manifest, source_identity, design_evidence)
        clean_manifest_payload = read_json(clean_manifest)
        stored_clean_receipt = read_json(clean_receipt)
        expected_receipt = clean.get("evidence", {})
        if clean["status"] != "PASS" or stored_clean_receipt.get("status") != "PASS" or any(
            stored_clean_receipt.get(field) != expected_receipt.get(field)
            for field in expected_receipt
        ):
            raise RuntimeError("STAGE06_RECEIPT_AUTHORITY_MISMATCH")
        if (
            clean_manifest_payload.get("clean_source_origin") != clean_source.get("origin")
            or clean_manifest_payload.get("fallback_reason") != clean_source.get("fallback_reason")
            or clean_manifest_payload.get("clean_source_sha256", "").lower()
            != str(clean_source.get("output_sha256", "")).lower()
        ):
            raise RuntimeError("STAGE06_CLEAN_SOURCE_ORIGIN_MISMATCH")

    state_path = Path(config["state_path"]).resolve()
    state = read_json(state_path)
    expected_state = "CAPCUT_STATIC_VALIDATED" if config.get("_clean_swap_from_provisional") else "AUDIO_CAPTION_VALIDATED"
    if state.get("episode_id") != episode_id or state.get("status") != expected_state:
        raise RuntimeError(
            "STAGE08_STATE_INVALID:"
            f"expected episode_id={episode_id} status={expected_state},"
            f" got episode_id={state.get('episode_id')} status={state.get('status')}"
        )
    audio_lock = resolved_declared_path(state_path, state.get("audio_lock_path", ""))
    caption_lock = resolved_declared_path(state_path, state.get("caption_lock_path", ""))
    if (
        not audio_lock.is_file() or not caption_lock.is_file()
        or _sha(audio_lock).lower() != str(state.get("audio_lock_sha256", "")).lower()
        or _sha(caption_lock).lower() != str(state.get("caption_lock_sha256", "")).lower()
    ):
        raise RuntimeError("STAGE07_EVIDENCE_MISSING")
    audio = validate_audio_caption.validate_audio_caption(audio_lock, caption_lock)
    if audio["status"] != "PASS":
        raise RuntimeError(f"STAGE07:{audio}")
    audio_payload = json.loads(audio_lock.read_text(encoding="utf-8"))
    caption_payload = json.loads(caption_lock.read_text(encoding="utf-8"))
    final_srt = resolved_declared_path(caption_lock, caption_payload["final_srt_path"])
    audio_source = resolved_declared_path(audio_lock, audio_payload["audio_path"])
    if (
        audio_payload.get("episode_id") != episode_id
        or audio_payload.get("audio_sha256") != _sha(audio_source)
        or audio_payload.get("measured_duration_us") != duration
        or caption_payload.get("episode_id") != episode_id
        or not final_srt.is_file()
    ):
        raise RuntimeError("STAGE07_AUTHORITY_MISMATCH")
    # Any policy that keeps A10 must bind the primary audio to the separated stem;
    # under MIXED the generated A9 narration rides alongside it as a role file.
    if config.get("audio_policy") in A10_POLICIES and audio_payload.get("audio_source") != "SOURCE_VOCAL_STEM":
        raise RuntimeError("STAGE07_VALIDATED_VOCAL_STEM_REQUIRED")
    return {
        "source_identity": source_identity, "approved_timeline": approved_timeline,
        "design_evidence": design_evidence, "build_manifest": build_manifest,
        "audio_lock": audio_lock, "caption_lock": caption_lock, "final_srt": final_srt,
        "audio_source": audio_source, "video_input": video_input,
        "width": width, "height": height,
    }


def _build_episode_once(config: dict) -> dict:
    _ensure_media_tools()
    _validate_config(config)
    video_input = Path(config["_visual_input"]["video_input_path"])
    if not video_input.is_file():
        raise FileNotFoundError("INPUT_MEDIA_MISSING")
    episode = Path(config["episode_root"]).resolve()
    target = Path(config["local_capcut_root"]).resolve() / config["project_name"]
    if target.exists():
        raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
    episode.mkdir(parents=True, exist_ok=True)
    build_root = episode / "50_capcut_project"
    evidence_root = build_root / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    work_root = Path(config["work_root"]).resolve()
    work_root.mkdir(parents=True, exist_ok=True)
    source = _extract_template(Path(config["template_zip"]).resolve(), work_root / "source_authority")
    pre = _stage_prerequisites(config, episode, [])
    source_rows = _normalize_source(source, config, pre["audio_source"], pre["build_manifest"])
    # The protected structure snapshot includes the approved polish bindings.
    # Apply them to the extracted authority before cloning; the later target
    # application is idempotent and produces the user-facing receipt.
    apply_capcut_polish_profile.apply_project(source)
    source_polish = validate_capcut_polish_profile.validate_project(source)
    if source_polish["status"] != "PASS":
        raise RuntimeError(f"STAGE08_POLISH_SOURCE:{source_polish}")

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

    _assert_capcut_closed_for_target(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(working, target)
    cloud_prepare = _prepare_cloud_project(
        target,
        project_name=config["project_name"],
        capcut_root=target.parent,
        draft_id=draft_id,
        duration_us=config["duration_us"],
    )
    polish_receipt_path = build_root / "capcut_polish_profile_receipt.json"
    polish_receipt = apply_capcut_polish_profile.apply_project(target)
    _write_json(polish_receipt_path, polish_receipt)
    polish_validation = validate_capcut_polish_profile.validate_project(target)
    if polish_validation["status"] != "PASS":
        raise RuntimeError(f"STAGE08_POLISH:{polish_validation}")
    model = capcut_model.load_project(target)
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
        "track_layout_version": TRACK_LAYOUT,
        "root_contract_path": config["root_contract_path"],
        "workspace_root": str(Path(config["workspace_root"]).resolve()),
        "root_profile": config["root_profile"],
        "root_template_profile": config["_resolved_root_contract"]["template_profile"],
        "visual_asset_mode": config["_visual_input"]["visual_asset_mode"],
        "video_asset_key": config["_visual_input"]["video_asset_key"],
        "video_input_path": str(pre["video_input"]),
        "video_input_sha256": _sha(pre["video_input"]),
        "upload_ready": config["_visual_input"]["upload_ready"],
        "source_project_path": str(source.resolve()), "working_project_path": str(target.resolve()),
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
        "approved_role_text": {"T1": config["T1"], "T2": config["T2"]},
        "approved_segment_text": {
            row["segment_id"]: {
                "role": row["role"], "start": row["start"], "duration": row["duration"],
                "text": row["text"],
                **({"color_role": row["color_role"]} if row["role"] == "A10_TEXT" else {}),
                **({"state_effect": row["state_effect"]} if row["role"] == "STATE" else {}),
            }
            for row in _approved_rows(config)
            if row.get("role") in {"A9_TEXT", "A10_TEXT", "STATE"}
        },
        "approved_actual_order": [row["segment_id"] for row in ordered], "timeline": ordered,
        "primary_timeline_roles": ["VIDEO"], "authorized_gaps": [],
        "authorized_overlaps": [], "parallel_pairs": [],
        "subtitle_roles": ["STATE", "A9_TEXT", "A10_TEXT"],
        "caption_bindings": build_caption_bindings(config, pre["caption_lock"]),
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
        target, snapshot_path, contract_path, capcut_evidence, evidence_root
    )
    if checked["status"] != "PASS":
        if target.is_dir():
            shutil.rmtree(target)
        raise RuntimeError(f"STAGE08_VALIDATE:{checked}")
    postbuild = validate_postbuild.validate_postbuild(
        Path(config["build_manifest_path"]), target
    )
    if postbuild["status"] != "PASS":
        if target.is_dir():
            shutil.rmtree(target)
        raise RuntimeError(f"STAGE08_POSTBUILD:{postbuild}")
    _register_capcut_project(
        target,
        target.parent,
        build_root / "root_meta_info.before.json",
    )
    state_path = Path(config["state_path"]).resolve()
    state = read_json(state_path)
    state.update({
        "episode_id": config["episode_id"], "current_stage": "09",
        "status": "CAPCUT_STATIC_VALIDATED", "project_name": config["project_name"],
        "local_capcut_project_path": str(target), "stage09_user_approval": "NOT_RUN",
        "visual_asset_mode": config["_visual_input"]["visual_asset_mode"],
        "video_asset_key": config["_visual_input"]["video_asset_key"],
        "upload_ready": config["_visual_input"]["upload_ready"],
        "cloud_prepare": cloud_prepare,
        "next_action": "WAIT_USER_CAPCUT_CHECK",
    })
    report_path = build_root / "build_report.json"
    report = {
        "episode_id": config["episode_id"], "status": "CAPCUT_STATIC_VALIDATED",
        "current_stage": "09", "project_name": config["project_name"],
        "project_path": str(target),
        "media_source_path": str(pre["video_input"]),
        "visual_asset_mode": state["visual_asset_mode"],
        "video_asset_key": state["video_asset_key"],
        "upload_ready": state["upload_ready"],
        "capcut_evidence_path": str(capcut_evidence),
        "next_action": "WAIT_USER_CAPCUT_CHECK",
    }
    _write_json(report_path, report)
    _write_json(state_path, state)
    return {
        "status": state["status"], "current_stage": "09", "stage08_validation": "PASS",
        "visual_asset_mode": state["visual_asset_mode"], "upload_ready": state["upload_ready"],
        "project_path": str(target), "capcut_evidence_path": str(capcut_evidence),
        "media_source_path": str(pre["video_input"]),
        "build_report_path": str(report_path), "next_action": "WAIT_USER_CAPCUT_CHECK",
    }


def _cleanup_generated_work(work_root: Path) -> None:
    work_root = Path(work_root).resolve()
    for name in ("normalized_source", "working_project"):
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


def _assert_clean_swap_lock(config: dict, target: Path) -> None:
    raw_path = config.get("edit_lock_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise RuntimeError("CLEAN_SWAP_EDIT_LOCK_REQUIRED")
    path = Path(raw_path).resolve()
    if not path.is_file():
        raise RuntimeError("CLEAN_SWAP_EDIT_LOCK_MISSING")
    payload = read_json(path)
    if (
        payload.get("episode_id") != config["episode_id"]
        or payload.get("action") != "STAGE08_VIDEO_ONLY_SWAP"
        or Path(payload.get("project_path", "")).resolve() != target.resolve()
    ):
        raise RuntimeError("CLEAN_SWAP_EDIT_LOCK_INVALID")


def _assert_capcut_closed_for_target(target: Path) -> None:
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


def _replace_video_material_only(target: Path, clean_video: Path, duration_us: int) -> None:
    media = target / "Resources" / "media"
    media.mkdir(parents=True, exist_ok=True)
    resource_name = "clean_video.mp4"
    shutil.copy2(clean_video, media / resource_name)
    dimensions = _video_dimensions(clean_video)
    changed = 0
    for path, payload in _documents(target):
        tracks = payload["tracks"]
        if len(tracks) != len(ROLE_BY_TRACK):
            raise RuntimeError("PINNED_TRACK_LAYOUT_INVALID")
        material_map = {
            row.get("id"): row for row in _materials(payload.get("materials", {}))
            if isinstance(row.get("id"), str)
        }
        video_ids = {
            segment.get("material_id") for segment in tracks[TRACK_INDEX["VIDEO"]].get("segments", [])
            if isinstance(segment.get("material_id"), str)
        }
        if not video_ids:
            raise RuntimeError("CLEAN_SWAP_VIDEO_MATERIAL_MISSING")
        prefix = _draft_path_prefix(target)
        for material_id in video_ids:
            material = material_map.get(material_id)
            if material is None:
                raise RuntimeError("CLEAN_SWAP_VIDEO_MATERIAL_MISSING")
            _set_media(
                material, media_type="video",
                portable_path=_portable_resource_path(prefix, f"Resources/media/{resource_name}"),
                role="VIDEO", duration_us=duration_us, dimensions=dimensions,
            )
            changed += 1
        _write_json(path, payload)
    if changed == 0:
        raise RuntimeError("CLEAN_SWAP_VIDEO_MATERIAL_MISSING")
    provisional_resource = media / "source.mp4"
    if provisional_resource.is_file():
        provisional_resource.unlink()


def swap_provisional_video_only(config: dict) -> dict:
    _ensure_media_tools()
    _validate_config(config)
    if config["visual_asset_mode"] != "CLEAN_VISUAL_READY":
        raise RuntimeError("CLEAN_SWAP_CLEAN_VISUAL_REQUIRED")
    target = Path(config["local_capcut_root"]).resolve() / config["project_name"]
    if not target.is_dir():
        raise RuntimeError("CLEAN_SWAP_PROVISIONAL_PROJECT_MISSING")
    _assert_clean_swap_lock(config, target)
    _assert_capcut_closed_for_target(target)
    episode = Path(config["episode_root"]).resolve()
    build_root = episode / "50_capcut_project"
    snapshot_path = build_root / "structure_snapshot.json"
    contract_path = build_root / "build_contract.json"
    state_path = Path(config["state_path"]).resolve()
    state = read_json(state_path)
    if (
        state.get("episode_id") != config["episode_id"]
        or state.get("status") != "CAPCUT_STATIC_VALIDATED"
        or state.get("visual_asset_mode") != "SOURCE_VIDEO_PROVISIONAL"
        or state.get("next_action") != "WAIT_USER_CAPCUT_CHECK"
    ):
        raise RuntimeError("CLEAN_SWAP_PROVISIONAL_STATE_REQUIRED")
    contract = read_json(contract_path)
    if (
        contract.get("visual_asset_mode") != "SOURCE_VIDEO_PROVISIONAL"
        or contract.get("video_asset_key") != "source_video"
        or contract.get("upload_ready") is not False
        or Path(contract.get("working_project_path", "")).resolve() != target
    ):
        raise RuntimeError("CLEAN_SWAP_PROVISIONAL_CONTRACT_REQUIRED")
    config["_clean_swap_from_provisional"] = True
    try:
        pre = _stage_prerequisites(config, episode, [])
    finally:
        config.pop("_clean_swap_from_provisional", None)
    clean_video = Path(pre["video_input"]).resolve()
    _replace_video_material_only(target, clean_video, config["duration_us"])
    contract.update({
        "visual_asset_mode": "CLEAN_VISUAL_READY",
        "video_asset_key": "clean_video",
        "video_input_path": str(clean_video),
        "video_input_sha256": _sha(clean_video),
        "upload_ready": False,
        "build_manifest_path": str(Path(config["build_manifest_path"]).resolve()),
        "build_manifest_sha256": _sha(Path(config["build_manifest_path"]).resolve()),
    })
    contract["required_asset_paths"] = [
        "Resources/media/clean_video.mp4" if path.endswith("/source.mp4") else path
        for path in contract["required_asset_paths"]
    ]
    contract["build_inputs_receipt_sha256"] = "0" * 64
    _write_json(contract_path, contract)
    inputs = validate_build_inputs.validate_build_inputs(
        Path(contract["caption_lock_path"]), Path(contract["final_srt_path"]), contract_path,
        Path(contract["approved_timeline_path"]),
    )
    if inputs["status"] != "PASS":
        raise RuntimeError(f"CLEAN_SWAP_INPUTS:{inputs}")
    receipt_path = Path(contract["build_inputs_receipt_path"])
    _write_json(receipt_path, inputs)
    contract["build_inputs_receipt_sha256"] = _sha(receipt_path)
    _write_json(contract_path, contract)
    _prepare_cloud_project(
        target, project_name=config["project_name"], capcut_root=target.parent,
        draft_id=contract["draft_id"], duration_us=config["duration_us"],
    )
    evidence_root = build_root / "evidence"
    capcut_evidence = evidence_root / "capcut_project_evidence.json"
    if capcut_evidence.exists():
        if not capcut_evidence.is_file() or capcut_evidence.parent.resolve() != evidence_root.resolve():
            raise RuntimeError("UNSAFE_PREVIOUS_CAPCUT_EVIDENCE")
        capcut_evidence.unlink()
    checked = validate_capcut_project.validate_capcut_project(
        target, snapshot_path, contract_path, capcut_evidence, evidence_root
    )
    if checked["status"] != "PASS":
        raise RuntimeError(f"CLEAN_SWAP_VALIDATE:{checked}")
    postbuild = validate_postbuild.validate_postbuild(Path(config["build_manifest_path"]), target)
    if postbuild["status"] != "PASS":
        raise RuntimeError(f"CLEAN_SWAP_POSTBUILD:{postbuild}")
    state.update({
        "current_stage": "09", "status": "CAPCUT_STATIC_VALIDATED",
        "visual_asset_mode": "CLEAN_VISUAL_READY", "video_asset_key": "clean_video",
        "upload_ready": False, "stage09_user_approval": "NOT_RUN",
        "next_action": "WAIT_USER_CAPCUT_CHECK",
    })
    report_path = build_root / "build_report.json"
    _write_json(report_path, {
        "episode_id": config["episode_id"], "status": "CAPCUT_STATIC_VALIDATED",
        "current_stage": "09", "project_name": config["project_name"],
        "project_path": str(target), "media_source_path": str(clean_video),
        "visual_asset_mode": "CLEAN_VISUAL_READY", "video_asset_key": "clean_video",
        "upload_ready": False, "capcut_evidence_path": str(capcut_evidence),
        "next_action": "WAIT_USER_CAPCUT_CHECK",
    })
    _write_json(state_path, state)
    return {
        "status": "CAPCUT_STATIC_VALIDATED", "current_stage": "09", "stage08_validation": "PASS",
        "visual_asset_mode": "CLEAN_VISUAL_READY", "upload_ready": False,
        "project_path": str(target), "capcut_evidence_path": str(capcut_evidence),
        "media_source_path": str(clean_video), "build_report_path": str(report_path),
        "next_action": "WAIT_USER_CAPCUT_CHECK",
    }


def build_episode(config: dict) -> dict:
    _validate_config(config)
    target = Path(config["local_capcut_root"]).resolve() / config["project_name"]
    if target.exists():
        raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
    _validate_mixed_audio_modes(
        config,
        read_json(Path(config["build_manifest_path"]).resolve()),
    )
    _assert_optional_edit_lock(config)
    work_root = Path(config["work_root"]).resolve()
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
    parser.add_argument("--swap-provisional-video-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    payload = swap_provisional_video_only(config) if args.swap_provisional_video_only else build_episode(config)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
