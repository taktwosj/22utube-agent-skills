from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import read_json, result, sha256_file
from validate_prebuild import validate_prebuild


def _error(code: str, **detail: Any) -> dict:
    return {"code": code, **detail}


def _material_map(value: Any) -> dict[str, dict]:
    found: dict[str, dict] = {}
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            found[value["id"]] = value
        for child in value.values():
            found.update(_material_map(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_material_map(child))
    return found


def _range(segment: dict, name: str) -> list[int] | None:
    value = segment.get(name)
    if not isinstance(value, dict):
        return None
    start, duration = value.get("start"), value.get("duration")
    if not isinstance(start, int) or not isinstance(duration, int) or duration <= 0:
        return None
    return [start, start + duration]


def _asset(project: Path, raw_path: object) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    normalized = raw_path.replace("\\", "/")
    marker = "Resources/"
    if marker in normalized:
        normalized = normalized[normalized.index(marker):]
    path = Path(normalized)
    if path.is_absolute():
        return None
    candidate = (project / path).resolve()
    try:
        candidate.relative_to(project.resolve())
    except ValueError:
        return None
    return candidate


def _volume_is(segment: dict, expected: float) -> bool:
    value = segment.get("volume")
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and abs(float(value) - expected) < 1e-9
    )


def validate_postbuild(build_manifest_path: Path, project_path: Path, *, visual_asset_mode: str = "CLEAN_VISUAL_READY") -> dict:
    manifest = read_json(Path(build_manifest_path).resolve())
    source_provisional = (
        visual_asset_mode == "SOURCE_VIDEO_PROVISIONAL"
        or manifest.get("visual_asset_mode") == "SOURCE_VIDEO_PROVISIONAL"
    )
    pre = validate_prebuild(build_manifest_path, allow_source_provisional=source_provisional)
    if pre["status"] != "PASS":
        return result([_error("E_MANIFEST_INVALID", prerequisite_errors=pre["errors"])])
    project = Path(project_path).resolve()
    content_path = project / "draft_content.json"
    try:
        content = read_json(content_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([_error("E_DRAFT_MISMATCH", detail=str(exc))])
    if not isinstance(content, dict) or not isinstance(content.get("tracks"), list):
        return result([_error("E_DRAFT_MISMATCH", detail="tracks")])
    materials = _material_map(content.get("materials", {}))
    actual_video: list[dict] = []
    actual_a10: list[dict] = []
    for track in content["tracks"]:
        for segment in track.get("segments", []) if isinstance(track, dict) else []:
            if not isinstance(segment, dict):
                continue
            role = segment.get("role")
            if role == "VIDEO":
                actual_video.append(segment)
            elif role == "A10":
                actual_a10.append(segment)
    actual_video.sort(key=lambda row: (_range(row, "target_timerange") or [10**30])[0])
    expected = sorted(manifest["urakkai"]["video_clips"], key=lambda row: row["target_range_us"][0])
    errors: list[dict] = []
    if len(actual_video) != len(expected):
        errors.append(_error("E_DRAFT_MISMATCH", detail="video_count"))
    for actual, planned in zip(actual_video, expected):
        if (
            actual.get("id") != planned["clip_id"]
            or _range(actual, "source_timerange") != planned["source_range_us"]
            or _range(actual, "target_timerange") != planned["target_range_us"]
        ):
            errors.append(_error("E_DRAFT_MISMATCH", clip_id=planned["clip_id"]))
            continue
        material = materials.get(actual.get("material_id"))
        asset = _asset(project, material.get("path") if isinstance(material, dict) else None)
        expected_sha = manifest["source"]["sha256"] if source_provisional else manifest["vmake"]["output_sha256"]
        if not isinstance(material, dict) or material.get("type") != "video" or asset is None or not asset.is_file() or sha256_file(asset).lower() != expected_sha.lower():
            errors.append(_error("E_DRAFT_MISMATCH", clip_id=planned["clip_id"], detail="vmake_media"))
        if source_provisional and not _volume_is(actual, 0.0):
            errors.append(_error(
                "E_DRAFT_MISMATCH", clip_id=planned["clip_id"],
                detail="provisional_video_not_muted",
            ))
    audio_by_clip = {row["clip_id"]: row for row in manifest["source_audio"] if row.get("mode") in {"on", "duck"}}
    if len(actual_a10) != len(audio_by_clip):
        errors.append(_error("E_DRAFT_MISMATCH", detail="a10_count"))
    actual_a10.sort(key=lambda row: (_range(row, "target_timerange") or [10**30])[0])
    for actual, planned in zip(actual_a10, [audio_by_clip[row["clip_id"]] for row in expected if row["clip_id"] in audio_by_clip]):
        expected_source_range = planned.get("capcut_source_range_us", planned["source_range_us"])
        if _range(actual, "source_timerange") != expected_source_range or _range(actual, "target_timerange") != planned["target_range_us"]:
            errors.append(_error("E_DRAFT_MISMATCH", detail="a10_range"))
        if source_provisional and not _volume_is(actual, 1.0):
            errors.append(_error("E_DRAFT_MISMATCH", detail="provisional_a10_volume"))
    if manifest["urakkai"].get("reorder_required"):
        if [row.get("id") for row in actual_video] != manifest["urakkai"].get("locked_permutation"):
            errors.append(_error("E_DRAFT_MISMATCH", detail="order"))
    return result(errors, {"actual_draft_content": str(content_path), "episode_id": manifest["episode_id"]})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--visual-asset-mode", default="CLEAN_VISUAL_READY")
    args = parser.parse_args()
    payload = validate_postbuild(args.build_manifest, args.project, visual_asset_mode=args.visual_asset_mode)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
