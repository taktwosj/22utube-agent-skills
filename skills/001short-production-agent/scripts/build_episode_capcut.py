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
import validate_capcut_grids
import validate_design_lock
import validate_executable_protocol
import resolve_shorts_capcut_root
import user_provided_media_overlay
from capcut_io import iter_primary_draft_documents
from common import manifest_sha256, meaningful_text_length, read_json, resolved_declared_path, resolve_state_artifact
from track_contract import A10_TEXT_TRACK_BY_COLOR, A12_INDEX, CANONICAL_TRACKS, STATE_TRACK_BY_EFFECT, TRACK_INDEX, TRACK_LAYOUT


ROLE_BY_TRACK = list(CANONICAL_TRACKS)

# A9 carries the narration we generate; A10 carries the retained source speech.
# MIXED keeps both, so the source stem must still be present while A9 is built.
AUDIO_POLICIES = frozenset({
    "SOURCE_ORDER_CLEAN_AUDIO", "A10_RETAINED_SYNC", "A10_REASSEMBLED_SYNC",
    "TTS_ONLY_MUTE_SOURCE", "A9_TTS_PLUS_A10_RETAINED", "A9_TTS_PLUS_A10_REASSEMBLED", "CAPTION_ONLY_MUTE_SOURCE",
})
TTS_POLICIES = frozenset({"TTS_ONLY_MUTE_SOURCE", "A9_TTS_PLUS_A10_RETAINED", "A9_TTS_PLUS_A10_REASSEMBLED"})
A10_POLICIES = frozenset({"SOURCE_ORDER_CLEAN_AUDIO", "A10_RETAINED_SYNC", "A10_REASSEMBLED_SYNC", "A9_TTS_PLUS_A10_RETAINED", "A9_TTS_PLUS_A10_REASSEMBLED"})
STEM_POLICIES = A10_POLICIES - {"SOURCE_ORDER_CLEAN_AUDIO"}
SOURCE_ORDER_PRODUCTION_MODES = frozenset({
    "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_ORDER_UNCHANGED_A10_RETAINED",
})
REQUIRED_TEMPLATE_SEED_ROLES = ("VIDEO", "A9", "A10")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_grid_harness(config: dict, *, state_payload: dict | None = None) -> dict:
    forbidden_overrides = (
        "original_grid_path",
        "urakkai_grid_path",
    )
    if any(key in config for key in forbidden_overrides):
        raise ValueError("TABLE_PATH_OVERRIDE_FORBIDDEN")
    episode_value = config.get("episode_root")
    if not isinstance(episode_value, str) or not episode_value.strip():
        raise ValueError("TABLE_EPISODE_ROOT_REQUIRED")
    episode = Path(episode_value).resolve()
    original = episode / "20_script" / "original-capcut-grid.md"
    urakkai = episode / "20_script" / "urakkai-capcut-grid.md"
    # Revisions use derived state paths, but original analysis is always bound
    # to the canonical episode state resolved by the grid validator.
    validation = validate_capcut_grids.validate_grids(original, urakkai)
    if validation["status"] != "PASS":
        first = validation["errors"][0]
        details = ":".join(
            str(first[key])
            for key in ("table", "row", "column")
            if key in first
        )
        suffix = f":{details}" if details else ""
        raise ValueError(f"{first['code']}{suffix}")
    required = (
        "build_manifest_path", "approved_timeline_path", "design_lock_evidence_path", "state_path"
    )
    missing = [key for key in required if not isinstance(config.get(key), str) or not config[key].strip()]
    if missing:
        raise ValueError(f"TABLE_LOCKED_ARTIFACT_REQUIRED:{','.join(missing)}")
    state_path = Path(config["state_path"]).resolve()
    if state_payload is None and not state_path.is_file():
        raise ValueError("TABLE_LOCKED_ARTIFACT_REQUIRED:state_path")
    state = copy.deepcopy(state_payload) if state_payload is not None else read_json(state_path)
    binding_specs = {
        "approved_timeline": ("approved_timeline_path", "approved_timeline_sha256", Path(config["approved_timeline_path"]).resolve()),
        "build_manifest": ("build_manifest_path", "build_manifest_sha256", Path(config["build_manifest_path"]).resolve()),
        "design_lock_evidence": ("design_lock_evidence_path", "design_lock_evidence_sha256", Path(config["design_lock_evidence_path"]).resolve()),
        "audio_lock": ("audio_lock_path", "audio_lock_sha256", None),
        "caption_lock": ("caption_lock_path", "caption_lock_sha256", None),
    }
    artifact_paths: dict[str, Path] = {}
    for name, (path_key, sha_key, expected_path) in binding_specs.items():
        declared_value = state.get(path_key)
        declared_sha = state.get(sha_key)
        if not isinstance(declared_value, str) or not declared_value.strip() or not isinstance(declared_sha, str):
            raise ValueError(f"TABLE_STATE_LOCK_MISSING:{name}")
        declared_path = resolve_state_artifact(state_path, declared_value)
        if expected_path is not None and declared_path != expected_path:
            raise ValueError(f"TABLE_STATE_LOCK_PATH_MISMATCH:{name}")
        if not declared_path.is_file() or _sha(declared_path).lower() != declared_sha.lower():
            raise ValueError(f"TABLE_STATE_LOCK_SHA_MISMATCH:{name}")
        artifact_paths[name] = declared_path
    semantic_errors = validate_capcut_grids.validate_locked_assembly(
        validation,
        read_json(artifact_paths["build_manifest"]),
        read_json(artifact_paths["approved_timeline"]),
        read_json(artifact_paths["audio_lock"]),
        read_json(artifact_paths["caption_lock"]),
    )
    if semantic_errors:
        first = semantic_errors[0]
        details = ":".join(
            str(first[key]) for key in ("table", "row", "column") if key in first
        )
        suffix = f":{details}" if details else ""
        raise ValueError(f"{first['code']}{suffix}")
    audio_payload = read_json(artifact_paths["audio_lock"])
    caption_payload = read_json(artifact_paths["caption_lock"])
    if audio_payload.get("schema_version") != "001short-audio-lock-v4":
        raise ValueError("AUDIO_LOCK_MIGRATION_REQUIRED")
    if caption_payload.get("schema_version") != "001short-caption-lock-v2":
        raise ValueError("CAPTION_LOCK_MIGRATION_REQUIRED")
    timing_path = resolved_declared_path(
        artifact_paths["caption_lock"],
        str(caption_payload.get("caption_timing_evidence_path", "")),
    )
    try:
        timing_payload = read_json(timing_path)
    except (OSError, TypeError, ValueError):
        raise ValueError("CAPTION_TIMING_EVIDENCE_MIGRATION_REQUIRED") from None
    if timing_payload.get("schema_version") != "001short-caption-timing-evidence-v2":
        raise ValueError("CAPTION_TIMING_EVIDENCE_MIGRATION_REQUIRED")
    for name in ("production_plan", "production_plan_validation_receipt"):
        path_key, sha_key = f"{name}_path", f"{name}_sha256"
        declared = state.get(path_key)
        expected_sha = state.get(sha_key)
        if not isinstance(declared, str) or not declared or not isinstance(expected_sha, str):
            raise ValueError(f"TABLE_STATE_LOCK_MISSING:{name}")
        bound_path = resolve_state_artifact(state_path, declared)
        if not bound_path.is_file() or _sha(bound_path).lower() != expected_sha.lower():
            raise ValueError(f"TABLE_STATE_LOCK_SHA_MISMATCH:{name}")
        artifact_paths[name] = bound_path
    production_plan = read_json(artifact_paths["production_plan"])
    if production_plan.get("schema_version") != "001short-production-plan-v2":
        raise ValueError("PRODUCTION_PLAN_MIGRATION_REQUIRED")
    if validate_executable_protocol.validate_production_plan(
        production_plan, validate_executable_protocol.load_protocol()
    ):
        raise ValueError("PRODUCTION_PLAN_VALIDATION_RECEIPT_INVALID")
    receipt = read_json(artifact_paths["production_plan_validation_receipt"])
    receipt_evidence = receipt.get("evidence", {})
    if (
        receipt.get("status") != "PASS"
        or receipt.get("errors") != []
        or os.path.realpath(str(receipt_evidence.get("production_plan_path", "")))
        != os.path.realpath(str(artifact_paths["production_plan"]))
        or str(receipt_evidence.get("production_plan_sha256", "")).lower()
        != _sha(artifact_paths["production_plan"]).lower()
    ):
        raise ValueError("PRODUCTION_PLAN_VALIDATION_RECEIPT_INVALID")
    design_required = ("source_identity_path", "design_handoff_path")
    design_missing = [
        key for key in design_required
        if not isinstance(config.get(key), str) or not config[key].strip()
    ]
    if design_missing:
        raise ValueError(f"TABLE_DESIGN_LOCK_REQUIRED:{','.join(design_missing)}")
    design_result = validate_design_lock.validate_handoff(
        Path(config["design_handoff_path"]).resolve(),
        Path(config["source_identity_path"]).resolve(),
        artifact_paths["approved_timeline"],
    )
    if design_result["status"] != "PASS":
        first_code = design_result["errors"][0]["code"] if design_result.get("errors") else "UNKNOWN"
        raise ValueError(f"TABLE_DESIGN_LOCK_INVALID:{first_code}")
    audio_caption = validate_audio_caption.validate_audio_caption(
        artifact_paths["audio_lock"], artifact_paths["caption_lock"],
        expected_production_plan_path=artifact_paths["production_plan"],
        expected_production_plan_sha256=state["production_plan_sha256"],
        expected_production_plan_receipt_path=artifact_paths["production_plan_validation_receipt"],
        expected_production_plan_receipt_sha256=state["production_plan_validation_receipt_sha256"],
    )
    if audio_caption["status"] != "PASS":
        first_code = audio_caption["errors"][0]["code"] if audio_caption.get("errors") else "UNKNOWN"
        raise ValueError(f"TABLE_AUDIO_CAPTION_LOCK_INVALID:{first_code}")
    validation["locked_assembly"] = "PASS"
    return validation


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


