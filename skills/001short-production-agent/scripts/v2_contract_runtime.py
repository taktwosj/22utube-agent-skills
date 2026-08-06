from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any

import clone_and_sync
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
PLAN_SCHEMA = SKILL_ROOT / "schemas" / "executable_production_plan.schema.json"

SUPPORTED_OPERATIONS = frozenset(
    {
        "clone_template_segment",
        "replace_template_text",
        "replace_text_preserve_style",
        "replace_media_and_range",
        "extend_seed_full_duration",
        "preserve_muted_seed",
        "omit",
        "clear",
    }
)
SFX_SEED_BY_KIND = {"TRANSITION": 1, "REVERSAL": 2, "WOW": 3}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _materials(value: Any):
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            yield value
        for child in value.values():
            yield from _materials(child)
    elif isinstance(value, list):
        for child in value:
            yield from _materials(child)


def _material_parent(value: Any, material_id: str) -> list[dict[str, Any]] | None:
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


def _material_text(material: dict[str, Any]) -> str | None:
    content = material.get("content")
    if isinstance(content, str) and content:
        try:
            rich = json.loads(content)
        except json.JSONDecodeError:
            return content
        if isinstance(rich, dict) and isinstance(rich.get("text"), str):
            return rich["text"]
    text = material.get("text")
    return text if isinstance(text, str) else None


def _set_text(material: dict[str, Any], text: str, role: str) -> None:
    try:
        rich = json.loads(material["content"])
    except (KeyError, TypeError, json.JSONDecodeError):
        raise ValueError(f"V2_TEXT_SEED_INVALID:{role}") from None
    styles = rich.get("styles")
    if not isinstance(styles, list) or not styles:
        raise ValueError(f"V2_TEXT_SEED_INVALID:{role}")
    rich["text"] = text
    for style in styles:
        if not isinstance(style, dict):
            raise ValueError(f"V2_TEXT_SEED_INVALID:{role}")
        style["range"] = [0, len(text)]
    material["content"] = json.dumps(rich, ensure_ascii=False, separators=(",", ":"))
    if "text" in material:
        material["text"] = text


def _resolve_profile(
    root_contract_path: Path, workspace_root: Path, root_profile: str
) -> tuple[dict[str, Any], Path, Path]:
    contract = read_json(root_contract_path)
    profiles = contract.get("profiles")
    if not isinstance(profiles, dict):
        raise ValueError("V2_ROOT_CONTRACT_PROFILES_INVALID")
    matches = [
        profile
        for profile in profiles.values()
        if isinstance(profile, dict) and profile.get("template_profile") == root_profile
    ]
    if len(matches) != 1:
        raise ValueError(f"V2_ROOT_PROFILE_AMBIGUOUS:{root_profile}:{len(matches)}")
    profile = matches[0]
    archive = workspace_root / str(profile.get("archive_relative_path", ""))
    layout = workspace_root / str(profile.get("layout_contract_relative_path", ""))
    if not archive.is_file() or not layout.is_file():
        raise FileNotFoundError("V2_ROOT_AUTHORITY_MISSING")
    expected_sha = str(profile.get("archive_sha256", "")).lower()
    if sha256(archive).lower() != expected_sha:
        raise ValueError("V2_ROOT_ARCHIVE_SHA_MISMATCH")
    layout_payload = read_json(layout)
    if (
        layout_payload.get("template_profile") != root_profile
        or str(layout_payload.get("archive_sha256", "")).lower() != expected_sha
    ):
        raise ValueError("V2_LAYOUT_CONTRACT_AUTHORITY_MISMATCH")
    return layout_payload, archive, layout


def _find_project(extracted: Path) -> Path:
    candidates = [
        path.parent
        for path in extracted.rglob("draft_content.json")
        if (path.parent / "draft_meta_info.json").is_file()
        and path.parent.parent.name != "Timelines"
        and "subdraft" not in path.parts
    ]
    if len(candidates) != 1:
        raise ValueError(f"V2_ROOT_PROJECT_AMBIGUOUS:{len(candidates)}")
    return candidates[0]


