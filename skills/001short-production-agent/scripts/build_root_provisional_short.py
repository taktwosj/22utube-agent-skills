from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import apply_capcut_polish_profile
import build_episode_capcut
import clone_and_sync
import resolve_shorts_capcut_root
import validate_capcut_polish_profile
from capcut_io import iter_timeline_json


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _capcut_open() -> bool:
    completed = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, check=False)
    names = completed.stdout.casefold()
    return "capcut.exe" in names or "lveditor.exe" in names


def _range(row: dict, start_key: str, duration_key: str) -> tuple[int, int]:
    start = row.get(start_key)
    duration = row.get(duration_key)
    if not isinstance(start, int) or not isinstance(duration, int) or start < 0 or duration <= 0:
        raise ValueError(f"ASSEMBLY_RANGE_INVALID:{row.get('clip_id', '')}")
    return start, start + duration


def _probe_duration_us(path: Path) -> int:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=False,
    )
    if completed.returncode:
        raise RuntimeError("MEDIA_PROBE_FAILED")
    try:
        value = round(float(completed.stdout.strip()) * 1_000_000)
    except ValueError as exc:
        raise RuntimeError("MEDIA_DURATION_INVALID") from exc
    if value <= 0:
        raise RuntimeError("MEDIA_DURATION_INVALID")
    return value


def _validate_root_timeline(
    project: Path,
    duration_us: int,
    clip_count: int,
    title1: str,
    title2: str,
    *,
    audio_policy: str,
    tts_cues: list[dict],
) -> dict:
    checked = 0
    for path, payload in [(project / "draft_content.json", json.loads((project / "draft_content.json").read_text(encoding="utf-8"))), *iter_timeline_json(project)]:
        if not isinstance(payload, dict) or not isinstance(payload.get("tracks"), list):
            continue
        tracks = payload["tracks"]
        if len(tracks) != 12:
            continue
        checked += 1
        tts_only = audio_policy == "TTS_ONLY_MUTE_SOURCE"
        expected_counts = (
            {0: clip_count, 1: 1, 2: 1, 3: 0, 4: 0, 5: len(tts_cues), 6: 1, 7: 1, 8: len(tts_cues), 9: 0, 10: 0, 11: 0}
            if tts_only
            else {0: clip_count, 1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 1, 7: 1, 8: 0, 9: clip_count, 10: 0, 11: 0}
        )
        for index, expected in expected_counts.items():
            if len(tracks[index].get("segments", [])) != expected:
                raise RuntimeError(f"ROOT_TRACK_SEGMENT_COUNT_INVALID:{index}")
        for index in (1, 2, 6, 7):
            segment = tracks[index]["segments"][0]
            target = segment.get("target_timerange", {})
            if target.get("start") != 0 or target.get("duration") != duration_us:
                raise RuntimeError(f"ROOT_FIXED_RANGE_INVALID:{index}")
        materials = {row.get("id"): row for row in build_episode_capcut._materials(payload.get("materials", {}))}
        expected_text = {6: title2, 7: title1}
        for index, text in expected_text.items():
            material = materials.get(tracks[index]["segments"][0].get("material_id"), {})
            actual = build_episode_capcut._material_text(material)
            if (text and actual != text) or (not text and actual not in {None, ""}):
                raise RuntimeError(f"ROOT_TITLE_TEXT_INVALID:{index}")
        if tts_only:
            for video in tracks[0]["segments"]:
                if video.get("volume") != 0.0:
                    raise RuntimeError("ROOT_VIDEO_NOT_MUTED")
            for cue, a9, caption in zip(tts_cues, tracks[8]["segments"], tracks[5]["segments"]):
                expected_range = {"start": cue["target_start_us"], "duration": cue["target_duration_us"]}
                if a9.get("target_timerange") != expected_range or caption.get("target_timerange") != expected_range:
                    raise RuntimeError("ROOT_A9_TEXT_TIME_MAPPING_INVALID")
                material = materials.get(caption.get("material_id"), {})
                if build_episode_capcut._material_text(material) != cue["text"]:
                    raise RuntimeError("ROOT_A9_TEXT_INVALID")
        else:
            for video, audio in zip(tracks[0]["segments"], tracks[9]["segments"]):
                if video.get("target_timerange") != audio.get("target_timerange") or video.get("source_timerange") != audio.get("source_timerange"):
                    raise RuntimeError("ROOT_VIDEO_A10_MAPPING_INVALID")
    if checked < 2:
        raise RuntimeError("ROOT_TIMELINE_MIRROR_MISSING")
    return {
        "root_and_mirrors_checked": checked,
        "track_layout": 12,
        "video_segments": clip_count,
        "a9_segments": len(tts_cues) if audio_policy == "TTS_ONLY_MUTE_SOURCE" else 0,
        "a10_segments": 0 if audio_policy == "TTS_ONLY_MUTE_SOURCE" else clip_count,
        "a12_segments": 0,
    }


