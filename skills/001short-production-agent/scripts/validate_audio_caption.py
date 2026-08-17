from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from audio_policy_matrix import ACCEPTED_MODE_TUPLES
from common import FRAME_TOLERANCE_US, ranges_match, times_match, read_json, resolved_declared_path, result, sha256_file
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
AUDIO_SCHEMA = SKILL_ROOT / "schemas" / "audio_lock.schema.json"
TTS_SCHEMA = SKILL_ROOT / "schemas" / "tts_evidence.schema.json"
CAPTION_SCHEMA = SKILL_ROOT / "schemas" / "caption_lock.schema.json"
TIMING_SCHEMA = SKILL_ROOT / "schemas" / "caption_timing_evidence.schema.json"
REASSEMBLED_SCHEMA = SKILL_ROOT / "schemas" / "reassembled_stem_manifest.schema.json"
SOURCE_IDENTITY_SCHEMA = SKILL_ROOT / "schemas" / "source_identity.schema.json"
TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
DEFAULT_CUE_LAYER = "0"


def _probe_audio(path: Path) -> tuple[int | None, set[str]]:
    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "stream=codec_type,codec_name:format=duration", "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(completed.stdout)
        if completed.returncode != 0:
            return None, set()
        duration = round(float(payload["format"]["duration"]) * 1_000_000)
        codecs = {
            str(stream.get("codec_name", "")).casefold()
            for stream in payload.get("streams", [])
            if isinstance(stream, dict)
            and stream.get("codec_type") == "audio"
            and stream.get("codec_name")
        }
        return duration, codecs
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None, set()


def _validate_audio_file(
    lock_path: Path,
    metadata: dict,
    errors: list[dict],
    *,
    role: str | None = None,
) -> None:
    code_prefix = "AUDIO_CAPTION_AUDIO" if role is None else "AUDIO_CAPTION_ROLE_AUDIO"
    audio = resolved_declared_path(lock_path, metadata["audio_path"])
    detail = {} if role is None else {"role": role}
    if not audio.is_file() or sha256_file(audio) != metadata["audio_sha256"]:
        errors.append({"code": f"{code_prefix}_FILE_INVALID", **detail})
        return
    measured, codecs = _probe_audio(audio)
    if not codecs:
        errors.append({"code": f"{code_prefix}_STREAM_MISSING", **detail})
    if measured is None or abs(measured - metadata["measured_duration_us"]) > 50_000:
        errors.append({"code": f"{code_prefix}_DURATION_MISMATCH", **detail})
    declared_codec = metadata.get("audio_codec")
    if declared_codec and declared_codec.casefold() not in codecs:
        errors.append({
            "code": f"{code_prefix}_CODEC_MISMATCH",
            "declared_codec": declared_codec,
            "measured_codecs": sorted(codecs),
            **detail,
        })


def _time_us(value: str) -> int:
    match = TIME_RE.fullmatch(value)
    if match is None:
        raise ValueError(value)
    hours, minutes, seconds, millis = (int(item) for item in match.groups())
    return ((hours * 60 + minutes) * 60 + seconds) * 1_000_000 + millis * 1_000


def parse_srt(path: Path) -> list[dict]:
    cues: list[dict] = []
    content = path.read_text(encoding="utf-8-sig").strip()
    if not content:
        return []
    for block in re.split(r"\r?\n\s*\r?\n", content):
        lines = block.splitlines()
        if len(lines) < 3 or " --> " not in lines[1]:
            raise ValueError("invalid SRT cue")
        start, end = lines[1].split(" --> ", 1)
        cues.append(
            {
                "cue_id": lines[0].strip(),
                "start_us": _time_us(start.strip()),
                "end_us": _time_us(end.strip()),
                "text": "\n".join(lines[2:]).strip(),
            }
        )
    return cues


def _valid_range(value: object) -> bool:
    return (
        isinstance(value, list) and len(value) == 2
        and all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        and 0 <= value[0] < value[1]
    )


def _bound_json(base: Path, payload: dict, path_key: str, sha_key: str) -> tuple[Path | None, dict | None]:
    raw_path, raw_sha = payload.get(path_key), payload.get(sha_key)
    if not isinstance(raw_path, str) or not isinstance(raw_sha, str):
        return None, None
    path = resolved_declared_path(base, raw_path)
    try:
        data = read_json(path)
    except (OSError, TypeError, ValueError):
        return path, None
    return (path, data) if path.is_file() and sha256_file(path) == raw_sha else (path, None)


