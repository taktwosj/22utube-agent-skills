#!/usr/bin/env python3
"""Deterministic P07 validator for the politics G00-G90 lane.

This adapter evaluates one gate and returns a gate-result-v1 document. It never
calls an external model, starts paid work, opens CapCut, uploads, or executes
the next gate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_CORE = (
    REPO_ROOT
    / "skills"
    / "111-politics-longform"
    / "scripts"
    / "_generated"
    / "workflow_harness_core.py"
)
LANE = "politics_longform"
PROFILES = {"politics_longform", "politics_derived_short"}
MODES = {"source_led", "narrated"}
ROOT_BY_PROFILE = {
    "politics_longform": "jungchilong_base_v3_intro15",
    "politics_derived_short": "SHRTJUNGCHI",
}


def _import_core():
    spec = importlib.util.spec_from_file_location("politics_workflow_core", GENERATED_CORE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["politics_workflow_core"] = module
    spec.loader.exec_module(module)
    return module


def _result(
    gate: str,
    *,
    errors: list[dict] | None = None,
    warnings: list[dict] | None = None,
    next_action: str,
    auto: bool,
    status: str | None = None,
    reason_code: str | None = None,
    subgate: str | None = None,
    evidence: list[dict] | None = None,
) -> dict:
    errors = errors or []
    return _import_core().validate_gate(
        lane=LANE,
        gate=gate,
        subgate=subgate,
        validated_inputs=[],
        evidence=evidence or [],
        errors=errors,
        warnings=warnings or [],
        next_action=next_action,
        auto_advance_allowed=auto,
        auto_advance_class="DETERMINISTIC_ONLY" if auto else "NONE",
        status=status,
        reason_code=reason_code,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _is_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdefABCDEF" for char in value)
    )


def _resolve(root: Path | None, value: object) -> Path | None:
    if root is None or not isinstance(value, str) or not value:
        return None
    root = root.resolve()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _read_json(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _probe(path: Path) -> dict | None:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        payload = json.loads(completed.stdout)
        duration_us = round(float(payload["format"]["duration"]) * 1_000_000)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    stream_types = {
        stream.get("codec_type")
        for stream in payload.get("streams", [])
        if isinstance(stream, dict)
    }
    return {
        "duration_us": duration_us,
        "has_audio": "audio" in stream_types,
        "has_video": "video" in stream_types,
    }


def _event_positions(
    events: list[dict] | None, event_type: str, gate: str, actor: str
) -> list[int]:
    return [
        index
        for index, event in enumerate(events or [])
        if event.get("event_type") == event_type
        and event.get("gate") == gate
        and event.get("actor") == actor
    ]


def validate_g00(*, intake: dict, previous_lock: dict | None = None) -> dict:
    errors: list[dict] = []
    required = (
        "schema_version",
        "episode_id",
        "content_profile",
        "production_mode",
        "requested_target",
        "source_fingerprint",
        "status",
    )
    if intake.get("schema_version") != "politics-intake-v1" or any(
        field not in intake for field in required
    ):
        errors.append({"code": "FAIL_G00_INTAKE_SCHEMA"})
    if intake.get("content_profile") not in PROFILES:
        errors.append({"code": "FAIL_G00_CONTENT_PROFILE"})
    if intake.get("production_mode") not in MODES:
        errors.append({"code": "FAIL_G00_PRODUCTION_MODE"})
    if not _is_sha(intake.get("source_fingerprint")):
        errors.append({"code": "FAIL_G00_SOURCE_FINGERPRINT"})
    if intake.get("status") != "LOCKED":
        errors.append({"code": "FAIL_G00_NOT_LOCKED"})
    if previous_lock:
        changed = [
            field
            for field in ("content_profile", "production_mode")
            if previous_lock.get(field) is not None
            and previous_lock.get(field) != intake.get(field)
        ]
        if changed:
            return _result(
                "G00",
                errors=[],
                next_action="WAIT_USER_EDITORIAL_CONFIRMATION",
                auto=False,
                status="WAIT_USER_INPUT",
                reason_code="MATERIAL_SCOPE_CHANGE",
                evidence=[{"changed_fields": changed}],
            )
    return _result(
        "G00",
        errors=errors,
        next_action="PREPARE_G10" if not errors else "NONE",
        auto=not errors,
    )


def validate_g10(*, blueprint: dict, g00_lock: dict | None = None) -> dict:
    errors: list[dict] = []
    if blueprint.get("schema_version") != "politics-design-blueprint-v1":
        errors.append({"code": "FAIL_G10_BLUEPRINT_SCHEMA"})
    if g00_lock:
        for field in ("episode_id", "content_profile", "production_mode", "source_fingerprint"):
            if blueprint.get(field) != g00_lock.get(field):
                errors.append({"code": "FAIL_G10_G00_LOCK_MISMATCH", "field": field})
    chapters = blueprint.get("chapters")
    required = {
        "chapter_title",
        "chapter_question",
        "source_transcript_excerpt",
        "source",
        "source_date",
        "original_time_range",
        "verified_fact",
        "claim_or_inference",
        "external_dialogue_slot",
        "bridge_question",
    }
    if not isinstance(chapters, list) or not chapters:
        errors.append({"code": "FAIL_G10_CHAPTERS_REQUIRED"})
    else:
        for index, chapter in enumerate(chapters):
            if not isinstance(chapter, dict) or required - chapter.keys():
                errors.append({"code": "FAIL_G10_CHAPTER_FIELDS", "chapter": index})
                continue
            title = str(chapter.get("chapter_title", "")).strip()
            if not title or title.upper().replace(" ", "").startswith("CHAPTER") and len(title.split()) <= 2:
                errors.append({"code": "FAIL_G10_GENERIC_CHAPTER_TITLE", "chapter": index})
    return _result(
        "G10",
        errors=errors,
        next_action="PREPARE_G20" if not errors else "NONE",
        auto=not errors,
    )


def validate_g20(
    *,
    editorial_lock: dict,
    review_result: dict | None = None,
    ledger_events: list[dict] | None = None,
) -> dict:
    errors: list[dict] = []
    required = (
        "schema_version",
        "episode_id",
        "content_profile",
        "production_mode",
        "editorial_status",
        "round1_conversation_id",
        "round2_conversation_id",
        "round1_return_sha256",
        "round2_return_sha256",
        "script_sha256",
    )
    if editorial_lock.get("schema_version") != "politics-editorial-lock-v1" or any(
        field not in editorial_lock for field in required
    ):
        errors.append({"code": "FAIL_G20_EDITORIAL_LOCK_SCHEMA"})
    if editorial_lock.get("content_profile") not in PROFILES:
        errors.append({"code": "FAIL_G20_CONTENT_PROFILE"})
    if editorial_lock.get("production_mode") not in MODES:
        errors.append({"code": "FAIL_G20_PRODUCTION_MODE"})
    if editorial_lock.get("editorial_status") != "LOCKED":
        errors.append({"code": "FAIL_G20_NOT_LOCKED"})
    if editorial_lock.get("round1_conversation_id") != editorial_lock.get(
        "round2_conversation_id"
    ):
        errors.append({"code": "FAIL_G20_SAME_CONVERSATION_REQUIRED"})
    for field in ("round1_return_sha256", "round2_return_sha256", "script_sha256"):
        if not _is_sha(editorial_lock.get(field)):
            errors.append({"code": "FAIL_G20_SHA_REQUIRED", "field": field})
    if not review_result or review_result.get("status") != "PASS":
        errors.append({"code": "FAIL_G20_TWO_PASS_REVIEW"})
    if ledger_events is None:
        errors.append({"code": "FAIL_G20_MANUAL_RETURN_LEDGER_REQUIRED"})
    else:
        required_events = ["RETURN_EXTERNAL_REVIEW_R1", "RETURN_EXTERNAL_REVIEW_R2"]
        if editorial_lock.get("production_mode") == "narrated":
            required_events.insert(0, "RETURN_NARRATION")
        for event_type in required_events:
            if not any(
                event.get("event_type") == event_type and event.get("actor") == "USER"
                for event in ledger_events
            ):
                errors.append({"code": "FAIL_G20_MANUAL_RETURN_EVENT", "event": event_type})
    return _result(
        "G20",
        errors=errors,
        next_action="PREPARE_G30" if not errors else "NONE",
        auto=not errors,
    )


def validate_g30(*, audio_lock: dict, artifact_root: Path | None = None) -> dict:
    errors: list[dict] = []
    mode = audio_lock.get("production_mode")
    required = (
        "schema_version",
        "episode_id",
        "production_mode",
        "status",
        "audio_source",
        "audio_path",
        "audio_sha256",
        "measured_duration_us",
        "measurement_evidence_path",
        "measurement_evidence_sha256",
        "ffprobe_verified",
    )
    if audio_lock.get("schema_version") != "politics-audio-lock-v1" or any(
        field not in audio_lock for field in required
    ):
        errors.append({"code": "FAIL_G30_AUDIO_LOCK_SCHEMA"})
    if mode == "source_led":
        if (
            audio_lock.get("status") != "NOT_REQUIRED"
            or audio_lock.get("reason_code") != "NO_GENERATED_TTS"
            or audio_lock.get("audio_source") != "SOURCE_CLIP"
        ):
            errors.append({"code": "FAIL_G30_SOURCE_LED_TTS_POLICY"})
    elif mode == "narrated":
        if audio_lock.get("status") != "PASS" or audio_lock.get("audio_source") != "NARRATION":
            errors.append({"code": "FAIL_G30_NARRATED_AUDIO_REQUIRED"})
    else:
        errors.append({"code": "FAIL_G30_PRODUCTION_MODE"})
    measured = audio_lock.get("measured_duration_us")
    if not isinstance(measured, int) or measured <= 0:
        errors.append({"code": "FAIL_G30_NO_MEASURED_AUDIO"})
    audio = _resolve(artifact_root, audio_lock.get("audio_path"))
    evidence_path = _resolve(artifact_root, audio_lock.get("measurement_evidence_path"))
    if audio is None or not audio.is_file():
        errors.append({"code": "FAIL_G30_AUDIO_FILE_MISSING"})
    elif not _is_sha(audio_lock.get("audio_sha256")) or _sha256(audio) != audio_lock.get(
        "audio_sha256"
    ):
        errors.append({"code": "FAIL_G30_AUDIO_SHA"})
    if evidence_path is None or not evidence_path.is_file():
        errors.append({"code": "FAIL_G30_MEASUREMENT_EVIDENCE_MISSING"})
        evidence = None
    elif not _is_sha(audio_lock.get("measurement_evidence_sha256")) or _sha256(
        evidence_path
    ) != audio_lock.get("measurement_evidence_sha256"):
        errors.append({"code": "FAIL_G30_MEASUREMENT_EVIDENCE_SHA"})
        evidence = None
    else:
        evidence = _read_json(evidence_path)
        if evidence is None:
            errors.append({"code": "FAIL_G30_MEASUREMENT_EVIDENCE_INVALID"})
    if audio is not None and audio.is_file():
        probe = _probe(audio)
        if (
            probe is None
            or not probe["has_audio"]
            or audio_lock.get("ffprobe_verified") is not True
        ):
            errors.append({"code": "FAIL_G30_FFPROBE"})
        elif not isinstance(measured, int) or abs(probe["duration_us"] - measured) > 50_000:
            errors.append({"code": "FAIL_G30_DURATION_MISMATCH"})
    if evidence:
        for field in ("audio_sha256", "measured_duration_us", "ffprobe_verified"):
            if evidence.get(field) != audio_lock.get(field):
                errors.append({"code": "FAIL_G30_EVIDENCE_MISMATCH", "field": field})
    return _result(
        "G30",
        errors=errors,
        next_action="PREPARE_G40" if not errors else "NONE",
        auto=not errors,
        reason_code="NO_GENERATED_TTS" if mode == "source_led" and not errors else None,
    )


def _parse_srt(text: str) -> list[tuple[int, int, str]]:
    import re

    timestamp = re.compile(
        r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
    )

    def micros(parts: tuple[str, ...]) -> int:
        h, m, s, ms = map(int, parts)
        return ((h * 3600 + m * 60 + s) * 1000 + ms) * 1000

    cues: list[tuple[int, int, str]] = []
    blocks = text.replace("\r\n", "\n").strip().split("\n\n")
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError("invalid cue")
        match = timestamp.fullmatch(lines[1].strip())
        if not match:
            raise ValueError("invalid timestamp")
        start, end = micros(match.groups()[:4]), micros(match.groups()[4:])
        cues.append((start, end, "\n".join(lines[2:])))
    return cues


def validate_g40(
    *,
    caption_lock: dict,
    audio_lock: dict,
    artifact_root: Path | None = None,
) -> dict:
    errors: list[dict] = []
    measured = audio_lock.get("measured_duration_us")
    if audio_lock.get("status") not in ("PASS", "NOT_REQUIRED") or not isinstance(
        measured, int
    ) or measured <= 0:
        errors.append({"code": "FAIL_G40_REQUIRES_MEASURED_G30"})
    required = (
        "schema_version",
        "episode_id",
        "production_mode",
        "status",
        "srt_path",
        "srt_sha256",
        "cue_count",
        "audio_lock_sha256",
        "user_corrected_srt_applicable",
        "final_corrected_caption_fidelity",
    )
    if caption_lock.get("schema_version") != "politics-caption-lock-v1" or any(
        field not in caption_lock for field in required
    ):
        errors.append({"code": "FAIL_G40_CAPTION_LOCK_SCHEMA"})
    srt = _resolve(artifact_root, caption_lock.get("srt_path"))
    if srt is None or not srt.is_file():
        errors.append({"code": "FAIL_G40_SRT_MISSING"})
        actual_sha = None
    else:
        actual_sha = _sha256(srt)
        if actual_sha != caption_lock.get("srt_sha256"):
            errors.append({"code": "FAIL_G40_SRT_SHA"})
        try:
            cues = _parse_srt(srt.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, ValueError):
            errors.append({"code": "FAIL_G40_SRT_PARSE"})
            cues = []
        if len(cues) != caption_lock.get("cue_count"):
            errors.append({"code": "FAIL_G40_CUE_COUNT"})
        for index, (start, end, text) in enumerate(cues):
            if start >= end or (index and start < cues[index - 1][1]):
                errors.append({"code": "FAIL_G40_CUE_TIMING", "cue": index + 1})
            if any(token in text for token in (">>", "[웃음]", "[콧방귀]")):
                errors.append({"code": "FAIL_G40_VISIBLE_NOISE_MARKER", "cue": index + 1})
        if cues and isinstance(measured, int) and cues[-1][1] > measured + 50_000:
            errors.append({"code": "FAIL_G40_EXCEEDS_AUDIO"})
    if caption_lock.get("user_corrected_srt_applicable") is True:
        corrected_sha = caption_lock.get("user_corrected_srt_sha256")
        if (
            not _is_sha(corrected_sha)
            or actual_sha is None
            or actual_sha != corrected_sha
            or caption_lock.get("final_corrected_caption_fidelity") != "PASS"
        ):
            errors.append({"code": "FAIL_G40_USER_CORRECTED_SRT_NOT_AUTHORITY"})
    elif caption_lock.get("final_corrected_caption_fidelity") != "NOT_APPLICABLE":
        errors.append({"code": "FAIL_G40_CORRECTED_FIDELITY_STATE"})
    return _result(
        "G40",
        errors=errors,
        next_action="PREPARE_G50" if not errors else "NONE",
        auto=not errors,
    )


def validate_g50(*, track_plan: dict, caption_lock: dict) -> dict:
    errors: list[dict] = []
    required = (
        "schema_version",
        "episode_id",
        "content_profile",
        "production_mode",
        "status",
        "capcut_root",
        "caption_lock_sha256",
        "timeline_order",
        "tracks",
    )
    if track_plan.get("schema_version") != "politics-track-plan-v1" or any(
        field not in track_plan for field in required
    ):
        errors.append({"code": "FAIL_G50_TRACK_PLAN_SCHEMA"})
    profile = track_plan.get("content_profile")
    if profile not in ROOT_BY_PROFILE or track_plan.get("capcut_root") != ROOT_BY_PROFILE.get(
        profile
    ):
        errors.append({"code": "FAIL_G50_CAPCUT_ROOT"})
    if caption_lock.get("status") != "PASS":
        errors.append({"code": "FAIL_G50_REQUIRES_G40"})
    if track_plan.get("production_mode") == "source_led" and any(
        isinstance(track, dict) and track.get("role") == "narration audio"
        for track in track_plan.get("tracks", [])
    ):
        errors.append({"code": "FAIL_G50_SOURCE_LED_NARRATION_TRACK"})
    return _result(
        "G50",
        errors=errors,
        next_action="PREPARE_G60" if not errors else "NONE",
        auto=not errors,
    )


def validate_g60(*, assembly_contract: dict, track_plan: dict) -> dict:
    errors: list[dict] = []
    if assembly_contract.get("schema_version") != "politics-assembly-contract-v1":
        errors.append({"code": "FAIL_G60_ASSEMBLY_SCHEMA"})
    profile = assembly_contract.get("content_profile")
    if assembly_contract.get("capcut_root") != ROOT_BY_PROFILE.get(profile):
        errors.append({"code": "FAIL_G60_CAPCUT_ROOT"})
    if track_plan.get("status") != "PASS":
        errors.append({"code": "FAIL_G60_REQUIRES_G50"})
    for field in (
        "reference_only_material_count",
        "reference_only_timeline_count",
        "unapproved_visible_text_count",
    ):
        if assembly_contract.get(field) != 0:
            errors.append({"code": "FAIL_G60_CONTAMINATION", "field": field})
    if assembly_contract.get("structural_contamination") is not False:
        errors.append({"code": "FAIL_G60_STRUCTURAL_CONTAMINATION"})
    if assembly_contract.get("static_harness_status") != "PASS":
        errors.append({"code": "FAIL_G60_STATIC_HARNESS"})
    return _result(
        "G60",
        errors=errors,
        next_action="WAIT_USER_VISUAL_GATE" if not errors else "NONE",
        auto=False,
    )


def validate_g60_user(*, ledger_events: list[dict] | None = None) -> dict:
    present = bool(_event_positions(ledger_events, "USER_VISUAL_PASS", "G60.USER", "USER"))
    errors = [] if present else [{"code": "FAIL_G60_NO_USER_VISUAL_PASS"}]
    return _result(
        "G60.USER",
        errors=errors,
        next_action="PREPARE_G70" if not errors else "WAIT_USER_VISUAL_GATE",
        auto=not errors,
        status=None if errors else "PASS",
    )


def validate_g70(*, upload_package: dict, ledger_events: list[dict] | None = None) -> dict:
    errors: list[dict] = []
    if not _event_positions(ledger_events, "USER_VISUAL_PASS", "G60.USER", "USER"):
        errors.append({"code": "FAIL_G70_NO_USER_VISUAL_PASS"})
    if upload_package.get("release_allowed") is not False:
        errors.append({"code": "FAIL_G70_RELEASE_MUST_BE_FALSE"})
    return _result(
        "G70",
        errors=errors,
        next_action="PREPARE_G80" if not errors else "NONE",
        auto=not errors,
    )


def validate_g80(
    *, render_evidence: dict, artifact_root: Path | None = None
) -> dict:
    errors: list[dict] = []
    rendered = _resolve(artifact_root, render_evidence.get("rendered_mp4_path"))
    if rendered is None or not rendered.is_file():
        errors.append({"code": "FAIL_G80_RENDER_FILE_MISSING"})
    elif not _is_sha(render_evidence.get("rendered_mp4_sha256")) or _sha256(
        rendered
    ) != render_evidence.get("rendered_mp4_sha256"):
        errors.append({"code": "FAIL_G80_RENDER_SHA"})
    if rendered is not None and rendered.is_file():
        probe = _probe(rendered)
        if (
            probe is None
            or not probe["has_audio"]
            or not probe["has_video"]
            or render_evidence.get("ffprobe_verified") is not True
        ):
            errors.append({"code": "FAIL_G80_MEDIA_INTEGRITY"})
        else:
            locked = render_evidence.get("measured_duration_us")
            if not isinstance(locked, int) or abs(probe["duration_us"] - locked) > 100_000:
                errors.append({"code": "FAIL_G80_DURATION"})
    return _result(
        "G80",
        errors=errors,
        next_action="PREPARE_G90" if not errors else "NONE",
        auto=not errors,
    )


def validate_g90(
    *,
    final_qc: dict,
    ledger_events: list[dict] | None = None,
    render_evidence: dict | None = None,
) -> dict:
    errors: list[dict] = []
    if (
        not isinstance(render_evidence, dict)
        or render_evidence.get("ffprobe_verified") is not True
        or not _is_sha(render_evidence.get("rendered_mp4_sha256"))
    ):
        errors.append({"code": "FAIL_G90_REQUIRES_G80"})
    final_positions = _event_positions(
        ledger_events, "FINAL_QC_PASS", "G90", "VALIDATOR"
    )
    upload_positions = _event_positions(
        ledger_events, "UPLOAD_APPROVED", "G90", "USER"
    )
    if not ledger_events:
        errors.append({"code": "FAIL_G90_LEDGER_REQUIRED"})
    if upload_positions and (not final_positions or upload_positions[0] < final_positions[0]):
        errors.append({"code": "FAIL_G90_UPLOAD_BEFORE_FINAL_QC"})
    if errors:
        return _result("G90", errors=errors, next_action="NONE", auto=False)
    if not final_positions:
        return _result(
            "G90",
            next_action="WAIT_USER_INPUT",
            auto=False,
            status="WAIT_USER_INPUT",
        )
    if not upload_positions:
        return _result(
            "G90",
            next_action="WAIT_UPLOAD_APPROVAL",
            auto=False,
            status="WAIT_UPLOAD_APPROVAL",
        )
    return _result("G90", next_action="EPISODE_RELEASED", auto=False, status="PASS")


VALIDATORS = {
    "G00": validate_g00,
    "G10": validate_g10,
    "G20": validate_g20,
    "G30": validate_g30,
    "G40": validate_g40,
    "G50": validate_g50,
    "G60": validate_g60,
    "G60.USER": validate_g60_user,
    "G70": validate_g70,
    "G80": validate_g80,
    "G90": validate_g90,
}


def _load_ledger(path: Path | None) -> list[dict] | None:
    if path is None:
        return None
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("ledger event must be object")
            events.append(value)
    return events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=VALIDATORS, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("payload must be object")
        if args.artifact_root is not None:
            payload.setdefault("artifact_root", args.artifact_root)
        if args.ledger is not None:
            payload.setdefault("ledger_events", _load_ledger(args.ledger))
        result = VALIDATORS[args.gate](**payload)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        result = _result(
            args.gate,
            errors=[{"code": "FAIL_CLI_INPUT", "detail": str(exc)}],
            next_action="NONE",
            auto=False,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