def build(args: argparse.Namespace) -> dict:
    if _capcut_open():
        raise RuntimeError("CAPCUT_PROCESS_OPEN")
    workspace = args.workspace_root.resolve()
    evidence = args.episode_evidence_root.resolve()
    source_video = args.source_video.resolve()
    source_audio = args.source_audio.resolve() if args.source_audio else None
    target_root = args.capcut_root.resolve()
    target = target_root / args.project_name
    if not source_video.is_file():
        raise RuntimeError("ASSEMBLY_INPUT_MEDIA_MISSING")
    if target.exists():
        raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
    contract = resolve_shorts_capcut_root.resolve_root_contract(workspace, "home_windows", args.root_contract)
    assembly = json.loads(args.assembly_input.read_text(encoding="utf-8"))
    timeline = assembly.get("timeline", {})
    clips = timeline.get("clips")
    duration_us = timeline.get("target_duration_us")
    if not isinstance(clips, list) or not clips or not isinstance(duration_us, int) or duration_us <= 0:
        raise RuntimeError("ASSEMBLY_INPUT_INVALID")
    audio_policy = timeline.get("audio_policy", "A10_RETAINED_SYNC")
    if audio_policy not in {"A10_RETAINED_SYNC", "TTS_ONLY_MUTE_SOURCE"}:
        raise RuntimeError("ASSEMBLY_AUDIO_POLICY_INVALID")
    tts_cues_raw = timeline.get("tts_cues", [])
    silent_visual_ranges_raw = timeline.get("silent_visual_ranges", [])
    if audio_policy == "TTS_ONLY_MUTE_SOURCE" and not isinstance(tts_cues_raw, list):
        raise RuntimeError("ASSEMBLY_TTS_CUES_INVALID")
    if audio_policy == "TTS_ONLY_MUTE_SOURCE" and not isinstance(silent_visual_ranges_raw, list):
        raise RuntimeError("ASSEMBLY_SILENT_VISUAL_RANGES_INVALID")
    cursor = 0
    video_clips, source_audio_rows, approved_rows = [], [], []
    source_sha = _sha256(source_video)
    for order, clip in enumerate(clips, start=1):
        source_start, source_end = _range(clip, "source_start_us", "source_duration_us")
        target_start, target_end = _range(clip, "target_start_us", "target_duration_us")
        if target_start != cursor or source_end - source_start != target_end - target_start:
            raise RuntimeError("ASSEMBLY_TIMELINE_NOT_CONTIGUOUS")
        cursor = target_end
        clip_id = str(clip.get("clip_id") or f"C{order:02d}")
        video_clips.append({"clip_id": clip_id, "source_range_us": [source_start, source_end], "target_range_us": [target_start, target_end], "source_sha256": source_sha})
        if audio_policy == "A10_RETAINED_SYNC":
            source_audio_rows.append({"clip_id": clip_id, "mode": "on", "source_range_us": [source_start, source_end], "target_range_us": [target_start, target_end], "source_sha256": source_sha})
        approved_rows.append({"segment_id": clip_id, "timeline_order": order, "role": "VIDEO", "start": target_start, "duration": target_end - target_start, "source_ref": clip_id})
        if audio_policy == "A10_RETAINED_SYNC":
            approved_rows.append({"segment_id": f"A10_{clip_id}", "timeline_order": 50 + order, "role": "A10", "start": target_start, "duration": target_end - target_start, "source_ref": clip_id})
    if cursor != duration_us:
        raise RuntimeError("ASSEMBLY_TARGET_DURATION_MISMATCH")
    tts_cues: list[dict] = []
    silent_visual_ranges: list[tuple[int, int]] = []
    if audio_policy == "A10_RETAINED_SYNC":
        if source_audio is None or not source_audio.is_file():
            raise RuntimeError("ASSEMBLY_INPUT_MEDIA_MISSING")
        audio_duration_us = _probe_duration_us(source_audio)
        if audio_duration_us + 100_000 < max(row["source_range_us"][1] for row in source_audio_rows):
            raise RuntimeError("ASSEMBLY_VOCAL_STEM_TOO_SHORT")
    else:
        if not tts_cues_raw:
            raise RuntimeError("ASSEMBLY_TTS_CUE_COUNT_MISMATCH")
        video_ranges = [tuple(row["target_range_us"]) for row in video_clips]
        cue_ranges: list[tuple[int, int]] = []
        for index, raw in enumerate(tts_cues_raw, start=1):
            if not isinstance(raw, dict):
                raise RuntimeError("ASSEMBLY_TTS_CUE_INVALID")
            audio_path = Path(str(raw.get("audio_path", ""))).resolve()
            text = raw.get("text")
            start = raw.get("target_start_us")
            cue_duration = raw.get("target_duration_us")
            if (
                not isinstance(text, str) or not text.strip() or not audio_path.is_file()
                or not isinstance(start, int) or not isinstance(cue_duration, int) or cue_duration <= 0
            ):
                raise RuntimeError(f"ASSEMBLY_TTS_CUE_INVALID:{index}")
            end = start + cue_duration
            if not any(video_start <= start and end <= video_end for video_start, video_end in video_ranges):
                raise RuntimeError(f"ASSEMBLY_TTS_CUE_OUTSIDE_VIDEO:{index}")
            cue_ranges.append((start, end))
            actual_duration = _probe_duration_us(audio_path)
            if abs(actual_duration - cue_duration) > 100_000:
                raise RuntimeError(f"ASSEMBLY_TTS_DURATION_MISMATCH:{index}")
            cue_id = str(raw.get("cue_id") or f"TTS_{index:02d}")
            resource_name = f"tts_{index:02d}{audio_path.suffix.lower() or '.wav'}"
            cue = {
                "cue_id": cue_id,
                "text": text.strip(),
                "audio_path": str(audio_path),
                "audio_sha256": _sha256(audio_path),
                "audio_duration_us": actual_duration,
                "resource_name": resource_name,
                "target_start_us": start,
                "target_duration_us": cue_duration,
                "target_range_us": [start, start + cue_duration],
            }
            tts_cues.append(cue)
            approved_rows.append({"segment_id": f"A9_{cue_id}", "timeline_order": 50 + index, "role": "A9", "start": start, "duration": cue_duration, "source_ref": cue_id})
            approved_rows.append({"segment_id": f"A9_TEXT_{cue_id}", "timeline_order": 70 + index, "role": "A9_TEXT", "start": start, "duration": cue_duration, "source_ref": cue_id})
        for index, raw in enumerate(silent_visual_ranges_raw, start=1):
            if not isinstance(raw, dict):
                raise RuntimeError("ASSEMBLY_SILENT_VISUAL_RANGE_INVALID")
            start = raw.get("target_start_us")
            silent_duration = raw.get("target_duration_us")
            if not isinstance(start, int) or not isinstance(silent_duration, int) or silent_duration <= 0:
                raise RuntimeError(f"ASSEMBLY_SILENT_VISUAL_RANGE_INVALID:{index}")
            end = start + silent_duration
            if not any(video_start <= start and end <= video_end for video_start, video_end in video_ranges):
                raise RuntimeError(f"ASSEMBLY_SILENT_VISUAL_OUTSIDE_VIDEO:{index}")
            silent_visual_ranges.append((start, end))
        coverage_ranges = cue_ranges + silent_visual_ranges
        if coverage_ranges != sorted(coverage_ranges):
            raise RuntimeError("ASSEMBLY_TTS_CUES_NOT_SORTED")
        for video_start, video_end in video_ranges:
            cursor = video_start
            for cue_start, cue_end in coverage_ranges:
                if cue_end <= video_start or cue_start >= video_end:
                    continue
                if cue_start != cursor or cue_end > video_end:
                    raise RuntimeError("ASSEMBLY_TTS_CUE_COVERAGE_INVALID")
                cursor = cue_end
            if cursor != video_end:
                raise RuntimeError("ASSEMBLY_TTS_CUE_COVERAGE_INVALID")
    approved_rows.extend([
        {"segment_id": "SCREEN_EFFECT_FIXED", "timeline_order": 100, "role": "SCREEN_EFFECT", "start": 0, "duration": duration_us, "source_ref": "root"},
        {"segment_id": "SCREEN_WHITE_FIXED", "timeline_order": 101, "role": "SCREEN_WHITE", "start": 0, "duration": duration_us, "source_ref": "root"},
        {"segment_id": "T2_FIXED", "timeline_order": 102, "role": "T2", "start": 0, "duration": duration_us, "source_ref": "new_copy"},
        {"segment_id": "T1_FIXED", "timeline_order": 103, "role": "T1", "start": 0, "duration": duration_us, "source_ref": "new_copy"},
    ])
    # The canonical builder compares the authority ledger to the root timeline
    # sorted by (target start, segment id), so make that order explicit here.
    for timeline_order, row in enumerate(sorted(approved_rows, key=lambda row: (row["start"], row["segment_id"])), start=1):
        row["timeline_order"] = timeline_order
    evidence.mkdir(parents=True, exist_ok=False)
    approved_path = evidence / "approved_timeline.json"
    _write(approved_path, {"episode_id": args.episode_id, "segments": approved_rows})
    build_manifest = {
        "urakkai": {"video_clips": video_clips},
        "source_audio": source_audio_rows,
        "tts_cues": tts_cues,
        "silent_visual_ranges": [
            {"target_range_us": [start, end], "role": "SILENT_VISUAL"}
            for start, end in silent_visual_ranges
        ],
    }
    manifest_path = evidence / "root_assembly_manifest.json"
    _write(manifest_path, {"status": "PROVISIONAL_SOURCE_VIDEO", "episode_id": args.episode_id, "title1": args.title1, "title2": args.title2, "audio_policy": audio_policy, "source_video": str(source_video), "source_video_sha256": source_sha, "source_audio": str(source_audio) if source_audio else "", "source_audio_sha256": _sha256(source_audio) if source_audio else "", "root_contract": contract, "timeline": build_manifest})

    staging = target_root / (".stage_" + args.project_name + "_" + uuid.uuid4().hex)
    authority = staging / "authority"
    working = staging / "working"
    registry_backup = evidence / "root_meta_info.before.json"
    try:
        source_root = build_episode_capcut._extract_template(Path(contract["archive"]), authority)
        source_hashes = clone_and_sync.hash_project_core(source_root)
        cloned = clone_and_sync.clone_project(source_root, working)
        if cloned["status"] != "PASS":
            raise RuntimeError(f"ROOT_CLONE_FAILED:{cloned['errors']}")
        synced = clone_and_sync.sync_project_ids(working, "project-" + uuid.uuid4().hex, "draft-" + uuid.uuid4().hex, "timeline-" + uuid.uuid4().hex, source_project_path=source_root, expected_source_hashes=source_hashes)
        if synced["status"] != "PASS":
            raise RuntimeError(f"ROOT_ID_SYNC_FAILED:{synced['errors']}")
        config = {
            "episode_id": args.episode_id, "clean_video": str(source_video), "duration_us": duration_us,
            "T1": args.title1, "T2": args.title2,
            "state_cues": [], "approved_timeline_path": str(approved_path), "audio_role": "A10",
            "audio_policy": audio_policy, "tts_cues": tts_cues,
            "segment_ids": {
                "SCREEN_EFFECT": "SCREEN_EFFECT_FIXED", "SCREEN_WHITE": "SCREEN_WHITE_FIXED", "T2": "T2_FIXED", "T1": "T1_FIXED",
                "A9": [f"A9_{cue['cue_id']}" for cue in tts_cues],
                "A9_TEXT": [f"A9_TEXT_{cue['cue_id']}" for cue in tts_cues],
            },
        }
        build_episode_capcut._normalize_source(working, config, source_audio, build_manifest)
        polish = apply_capcut_polish_profile.apply_project(working)
        polish_check = validate_capcut_polish_profile.validate_project(working)
        if polish_check["status"] != "PASS":
            raise RuntimeError(f"POLISH_VALIDATION_FAILED:{polish_check['errors']}")
        static = _validate_root_timeline(working, duration_us, len(clips), args.title1, args.title2, audio_policy=audio_policy, tts_cues=tts_cues)
        if target.exists():
            raise RuntimeError("LOCAL_CAPCUT_PROJECT_EXISTS")
        working.rename(target)
        cloud_prepare = build_episode_capcut._prepare_cloud_project(target, project_name=args.project_name, capcut_root=target_root, draft_id=synced["evidence"]["draft_id"], duration_us=duration_us)
        post_prepare_polish = validate_capcut_polish_profile.validate_project(target)
        if post_prepare_polish["status"] != "PASS":
            raise RuntimeError(f"POST_PREPARE_POLISH_VALIDATION_FAILED:{post_prepare_polish['errors']}")
        static = _validate_root_timeline(target, duration_us, len(clips), args.title1, args.title2, audio_policy=audio_policy, tts_cues=tts_cues)
        build_episode_capcut._register_capcut_project(target, target_root, registry_backup)
        report = {"status": "PROJECT_CREATED_WAIT_CAPCUT_OPEN", "episode_id": args.episode_id, "project_name": args.project_name, "local_capcut_path": str(target), "root_contract": contract, "visual_asset_mode": "SOURCE_VIDEO_PROVISIONAL", "source_audio_mode": "TTS_ONLY_MUTE_SOURCE_A9" if audio_policy == "TTS_ONLY_MUTE_SOURCE" else "DEMUCs_VOCAL_STEM_A10", "a12_policy": "EMPTY", "titles": {"T1": args.title1, "T2": args.title2}, "polish": polish, "cloud_prepare": cloud_prepare, "static_validation": static, "capcut_registration": "LOCAL_ROOT_META_REGISTERED", "next_gate": "CAPCUT_REOPEN_AND_USER_VISUAL_AUDIO_QC"}
        _write(args.report.resolve(), report)
        return report
    except Exception:
        if registry_backup.is_file():
            shutil.copy2(registry_backup, target_root / "root_meta_info.json")
        if target.exists():
            shutil.rmtree(target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a root-template 001 Shorts project from a locked structural assembly input.")
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--root-contract", type=Path, required=True)
    parser.add_argument("--assembly-input", type=Path, required=True)
    parser.add_argument("--source-video", type=Path, required=True)
    parser.add_argument("--source-audio", type=Path)
    parser.add_argument("--episode-evidence-root", type=Path, required=True)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--title1", required=True)
    parser.add_argument("--title2", required=True)
    parser.add_argument("--capcut-root", type=Path, required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build(args)
    except (OSError, ValueError, KeyError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
