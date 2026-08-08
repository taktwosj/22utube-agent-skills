from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from common import read_json, resolved_declared_path, result, sha256_file
from schema_runtime import validate_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]
AUDIO_SCHEMA = SKILL_ROOT / "schemas" / "audio_lock.schema.json"
TTS_SCHEMA = SKILL_ROOT / "schemas" / "tts_evidence.schema.json"
CAPTION_SCHEMA = SKILL_ROOT / "schemas" / "caption_lock.schema.json"
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
    for block in re.split(r"\r?\n\s*\r?\n", path.read_text(encoding="utf-8-sig").strip()):
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


def validate_audio_caption(audio_lock_path: Path, caption_lock_path: Path) -> dict:
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

    if audio_lock["audio_source"] == "SOURCE_CLIP":
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
            if any(expected.get(field) != actual.get(field) for field in ("start_us", "end_us", "text")):
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
    })