def _flatten_placements(plan: dict[str, Any]) -> list[dict[str, Any]]:
    placements: list[dict[str, Any]] = []
    for row in plan.get("timeline", []):
        if isinstance(row, dict) and isinstance(row.get("placements"), list):
            placements.extend(item for item in row["placements"] if isinstance(item, dict))
    return placements


def _ordered_range(value: Any, *, maximum: int | None = None) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        and 0 <= value[0] < value[1]
        and (maximum is None or value[1] <= maximum)
    )


def validate_plan_document(plan: dict[str, Any]) -> list[str]:
    errors = validate_schema(plan, read_json(PLAN_SCHEMA))
    duration = plan.get("total_duration_us")
    maximum = duration if isinstance(duration, int) and not isinstance(duration, bool) else None
    for index, row in enumerate(plan.get("timeline", [])):
        if not isinstance(row, dict):
            continue
        if not _ordered_range(row.get("target_range_us"), maximum=maximum):
            errors.append(f"$.timeline[{index}].target_range_us: unordered or out of bounds")
        for placement_index, placement in enumerate(row.get("placements", [])):
            if not isinstance(placement, dict):
                continue
            if not _ordered_range(placement.get("target_range_us"), maximum=maximum):
                errors.append(
                    f"$.timeline[{index}].placements[{placement_index}].target_range_us: unordered or out of bounds"
                )
            if "source_range_us" in placement and not _ordered_range(
                placement.get("source_range_us")
            ):
                errors.append(
                    f"$.timeline[{index}].placements[{placement_index}].source_range_us: unordered"
                )
    placements = _flatten_placements(plan)
    placement_ids = [row.get("placement_id") for row in placements]
    if len(placement_ids) != len(set(placement_ids)):
        errors.append("V2_DUPLICATE_PLACEMENT_ID")
    timeline = plan.get("timeline", [])
    segment_keys = [row.get("segment_key") for row in timeline if isinstance(row, dict)]
    if len(segment_keys) != len(set(segment_keys)):
        errors.append("V2_DUPLICATE_SEGMENT_KEY")
    for placement in placements:
        if placement.get("anchor") == "A11_SFX" and SFX_SEED_BY_KIND.get(
            placement.get("sfx_kind")
        ) != placement.get("sfx_seed"):
            errors.append(
                f"V2_A11_SFX_MAPPING_INVALID:{placement.get('placement_id')}"
            )
    policies = plan.get("lane_policies", {})
    for lane in ("VIDEO", "A9", "A10"):
        rows = sorted(
            [
                row
                for row in placements
                if row.get("anchor") == lane
                and row.get("operation") not in {"omit", "clear", "preserve_muted_seed"}
            ],
            key=lambda row: row.get("target_range_us", [0, 0]),
        )
        if not rows and lane != "VIDEO":
            continue
        policy = policies.get(lane, {}) if isinstance(policies, dict) else {}
        cursor = 0
        for row in rows:
            value = row.get("target_range_us")
            if not _ordered_range(value, maximum=maximum):
                continue
            start, end = value
            if start > cursor and policy.get("allow_gaps") is not True:
                errors.append(f"$.lane_policies.{lane}: undeclared gap {cursor}:{start}")
            if start < cursor and policy.get("allow_overlaps") is not True:
                errors.append(f"$.lane_policies.{lane}: undeclared overlap {start}:{cursor}")
            cursor = max(cursor, end)
        if maximum is not None and cursor < maximum and policy.get("allow_gaps") is not True:
            errors.append(f"$.lane_policies.{lane}: undeclared gap {cursor}:{maximum}")
    return errors