def _mapping_signature(row: dict) -> tuple:
    return (
        row.get("source_beat_id"), row.get("target_segment_id"),
        tuple(row.get("source_range_us", ())), tuple(row.get("target_range_us", ())),
    )


def _signature_sets_match(observed: list, expected: list) -> bool:
    """Same beat/segment ids, and every range within one frame."""
    if len(observed) != len(expected):
        return False
    remaining = list(expected)
    for row in observed:
        for index, candidate in enumerate(remaining):
            if (
                row[0] == candidate[0] and row[1] == candidate[1]
                and ranges_match(list(row[2]), list(candidate[2]))
                and ranges_match(list(row[3]), list(candidate[3]))
            ):
                remaining.pop(index)
                break
        else:
            return False
    return True


def _authoritative_mapping(
    evidence_path: Path, evidence: dict, errors: list[dict],
    expected_production_plan_path: Path | None = None,
    expected_production_plan_sha256: str | None = None,
) -> tuple[dict | None, set[tuple]]:
    timeline_path, timeline = _bound_json(evidence_path, evidence, "approved_timeline_path", "approved_timeline_sha256")
    manifest_path, manifest = _bound_json(evidence_path, evidence, "build_manifest_path", "build_manifest_sha256")
    plan_path, plan = _bound_json(evidence_path, evidence, "production_plan_path", "production_plan_sha256")
    original_raw, original_sha = evidence.get("original_grid_path"), evidence.get("original_grid_sha256")
    urakkai_raw, urakkai_sha = evidence.get("urakkai_grid_path"), evidence.get("urakkai_grid_sha256")
    if not all(isinstance(value, str) for value in (original_raw, original_sha, urakkai_raw, urakkai_sha)):
        errors.append({"code": "CAPTION_TIMING_AUTHORITY_BINDING_INVALID"})
        return timeline, set()
    original = resolved_declared_path(evidence_path, original_raw)
    urakkai = resolved_declared_path(evidence_path, urakkai_raw)
    if (
        timeline is None or manifest is None or plan is None or not original.is_file() or not urakkai.is_file()
        or sha256_file(original) != original_sha or sha256_file(urakkai) != urakkai_sha
    ):
        errors.append({"code": "CAPTION_TIMING_AUTHORITY_BINDING_INVALID"})
        return timeline, set()
    if expected_production_plan_path is not None and (
        plan_path != Path(expected_production_plan_path).resolve()
        or evidence.get("production_plan_sha256") != expected_production_plan_sha256
    ):
        errors.append({"code": "CAPTION_TIMING_AUTHORITY_BINDING_INVALID"})
    from validate_capcut_grids import HEADER_PATTERNS, _header_range_us, validate_grids
    grids = validate_grids(original, urakkai)
    if grids["status"] != "PASS":
        errors.append({"code": "CAPTION_TIMING_GRID_INVALID"})
        return timeline, set()
    source_ranges = [_header_range_us("original", header) for header in grids["original"].headers]
    clips = manifest.get("urakkai", {}).get("video_clips", [])
    expected: list[tuple] = []
    for index, header in enumerate(grids["urakkai"].headers, start=1):
        match = HEADER_PATTERNS["urakkai"].fullmatch(header)
        if match is None:
            continue
        source_id = match.group("source")
        source_index = int(source_id[1:]) - 1
        target_id = f"V{index:02d}"
        source_range = source_ranges[source_index]
        target_range = _header_range_us("urakkai", header)
        matches = [clip for clip in clips if tuple(clip.get("source_range_us", ())) == source_range and tuple(clip.get("target_range_us", ())) == target_range]
        if len(matches) != 1:
            errors.append({"code": "CAPTION_TIMING_BUILD_MAPPING_MISMATCH", "target_segment_id": target_id})
        plan_matches = [
            row for row in plan.get("timeline", [])
            if row.get("source_beat_id") == source_id
            and row.get("target_segment_id") == target_id
            and any(
                placement.get("anchor") == "VIDEO"
                and tuple(placement.get("source_range_us", ())) == source_range
                and tuple(placement.get("target_range_us", ())) == target_range
                for placement in row.get("placements", [])
            )
        ]
        if len(plan_matches) != 1:
            errors.append({"code": "CAPTION_TIMING_PLAN_MAPPING_MISMATCH", "target_segment_id": target_id})
        expected.append((source_id, target_id, source_range, target_range))
    # In a zero-caption receipt, mapping describes caption-cue provenance and is
    # therefore empty.  VIDEO/audio B->V authority is still checked above
    # against both the build manifest and production plan.
    observed = [_mapping_signature(row) for row in evidence.get("mapping", [])]
    if not evidence.get("zero_caption") and not _signature_sets_match(observed, expected):
        errors.append({"code": "CAPTION_TIMING_BUILD_MAPPING_MISMATCH"})
    return timeline, set(expected)


