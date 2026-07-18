#!/usr/bin/env python3
"""Validate active CapCut media links for source-derived Shorts drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


SOURCE_VIDEO_ROLES = {"source_video", "V8", "source_clip"}
DRAFT_PATH_PLACEHOLDER = re.compile(r"^##_draftpath_placeholder_[^#]+_##[\\/](.+)$")
NATIVE_MEDIA_GROUPS = ("videos", "audios", "images")
NATIVE_META_MEDIA_TYPES = {0, 1, "media", "video", "audio", "image"}


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise GateFail(f"FAIL_MEDIA_LINK: {label} missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise GateFail(f"FAIL_MEDIA_LINK: {label} root must be object")
    return data


def as_path(root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else root / path


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def capcut_runtime_path(project_dir: Path, raw_path: str) -> Path:
    placeholder = DRAFT_PATH_PLACEHOLDER.match(raw_path)
    if placeholder:
        return project_dir / Path(placeholder.group(1))
    return as_path(project_dir, raw_path)


def runtime_media_paths(draft: dict[str, Any], meta: dict[str, Any] | None) -> list[str]:
    paths: list[str] = []
    materials = draft.get("materials")
    if isinstance(materials, dict):
        for group_name in NATIVE_MEDIA_GROUPS:
            values = materials.get(group_name)
            if not isinstance(values, list):
                continue
            for material in values:
                if not isinstance(material, dict):
                    continue
                for key in ("path", "media_path", "file_path", "material_path"):
                    value = material.get(key)
                    if isinstance(value, str) and value.strip():
                        paths.append(value)

    active = draft.get("active_materials")
    if isinstance(active, list):
        for material in active:
            if not isinstance(material, dict):
                continue
            value = material_path(material)
            if value:
                paths.append(value)

    if isinstance(meta, dict):
        groups = meta.get("draft_materials")
        if isinstance(groups, list):
            for group in groups:
                if not isinstance(group, dict):
                    continue
                group_type = group.get("type")
                normalized_type = (
                    group_type.strip().lower()
                    if isinstance(group_type, str)
                    else group_type
                )
                if normalized_type not in NATIVE_META_MEDIA_TYPES:
                    continue
                values = group.get("value")
                if not isinstance(values, list):
                    continue
                for material in values:
                    if not isinstance(material, dict):
                        continue
                    value = material.get("file_Path") or material.get("file_path")
                    if isinstance(value, str) and value.strip():
                        paths.append(value)
    return list(dict.fromkeys(paths))


def validate_capcut_runtime_media(draft_path: Path, draft: dict[str, Any]) -> None:
    project_dir = draft_path.parent
    meta_path = project_dir / "draft_meta_info.json"
    if not meta_path.exists():
        raise GateFail(
            "FAIL_CAPCUT_RUNTIME_MEDIA_LINK: draft_meta_info.json missing beside "
            f"draft_content.json: {meta_path}"
        )
    meta = load_json(meta_path, "draft_meta_info.json")
    for raw_path in runtime_media_paths(draft, meta):
        resolved = capcut_runtime_path(project_dir, raw_path)
        if not resolved.exists():
            raise GateFail(
                "FAIL_CAPCUT_RUNTIME_MEDIA_LINK: imported media path is not "
                f"resolvable from the CapCut project: {raw_path} -> {resolved}"
            )


def material_path(material: dict[str, Any]) -> str:
    for key in ("path", "local_path", "file_path", "material_path"):
        value = material.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def native_segment_index(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    tracks = data.get("tracks")
    if not isinstance(tracks, list):
        return result
    for track in tracks:
        if not isinstance(track, dict):
            continue
        track_type = str(track.get("type") or "").strip().lower()
        segments = track.get("segments")
        if not isinstance(segments, list):
            continue
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            material_id = segment.get("material_id")
            if not isinstance(material_id, str) or not material_id.strip():
                continue
            result.setdefault(material_id, []).append(
                {**segment, "_validation_track_type": track_type}
            )
    return result


def active_materials(data: dict[str, Any]) -> list[dict[str, Any]]:
    materials = data.get("active_materials")
    if isinstance(materials, list):
        return [
            {**item, "_validation_explicit_active_material": True}
            for item in materials
            if isinstance(item, dict)
        ]
    result: list[dict[str, Any]] = []
    segment_index = native_segment_index(data)
    materials_root = data.get("materials")
    if isinstance(materials_root, dict):
        for key in NATIVE_MEDIA_GROUPS:
            value = materials_root.get(key)
            if isinstance(value, list):
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    material_id = item.get("id")
                    segments = (
                        segment_index.get(material_id, [])
                        if isinstance(material_id, str)
                        else []
                    )
                    expected_track_type = "audio" if key == "audios" else "video"
                    segments = [
                        segment
                        for segment in segments
                        if segment.get("_validation_track_type") == expected_track_type
                    ]
                    result.append(
                        {
                            **item,
                            "_validation_native_material": True,
                            "_validation_native_group": key,
                            "_validation_native_segments": segments,
                        }
                    )
    return result


def is_source_video_material(material: dict[str, Any]) -> bool:
    role = str(material.get("role") or material.get("track_id") or material.get("track") or "")
    return (
        role in SOURCE_VIDEO_ROLES
        or material.get("is_source_video") is True
        or (
            material.get("_validation_explicit_active_material") is True
            and str(material.get("type") or "").lower() == "video"
        )
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def same_media(left: Path, right: Path, hash_cache: dict[Path, str]) -> bool:
    left = left.resolve()
    right = right.resolve()
    if str(left).lower() == str(right).lower():
        return True
    if not left.exists() or not right.exists():
        return False
    left_hash = hash_cache.get(left)
    if left_hash is None:
        left_hash = file_sha256(left)
        hash_cache[left] = left_hash
    right_hash = hash_cache.get(right)
    if right_hash is None:
        right_hash = file_sha256(right)
        hash_cache[right] = right_hash
    return left_hash == right_hash


def normalized_declared_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip().lower()


def same_declared_media(
    raw_path: str,
    resolved_path: Path,
    source_declaration: str,
    source_path: Path,
) -> bool:
    return (
        normalized_declared_path(raw_path) == normalized_declared_path(source_declaration)
        or str(resolved_path.resolve()).lower() == str(source_path.resolve()).lower()
    )


def expected_speaker_quote_edit_ids(root: Path) -> set[str]:
    timeline_path = root / "20_script" / "timeline_design.json"
    if not timeline_path.exists():
        return set()
    timeline = load_json(timeline_path, "timeline_design.json")
    segments = timeline.get("segments")
    if not isinstance(segments, list):
        return set()
    result: set[str] = set()
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        speaker_quote = (
            str(segment.get("caption_type") or "").strip().lower() == "speaker_quote"
            or str(segment.get("assembly_role") or "").strip().lower()
            == "verified_speaker_quote"
            or str(segment.get("audio_role") or "").strip().lower()
            == "audio.speaker_source"
        )
        edit_id = segment.get("edit_id")
        if speaker_quote and isinstance(edit_id, str) and edit_id.strip():
            result.add(edit_id.strip())
    return result


def speaker_q_material_edit_id(material: dict[str, Any], raw_path: str) -> str:
    declared_edit_id = material.get("edit_id")
    if isinstance(declared_edit_id, str) and declared_edit_id.strip():
        return declared_edit_id.strip()
    role = str(material.get("role") or "")
    if role.startswith("speaker_q_"):
        return role.removeprefix("speaker_q_").strip()
    normalized_path = raw_path.replace("\\", "/")
    if "/speaker_q/" in f"/{normalized_path.lower()}":
        return Path(normalized_path).stem.split("_", 1)[0]
    return ""


def active_speaker_q_materials(
    draft: dict[str, Any],
    media_root: Path,
    is_runtime_draft: bool,
) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for material in active_materials(draft):
        raw_path = material_path(material)
        if not raw_path:
            continue
        native_segments = material.get("_validation_native_segments")
        active_instance_count = 1
        if material.get("_validation_native_material") is True:
            if material.get("_validation_native_group") != "audios":
                continue
            if not isinstance(native_segments, list) or not native_segments:
                continue
            audible_segments = [
                segment
                for segment in native_segments
                if (
                    isinstance(segment.get("volume"), (int, float))
                    and float(segment["volume"]) > 1e-9
                )
            ]
            if not audible_segments:
                continue
            active_instance_count = len(audible_segments)
        elif material.get("active", True) is False:
            continue
        edit_id = speaker_q_material_edit_id(material, raw_path)
        if not edit_id:
            continue
        resolved_path = (
            capcut_runtime_path(media_root, raw_path)
            if is_runtime_draft
            else as_path(media_root, raw_path)
        )
        result.extend((edit_id, resolved_path) for _ in range(active_instance_count))
    return result


def validate_speaker_q_provenance(
    root: Path,
    draft: dict[str, Any],
    media_root: Path,
    is_runtime_draft: bool,
) -> str:
    separation_path = root / "10_analysis" / "source_voice_separation.json"
    manifest_path = root / "30_audio_srt" / "audio_asset_manifest.json"
    expected_edit_ids = expected_speaker_quote_edit_ids(root)
    if not manifest_path.exists():
        if expected_edit_ids:
            raise GateFail(
                "FAIL_SPEAKER_Q_PROVENANCE: audio_asset_manifest.json missing for "
                f"speaker_quote edits: {', '.join(sorted(expected_edit_ids))}"
            )
        return "NOT_REQUIRED"
    if not separation_path.exists():
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: source voice or audio asset manifest missing")

    separation = load_json(separation_path, "source_voice_separation.json")
    manifest = load_json(manifest_path, "audio_asset_manifest.json")
    if str(manifest.get("status") or "").upper() != "PASS":
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: audio asset manifest is not PASS")
    if str(separation.get("status") or "").upper() != "PASS":
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: source voice separation is not PASS")
    vocals_raw = separation.get("vocals_path")
    vocals_hash = str(separation.get("vocals_sha256") or "").lower()
    if not isinstance(vocals_raw, str) or not vocals_raw.strip():
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: vocals_path missing")
    vocals_path = as_path(root, vocals_raw)
    if not vocals_path.exists() or file_sha256(vocals_path).lower() != vocals_hash:
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: validated vocals hash mismatch")

    speaker_q_lane = manifest.get("speaker_q_lane")
    if speaker_q_lane == []:
        if expected_edit_ids:
            raise GateFail(
                "FAIL_SPEAKER_Q_PROVENANCE: speaker_q_lane is empty for "
                f"speaker_quote edits: {', '.join(sorted(expected_edit_ids))}"
            )
        return "NOT_REQUIRED"
    if not isinstance(speaker_q_lane, list):
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: speaker_q_lane missing")
    lane_edit_id_list: list[str] = []
    for item in speaker_q_lane:
        if not isinstance(item, dict):
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: invalid speaker_q_lane entry")
        edit_id = str(item.get("edit_id") or "").strip()
        if not edit_id:
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: speaker_q_lane edit_id missing")
        lane_edit_id_list.append(edit_id)
    lane_edit_ids = set(lane_edit_id_list)
    if len(lane_edit_ids) != len(lane_edit_id_list):
        raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: duplicate speaker_q_lane edit_id")
    missing_edit_ids = expected_edit_ids - lane_edit_ids
    if missing_edit_ids:
        raise GateFail(
            "FAIL_SPEAKER_Q_PROVENANCE: speaker_q_lane missing edits: "
            f"{', '.join(sorted(missing_edit_ids))}"
        )
    unexpected_edit_ids = lane_edit_ids - expected_edit_ids
    if unexpected_edit_ids:
        raise GateFail(
            "FAIL_SPEAKER_Q_PROVENANCE: unexpected speaker_q_lane edits: "
            f"{', '.join(sorted(unexpected_edit_ids))}"
        )
    active_q_materials = active_speaker_q_materials(
        draft,
        media_root,
        is_runtime_draft,
    )
    active_q_edit_ids = {edit_id for edit_id, _ in active_q_materials}
    active_q_counts = {
        edit_id: sum(1 for active_edit_id, _ in active_q_materials if active_edit_id == edit_id)
        for edit_id in active_q_edit_ids
    }
    duplicate_active_edit_ids = {
        edit_id for edit_id, count in active_q_counts.items() if count != 1
    }
    if duplicate_active_edit_ids:
        raise GateFail(
            "FAIL_SPEAKER_Q_PROVENANCE: duplicate active audio Q edits: "
            f"{', '.join(sorted(duplicate_active_edit_ids))}"
        )
    missing_active_edit_ids = expected_edit_ids - active_q_edit_ids
    unexpected_active_edit_ids = active_q_edit_ids - expected_edit_ids
    if missing_active_edit_ids or unexpected_active_edit_ids:
        details: list[str] = []
        if missing_active_edit_ids:
            details.append(f"missing={','.join(sorted(missing_active_edit_ids))}")
        if unexpected_active_edit_ids:
            details.append(f"unexpected={','.join(sorted(unexpected_active_edit_ids))}")
        raise GateFail(
            "FAIL_SPEAKER_Q_PROVENANCE: active audio track Q coverage mismatch: "
            + " ".join(details)
        )
    hash_cache: dict[Path, str] = {}
    for item in speaker_q_lane:
        if item.get("source_audio_provenance") != "demucs_full_source_vocals":
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: non-Demucs speaker Q provenance")
        if normalized_declared_path(item.get("source_audio_ref") or "") != normalized_declared_path(
            vocals_raw
        ):
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: speaker Q vocals reference mismatch")
        if str(item.get("source_voice_vocals_sha256") or "").lower() != vocals_hash:
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: speaker Q vocals hash mismatch")
        asset_raw = item.get("path")
        asset_hash = str(item.get("asset_sha256") or "").lower()
        if not isinstance(asset_raw, str) or not asset_raw.strip():
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: speaker Q asset path missing")
        asset_path = as_path(root, asset_raw)
        if not asset_path.exists() or file_sha256(asset_path).lower() != asset_hash:
            raise GateFail("FAIL_SPEAKER_Q_PROVENANCE: speaker Q asset hash mismatch")
        asset_referenced = False
        edit_id = str(item.get("edit_id") or "").strip()
        for active_edit_id, draft_media_path in active_q_materials:
            if active_edit_id != edit_id or not same_media(
                draft_media_path,
                asset_path,
                hash_cache,
            ):
                continue
            if draft_media_path.exists() and file_sha256(draft_media_path).lower() == asset_hash:
                asset_referenced = True
                break
        if not asset_referenced:
            raise GateFail(
                "FAIL_SPEAKER_Q_PROVENANCE: speaker Q asset is not referenced by "
                f"an active audio track for {edit_id}: {asset_raw}"
            )
    return "PASS"


def clean_visual_path(root: Path) -> Path | None:
    binding_path = root / "10_analysis" / "clean_source_binding.json"
    if binding_path.exists():
        binding = load_json(binding_path, "clean_source_binding.json")
        if str(binding.get("status") or "").upper() == "PASS":
            clean_visual = binding.get("clean_visual")
            candidates = [
                clean_visual.get("relative_path") if isinstance(clean_visual, dict) else None,
                binding.get("local_clean_visual_relative_path"),
                binding.get("clean_visual_path"),
            ]
            for candidate in candidates:
                if isinstance(candidate, str) and candidate.strip():
                    return as_path(root, candidate)

    manifest_path = root / "00_source" / "source_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = load_json(manifest_path, "source_manifest.json")
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        return None
    for source in sources:
        if not isinstance(source, dict):
            continue
        role = str(source.get("role") or "").strip().lower()
        if role != "capcut_visual_only":
            continue
        candidate = source.get("local_source_path") or source.get("relative_path")
        if isinstance(candidate, str) and candidate.strip():
            return as_path(root, candidate)
    return None


def validate_capcut_media_links(
    root: Path,
    draft_content_path: Path,
    source_path: Path,
    virtual_store_path: Path | None = None,
    runtime_project: bool = False,
) -> dict[str, Any]:
    root = Path(root)
    source_declaration = str(source_path)
    source_path = as_path(root, source_path)
    if Path(source_declaration).is_absolute() and is_within(source_path, root):
        source_declaration = str(source_path.resolve().relative_to(root.resolve()))
    if not source_path.exists():
        raise GateFail(f"FAIL_MEDIA_LINK: source media missing: {source_path}")
    resolved_draft_path = as_path(root, draft_content_path)
    draft = load_json(resolved_draft_path, "draft_content.json")
    is_runtime_draft = runtime_project or not is_within(resolved_draft_path, root)
    media_root = resolved_draft_path.parent if is_runtime_draft else root
    if is_runtime_draft:
        validate_capcut_runtime_media(resolved_draft_path, draft)
    if virtual_store_path is not None and as_path(root, virtual_store_path).exists():
        load_json(as_path(root, virtual_store_path), "draft_virtual_store.json")

    materials = active_materials(draft)
    if not materials:
        raise GateFail("FAIL_MEDIA_LINK: active materials missing")

    visual_source_path = clean_visual_path(root)
    if visual_source_path is not None and not visual_source_path.exists():
        raise GateFail(f"FAIL_MEDIA_LINK: clean visual media missing: {visual_source_path}")

    expected_active_visual = visual_source_path or source_path
    hash_cache: dict[Path, str] = {}
    runtime_meta = None
    if is_runtime_draft:
        meta_path = resolved_draft_path.parent / "draft_meta_info.json"
        runtime_meta = load_json(meta_path, "draft_meta_info.json")
    source_linked = False
    for raw_path in runtime_media_paths(draft, runtime_meta):
        resolved = (
            capcut_runtime_path(media_root, raw_path)
            if is_runtime_draft
            else as_path(media_root, raw_path)
        )
        if same_declared_media(
            raw_path,
            resolved,
            source_declaration,
            source_path,
        ) and same_media(resolved, source_path, hash_cache):
            source_linked = True
            break
    active_visual_linked = False
    active_visual_media_path = ""
    for material in materials:
        raw_path = material_path(material)
        native_segments = material.get("_validation_native_segments")
        native_active = isinstance(native_segments, list) and bool(native_segments)
        default_active = (
            native_active
            if material.get("_validation_native_material") is True
            else True
        )
        is_active = material.get("active", default_active) is not False
        if not is_active and not raw_path:
            continue
        if not raw_path:
            raise GateFail("FAIL_MEDIA_LINK: active material path missing")
        resolved = (
            capcut_runtime_path(media_root, raw_path)
            if is_runtime_draft
            else as_path(media_root, raw_path)
        )
        if not resolved.exists():
            state = "active" if is_active else "listed"
            raise GateFail(f"FAIL_MEDIA_LINK: {state} material path missing on disk: {resolved}")
        if not is_active:
            continue
        placeholder = str(material.get("placeholder") or material.get("placeholder_id") or "")
        if placeholder or "placeholder" in raw_path.lower():
            raise GateFail("FAIL_PLACEHOLDER_MEDIA_ACTIVE: template placeholder media is active")
        source_video_material = is_source_video_material(material)
        matches_original_source = same_declared_media(
            raw_path,
            resolved,
            source_declaration,
            source_path,
        ) and same_media(resolved, source_path, hash_cache)
        matches_expected_visual = same_media(
            resolved,
            expected_active_visual,
            hash_cache,
        )
        if source_video_material:
            if "audio_enabled" in material:
                audio_enabled = material["audio_enabled"]
            elif "source_video_audio_enabled" in material:
                audio_enabled = material["source_video_audio_enabled"]
            else:
                raise GateFail(
                    "FAIL_SOURCE_VIDEO_AUDIO_MUTE_UNPROVEN: source-video material "
                    "must declare audio_enabled=false"
                )
            if audio_enabled is not False:
                raise GateFail(
                    "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED: source-video embedded audio must be muted"
                )
            if visual_source_path is not None and matches_original_source:
                raise GateFail(
                    "FAIL_ORIGINAL_SOURCE_VIDEO_ACTIVE: original source must stay "
                    "in the media bin when a clean visual is selected"
                )
            if matches_expected_visual:
                active_visual_linked = True
                active_visual_media_path = str(resolved)
        elif (
            material.get("_validation_native_material") is True
            and material.get("_validation_native_group") in {"videos", "images"}
            and (matches_expected_visual or matches_original_source)
        ):
            if material.get("_validation_native_group") == "videos":
                if not native_segments:
                    raise GateFail(
                        "FAIL_SOURCE_VIDEO_AUDIO_MUTE_UNPROVEN: native source-video "
                        "material has no active track segment"
                    )
                for segment in native_segments:
                    volume = segment.get("volume")
                    if not isinstance(volume, (int, float)):
                        raise GateFail(
                            "FAIL_SOURCE_VIDEO_AUDIO_MUTE_UNPROVEN: native source-video "
                            "segment volume is missing"
                        )
                    if abs(float(volume)) > 1e-9:
                        raise GateFail(
                            "FAIL_SOURCE_VIDEO_AUDIO_NOT_MUTED: native source-video "
                            "segment volume must be 0"
                        )
            if visual_source_path is not None and matches_original_source:
                raise GateFail(
                    "FAIL_ORIGINAL_SOURCE_VIDEO_ACTIVE: original source must stay "
                    "in the media bin when a clean visual is selected"
                )
            if matches_expected_visual:
                active_visual_linked = True
                active_visual_media_path = str(resolved)

    if not source_linked:
        raise GateFail(
            "FAIL_MEDIA_LINK: original source media is not listed by exact path in the draft"
        )
    if not active_visual_linked:
        label = "clean visual media" if visual_source_path is not None else "source media"
        raise GateFail(f"FAIL_MEDIA_LINK: active source video does not point to {label}")
    speaker_q_provenance_status = validate_speaker_q_provenance(
        root,
        draft,
        media_root,
        is_runtime_draft,
    )
    return {
        "capcut_media_links_status": "PASS",
        "source_media_path": str(source_path),
        "active_visual_media_path": active_visual_media_path,
        "original_source_media_bin_status": "PASS",
        "dual_source_binding_status": "PASS" if visual_source_path is not None else "NOT_REQUIRED",
        "speaker_q_provenance_status": speaker_q_provenance_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--draft-content", default="50_capcut_project/draft_content.json")
    parser.add_argument("--source", default="00_source/source.mp4")
    parser.add_argument("--virtual-store", default="")
    args = parser.parse_args()
    try:
        result = validate_capcut_media_links(
            Path(args.root),
            Path(args.draft_content),
            Path(args.source),
            Path(args.virtual_store) if args.virtual_store else None,
        )
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