def _asset_path(manifest_path: Path, manifest: dict[str, Any], asset_key: str) -> tuple[Path, str]:
    assets = manifest.get("assets")
    row = assets.get(asset_key) if isinstance(assets, dict) else None
    if not isinstance(row, dict) or not isinstance(row.get("path"), str):
        raise ValueError(f"V2_ASSET_BINDING_MISSING:{asset_key}")
    candidate = Path(row["path"])
    source = candidate if candidate.is_absolute() else manifest_path.parent / candidate
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"V2_ASSET_MISSING:{asset_key}")
    relative_name = row.get("relative_name")
    name = relative_name if isinstance(relative_name, str) and relative_name else f"{asset_key}{source.suffix}"
    if Path(name).name != name:
        raise ValueError(f"V2_ASSET_NAME_INVALID:{asset_key}")
    return source, name


def _validate_asset_destinations(
    plan: dict[str, Any], manifest_path: Path, manifest: dict[str, Any]
) -> None:
    destinations: dict[str, tuple[Path, str, str]] = {}
    for placement in _flatten_placements(plan):
        if placement.get("operation") != "replace_media_and_range":
            continue
        asset_key = str(placement.get("asset_key", ""))
        source, name = _asset_path(manifest_path, manifest, asset_key)
        identity = (source, sha256(source), asset_key)
        destination_key = name.casefold()
        previous = destinations.get(destination_key)
        if previous is not None and previous[:2] != identity[:2]:
            raise ValueError(
                f"V2_ASSET_DESTINATION_COLLISION:{name}:{previous[2]}:{asset_key}"
            )
        destinations[destination_key] = identity


def _validate_root_asset_destinations(
    plan: dict[str, Any],
    manifest_path: Path,
    manifest: dict[str, Any],
    source_project: Path,
) -> None:
    media_root = source_project / "Resources" / "media"
    existing = {
        path.relative_to(media_root).as_posix().casefold(): (sha256(path), path)
        for path in media_root.rglob("*")
        if path.is_file()
    } if media_root.is_dir() else {}
    for placement in _flatten_placements(plan):
        if placement.get("operation") != "replace_media_and_range":
            continue
        asset_key = str(placement.get("asset_key", ""))
        source, name = _asset_path(manifest_path, manifest, asset_key)
        fixed = existing.get(name.casefold())
        if fixed is not None and fixed[0] != sha256(source):
            raise ValueError(
                f"V2_ROOT_ASSET_DESTINATION_COLLISION:{name}:{fixed[1].name}:{asset_key}"
            )


def _contracted_documents(project: Path, track_ids: set[str]) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(project.rglob("*")):
        if not path.is_file() or path.name not in {"draft_content.json", "draft_info.json", "template-2.tmp"}:
            continue
        try:
            payload = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        tracks = payload.get("tracks")
        observed = {row.get("id") for row in tracks if isinstance(row, dict)} if isinstance(tracks, list) else set()
        if track_ids.issubset(observed):
            paths.append(path)
    return paths