def _validate_source_identity(lock_path: Path, audio_lock: dict, errors: list[dict]) -> None:
    raw_path = audio_lock.get("source_identity_path")
    raw_sha = audio_lock.get("source_identity_sha256")
    if not raw_path or not raw_sha:
        errors.append({"code": "AUDIO_CAPTION_SOURCE_IDENTITY_MISSING"})
        return
    identity_path = resolved_declared_path(lock_path, raw_path)
    try:
        identity = read_json(identity_path)
    except (OSError, ValueError, TypeError):
        identity = None
    if (
        not identity_path.is_file() or sha256_file(identity_path) != raw_sha
        or not isinstance(identity, dict)
        or validate_schema(identity, read_json(SOURCE_IDENTITY_SCHEMA))
        or identity.get("episode_id") != audio_lock.get("episode_id")
    ):
        errors.append({"code": "AUDIO_CAPTION_SOURCE_IDENTITY_INVALID"})
        return
    media = resolved_declared_path(identity_path, identity["media_path"])
    primary = resolved_declared_path(lock_path, audio_lock["audio_path"])
    if (
        not media.is_file() or sha256_file(media) != identity["media_sha256"]
        or primary != media or audio_lock.get("audio_sha256") != identity["media_sha256"]
    ):
        errors.append({"code": "AUDIO_CAPTION_CLEAN_SOURCE_IDENTITY_MISMATCH"})
    duration = identity.get("duration_us")
    if isinstance(duration, int) and abs(duration - audio_lock["measured_duration_us"]) > 50_000:
        errors.append({"code": "AUDIO_CAPTION_CLEAN_SOURCE_DURATION_MISMATCH"})


def _validate_mode_matrix(lock_path: Path, audio_lock: dict, errors: list[dict]) -> None:
    if audio_lock.get("schema_version") != "001short-audio-lock-v4":
        return
    mode = audio_lock.get("production_mode")
    policy = audio_lock.get("audio_policy")
    source = audio_lock.get("audio_source")
    if (mode, policy, source) not in ACCEPTED_MODE_TUPLES:
        errors.append({"code": "AUDIO_CAPTION_MODE_MATRIX_MISMATCH", "production_mode": mode, "audio_policy": policy, "audio_source": source})
        return
    if mode == "SOURCE_ORDER_UNCHANGED_CLEAN_ONLY":
        _validate_source_identity(lock_path, audio_lock, errors)