def _validate_template_track_layout(template_zip: Path) -> None:
    """Preflight every primary draft in the pinned archive without writing files."""
    try:
        with zipfile.ZipFile(template_zip) as archive:
            root_candidates = []
            for name in archive.namelist():
                parts = name.replace("\\", "/").split("/")
                if parts[-1] == "draft_content.json" and "Timelines" not in parts and "subdraft" not in parts:
                    root_candidates.append(name)
            if len(root_candidates) != 1:
                raise RuntimeError(f"PINNED_TEMPLATE_ROOT_AMBIGUOUS:{len(root_candidates)}")
            root_name = root_candidates[0]
            root_parent = root_name.replace("\\", "/").split("/")[:-1]
            timeline_candidates = []
            for name in archive.namelist():
                parts = name.replace("\\", "/").split("/")
                if (
                    parts[:len(root_parent)] == root_parent
                    and len(parts) == len(root_parent) + 3
                    and parts[len(root_parent)] == "Timelines"
                    and parts[-1] == "draft_content.json"
                ):
                    timeline_candidates.append(name)
            if not timeline_candidates:
                raise RuntimeError("PINNED_TEMPLATE_TIMELINE_MISSING")
            documents = [
                (name, json.loads(archive.read(name).decode("utf-8")))
                for name in [root_name, *sorted(timeline_candidates)]
            ]
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("PINNED_TEMPLATE_ROOT_INVALID") from exc
    for _name, payload in documents:
        tracks = payload.get("tracks") if isinstance(payload, dict) else None
        if (
            not isinstance(tracks, list) or len(tracks) != len(ROLE_BY_TRACK)
            or any(
                not isinstance(track, dict)
                or not isinstance(track.get("id"), str)
                or not isinstance(track.get("segments"), list)
                for track in tracks
            )
        ):
            raise RuntimeError("PINNED_TRACK_LAYOUT_INVALID")
        material_map = {
            row.get("id"): row for row in _materials(payload.get("materials", {}))
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
        for role in REQUIRED_TEMPLATE_SEED_ROLES:
            segments = tracks[TRACK_INDEX[role]]["segments"]
            if (
                not segments or not isinstance(segments[0], dict)
                or not isinstance(segments[0].get("id"), str)
                or not isinstance(segments[0].get("material_id"), str)
            ):
                raise RuntimeError(f"PINNED_TEMPLATE_ANCHOR_MISSING:{role}")
            if segments[0]["material_id"] not in material_map:
                raise RuntimeError(f"PINNED_TEMPLATE_MATERIAL_MISSING:{role}")


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
    if mode == "USER_APPROVED_NONMATCHING_CLEAN_SOURCE":
        raw = config.get("clean_video")
        raw_override = config.get("user_clean_override_path")
        if not isinstance(raw, str) or not raw:
            raise ValueError("USER_CLEAN_VIDEO_REQUIRED")
        if not isinstance(raw_override, str) or not raw_override:
            raise ValueError("USER_CLEAN_OVERRIDE_REQUIRED")
        video = Path(raw).resolve()
        override_path = Path(raw_override).resolve()
        if not video.is_file():
            raise FileNotFoundError("USER_CLEAN_VIDEO_MISSING")
        try:
            override = read_json(override_path)
        except (OSError, ValueError, TypeError) as exc:
            raise RuntimeError(f"USER_CLEAN_OVERRIDE_INVALID:{exc}") from exc
        authority = override.get("user_authority")
        declared_video = resolved_declared_path(
            override_path, override.get("episode_clean_source_path", "")
        )
        if (
            override.get("schema_version") != "001short-user-clean-override-v1"
            or override.get("episode_id") != config.get("episode_id")
            or override.get("status") != mode
            or not isinstance(authority, dict)
            or not isinstance(authority.get("evidence"), str)
            or not authority["evidence"].strip()
            or not isinstance(authority.get("exact_text"), str)
            or not authority["exact_text"].strip()
            or declared_video != video
            or str(override.get("clean_source_sha256", "")).lower() != _sha(video).lower()
            or override.get("clean_visual_ready_claim") is not False
        ):
            raise RuntimeError("USER_CLEAN_OVERRIDE_AUTHORITY_INVALID")
        return {
            "visual_asset_mode": mode,
            "video_asset_key": "user_approved_clean_video",
            "video_input_path": video,
            "video_input_sha256": _sha(video),
            "resource_name": "clean_video.mp4",
            "upload_ready": False,
            "user_clean_override_path": override_path,
            "user_clean_override_sha256": _sha(override_path),
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
            or len(cue["text"].splitlines()) > 2
            or any(meaningful_text_length(line) > 15 for line in cue["text"].splitlines())
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
    locked_cues = {str(cue.get("cue_id")) for cue in cues}
    if used_cues != locked_cues:
        raise RuntimeError("CAPTION_LOCK_CUE_UNASSEMBLED")
    return bindings


def assert_a12_empty(segments: list[dict]) -> None:
    if any(row.get("role") in {"A12", "A12_RESERVED_EMPTY"} for row in segments):
        raise RuntimeError("A12_RESERVED_EMPTY")


REVISION_ID_PATTERN = re.compile(r"v[1-9][0-9]*\Z")
REVISION_SWAP_OVERRIDE_KEYS = frozenset({
    "visual_asset_mode", "clean_video", "clean_asset_root", "clean_evidence_root",
    "edit_lock_path",
})


def prepare_revision_config(config: dict) -> None:
    """Resolve an optional rebuild revision without touching legacy builds."""
    revision_id = config.get("revision_id")
    if revision_id is None:
        return
    if not isinstance(revision_id, str) or not REVISION_ID_PATTERN.fullmatch(revision_id):
        raise ValueError("REVISION_ID_INVALID")
    episode = Path(config["episode_root"]).resolve()
    canonical_state = episode / "90_workflow" / "state.json"
    revision_state = episode / "90_workflow" / "revisions" / revision_id / "state.json"
    configured_state = config.get("state_path")
    if configured_state:
        resolved_state = Path(configured_state).resolve()
        if resolved_state not in {canonical_state, revision_state}:
            raise ValueError("REVISION_STATE_PATH_INVALID")
    project_name = config.get("project_name")
    if not isinstance(project_name, str) or not project_name.strip():
        raise ValueError("REVISION_PROJECT_NAME_INVALID")
    base_project_name = re.sub(r"_v[1-9][0-9]*$", "", project_name)
    build_root = episode / "50_capcut_project" / "revisions" / revision_id
    config.update({
        "state_path": str(revision_state),
        "work_root": str(build_root / "build_work"),
        "project_name": f"{base_project_name}_{revision_id}",
        "_revision_context": {
            "revision_id": revision_id,
            "canonical_state_path": str(canonical_state),
            "build_root": str(build_root),
        },
    })


def _revision_snapshot_path(config: dict) -> Path | None:
    context = config.get("_revision_context")
    if not isinstance(context, dict):
        return None
    return Path(config["state_path"]).resolve().with_name("build_config.json")


def _revision_snapshot_payload(config: dict) -> dict:
    return {
        key: copy.deepcopy(value)
        for key, value in config.items()
        if not key.startswith("_")
    }


def bind_revision_snapshot(config: dict, *, operation: str) -> None:
    """Verify a revision's immutable config or load it for an allowed swap."""
    snapshot_path = _revision_snapshot_path(config)
    if snapshot_path is None:
        return
    state_path = Path(config["state_path"]).resolve()
    if not snapshot_path.exists():
        if state_path.exists():
            raise RuntimeError("REVISION_CONFIG_SNAPSHOT_MISSING")
        return
    if not snapshot_path.is_file() or not state_path.is_file():
        raise RuntimeError("REVISION_CONFIG_BINDING_MISSING")
    state = read_json(state_path)
    if (
        Path(state.get("build_config_path", "")).resolve() != snapshot_path
        or state.get("build_config_sha256") != _sha(snapshot_path)
    ):
        raise RuntimeError("REVISION_CONFIG_BINDING_INVALID")
    snapshot = read_json(snapshot_path)
    observed = _revision_snapshot_payload(config)
    if operation == "build":
        if observed != snapshot:
            raise ValueError("REVISION_CONFIG_DRIFT")
    elif operation == "swap":
        overrides = {
            key: copy.deepcopy(config[key])
            for key in REVISION_SWAP_OVERRIDE_KEYS
            if key in config
        }
        config.clear()
        config.update(copy.deepcopy(snapshot))
        config.update(overrides)
        prepare_revision_config(config)
    else:
        raise ValueError("REVISION_OPERATION_INVALID")


def prepare_revision_state_payload(config: dict) -> tuple[dict, dict] | None:
    """Build a fresh revision state and config snapshot without filesystem writes."""
    context = config.get("_revision_context")
    if not isinstance(context, dict):
        return None
    revision_state = Path(config["state_path"]).resolve()
    if revision_state.exists():
        if not _revision_snapshot_path(config).is_file():
            raise RuntimeError("REVISION_CONFIG_SNAPSHOT_MISSING")
        return read_json(revision_state), read_json(_revision_snapshot_path(config))
    canonical_state = Path(context["canonical_state_path"]).resolve()
    if not canonical_state.is_file():
        raise RuntimeError("REVISION_SOURCE_STATE_MISSING")
    source_state = read_json(canonical_state)
    if source_state.get("episode_id") != config["episode_id"]:
        raise RuntimeError("REVISION_SOURCE_STATE_EPISODE_MISMATCH")
    state = copy.deepcopy(source_state)
    for key in ("local_capcut_project_path", "cloud_prepare", "video_asset_key", "upload_ready"):
        state.pop(key, None)
    for key in (
        "approved_timeline_path", "build_manifest_path", "design_lock_evidence_path",
        "audio_lock_path", "caption_lock_path", "production_plan_path",
        "production_plan_validation_receipt_path",
    ):
        value = state.get(key)
        if isinstance(value, str) and value:
            state[key] = str(resolve_state_artifact(canonical_state, value))
    for name, config_key in (
        ("approved_timeline", "approved_timeline_path"),
        ("build_manifest", "build_manifest_path"),
        ("design_lock_evidence", "design_lock_evidence_path"),
    ):
        raw_path = config.get(config_key)
        if not isinstance(raw_path, str) or not raw_path:
            continue
        path = Path(raw_path).resolve()
        state[f"{name}_path"] = str(path)
        state[f"{name}_sha256"] = _sha(path)
    state.update({
        "episode_id": config["episode_id"],
        "revision_id": context["revision_id"],
        "current_stage": "08",
        "status": "AUDIO_CAPTION_VALIDATED",
        "project_name": config["project_name"],
        "stage09_user_approval": "NOT_RUN",
        "next_action": "CAPCUT_BUILD",
    })
    snapshot_path = _revision_snapshot_path(config)
    snapshot = _revision_snapshot_payload(config)
    state["build_config_path"] = str(snapshot_path)
    return state, snapshot


def initialize_revision_state(
    config: dict, prepared: tuple[dict, dict] | None = None,
) -> None:
    """Persist a validated fresh revision state and immutable config snapshot."""
    context = config.get("_revision_context")
    if not isinstance(context, dict):
        return
    revision_state = Path(config["state_path"]).resolve()
    if revision_state.exists():
        if not _revision_snapshot_path(config).is_file():
            raise RuntimeError("REVISION_CONFIG_SNAPSHOT_MISSING")
        return
    payload = prepared if prepared is not None else prepare_revision_state_payload(config)
    if payload is None:
        return
    state, snapshot = payload
    snapshot_path = _revision_snapshot_path(config)
    _write_json(snapshot_path, snapshot)
    state["build_config_sha256"] = _sha(snapshot_path)
    _write_json(revision_state, state)


def _build_root(config: dict, episode: Path) -> Path:
    context = config.get("_revision_context")
    if isinstance(context, dict):
        return Path(context["build_root"]).resolve()
    return episode / "50_capcut_project"


def _validate_config(config: dict, *, revision_operation: str = "build") -> None:
    prepare_revision_config(config)
    _bind_portable_root_contract(config)
    bind_revision_snapshot(config, operation=revision_operation)
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
    episode = Path(config["episode_root"]).resolve()
    canonical_state = episode / "90_workflow" / "state.json"
    context = config.get("_revision_context")
    expected_state = (
        episode / "90_workflow" / "revisions" / context["revision_id"] / "state.json"
        if isinstance(context, dict)
        else canonical_state
    )
    if Path(config["state_path"]).resolve() != expected_state:
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


def _remove_extra_material_ref_types(
    segment: dict, material_map: dict[str, dict], forbidden_types: set[str]
) -> None:
    def forbidden(material_id: object) -> bool:
        return (
            isinstance(material_id, str)
            and isinstance(material_map.get(material_id), dict)
            and material_map[material_id].get("type") in forbidden_types
        )

    def scrub(value: object) -> object:
        if isinstance(value, list):
            return [scrub(child) for child in value if not forbidden(child)]
        if not isinstance(value, dict):
            return value
        cleaned = {}
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized == "material_id" or normalized.endswith("_material_id"):
                if forbidden(child):
                    continue
                if isinstance(child, list):
                    cleaned[key] = [item for item in child if not forbidden(item)]
                else:
                    cleaned[key] = child
            else:
                cleaned[key] = scrub(child)
        return cleaned

    reference_keys = {
        "effects", "effect", "animations", "animation", "transition", "transitions",
        "extra_material_refs", "extra_material_ids",
    }
    for key in list(segment):
        normalized = str(key).lower()
        if normalized in reference_keys or "material_ref" in normalized:
            segment[key] = scrub(segment[key])


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
    else:
        # CapCut's UI-created local-audio schema uses extract_music plus a
        # draft_meta_info local-material row.  A bare inherited music material
        # is interpreted as a preset/combination and is rewritten on open.
        material["type"] = "extract_music"
    material["role"] = role
    material["desc"] = f"001short production {role}"
    material["path"] = portable_path
    material["duration"] = duration_us


def _project_media_path(project: Path, raw_path: str) -> Path | None:
    normalized = raw_path.replace("\\", "/")
    match = re.match(r"^##_draftpath_placeholder_[^#]+_##/(Resources/.+)$", normalized)
    candidate = project / Path(match.group(1)) if match else Path(raw_path)
    if not candidate.is_absolute():
        candidate = project / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(project.resolve())
    except ValueError:
        return None
    return candidate


def _measured_audio_duration_us(path: Path) -> int:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "format=duration", "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    try:
        duration = float(json.loads(completed.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        duration = 0.0
    if completed.returncode or duration <= 0:
        raise RuntimeError(f"AUDIO_MATERIAL_DECODE_FAILED:{path.name}")
    return round(duration * 1_000_000)


def register_project_local_audio_materials(
    project: Path, *, project_key: str | None = None
) -> dict:
    """Register generated audio using CapCut's UI-created direct-local schema."""
    project = Path(project).resolve()
    meta_path = project / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    project_key = str(project_key or meta.get("draft_id") or project.name)
    registrations: dict[str, dict] = {}
    for path, payload in iter_primary_draft_documents(project):
        referenced_ids = {
            segment.get("material_id")
            for track in payload.get("tracks", [])
            if isinstance(track, dict)
            for segment in track.get("segments", [])
            if isinstance(segment, dict) and isinstance(segment.get("material_id"), str)
        }
        changed = False
        for material in _materials(payload.get("materials", {})):
            if not isinstance(material, dict):
                continue
            if material.get("id") not in referenced_ids:
                continue
            name = str(material.get("name", ""))
            role = material.get("role")
            if role not in {"A9", "A10", "USER_PROVIDED_AUDIO"}:
                continue
            raw_path = material.get("path")
            media_path = _project_media_path(project, raw_path) if isinstance(raw_path, str) else None
            if media_path is None or not media_path.is_file():
                raise RuntimeError(f"AUDIO_MATERIAL_LOCAL_FILE_MISSING:{name}")
            relative = media_path.relative_to(project).as_posix()
            duration = _measured_audio_duration_us(media_path)
            local_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL, f"001short:{project_key}:local-audio:{relative}"
            ))
            material_id = str(material["id"])
            material.update({
                "type": "extract_music", "duration": duration,
                "local_material_id": local_id, "music_id": material_id,
                "resource_id": "", "third_resource_id": "", "remote_url": None,
                "source_platform": 0, "category_id": "", "category_name": "local",
                "request_id": "", "team_id": "", "check_flag": 1,
                "copyright_limit_type": "none",
            })
            if "local_resource_id" in material:
                material["local_resource_id"] = local_id
            registrations[material_id] = {
                "ai_group_type": "", "create_time": -1, "duration": duration,
                "enter_from": 0, "extra_info": media_path.name,
                "file_Path": media_path.as_posix(), "height": 0, "id": material_id,
                "import_time": -1, "import_time_ms": -1, "item_source": 1,
                "material_color_tag": "", "md5": "", "metetype": "music",
                "roughcut_time_range": {"start": 0, "duration": duration},
                "sub_time_range": {"start": -1, "duration": -1},
                "type": 0, "width": 0,
            }
            changed = True
        if changed:
            _write_json(path, payload)

    groups = meta.setdefault("draft_materials", [])
    local_group = next(
        (row for row in groups if isinstance(row, dict) and row.get("type") == 0),
        None,
    )
    if local_group is None:
        local_group = {"type": 0, "value": []}
        groups.append(local_group)
    existing = [
        row for row in local_group.get("value", [])
        if isinstance(row, dict) and row.get("id") not in registrations
    ]
    local_group["value"] = existing + list(registrations.values())
    _write_json(meta_path, meta)
    return {"registered_audio_count": len(registrations)}


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
    registration = register_project_local_audio_materials(project, project_key=draft_id)
    # Registration happens after generic Windows-cache scrubbing so its
    # project-local absolute file_Path values are preserved. Refresh every
    # CapCut mirror from the now-registered primary documents.
    shutil.copy2(project / "draft_content.json", project / "draft_info.json")
    shutil.copy2(project / "draft_content.json", project / "template-2.tmp")
    for content in (project / "Timelines").glob("*/draft_content.json"):
        shutil.copy2(content, content.with_name("draft_info.json"))
        shutil.copy2(content, content.with_name("template-2.tmp"))
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
    return {
        "windows_paths_scrubbed": changed, "draft_meta": meta,
        "audio_material_registration": registration,
    }


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
    if config.get("audio_policy") not in {"A9_TTS_PLUS_A10_RETAINED", "A9_TTS_PLUS_A10_REASSEMBLED"}:
        return
    narration_cues = config.get("tts_cues", [])
    user_audio_items = [
        item for item in config.get("user_provided_media_overlay", [])
        if item.get("media_kind") == "audio"
    ]

    def is_bound_user_audio(cue: dict) -> bool:
        cue_path = cue.get("audio_path")
        cue_range = cue.get("target_range_us")
        if not isinstance(cue_path, str) or not isinstance(cue_range, list):
            return False
        resolved = str(Path(cue_path).resolve())
        return any(
            item.get("source_path") == resolved
            and item.get("target_range_us") == cue_range
            and item.get("measured_duration_us") == cue_range[1] - cue_range[0]
            for item in user_audio_items
        )

    for row in build_manifest.get("source_audio", []):
        target_range = row.get("target_range_us")
        if not isinstance(target_range, list) or len(target_range) != 2:
            continue
        overlapping_cues = [
            cue for cue in narration_cues
            if _ranges_overlap(target_range, cue.get("target_range_us"))
        ]
        if overlapping_cues and all(is_bound_user_audio(cue) for cue in overlapping_cues):
            if row.get("mode") != "on":
                raise RuntimeError(f"USER_MEDIA_OVERLAY_A10_ON_REQUIRED:{row.get('clip_id')}")
            continue
        overlapping_ranges = [cue["target_range_us"] for cue in overlapping_cues]
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


def _bind_user_media_overlay(config: dict, build_manifest: dict) -> list[dict]:
    checked_overlay = user_provided_media_overlay.validate_bundle(
        build_manifest.get("user_provided_media_overlay"),
        episode_id=config["episode_id"],
        timeline_duration_us=config["duration_us"],
    )
    if checked_overlay["status"] != "PASS":
        first = checked_overlay["errors"][0]["code"] if checked_overlay.get("errors") else "UNKNOWN"
        raise RuntimeError(f"USER_MEDIA_OVERLAY_INVALID:{first}")
    user_media_overlay = checked_overlay["items"]
    config["user_provided_media_overlay"] = user_media_overlay
    a10_policy_errors = user_provided_media_overlay.validate_a10_overlap_policy(
        build_manifest.get("source_audio"), user_media_overlay,
    )
    if a10_policy_errors:
        raise RuntimeError(
            f"USER_MEDIA_OVERLAY_A10_ON_REQUIRED:{a10_policy_errors[0].get('clip_id')}"
        )
    return user_media_overlay


def _normalize_source(
    project: Path, config: dict, audio_source: Path | None, build_manifest: dict
) -> list[dict]:
    user_media_overlay = _bind_user_media_overlay(config, build_manifest)
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
        audio_name = (
            f"a10_source_clean_audio{audio_suffix}"
            if policy == "SOURCE_ORDER_CLEAN_AUDIO"
            else f"a10_vocal_stem{audio_suffix}"
        )
        shutil.copy2(audio_source, media / audio_name)
    draft_prefix = _draft_path_prefix(project)

    root_rows: list[dict] = []
    for document_index, (path, payload) in enumerate(_documents(project)):
        tracks = payload["tracks"]
        if len(tracks) != len(ROLE_BY_TRACK):
            raise RuntimeError("PINNED_TRACK_LAYOUT_INVALID")
        payload["duration"] = duration
        draft_config = payload.get("config")
        if not isinstance(draft_config, dict):
            draft_config = {}
            payload["config"] = draft_config
        # Preserve CapCut's clip mute toggle in addition to the per-segment
        # zero-volume layer. The source MP4 remains intact; A10 is audible.
        draft_config["video_mute"] = True
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

        overlay_audio_seed = seed_segments.get(TRACK_INDEX["A9"])
        overlay_visual_seed = seed_segments.get(TRACK_INDEX["VIDEO"])
        if user_media_overlay:
            if overlay_audio_seed is None or overlay_visual_seed is None:
                raise RuntimeError("USER_MEDIA_OVERLAY_TEMPLATE_MISSING")
            overlay_audio_material = material_map.get(overlay_audio_seed.get("material_id"))
            overlay_visual_material = material_map.get(overlay_visual_seed.get("material_id"))
            overlay_audio_parent = _material_parent(
                payload["materials"], overlay_audio_seed.get("material_id")
            )
            overlay_visual_parent = _material_parent(
                payload["materials"], overlay_visual_seed.get("material_id")
            )
            if (
                overlay_audio_material is None or overlay_visual_material is None
                or overlay_audio_parent is None or overlay_visual_parent is None
            ):
                raise RuntimeError("USER_MEDIA_OVERLAY_TEMPLATE_MISSING")

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
                sound["volume"] = 1.0
                sound["last_nonzero_volume"] = 1.0
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
                _remove_extra_material_ref_types(
                    a10_segment, material_map, {"combination"}
                )
                a10_segments.append(a10_segment)
            tracks[TRACK_INDEX["A10"]]["segments"] = a10_segments

        for item in user_media_overlay:
            is_audio = item["media_kind"] == "audio"
            seed_track_index = TRACK_INDEX["A9"] if is_audio else TRACK_INDEX["VIDEO"]
            seed_segment = overlay_audio_seed if is_audio else overlay_visual_seed
            seed_material = overlay_audio_material if is_audio else overlay_visual_material
            parent = overlay_audio_parent if is_audio else overlay_visual_parent
            assert seed_segment is not None and seed_material is not None and parent is not None
            track = copy.deepcopy(tracks[seed_track_index])
            track_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{config['episode_id']}:user-media-track:{item['overlay_id']}",
            ))
            track["id"] = track_id
            track["segments"] = []
            resource_name = (
                f"user_overlay_{item['track_index']:02d}"
                f"{Path(item['source_path']).suffix.lower()}"
            )
            shutil.copy2(Path(item["source_path"]), media / resource_name)
            material = copy.deepcopy(seed_material)
            material_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{config['episode_id']}:user-media-material:{item['overlay_id']}",
            ))
            material["id"] = material_id
            _set_media(
                material,
                media_type="audio" if is_audio else "video",
                portable_path=_portable_resource_path(
                    draft_prefix, f"Resources/media/{resource_name}"
                ),
                role=item["role"],
                duration_us=item["target_range_us"][1] - item["target_range_us"][0],
                dimensions=(
                    item["dimensions"]["width"], item["dimensions"]["height"]
                ) if not is_audio else None,
            )
            material["name"] = resource_name
            parent.append(material)
            material_map[material_id] = material
            segment = copy.deepcopy(seed_segment)
            segment["id"] = item["segment_id"]
            segment["material_id"] = material_id
            segment["track_id"] = track_id
            segment["role"] = item["role"]
            segment["target_timerange"] = {
                "start": item["target_range_us"][0],
                "duration": item["target_range_us"][1] - item["target_range_us"][0],
            }
            if item.get("source_range_us") is not None:
                segment["source_timerange"] = {
                    "start": item["source_range_us"][0],
                    "duration": item["source_range_us"][1] - item["source_range_us"][0],
                }
            else:
                segment.pop("source_timerange", None)
            segment["volume"] = 1.0 if is_audio else 0.0
            segment["last_nonzero_volume"] = segment["volume"]
            if is_audio:
                _remove_extra_material_ref_types(segment, material_map, {"combination"})
            track["segments"].append(segment)
            tracks.append(track)
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
    ] + [
        {
            "segment_id": item["segment_id"],
            "role": item["role"],
            "start": item["target_range_us"][0],
            "duration": item["target_range_us"][1] - item["target_range_us"][0],
        }
        for item in user_media_overlay
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


def _stage_prerequisites(
    config: dict, episode: Path, source_rows: list[dict], *, state_payload: dict | None = None,
) -> dict:
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
    elif visual["visual_asset_mode"] == "CLEAN_VISUAL_READY":
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
    else:
        clean_source = build_manifest.get("clean_source", {})
        override_path = Path(visual["user_clean_override_path"]).resolve()
        if (
            clean_source.get("origin") != "USER_APPROVED_NONMATCHING_CLEAN_SOURCE"
            or Path(clean_source.get("output_path", "")).resolve() != video_input
            or str(clean_source.get("output_sha256", "")).lower() != _sha(video_input).lower()
            or Path(clean_source.get("user_clean_override_path", "")).resolve() != override_path
            or str(clean_source.get("user_clean_override_sha256", "")).lower()
            != _sha(override_path).lower()
        ):
            raise RuntimeError("STAGE08_USER_CLEAN_OVERRIDE_AUTHORITY_MISMATCH")

    state_path = Path(config["state_path"]).resolve()
    state = copy.deepcopy(state_payload) if state_payload is not None else read_json(state_path)
    expected_state = "CAPCUT_STATIC_VALIDATED" if config.get("_clean_swap_from_provisional") else "AUDIO_CAPTION_VALIDATED"
    if state.get("episode_id") != episode_id or state.get("status") != expected_state:
        raise RuntimeError(
            "STAGE08_STATE_INVALID:"
            f"expected episode_id={episode_id} status={expected_state},"
            f" got episode_id={state.get('episode_id')} status={state.get('status')}"
        )
    audio_lock = resolve_state_artifact(state_path, state.get("audio_lock_path", ""))
    caption_lock = resolve_state_artifact(state_path, state.get("caption_lock_path", ""))
    if (
        not audio_lock.is_file() or not caption_lock.is_file()
        or _sha(audio_lock).lower() != str(state.get("audio_lock_sha256", "")).lower()
        or _sha(caption_lock).lower() != str(state.get("caption_lock_sha256", "")).lower()
    ):
        raise RuntimeError("STAGE07_EVIDENCE_MISSING")
    plan_path = resolve_state_artifact(state_path, state.get("production_plan_path", ""))
    plan_receipt_path = resolve_state_artifact(
        state_path, state.get("production_plan_validation_receipt_path", "")
    )
    audio = validate_audio_caption.validate_audio_caption(
        audio_lock, caption_lock,
        expected_production_plan_path=plan_path,
        expected_production_plan_sha256=state.get("production_plan_sha256"),
        expected_production_plan_receipt_path=plan_receipt_path,
        expected_production_plan_receipt_sha256=state.get("production_plan_validation_receipt_sha256"),
    )
    if audio["status"] != "PASS":
        raise RuntimeError(f"STAGE07:{audio}")
    audio_payload = json.loads(audio_lock.read_text(encoding="utf-8"))
    caption_payload = json.loads(caption_lock.read_text(encoding="utf-8"))
    final_srt = resolved_declared_path(caption_lock, caption_payload["final_srt_path"])
    audio_source = resolved_declared_path(audio_lock, audio_payload["audio_path"])
    measured_duration = audio_payload.get("measured_duration_us")
    duration_matches = (
        isinstance(measured_duration, int) and not isinstance(measured_duration, bool)
        and (
            abs(measured_duration - duration) <= validate_prebuild.SOURCE_ORDER_DURATION_TOLERANCE_US
            if config.get("production_mode") in SOURCE_ORDER_PRODUCTION_MODES
            else measured_duration == duration
        )
    )
    if (
        audio_payload.get("episode_id") != episode_id
        or audio_payload.get("audio_sha256") != _sha(audio_source)
        or not duration_matches
        or caption_payload.get("episode_id") != episode_id
        or not final_srt.is_file()
    ):
        raise RuntimeError("STAGE07_AUTHORITY_MISMATCH")
    # Any policy that keeps A10 must bind the primary audio to the separated stem;
    # under MIXED the generated A9 narration rides alongside it as a role file.
    if audio_payload.get("schema_version") == "001short-audio-lock-v4":
        expected_matrix = {
            "SOURCE_ORDER_CLEAN_AUDIO": ("SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "SOURCE_CLIP"),
            "A10_RETAINED_SYNC": ("SOURCE_ORDER_UNCHANGED_A10_RETAINED", "SOURCE_VOCAL_STEM"),
            "A10_REASSEMBLED_SYNC": ("URAKKAI", "REASSEMBLED_VOCAL_STEM"),
            "A9_TTS_PLUS_A10_REASSEMBLED": ("URAKKAI", "REASSEMBLED_VOCAL_STEM"),
            "TTS_ONLY_MUTE_SOURCE": ("URAKKAI", "GENERATED_TTS"),
            "CAPTION_ONLY_MUTE_SOURCE": ("URAKKAI", "SILENCE"),
        }
        observed = (config.get("production_mode"), audio_payload.get("audio_source"))
        if expected_matrix.get(config.get("audio_policy")) != observed or audio_payload.get("production_mode") != observed[0] or audio_payload.get("audio_policy") != config.get("audio_policy"):
            raise RuntimeError("STAGE07_AUDIO_MODE_MATRIX_MISMATCH")
    elif config.get("audio_policy") in STEM_POLICIES and audio_payload.get("audio_source") != "SOURCE_VOCAL_STEM":
        raise RuntimeError("STAGE07_VALIDATED_VOCAL_STEM_REQUIRED")
    return {
        "source_identity": source_identity, "approved_timeline": approved_timeline,
        "design_evidence": design_evidence, "build_manifest": build_manifest,
        "audio_lock": audio_lock, "caption_lock": caption_lock, "final_srt": final_srt,
        "audio_source": audio_source, "video_input": video_input,
        "width": width, "height": height,
    }


def _build_episode_once(config: dict, *, prerequisites: dict | None = None) -> dict:
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
    build_root = _build_root(config, episode)
    evidence_root = build_root / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    work_root = Path(config["work_root"]).resolve()
    work_root.mkdir(parents=True, exist_ok=True)
    source = _extract_template(Path(config["template_zip"]).resolve(), work_root / "source_authority")
    pre = prerequisites if prerequisites is not None else _stage_prerequisites(config, episode, [])
    source_manifest = clone_and_sync.hash_project_core(source)
    source_root_sha = manifest_sha256(source_manifest)
    template_sha = clone_and_sync.template_fingerprint_sha256(source)
    source_structure = capcut_model.capture_structure(capcut_model.load_project(source))
    working = work_root / "working_project"
    cloned = clone_and_sync.clone_project(source, working)
    if cloned["status"] != "PASS":
        raise RuntimeError(f"STAGE08_CLONE:{cloned}")
    project_id = "project-" + uuid.uuid4().hex
    draft_id = "draft-" + uuid.uuid4().hex
    timeline_id = "timeline-" + uuid.uuid4().hex
    synced = clone_and_sync.sync_project_ids(
        working, project_id, draft_id, timeline_id,
        source_project_path=source, expected_source_hashes=source_manifest,
    )
    if synced["status"] != "PASS":
        raise RuntimeError(f"STAGE08_ID_SYNC:{synced}")

    _normalize_source(working, config, pre["audio_source"], pre["build_manifest"])
    # Episode assets and the approved polish profile belong only to the clone.
    apply_capcut_polish_profile.apply_project(working)
    working_polish = validate_capcut_polish_profile.validate_project(working)
    if working_polish["status"] != "PASS":
        raise RuntimeError(f"STAGE08_POLISH_WORKING:{working_polish}")
    source_unchanged = clone_and_sync.verify_source_unchanged(source, source_manifest)
    if source_unchanged["status"] != "PASS":
        raise RuntimeError(f"STAGE08_SOURCE_AUTHORITY_CHANGED:{source_unchanged}")

    snapshot = capcut_model.capture_structure(capcut_model.load_project(working))
    snapshot["authority"] = {
        "captured_from": "working_project", "source_project_path": str(source.resolve()),
        "source_root_sha256": source_root_sha, "template_sha256": template_sha,
        "source_structure_sha256": manifest_sha256(source_structure),
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
        "track_layout_extension": user_provided_media_overlay.build_track_layout_extension(
            config.get("user_provided_media_overlay", [])
        ),
        "audio_policy": config.get("audio_policy"),
        "source_audio": pre["build_manifest"].get("source_audio", []),
        "root_contract_path": config["root_contract_path"],
        "workspace_root": str(Path(config["workspace_root"]).resolve()),
        "root_profile": config["root_profile"],
        "root_template_profile": config["_resolved_root_contract"]["template_profile"],
        "visual_asset_mode": config["_visual_input"]["visual_asset_mode"],
        "video_asset_key": config["_visual_input"]["video_asset_key"],
        "video_input_path": str(pre["video_input"]),
        "video_input_sha256": _sha(pre["video_input"]),
        "upload_ready": config["_visual_input"]["upload_ready"],
        **({
            "user_clean_override_path": str(config["_visual_input"]["user_clean_override_path"]),
            "user_clean_override_sha256": config["_visual_input"]["user_clean_override_sha256"],
        } if config["_visual_input"]["visual_asset_mode"] == "USER_APPROVED_NONMATCHING_CLEAN_SOURCE" else {}),
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


def _remove_generated_tree(path: Path) -> None:
    def make_writable_and_retry(function, raw_path, _exc_info):
        os.chmod(raw_path, 0o700)
        function(raw_path)

    shutil.rmtree(path, onerror=make_writable_and_retry)


def _cleanup_generated_work(work_root: Path) -> None:
    work_root = Path(work_root).resolve()
    for name in ("normalized_source", "working_project"):
        candidate = work_root / name
        if candidate.parent != work_root:
            raise RuntimeError("UNSAFE_GENERATED_WORK_PATH")
        if candidate.is_dir():
            _remove_generated_tree(candidate)
        elif candidate.exists():
            candidate.unlink()


def _reset_source_authority(work_root: Path) -> None:
    work_root = Path(work_root).resolve()
    candidate = work_root / "source_authority"
    if candidate.parent != work_root:
        raise RuntimeError("UNSAFE_SOURCE_AUTHORITY_PATH")
    if candidate.is_dir():
        _remove_generated_tree(candidate)
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
    if config.get("revision_id") is None:
        validate_grid_harness(config)
        _validate_config(config, revision_operation="swap")
    else:
        _validate_config(config, revision_operation="swap")
        validate_grid_harness(config)
    _ensure_media_tools()
    if config["visual_asset_mode"] != "CLEAN_VISUAL_READY":
        raise RuntimeError("CLEAN_SWAP_CLEAN_VISUAL_REQUIRED")
    target = Path(config["local_capcut_root"]).resolve() / config["project_name"]
    if not target.is_dir():
        raise RuntimeError("CLEAN_SWAP_PROVISIONAL_PROJECT_MISSING")
    _assert_clean_swap_lock(config, target)
    _assert_capcut_closed_for_target(target)
    episode = Path(config["episode_root"]).resolve()
    build_root = _build_root(config, episode)
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
        "audio_lock_path": str(pre["audio_lock"].resolve()),
        "audio_lock_sha256": _sha(pre["audio_lock"]),
        "caption_lock_path": str(pre["caption_lock"].resolve()),
        "caption_lock_sha256": _sha(pre["caption_lock"]),
        "final_srt_path": str(pre["final_srt"].resolve()),
        "final_srt_sha256": _sha(pre["final_srt"]),
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
    _ensure_media_tools()
    if config.get("revision_id") is None:
        validate_grid_harness(config)
        _validate_config(config)
    else:
        _validate_config(config)
    _validate_template_track_layout(Path(config["template_zip"]).resolve())
    prepared_revision = prepare_revision_state_payload(config)
    revision_state = prepared_revision[0] if prepared_revision is not None else None
    if prepared_revision is not None:
        validate_grid_harness(config, state_payload=revision_state)
    target = Path(config["local_capcut_root"]).resolve() / config["project_name"]
    if target.exists():
        raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
    build_manifest = read_json(Path(config["build_manifest_path"]).resolve())
    _bind_user_media_overlay(config, build_manifest)
    _validate_mixed_audio_modes(config, build_manifest)
    _assert_optional_edit_lock(config)
    episode = Path(config["episode_root"]).resolve()
    prerequisites = _stage_prerequisites(
        config, episode, [], state_payload=revision_state,
    )
    initialize_revision_state(config, prepared_revision)
    work_root = Path(config["work_root"]).resolve()
    work_root.mkdir(parents=True, exist_ok=True)
    _cleanup_generated_work(work_root)
    _reset_source_authority(work_root)
    try:
        return _build_episode_once(config, prerequisites=prerequisites)
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
