from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from common import read_json, result, sha256_file


def _error(code: str, **detail: Any) -> dict:
    return {"code": code, **detail}


def _range(value: object) -> tuple[int, int] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    start, end = value
    if any(not isinstance(item, int) or isinstance(item, bool) for item in (start, end)):
        return None
    return (start, end) if 0 <= start < end else None


def _coalesced_clip_count(clips: list[dict]) -> int:
    ordered = sorted(clips, key=lambda row: row["target_range_us"][0])
    groups = 0
    previous: dict | None = None
    for clip in ordered:
        if previous is None:
            groups += 1
        else:
            same_source = clip["source_sha256"].lower() == previous["source_sha256"].lower()
            source_continuous = clip["source_range_us"][0] == previous["source_range_us"][1]
            target_continuous = clip["target_range_us"][0] == previous["target_range_us"][1]
            same_speed = clip.get("speed", 1) == previous.get("speed", 1)
            if not (same_source and source_continuous and target_continuous and same_speed):
                groups += 1
        previous = clip
    return groups


def _probe_video(path: Path) -> dict | None:
    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                "-show_entries", "stream=width,height,nb_read_frames:format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode:
            return None
        payload = json.loads(completed.stdout)
        stream = payload["streams"][0]
        measured = {
            "duration_us": round(float(payload["format"]["duration"]) * 1_000_000),
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "frame_count": int(stream["nb_read_frames"]),
        }
        return measured if all(value > 0 for value in measured.values()) else None
    except (OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _media_binding_valid(section: dict, path: Path, sha_field: str) -> bool:
    declared_sha = section.get(sha_field)
    measured = _probe_video(path) if path.is_file() and not path.is_symlink() else None
    return bool(
        measured
        and isinstance(declared_sha, str)
        and len(declared_sha) == 64
        and sha256_file(path).lower() == declared_sha.lower()
        and all(
            isinstance(section.get(field), int)
            and not isinstance(section.get(field), bool)
            and section[field] == measured[field]
            for field in ("duration_us", "width", "height", "frame_count")
        )
    )


def _manifest_errors(manifest: object) -> tuple[list[dict], dict | None]:
    if not isinstance(manifest, dict):
        return [_error("E_MANIFEST_INVALID", field="root")], None
    required = ("schema_version", "episode_id", "source", "template", "vmake", "urakkai", "source_audio")
    if any(field not in manifest for field in required):
        return [_error("E_MANIFEST_INVALID", field="required")], None
    if manifest.get("schema_version") != "001short-build-manifest-v1":
        return [_error("E_MANIFEST_INVALID", field="schema_version")], None
    if not isinstance(manifest.get("episode_id"), str) or not manifest["episode_id"].strip():
        return [_error("E_MANIFEST_INVALID", field="episode_id")], None
    return [], manifest


def validate_prebuild(build_manifest_path: Path) -> dict:
    path = Path(build_manifest_path).resolve()
    try:
        manifest = read_json(path)
    except (OSError, ValueError, TypeError) as exc:
        return result([_error("E_MANIFEST_INVALID", detail=str(exc))])
    errors, payload = _manifest_errors(manifest)
    if errors or payload is None:
        return result(errors)

    source = payload["source"]
    template = payload["template"]
    # `vmake` is the locked external key for the generic clean-source envelope.
    clean_source = payload["vmake"]
    urakkai = payload["urakkai"]
    if not isinstance(source, dict) or not isinstance(template, dict) or not isinstance(clean_source, dict) or not isinstance(urakkai, dict):
        return result([_error("E_MANIFEST_INVALID", field="sections")])
    source_path = Path(source.get("path", "")).resolve()
    source_sha = source.get("sha256")
    source_duration = source.get("duration_us")
    if not _media_binding_valid(source, source_path, "sha256"):
        errors.append(_error("E_MANIFEST_INVALID", field="source"))
    root_zip = Path(template.get("root_zip_path", "")).resolve()
    root_sha = template.get("root_zip_sha256")
    if (
        template.get("root_name") != "shrt white" or not root_zip.is_file()
        or not isinstance(root_sha, str) or len(root_sha) != 64
        or sha256_file(root_zip).lower() != root_sha.lower()
    ):
        errors.append(_error("E_MANIFEST_INVALID", field="template"))

    clean_source_type = clean_source.get("source_type", "VMAKE")
    output_path = Path(clean_source.get("output_path", "")).resolve()
    output_sha = clean_source.get("output_sha256")
    if clean_source_type not in {"VMAKE", "USER_PROVIDED", "SOURCE_PROVISIONAL"}:
        errors.append(_error("E_CLEAN_SOURCE_TYPE", actual=clean_source_type))
    if not _media_binding_valid(clean_source, output_path, "output_sha256"):
        errors.append(_error("E_CLEAN_MEDIA_BINDING"))
    if str(clean_source.get("input_sha256", "")).lower() != str(source_sha).lower():
        errors.append(_error("E_CLEAN_MEDIA_BINDING", detail="source_origin"))
    if isinstance(source_duration, int) and isinstance(clean_source.get("duration_us"), int):
        if abs(clean_source["duration_us"] - source_duration) > 50_000:
            errors.append(_error("E_CLEAN_MEDIA_BINDING", detail="duration"))

    receipt_path = Path(clean_source.get("receipt_path", "")).resolve()
    try:
        receipt = read_json(receipt_path)
    except (OSError, ValueError, TypeError):
        receipt = None
    vmake_receipt_binding_fields = ("run_id", "job_id", "input_sha256", "output_sha256")
    if clean_source_type == "VMAKE" and (
        not isinstance(receipt, dict) or receipt.get("provider") != "vmake"
        or not clean_source.get("final_download") or not receipt.get("final_download")
        or any(
            not isinstance(clean_source.get(field), str) or not clean_source[field]
            for field in vmake_receipt_binding_fields
        )
        or receipt.get("run_id") != clean_source.get("run_id")
        or receipt.get("job_id") != clean_source.get("job_id")
        or receipt.get("uploaded_source_sha256", "").lower() != str(clean_source.get("input_sha256", "")).lower()
        or receipt.get("downloaded_output_sha256", "").lower() != str(clean_source.get("output_sha256", "")).lower()
        or str(clean_source.get("input_sha256", "")).lower() != str(source_sha).lower()
        or str(clean_source.get("output_sha256", "")).lower() == str(source_sha).lower()
    ):
        errors.append(_error("E_VMAKE_BINDING"))
    if clean_source_type == "USER_PROVIDED" and (
        output_path == source_path or str(output_sha).lower() == str(source_sha).lower()
    ):
        code = "E_SOURCE_AS_CLEAN_VIDEO" if output_path.name.casefold() == "clean_video.mp4" else "E_CLEAN_MEDIA_BINDING"
        errors.append(_error(code))
    if clean_source_type == "SOURCE_PROVISIONAL" and (
        output_path != source_path or str(output_sha).lower() != str(source_sha).lower()
    ):
        errors.append(_error("E_SOURCE_PROVISIONAL_BINDING"))

    clips = urakkai.get("video_clips")
    target_duration = urakkai.get("target_duration_us")
    if urakkai.get("production_type") != "URAKKAI" or not isinstance(clips, list) or not clips:
        errors.append(_error("E_MANIFEST_INVALID", field="urakkai"))
        clips = []
    if not isinstance(target_duration, int) or isinstance(target_duration, bool) or target_duration <= 0:
        errors.append(_error("E_MANIFEST_INVALID", field="urakkai.target_duration_us"))
        target_duration = 0
    normalized_clips: list[dict] = []
    clip_ids: set[str] = set()
    for clip in clips:
        if not isinstance(clip, dict) or not isinstance(clip.get("clip_id"), str) or clip["clip_id"] in clip_ids:
            errors.append(_error("E_VIDEO_RANGE"))
            continue
        clip_ids.add(clip["clip_id"])
        source_range = _range(clip.get("source_range_us"))
        target_range = _range(clip.get("target_range_us"))
        if (
            source_range is None or target_range is None
            or source_range[1] > source_duration or target_range[1] > target_duration
            or clip.get("source_sha256", "").lower() != str(source_sha).lower()
            or source_range[1] - source_range[0] != target_range[1] - target_range[0]
        ):
            errors.append(_error("E_VIDEO_RANGE", clip_id=clip.get("clip_id")))
            continue
        normalized_clips.append({**clip, "source_range_us": list(source_range), "target_range_us": list(target_range)})
    ordered = sorted(normalized_clips, key=lambda row: row["target_range_us"][0])
    target_cursor = 0
    for clip in ordered:
        if clip["target_range_us"][0] != target_cursor:
            errors.append(_error("E_VIDEO_RANGE", detail="target_coverage"))
            break
        target_cursor = clip["target_range_us"][1]
    if target_cursor != target_duration:
        errors.append(_error("E_VIDEO_RANGE", detail="target_end"))
    if _coalesced_clip_count(normalized_clips) < 2:
        errors.append(_error("E_EFFECTIVE_CLIP"))

    if urakkai.get("reorder_required"):
        permutation = urakkai.get("locked_permutation")
        if not isinstance(permutation, list) or permutation != [row["clip_id"] for row in ordered]:
            errors.append(_error("E_LOCKED_ORDER"))

    audio_rows = payload.get("source_audio")
    if not isinstance(audio_rows, list):
        errors.append(_error("E_MANIFEST_INVALID", field="source_audio"))
        audio_rows = []
    audio_by_clip: dict[str, list[dict]] = {}
    for row in audio_rows:
        if not isinstance(row, dict) or row.get("mode") not in {"on", "duck", "mute"}:
            errors.append(_error("E_AUDIO_BINDING"))
            continue
        audio_by_clip.setdefault(str(row.get("clip_id")), []).append(row)
    for clip in normalized_clips:
        rows = audio_by_clip.get(clip["clip_id"], [])
        if len(rows) != 1:
            errors.append(_error("E_AUDIO_BINDING", clip_id=clip["clip_id"]))
            continue
        row = rows[0]
        if row.get("mode") in {"on", "duck"} and (
            str(row.get("source_sha256", "")).lower() != str(source_sha).lower()
            or row.get("source_range_us") != clip["source_range_us"]
            or row.get("target_range_us") != clip["target_range_us"]
        ):
            errors.append(_error("E_AUDIO_BINDING", clip_id=clip["clip_id"]))
        capcut_source_range = row.get("capcut_source_range_us")
        if capcut_source_range is not None:
            normalized_capcut_range = _range(capcut_source_range)
            target_range = _range(clip["target_range_us"])
            if (
                normalized_capcut_range is None
                or target_range is None
                or normalized_capcut_range[1] - normalized_capcut_range[0]
                != target_range[1] - target_range[0]
            ):
                errors.append(_error("E_AUDIO_BINDING", clip_id=clip["clip_id"]))
    evidence = {
        "build_manifest_path": str(path),
        "episode_id": payload["episode_id"],
        "clean_source_type": clean_source_type,
        "provisional": clean_source_type == "SOURCE_PROVISIONAL",
        "deferred_replacements": (
            ["CLEAN_SOURCE_SWAP_NONBLOCKING"] if clean_source_type == "SOURCE_PROVISIONAL" else []
        ),
    }
    return result(errors, evidence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-manifest", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_prebuild(args.build_manifest)
    print(__import__("json").dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