def _validate_reassembled_stem(
    lock_path: Path, audio_lock: dict, role_files: dict[str, dict], errors: list[dict],
    expected_production_plan_path: Path | None = None,
    expected_production_plan_sha256: str | None = None,
    expected_production_plan_receipt_path: Path | None = None,
    expected_production_plan_receipt_sha256: str | None = None,
) -> None:
    manifest_value = audio_lock.get("reassembled_stem_manifest_path")
    manifest_sha = audio_lock.get("reassembled_stem_manifest_sha256")
    if not manifest_value or not manifest_sha:
        errors.append({"code": "AUDIO_CAPTION_REASSEMBLED_STEM_EVIDENCE_MISSING"})
        return
    manifest_path = resolved_declared_path(lock_path, manifest_value)
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError, TypeError):
        manifest = None
    if (
        not manifest_path.is_file() or sha256_file(manifest_path) != manifest_sha
        or not isinstance(manifest, dict)
        or validate_schema(manifest, read_json(REASSEMBLED_SCHEMA))
        or manifest.get("episode_id") != audio_lock.get("episode_id")
    ):
        errors.append({"code": "AUDIO_CAPTION_REASSEMBLED_STEM_EVIDENCE_INVALID"})
        return
    if manifest.get("schema_version") == "001short-reassembled-stem-manifest-v2":
        _, build_manifest = _bound_json(manifest_path, manifest, "build_manifest_path", "build_manifest_sha256")
        _, production_plan = _bound_json(manifest_path, manifest, "production_plan_path", "production_plan_sha256")
        declared_plan_path = resolved_declared_path(manifest_path, manifest.get("production_plan_path", ""))
        mapped_ranges = [
            (tuple(row.get("source_range_us", ())), tuple(row.get("target_range_us", ())))
            for row in manifest.get("mapping", [])
        ]
        build_ranges = [
            (tuple(row.get("source_range_us", ())), tuple(row.get("target_range_us", ())))
            for row in (build_manifest or {}).get("urakkai", {}).get("video_clips", [])
        ]
        plan_ranges = [
            (tuple(placement.get("source_range_us", ())), tuple(placement.get("target_range_us", ())))
            for segment in (production_plan or {}).get("timeline", [])
            for placement in segment.get("placements", [])
            if placement.get("anchor") == "VIDEO"
        ]
        mapped_tuples = sorted(
            (
                row.get("source_beat_id"), row.get("target_segment_id"),
                tuple(row.get("source_range_us", ())), tuple(row.get("target_range_us", ())),
            )
            for row in manifest.get("mapping", [])
        )
        plan_tuples = sorted(
            (
                segment.get("source_beat_id"), segment.get("target_segment_id"),
                tuple(placement.get("source_range_us", ())), tuple(placement.get("target_range_us", ())),
            )
            for segment in (production_plan or {}).get("timeline", [])
            for placement in segment.get("placements", [])
            if placement.get("anchor") == "VIDEO"
        )
        if (
            build_manifest is None or production_plan is None
            or build_manifest.get("episode_id") != audio_lock.get("episode_id")
            or production_plan.get("episode_id") != audio_lock.get("episode_id")
            or production_plan.get("schema_version") != "001short-production-plan-v2"
            or sorted(mapped_ranges) != sorted(build_ranges)
            or sorted(mapped_ranges) != sorted(plan_ranges)
            or mapped_tuples != plan_tuples
        ):
            errors.append({"code": "AUDIO_CAPTION_REASSEMBLED_STEM_AUTHORITY_MISMATCH"})
        if expected_production_plan_path is not None:
            receipt_path = Path(expected_production_plan_receipt_path or "").resolve()
            try:
                receipt = read_json(receipt_path)
            except (OSError, TypeError, ValueError):
                receipt = None
            receipt_evidence = (receipt or {}).get("evidence", {})
            canonical_plan = Path(expected_production_plan_path).resolve()
            if (
                declared_plan_path != canonical_plan
                or manifest.get("production_plan_sha256") != expected_production_plan_sha256
                or not canonical_plan.is_file()
                or sha256_file(canonical_plan) != expected_production_plan_sha256
                or not receipt_path.is_file()
                or sha256_file(receipt_path) != expected_production_plan_receipt_sha256
                or (receipt or {}).get("status") != "PASS"
                or (receipt or {}).get("errors") != []
                or not isinstance(receipt_evidence.get("production_plan_path"), str)
                or Path(receipt_evidence["production_plan_path"]).resolve() != canonical_plan
                or receipt_evidence.get("production_plan_sha256") != expected_production_plan_sha256
            ):
                errors.append({"code": "AUDIO_CAPTION_REASSEMBLED_STEM_AUTHORITY_MISMATCH"})
    full_manifest = resolved_declared_path(manifest_path, manifest["full_stem_manifest_path"])
    reassembled = resolved_declared_path(manifest_path, manifest["reassembled_audio_path"])
    mapping = manifest["mapping"]
    ordered = sorted(mapping, key=lambda row: row.get("target_range_us", [0, 0])[0])
    cursor = 0
    for row in ordered:
        if not _valid_range(row.get("source_range_us")) or not _valid_range(row.get("target_range_us")) or row["target_range_us"][0] != cursor or row["source_range_us"][1] - row["source_range_us"][0] != row["target_range_us"][1] - row["target_range_us"][0]:
            errors.append({"code": "AUDIO_CAPTION_REASSEMBLED_STEM_MAPPING_INVALID"})
            break
        cursor = row["target_range_us"][1]
    a10 = role_files.get("A10")
    try:
        from validate_vocal_stem import validate_vocal_stem
        full_result = validate_vocal_stem(full_manifest) if full_manifest.is_file() else {"status": "FAIL"}
    except (OSError, ValueError, TypeError):
        full_result = {"status": "FAIL"}
    try:
        source_duration = read_json(full_manifest).get("source_duration_us")
    except (OSError, TypeError, ValueError):
        source_duration = None
    if (
        not full_manifest.is_file() or sha256_file(full_manifest) != manifest["full_stem_manifest_sha256"]
        or full_result.get("status") != "PASS"
        or full_result.get("evidence", {}).get("episode_id") != audio_lock.get("episode_id")
        or not isinstance(source_duration, int)
        or any(row.get("source_range_us", [0, source_duration + 1])[1] > source_duration for row in mapping)
        or not reassembled.is_file() or sha256_file(reassembled) != manifest["reassembled_audio_sha256"]
        or cursor != manifest["target_duration_us"]
        or abs(manifest["target_duration_us"] - audio_lock["measured_duration_us"]) > 50_000
        or resolved_declared_path(lock_path, audio_lock["audio_path"]) != reassembled
        or a10 is None or resolved_declared_path(lock_path, a10["audio_path"]) != reassembled
    ):
        errors.append({"code": "AUDIO_CAPTION_REASSEMBLED_STEM_EVIDENCE_INVALID"})