def _apply_document(
    payload: dict[str, Any],
    *,
    plan: dict[str, Any],
    layout: dict[str, Any],
    assets: dict[str, Any],
    asset_manifest_path: Path,
    project: Path,
) -> None:
    duration = plan["total_duration_us"]
    payload["duration"] = duration
    track_by_id = {track.get("id"): track for track in payload["tracks"] if isinstance(track, dict)}
    role_contract = {row["role"]: row for row in layout["tracks"]}
    material_map = {
        row.get("id"): row for row in _materials(payload.get("materials", {})) if isinstance(row.get("id"), str)
    }
    placements = _flatten_placements(plan)
    by_anchor: dict[str, list[dict[str, Any]]] = {}
    for placement in placements:
        by_anchor.setdefault(str(placement.get("anchor")), []).append(placement)

    copied_assets: dict[str, tuple[str, int]] = {}
    media_root = project / "Resources" / "media"
    media_root.mkdir(parents=True, exist_ok=True)
    for anchor, contract_row in role_contract.items():
        track = track_by_id.get(contract_row["track_id"])
        if not isinstance(track, dict):
            raise ValueError(f"V2_CONTRACT_TRACK_MISSING:{anchor}")
        seeds = copy.deepcopy(track.get("segments", []))
        if not seeds:
            raise ValueError(f"V2_CONTRACT_SEED_MISSING:{anchor}")
        output_segments: list[dict[str, Any]] = []
        for placement in by_anchor.get(anchor, []):
            operation = placement.get("operation")
            if operation not in SUPPORTED_OPERATIONS:
                raise ValueError(f"V2_OPERATION_UNSUPPORTED:{operation}")
            if operation in {"omit", "clear"}:
                continue
            seed_index = int(placement.get("sfx_seed", 1)) - 1
            if seed_index < 0 or seed_index >= len(seeds):
                raise ValueError(f"V2_SEED_INDEX_INVALID:{placement.get('placement_id')}")
            segment = copy.deepcopy(seeds[seed_index])
            segment["id"] = placement["placement_id"]
            start, end = placement["target_range_us"]
            segment["target_timerange"] = {"start": start, "duration": end - start}
            if operation == "preserve_muted_seed":
                segment["volume"] = 0
                segment["last_nonzero_volume"] = 0
            elif operation == "extend_seed_full_duration":
                pass
            elif operation == "clone_template_segment":
                segment["volume"] = placement.get("volume", 1)
            elif operation in {"replace_text_preserve_style", "replace_template_text"}:
                base_material = material_map.get(segment.get("material_id"))
                if not isinstance(base_material, dict):
                    raise ValueError(f"V2_TEXT_MATERIAL_MISSING:{anchor}")
                parent = _material_parent(payload["materials"], base_material["id"])
                if parent is None:
                    raise ValueError(f"V2_MATERIAL_CONTAINER_MISSING:{anchor}")
                material = copy.deepcopy(base_material)
                material_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{plan['episode_id']}:{placement['placement_id']}:material"))
                material["id"] = material_id
                _set_text(material, placement["text"], anchor)
                parent.append(material)
                material_map[material_id] = material
                segment["material_id"] = material_id
            elif operation == "replace_media_and_range":
                base_material = material_map.get(segment.get("material_id"))
                if not isinstance(base_material, dict):
                    raise ValueError(f"V2_MEDIA_MATERIAL_MISSING:{anchor}")
                parent = _material_parent(payload["materials"], base_material["id"])
                if parent is None:
                    raise ValueError(f"V2_MATERIAL_CONTAINER_MISSING:{anchor}")
                asset_key = placement["asset_key"]
                if asset_key not in copied_assets:
                    source, name = _asset_path(asset_manifest_path, assets, asset_key)
                    shutil.copy2(source, media_root / name)
                    copied_assets[asset_key] = (name, source.stat().st_size)
                name, _ = copied_assets[asset_key]
                material = copy.deepcopy(base_material)
                material_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{plan['episode_id']}:{placement['placement_id']}:material"))
                material["id"] = material_id
                material["role"] = anchor
                material["desc"] = f"001short v2 {anchor}"
                material["path"] = f"##_draftpath_placeholder_v2_##/Resources/media/{name}"
                material["duration"] = end - start
                if anchor == "VIDEO":
                    material["type"] = "video"
                    material["media_path"] = ""
                elif material.get("type") not in {"music", "extract_music"}:
                    material["type"] = "music"
                parent.append(material)
                material_map[material_id] = material
                segment["material_id"] = material_id
                source_start, source_end = placement["source_range_us"]
                segment["source_timerange"] = {
                    "start": source_start,
                    "duration": source_end - source_start,
                }
                segment["volume"] = placement["volume"]
                if placement["volume"] == 0:
                    segment["last_nonzero_volume"] = 0
            output_segments.append(segment)
        track["segments"] = output_segments