def _validate_timing_evidence(
    caption_lock_path: Path, caption: dict, errors: list[dict],
    expected_production_plan_path: Path | None = None,
    expected_production_plan_sha256: str | None = None,
) -> None:
    if caption.get("schema_version") != "001short-caption-lock-v2":
        return
    raw_path = caption.get("caption_timing_evidence_path")
    raw_sha = caption.get("caption_timing_evidence_sha256")
    if not raw_path or not raw_sha:
        errors.append({"code": "CAPTION_TIMING_EVIDENCE_MISSING"})
        return
    evidence_path = resolved_declared_path(caption_lock_path, raw_path)
    try:
        evidence = read_json(evidence_path)
    except (OSError, ValueError, TypeError):
        evidence = None
    if (
        not evidence_path.is_file() or sha256_file(evidence_path) != raw_sha
        or not isinstance(evidence, dict)
        or validate_schema(evidence, read_json(TIMING_SCHEMA))
        or evidence.get("episode_id") != caption.get("episode_id")
    ):
        errors.append({"code": "CAPTION_TIMING_EVIDENCE_INVALID"})
        return
    identity = resolved_declared_path(evidence_path, evidence["source_identity_path"])
    if not identity.is_file() or sha256_file(identity) != evidence["source_identity_sha256"]:
        errors.append({"code": "CAPTION_TIMING_SOURCE_IDENTITY_MISMATCH"})
    timeline = None
    if evidence.get("schema_version") == "001short-caption-timing-evidence-v2":
        timeline, _ = _authoritative_mapping(
            evidence_path, evidence, errors,
            expected_production_plan_path, expected_production_plan_sha256,
        )
    locked = caption.get("cues", [])
    evidence_cues = evidence.get("cues", [])
    if bool(evidence.get("zero_caption")) != (len(locked) == 0) or (not locked and (evidence_cues or evidence.get("mapping"))):
        errors.append({"code": "CAPTION_TIMING_ZERO_CAPTION_MISMATCH"})
        return
    timeline_caption_rows = [
        row for row in (timeline or {}).get("segments", [])
        if row.get("role") in {"A9_TEXT", "A10_TEXT", "STATE"}
    ]
    if timeline is not None and {row.get("cue_id") for row in timeline_caption_rows} != {row.get("cue_id") for row in locked}:
        errors.append({"code": "CAPTION_TIMING_TIMELINE_CUE_SET_MISMATCH"})
    by_id = {row.get("cue_id"): row for row in evidence_cues}
    mapping = {row.get("mapping_id"): row for row in evidence.get("mapping", [])}
    tolerance = max(int(evidence.get("tolerance_us", 0) or 0), FRAME_TOLERANCE_US)
    if len(by_id) != len(evidence_cues) or set(by_id) != {row.get("cue_id") for row in locked}:
        errors.append({"code": "CAPTION_TIMING_CUE_SET_MISMATCH"})
        return
    for cue in locked:
        receipt = by_id[cue["cue_id"]]
        map_row = mapping.get(receipt.get("mapping_id"))
        if not map_row or not _valid_range(receipt.get("source_range_us")) or not _valid_range(receipt.get("target_range_us")) or not _valid_range(map_row.get("source_range_us")) or not _valid_range(map_row.get("target_range_us")):
            errors.append({"code": "CAPTION_TIMING_SOURCE_MISMATCH", "cue_id": cue["cue_id"]})
            continue
        if receipt["source_range_us"][0] < map_row["source_range_us"][0] or receipt["source_range_us"][1] > map_row["source_range_us"][1]:
            errors.append({"code": "CAPTION_TIMING_SOURCE_MISMATCH", "cue_id": cue["cue_id"]})
            continue
        derived = [map_row["target_range_us"][0] + receipt["source_range_us"][i] - map_row["source_range_us"][0] for i in (0, 1)]
        bound = resolved_declared_path(evidence_path, receipt["bound_file_path"])
        timeline_rows = [row for row in timeline_caption_rows if row.get("cue_id") == cue["cue_id"]]
        timeline_mismatch = False
        if timeline is not None:
            if len(timeline_rows) != 1:
                timeline_mismatch = True
            else:
                row = timeline_rows[0]
                authoritative_target = [row.get("start"), row.get("start", 0) + row.get("duration", 0)]
                authoritative_source = row.get("source_range_us")
                timeline_mismatch = (
                    row.get("text") != cue.get("text")
                    or any(abs(receipt["target_range_us"][i] - authoritative_target[i]) > tolerance for i in (0, 1))
                    or (_valid_range(authoritative_source) and any(abs(receipt["source_range_us"][i] - authoritative_source[i]) > tolerance for i in (0, 1)))
                )
        if (
            receipt.get("text") != cue.get("text")
            or any(abs(receipt["target_range_us"][i] - cue[("start_us", "end_us")[i]]) > tolerance for i in (0, 1))
            or any(abs(receipt["target_range_us"][i] - derived[i]) > tolerance for i in (0, 1))
            or not bound.is_file() or sha256_file(bound) != receipt["bound_file_sha256"]
            or timeline_mismatch
        ):
            errors.append({"code": "CAPTION_TIMING_SOURCE_MISMATCH", "cue_id": cue["cue_id"]})