def _active_mirror(project: Path) -> Path:
    root = read_json(project / "draft_content.json")
    timeline_id = root.get("main_timeline_id") or root.get("id")
    return project / "Timelines" / str(timeline_id) / "draft_content.json"


def validate_project(
    project: Path, production_plan_path: Path, layout_contract_path: Path
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        plan = read_json(production_plan_path)
        plan_errors = validate_plan_document(plan)
        if plan_errors:
            return {
                "status": "FAIL",
                "errors": [f"V2_PRODUCTION_PLAN_SCHEMA_INVALID:{plan_errors}"],
            }
        layout = read_json(layout_contract_path)
        root = read_json(project / "draft_content.json")
        mirror_path = _active_mirror(project)
        mirror = read_json(mirror_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"V2_PROJECT_READ:{exc}"]}
    if root != mirror:
        errors.append("V2_ROOT_TIMELINE_PARITY_MISMATCH")
    id_result = clone_and_sync.validate_id_mirrors(project)
    if id_result.get("status") != "PASS":
        errors.append("V2_ID_MIRROR_INVALID")
    role_contract = {row["role"]: row for row in layout.get("tracks", [])}
    track_by_id = {row.get("id"): row for row in root.get("tracks", []) if isinstance(row, dict)}
    if len(track_by_id) != 15:
        errors.append("V2_TRACK_COUNT_INVALID")
    material_map = {
        row.get("id"): row for row in _materials(root.get("materials", {})) if isinstance(row.get("id"), str)
    }
    text_styles = layout.get("text_styles", {})
    readback: dict[str, list[str]] = {"A10_TEXT_UNASSIGNED": []}
    observed_ids: set[str] = set()
    for role, contract_row in role_contract.items():
        track = track_by_id.get(contract_row.get("track_id"))
        if not isinstance(track, dict) or track.get("type") != contract_row.get("type"):
            errors.append(f"V2_TRACK_IDENTITY_INVALID:{role}")
            continue
        readback[role] = [row.get("id") for row in track.get("segments", []) if isinstance(row, dict)]
        for segment in track.get("segments", []):
            if not isinstance(segment, dict):
                continue
            observed_ids.add(str(segment.get("id")))
            if segment.get("material_id") not in material_map:
                errors.append(f"V2_LIVE_MATERIAL_MISSING:{segment.get('id')}")
            if role == "VIDEO" and segment.get("volume") != 0:
                errors.append("V2_VIDEO_VOLUME_INVALID")
            if role == "A11_SFX" and segment.get("volume") != 1:
                errors.append("V2_A11_SFX_VOLUME_INVALID")
        if role in {"A10_TEXT_WHITE", "A10_TEXT_YELLOW"}:
            style_contract = text_styles.get(role, {}) if isinstance(text_styles, dict) else {}
            animations = style_contract.get("animations", []) if isinstance(style_contract, dict) else []
            fuzzy_groups = {
                row.get("group_id")
                for row in animations
                if isinstance(row, dict)
                and row.get("name") == "퍼지 블러"
                and row.get("effect_id") == "7596971792351153424"
                and isinstance(row.get("group_id"), str)
            }
            if len(fuzzy_groups) != 1:
                errors.append(f"V2_FUZZY_BLUR_CONTRACT_INVALID:{role}")
            else:
                expected_group = next(iter(fuzzy_groups))
                for segment in track.get("segments", []):
                    refs = segment.get("extra_material_refs", []) if isinstance(segment, dict) else []
                    if expected_group not in refs:
                        errors.append(f"V2_FUZZY_BLUR_STYLE_INVALID:{role}")
                        break
    duration = plan.get("total_duration_us")
    for role in ("T1", "T2", "SCREEN_WHITE", "SCREEN_EFFECT"):
        contract_row = role_contract.get(role, {})
        track = track_by_id.get(contract_row.get("track_id"), {})
        segments = track.get("segments", []) if isinstance(track, dict) else []
        if len(segments) != 1 or segments[0].get("target_timerange") != {"start": 0, "duration": duration}:
            errors.append(f"V2_FULL_DURATION_READBACK_INVALID:{role}")
    a12_contract = role_contract.get("A12", {})
    a12_track = track_by_id.get(a12_contract.get("track_id"), {})
    a12_segments = a12_track.get("segments", []) if isinstance(a12_track, dict) else []
    if (
        len(a12_segments) != 1
        or a12_segments[0].get("target_timerange") != {"start": 0, "duration": duration}
        or a12_segments[0].get("volume") != 1
    ):
        errors.append("V2_A12_READBACK_INVALID")
    for placement in _flatten_placements(plan):
        placement_id = placement.get("placement_id")
        anchor = placement.get("anchor")
        if placement.get("operation") in {"omit", "clear"}:
            if placement_id in observed_ids:
                errors.append(f"V2_OMITTED_PLACEMENT_PRESENT:{placement_id}")
            continue
        if placement_id not in readback.get(str(anchor), []):
            errors.append(f"V2_PLACEMENT_READBACK_MISSING:{placement_id}")
            continue
        track = track_by_id[role_contract[str(anchor)]["track_id"]]
        segment = next(row for row in track["segments"] if row.get("id") == placement_id)
        start, end = placement["target_range_us"]
        if segment.get("target_timerange") != {"start": start, "duration": end - start}:
            errors.append(f"V2_PLACEMENT_RANGE_MISMATCH:{placement_id}")
        if "volume" in placement and segment.get("volume") != placement.get("volume"):
            errors.append(f"V2_PLACEMENT_VOLUME_MISMATCH:{placement_id}")
        if placement.get("operation") == "replace_media_and_range":
            material = material_map.get(segment.get("material_id"), {})
            media_path = material.get("path") if isinstance(material, dict) else None
            prefix = "##_draftpath_placeholder_v2_##/Resources/media/"
            if not isinstance(media_path, str) or not media_path.startswith(prefix):
                errors.append(f"V2_MEDIA_PATH_NOT_PORTABLE:{placement_id}")
            else:
                relative_name = media_path[len(prefix):]
                if (
                    not relative_name
                    or "/" in relative_name
                    or "\\" in relative_name
                    or not (project / "Resources" / "media" / relative_name).is_file()
                ):
                    errors.append(f"V2_MEDIA_PATH_NOT_PORTABLE:{placement_id}")
        if "text" in placement:
            material = material_map.get(segment.get("material_id"), {})
            if _material_text(material) != placement["text"]:
                errors.append(f"V2_PLACEMENT_TEXT_MISMATCH:{placement_id}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "readback": readback,
        "track_count": len(track_by_id),
        "root_timeline_parity": "PASS" if root == mirror else "FAIL",
        "id_mirror": id_result.get("status"),
    }