def validate_audio_caption(
    audio_lock_path: Path, caption_lock_path: Path, *,
    expected_production_plan_path: Path | None = None,
    expected_production_plan_sha256: str | None = None,
    expected_production_plan_receipt_path: Path | None = None,
    expected_production_plan_receipt_sha256: str | None = None,
) -> dict:
    audio_lock_path = Path(audio_lock_path).resolve()
    caption_lock_path = Path(caption_lock_path).resolve()
    try:
        audio_lock = read_json(audio_lock_path)
        caption = read_json(caption_lock_path)
    except (OSError, ValueError, TypeError) as exc:
        return result([{"code": "AUDIO_CAPTION_INPUT_INVALID", "detail": str(exc)}])
    errors: list[dict] = []
    audio_schema_errors = validate_schema(audio_lock, read_json(AUDIO_SCHEMA))
    if (
        audio_lock.get("schema_version") in {"001short-audio-lock-v2", "001short-audio-lock-v3"}
        and not audio_lock.get("audio_codec")
    ):
        audio_schema_errors.append("$: missing audio_codec")
    if audio_schema_errors:
        errors.append({"code": "AUDIO_CAPTION_AUDIO_LOCK_SCHEMA", "detail": audio_schema_errors})
    if schema_errors := validate_schema(caption, read_json(CAPTION_SCHEMA)):
        errors.append({"code": "AUDIO_CAPTION_CAPTION_LOCK_SCHEMA", "detail": schema_errors})
    if errors:
        return result(errors)
    _validate_mode_matrix(audio_lock_path, audio_lock, errors)
    if audio_lock["episode_id"] != caption["episode_id"]:
        errors.append({
            "code": "AUDIO_CAPTION_EPISODE_ID_MISMATCH",
            "audio_lock_episode_id": audio_lock["episode_id"],
            "caption_lock_episode_id": caption["episode_id"],
        })
    if sha256_file(audio_lock_path) != caption["audio_lock_sha256"]:
        errors.append({"code": "AUDIO_CAPTION_AUDIO_LOCK_SHA_MISMATCH"})
    _validate_audio_file(audio_lock_path, audio_lock, errors)
    role_files: dict[str, dict] = {}
    for role_file in audio_lock.get("role_files", []):
        role = role_file["role"]
        if role == "A12":
            errors.append({"code": "AUDIO_CAPTION_A12_RESERVED_EMPTY"})
            continue
        if role in role_files:
            errors.append({"code": "AUDIO_CAPTION_ROLE_DUPLICATE", "role": role})
            continue
        role_files[role] = role_file
        _validate_audio_file(audio_lock_path, role_file, errors, role=role)

    if audio_lock.get("schema_version") == "001short-audio-lock-v4":
        expected_roles = {
            "SOURCE_ORDER_CLEAN_AUDIO": {"A10"},
            "A10_RETAINED_SYNC": {"A10"},
            "A10_REASSEMBLED_SYNC": {"A10"},
            "A9_TTS_PLUS_A10_REASSEMBLED": {"A9", "A10"},
            "TTS_ONLY_MUTE_SOURCE": {"A9"},
            "CAPTION_ONLY_MUTE_SOURCE": set(),
        }.get(audio_lock.get("audio_policy"))
        if expected_roles is None or set(role_files) != expected_roles:
            errors.append({"code": "AUDIO_CAPTION_ROLE_MATRIX_MISMATCH", "expected": sorted(expected_roles or ()), "actual": sorted(role_files)})

    # Raw SOURCE_CLIP audio is also legal under URAKKAI for an order-preserved
    # trim (SOURCE_ORDER_CLEAN_AUDIO policy, no Demucs stem available); the
    # per-segment source_range_us match against paired VIDEO is enforced
    # elsewhere.
    if audio_lock["audio_source"] == "SOURCE_CLIP" and not (
        audio_lock.get("schema_version") == "001short-audio-lock-v4"
        and audio_lock.get("production_mode") in {"SOURCE_ORDER_UNCHANGED_CLEAN_ONLY", "URAKKAI"}
        and audio_lock.get("audio_policy") == "SOURCE_ORDER_CLEAN_AUDIO"
    ):
        errors.append({"code": "AUDIO_CAPTION_RAW_SOURCE_AUDIO_FORBIDDEN"})

    if audio_lock["audio_source"] == "SOURCE_VOCAL_STEM":
        manifest_value = audio_lock.get("vocal_stem_manifest_path")
        manifest_sha = audio_lock.get("vocal_stem_manifest_sha256")
        if not manifest_value or not manifest_sha:
            errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_EVIDENCE_MISSING"})
        else:
            manifest_path = resolved_declared_path(audio_lock_path, manifest_value)
            if not manifest_path.is_file() or sha256_file(manifest_path) != manifest_sha:
                errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_EVIDENCE_INVALID"})
            else:
                from validate_vocal_stem import validate_vocal_stem

                stem = validate_vocal_stem(manifest_path)
                if stem["status"] != "PASS":
                    errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_EVIDENCE_INVALID", "detail": stem["errors"]})
                elif stem["evidence"].get("episode_id") != audio_lock["episode_id"]:
                    errors.append({"code": "AUDIO_CAPTION_EPISODE_ID_MISMATCH"})
                else:
                    a10 = role_files.get("A10")
                    stem_audio = Path(stem["evidence"]["a10_audio_path"])
                    if a10 is None:
                        errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_A10_MISSING"})
                    else:
                        a10_audio = resolved_declared_path(audio_lock_path, a10["audio_path"])
                        if a10_audio != stem_audio:
                            errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_A10_PATH_MISMATCH"})
                        if any(
                            audio_lock.get(field) != a10.get(field)
                            for field in ("audio_path", "audio_sha256", "measured_duration_us", "audio_codec", "ffprobe_verified")
                        ):
                            errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_PRIMARY_A10_MISMATCH"})
                        if resolved_declared_path(audio_lock_path, audio_lock["audio_path"]) != stem_audio:
                            errors.append({"code": "AUDIO_CAPTION_VOCAL_STEM_PRIMARY_PATH_MISMATCH"})

    if audio_lock["audio_source"] == "REASSEMBLED_VOCAL_STEM":
        _validate_reassembled_stem(
            audio_lock_path, audio_lock, role_files, errors,
            expected_production_plan_path, expected_production_plan_sha256,
            expected_production_plan_receipt_path, expected_production_plan_receipt_sha256,
        )

    tts_required = audio_lock["audio_source"] == "GENERATED_TTS" or "A9" in role_files
    tts_path_value = audio_lock.get("tts_evidence_path")
    tts_sha_value = audio_lock.get("tts_evidence_sha256")
    tts_declared = bool(tts_path_value or tts_sha_value)
    if tts_required or tts_declared:
        if not tts_path_value or not tts_sha_value:
            errors.append({"code": "AUDIO_CAPTION_TTS_EVIDENCE_MISSING"})
        else:
            tts_path = resolved_declared_path(audio_lock_path, tts_path_value)
            if not tts_path.is_file():
                errors.append({"code": "AUDIO_CAPTION_TTS_EVIDENCE_MISSING"})
            elif sha256_file(tts_path) != tts_sha_value:
                errors.append({"code": "AUDIO_CAPTION_TTS_EVIDENCE_SHA_MISMATCH"})
            else:
                try:
                    tts = read_json(tts_path)
                except (OSError, ValueError):
                    tts = None
                    errors.append({"code": "AUDIO_CAPTION_TTS_EVIDENCE_INVALID"})
                if tts is not None:
                    tts_schema_errors = validate_schema(tts, read_json(TTS_SCHEMA))
                    if (
                        tts.get("schema_version") == "001short-tts-evidence-v2"
                        and not tts.get("audio_codec")
                    ):
                        tts_schema_errors.append("$: missing audio_codec")
                    if tts_schema_errors:
                        errors.append({
                            "code": "AUDIO_CAPTION_TTS_EVIDENCE_INVALID",
                            "detail": tts_schema_errors,
                        })
                    elif tts["episode_id"] != audio_lock["episode_id"]:
                        errors.append({
                            "code": "AUDIO_CAPTION_EPISODE_ID_MISMATCH",
                            "audio_lock_episode_id": audio_lock["episode_id"],
                            "tts_evidence_episode_id": tts["episode_id"],
                        })
                    else:
                        tts_audio = role_files.get("A9", audio_lock)
                        mismatch_fields = [
                            field
                            for field in ("audio_sha256", "measured_duration_us", "ffprobe_verified")
                            if tts.get(field) != tts_audio.get(field)
                        ]
                        if tts.get("audio_codec") and (
                            tts.get("audio_codec", "").casefold()
                            != tts_audio.get("audio_codec", "").casefold()
                        ):
                            mismatch_fields.append("audio_codec")
                        if mismatch_fields:
                            errors.append({
                                "code": "AUDIO_CAPTION_TTS_EVIDENCE_MISMATCH",
                                "fields": mismatch_fields,
                            })
    srt = resolved_declared_path(caption_lock_path, caption["final_srt_path"])
    _validate_timing_evidence(
        caption_lock_path, caption, errors,
        expected_production_plan_path, expected_production_plan_sha256,
    )
    if not srt.is_file() or sha256_file(srt) != caption["final_srt_sha256"]:
        errors.append({"code": "AUDIO_CAPTION_SRT_SHA_MISMATCH"})
    else:
        try:
            parsed = parse_srt(srt)
        except (OSError, ValueError):
            errors.append({"code": "AUDIO_CAPTION_SRT_INVALID"})
            parsed = []
        if len(parsed) != caption["final_cue_count"] or len(parsed) != len(caption["cues"]):
            errors.append({"code": "AUDIO_CAPTION_CUE_COUNT_MISMATCH"})
        previous_end_by_layer: dict[str, int] = {}
        for expected, actual in zip(caption["cues"], parsed):
            layer = str(expected.get("layer", DEFAULT_CUE_LAYER))
            caption_role = expected.get("caption_role")
            if "layer" in expected and caption_role is not None and caption_role != layer:
                errors.append({
                    "code": "AUDIO_CAPTION_CUE_LAYER_ROLE_MISMATCH",
                    "cue_id": expected.get("cue_id"),
                    "layer": layer,
                    "caption_role": caption_role,
                })
            if actual["end_us"] <= actual["start_us"]:
                errors.append({"code": "AUDIO_CAPTION_CUE_REVERSED", "cue_id": expected.get("cue_id")})
            if (
                expected.get("text") != actual.get("text")
                or not times_match(expected.get("start_us"), actual.get("start_us"))
                or not times_match(expected.get("end_us"), actual.get("end_us"))
            ):
                errors.append({"code": "AUDIO_CAPTION_CUE_MISMATCH", "cue_id": expected.get("cue_id")})
            if actual["start_us"] < previous_end_by_layer.get(layer, 0):
                errors.append({
                    "code": "AUDIO_CAPTION_CUE_OVERLAP",
                    "cue_id": expected.get("cue_id"),
                    "layer": layer,
                })
            if actual["end_us"] > audio_lock["measured_duration_us"]:
                errors.append({"code": "AUDIO_CAPTION_CUE_OUTSIDE_AUDIO", "cue_id": expected.get("cue_id")})
            previous_end_by_layer[layer] = actual["end_us"]
    return result(errors, {
        "episode_id": audio_lock["episode_id"],
        "audio_lock_sha256": sha256_file(audio_lock_path),
        "caption_lock_sha256": sha256_file(caption_lock_path),
        "caption_cue_count": len(caption.get("cues", [])),
    })


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-lock", type=Path, required=True)
    parser.add_argument("--caption-lock", type=Path, required=True)
    args = parser.parse_args()
    payload = validate_audio_caption(args.audio_lock, args.caption_lock)
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