def build_project(
    production_plan_path: Path,
    root_contract_path: Path,
    workspace_root: Path,
    asset_manifest_path: Path,
    output_project: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    output_project = output_project.resolve()
    stage_root = output_project.parent / f".{output_project.name}.staging-{uuid.uuid4().hex}"
    archive: Path | None = None
    archive_sha_before: str | None = None
    promoted_by_this_run = False
    try:
        plan = read_json(production_plan_path)
        plan_errors = validate_plan_document(plan)
        if plan_errors:
            raise ValueError(f"V2_PRODUCTION_PLAN_SCHEMA_INVALID:{plan_errors}")
        if plan.get("schema_version") != "001short-production-plan-v2":
            raise ValueError("V2_PRODUCTION_PLAN_REQUIRED")
        if output_project.exists():
            raise ValueError("V2_OUTPUT_PROJECT_EXISTS")
        layout, archive, layout_path = _resolve_profile(
            root_contract_path.resolve(), workspace_root.resolve(), str(plan.get("root_profile", ""))
        )
        archive_sha_before = sha256(archive)
        assets = read_json(asset_manifest_path)
        _validate_asset_destinations(plan, asset_manifest_path.resolve(), assets)
        stage_root.mkdir(parents=True)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(stage_root)
        source_project = _find_project(stage_root)
        _validate_root_asset_destinations(
            plan, asset_manifest_path.resolve(), assets, source_project
        )
        source_hashes = clone_and_sync.hash_project_core(source_project)
        project = stage_root / "working_project"
        cloned = clone_and_sync.clone_project(source_project, project)
        if cloned.get("status") != "PASS":
            raise ValueError(f"V2_ROOT_CLONE_FAILED:{cloned}")
        track_ids = {row["track_id"] for row in layout["tracks"]}
        documents = _contracted_documents(project, track_ids)
        if len(documents) < 2:
            raise ValueError(f"V2_ROOT_TIMELINE_MIRROR_MISSING:{len(documents)}")
        for path in documents:
            payload = read_json(path)
            _apply_document(
                payload,
                plan=plan,
                layout=layout,
                assets=assets,
                asset_manifest_path=asset_manifest_path.resolve(),
                project=project,
            )
            write_json(path, payload)
        project_id = "project-" + uuid.uuid5(uuid.NAMESPACE_URL, f"{plan['episode_id']}:project").hex
        draft_id = "draft-" + uuid.uuid5(uuid.NAMESPACE_URL, f"{plan['episode_id']}:draft").hex
        timeline_id = "timeline-" + uuid.uuid5(uuid.NAMESPACE_URL, f"{plan['episode_id']}:timeline").hex
        synced = clone_and_sync.sync_project_ids(
            project,
            project_id,
            draft_id,
            timeline_id,
            source_project_path=source_project,
            expected_source_hashes=source_hashes,
        )
        if synced.get("status") != "PASS":
            raise ValueError(f"V2_ID_SYNC_FAILED:{synced}")
        meta_path = project / "draft_meta_info.json"
        meta = read_json(meta_path)
        meta.update(draft_id=draft_id, draft_name=plan["project_name"], tm_duration=plan["total_duration_us"])
        write_json(meta_path, meta)
        root_payload = read_json(project / "draft_content.json")
        mirror_path = _active_mirror(project)
        for path in (
            project / "draft_info.json",
            project / "template-2.tmp",
            mirror_path.with_name("draft_info.json"),
            mirror_path.with_name("template-2.tmp"),
        ):
            write_json(path, root_payload)
        checked = validate_project(project, production_plan_path, layout_path)
        if checked["status"] != "PASS":
            raise ValueError(f"V2_PROJECT_VALIDATION_FAILED:{checked['errors']}")
        if sha256(archive) != archive_sha_before:
            raise ValueError("V2_ROOT_ARCHIVE_MUTATED")
        output_project.parent.mkdir(parents=True, exist_ok=True)
        project.rename(output_project)
        promoted_by_this_run = True
        if stage_root.exists():
            shutil.rmtree(stage_root)
        receipt = {
            "status": "PASS",
            "episode_id": plan["episode_id"],
            "project_path": str(output_project),
            "production_plan_path": str(production_plan_path.resolve()),
            "production_plan_sha256": sha256(production_plan_path),
            "root_contract_path": str(root_contract_path.resolve()),
            "layout_contract_path": str(layout_path.resolve()),
            "root_archive_path": str(archive.resolve()),
            "root_archive_sha256_before": archive_sha_before,
            "root_archive_sha256_after": sha256(archive),
            "track_count": checked["track_count"],
            "root_timeline_parity": checked["root_timeline_parity"],
            "id_mirror": checked["id_mirror"],
            "readback": checked["readback"],
        }
        write_json(receipt_path, receipt)
        return receipt
    except Exception as exc:
        if stage_root.exists():
            shutil.rmtree(stage_root)
        if promoted_by_this_run and output_project.exists():
            shutil.rmtree(output_project)
        return {"status": "FAIL", "errors": [str(exc)]}
