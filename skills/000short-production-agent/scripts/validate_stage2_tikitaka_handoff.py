#!/usr/bin/env python3
"""Validate 00-tikitaka v3 handoff inputs before Stage 2 CapCut work."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


REQUIRED_SEGMENT_FIELDS = {
    "edit_id",
    "source_ref",
    "source_order",
    "timeline_order",
    "assembly_role",
    "caption_type",
    "visible_text_role",
    "audio_role",
    "time_start",
    "time_end",
    "track",
    "duration_basis",
    "duration_status",
    "audio_policy",
    "visual_strategy",
}
ALLOWED_ASSEMBLY_ROLES = {
    "intro_narration",
    "context_narration",
    "payoff_narration",
    "ending_narration",
    "verified_speaker_quote",
    "situation_caption",
    "reaction_caption",
    "card_or_comment_caption",
    "source_visual_hold",
    "source_visual_action",
    "transition_or_separator",
    "ranking_item",
}
ALLOWED_DURATION_BASIS = {
    "source_range",
    "estimated_tts_duration",
    "actual_tts_duration",
    "fixed_design_duration",
    "visual_hold",
}
ALLOWED_DURATION_STATUS = {
    "SOURCE_AUDIO_LOCKED",
    "ESTIMATED_ACCEPTED",
    "ACTUAL_AUDIO_LOCKED",
    "FIXED_DESIGN_LOCKED",
    "WAIT_ACTUAL_TTS_AUDIO",
}
NARRATION_AUDIO_TTS_STATUSES = {
    "ESTIMATED_ACCEPTED",
    "ACTUAL_AUDIO_LOCKED",
    "WAIT_ACTUAL_TTS_AUDIO",
}
READY_TTS_TIMING_STATUSES = {
    "ESTIMATED_ACCEPTED",
    "ACTUAL_AUDIO_LOCKED",
}
ALLOWED_RECONCILIATION_ACTIONS = {
    "",
    "none",
    "extend_visual",
    "retime_segment",
    "split_segment",
    "shorten_text",
    "manual_acceptance",
}
SEMANTIC_AUDIO_TRACKS = {
    "audio.narration_tts",
    "audio.speaker_source",
    "audio.sfx",
    "audio.bgm",
}
FORBIDDEN_STAGE1_CAPCUT_AUDIO_TRACKS = {"A9", "A10", "A11", "A12"}


def as_path(root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else root / path


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise GateFail(f"{label} missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise GateFail(f"{label} json parse failed: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GateFail(f"{label} json root must be object: {path}")
    return data


def status_value(data: dict[str, Any]) -> str:
    return str(
        data.get("status")
        or data.get("gate_status")
        or data.get("overall_status")
        or ""
    ).upper()


def truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "approved", "decided"}
    return False


def handoff_or_contract_true(
    data: dict[str, Any],
    contract: dict[str, Any] | None,
    key: str,
) -> bool:
    if key in data:
        return data.get(key) is True
    return truthy((contract or {}).get(key))


def require_status_pass(path: Path, label: str, fail_token: str) -> dict[str, Any]:
    data = load_json(path, label)
    if status_value(data) != "PASS":
        raise GateFail(f"{fail_token}: {label} status must be PASS")
    return data


def require_existing_file(path: Path, label: str, fail_token: str) -> Path:
    if not path.exists():
        raise GateFail(f"{fail_token}: {label} missing: {path}")
    return path


def require_number(value: Any, field: str, fail_token: str) -> None:
    if isinstance(value, bool):
        raise GateFail(f"{fail_token}: {field} must be numeric")
    if isinstance(value, (int, float)) and value >= 0:
        return
    raise GateFail(f"{fail_token}: {field} must be numeric")


def segment_uses_narration_audio(segment: dict[str, Any]) -> bool:
    return (
        segment.get("caption_type") == "tts_narration"
        or segment.get("audio_role") == "audio.narration_tts"
    )


def segment_uses_speaker_quote(segment: dict[str, Any]) -> bool:
    return (
        segment.get("caption_type") == "speaker_quote"
        or segment.get("assembly_role") == "verified_speaker_quote"
    )


def validate_source_voice_separation(root: Path) -> dict[str, Any]:
    validator_path = (
        Path(__file__).resolve().parents[2]
        / "00-tikitaka"
        / "scripts"
        / "validate_source_voice_separation.py"
    )
    spec = importlib.util.spec_from_file_location(
        "stage2_source_voice_validator",
        validator_path,
    )
    if spec is None or spec.loader is None:
        raise GateFail("WAIT_SOURCE_VOICE_SEPARATION: validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.validate_source_voice_separation(root)
    except module.GateFail as exc:
        raise GateFail(str(exc)) from exc


def validate_report1_handoff(
    root: Path,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = root / "20_script" / "report1_handoff.json"
    data = load_json(path, "report1_handoff.json")
    if data.get("gate_name") != "REPORT1_HANDOFF_GATE":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: gate_name must be REPORT1_HANDOFF_GATE")
    if status_value(data) != "PASS":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: report1_handoff status must be PASS")
    if data.get("owner_skill") != "00-tikitaka":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: owner_skill must be 00-tikitaka")
    if data.get("next_skill") != "000short-production-agent":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: next_skill must be 000short-production-agent")
    if data.get("report1_approved") is not True:
        raise GateFail("WAIT_REPORT1_APPROVAL_TTS_DECISION: report1_approved must be true")
    if data.get("voice_audio_route_decided") is not True:
        raise GateFail("WAIT_REPORT1_APPROVAL_TTS_DECISION: voice_audio_route_decided must be true")
    return data


def validate_script_handoff(root: Path) -> dict[str, Any]:
    path = root / "20_script" / "script_handoff_gate.json"
    data = load_json(path, "script_handoff_gate.json")
    if data.get("gate_name") != "SCRIPT_HANDOFF_GATE":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: gate_name must be SCRIPT_HANDOFF_GATE")
    if status_value(data) != "PASS":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: script_handoff_gate status must be PASS")
    if data.get("capcut_allowed") is not True:
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: capcut_allowed must be true")
    return data


def validate_timeline_design(root: Path) -> tuple[dict[str, Any], bool]:
    path = root / "20_script" / "timeline_design.json"
    if not path.exists():
        raise GateFail(f"WAIT_TIMELINE_DESIGN_REQUIRED: timeline_design.json missing: {path}")
    data = load_json(path, "timeline_design.json")
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise GateFail("WAIT_TIMELINE_DESIGN_REQUIRED: timeline_design.segments missing")

    has_narration_audio = False
    seen_edit_ids: set[str] = set()
    seen_timeline_orders: dict[Any, str] = {}
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise GateFail(f"WAIT_TIMELINE_DESIGN_REPAIR: segments[{index}] must be object")
        missing = sorted(key for key in REQUIRED_SEGMENT_FIELDS if segment.get(key) in (None, ""))
        if missing:
            raise GateFail(
                f"WAIT_TIMELINE_DESIGN_REPAIR: segments[{index}] missing {', '.join(missing)}"
            )

        edit_id = str(segment.get("edit_id"))
        if edit_id in seen_edit_ids:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: duplicate edit_id")
        seen_edit_ids.add(edit_id)

        timeline_order = segment.get("timeline_order")
        parallel_group_id = str(segment.get("parallel_group_id") or "")
        existing_parallel_group_id = seen_timeline_orders.get(timeline_order)
        if existing_parallel_group_id is not None:
            if not parallel_group_id or existing_parallel_group_id != parallel_group_id:
                raise GateFail(
                    "WAIT_TIMELINE_DESIGN_REPAIR: duplicate timeline_order without parallel_group_id"
                )
        else:
            seen_timeline_orders[timeline_order] = parallel_group_id

        if segment.get("assembly_role") not in ALLOWED_ASSEMBLY_ROLES:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: unsupported assembly_role")
        if segment.get("duration_basis") not in ALLOWED_DURATION_BASIS:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: unsupported duration_basis")
        if segment.get("duration_status") not in ALLOWED_DURATION_STATUS:
            raise GateFail("WAIT_TIMELINE_DESIGN_REPAIR: unsupported duration_status")

        track = str(segment.get("track") or "")
        if track in FORBIDDEN_STAGE1_CAPCUT_AUDIO_TRACKS:
            raise GateFail(
                "WAIT_TIMELINE_DESIGN_REPAIR: timeline_design must use semantic audio track, not "
                f"{track}"
            )
        if track.startswith("audio.") and track not in SEMANTIC_AUDIO_TRACKS:
            raise GateFail(
                "WAIT_TIMELINE_DESIGN_REPAIR: unsupported semantic audio track "
                f"{track}"
            )

        if segment_uses_narration_audio(segment):
            has_narration_audio = True
            for field in ("tts_text_ref", "planned_tts_duration_sec", "tts_duration_status"):
                if segment.get(field) in (None, ""):
                    raise GateFail(f"WAIT_TTS_TIMING_RELOCK: segments[{index}] missing {field}")
            require_number(
                segment.get("planned_tts_duration_sec"),
                f"segments[{index}].planned_tts_duration_sec",
                "WAIT_TTS_TIMING_RELOCK",
            )
            tts_status = str(segment.get("tts_duration_status") or "")
            if tts_status not in NARRATION_AUDIO_TTS_STATUSES:
                raise GateFail("WAIT_TTS_TIMING_RELOCK: unsupported tts_duration_status")
            if tts_status == "ESTIMATED_ACCEPTED":
                if segment.get("estimated_tts_duration_sec") in (None, ""):
                    raise GateFail(
                        f"WAIT_TTS_TIMING_RELOCK: segments[{index}] missing estimated_tts_duration_sec"
                    )
                require_number(
                    segment.get("estimated_tts_duration_sec"),
                    f"segments[{index}].estimated_tts_duration_sec",
                    "WAIT_TTS_TIMING_RELOCK",
                )
            if tts_status == "ACTUAL_AUDIO_LOCKED":
                if segment.get("actual_tts_duration_sec") in (None, ""):
                    raise GateFail(
                        f"WAIT_TTS_TIMING_RELOCK: segments[{index}] missing actual_tts_duration_sec"
                    )
                require_number(
                    segment.get("actual_tts_duration_sec"),
                    f"segments[{index}].actual_tts_duration_sec",
                    "WAIT_TTS_TIMING_RELOCK",
                )

        if segment_uses_speaker_quote(segment):
            for field in (
                "source_audio_range",
                "quote_verification_status",
                "source_audio_ref",
                "source_audio_provenance",
            ):
                if segment.get(field) in (None, ""):
                    raise GateFail(
                        f"WAIT_SOURCE_VOICE_Q_PROVENANCE: segments[{index}] missing {field}"
                    )
            if (
                segment.get("source_audio_ref")
                != "10_analysis/audio/vocals.wav"
                or segment.get("source_audio_provenance")
                != "demucs_full_source_vocals"
            ):
                raise GateFail(
                    "WAIT_SOURCE_VOICE_Q_PROVENANCE: speaker_quote must use "
                    "10_analysis/audio/vocals.wav from demucs_full_source_vocals"
                )

    return data, has_narration_audio


def validate_tts_timing(root: Path, has_narration_audio: bool) -> None:
    if not has_narration_audio:
        return

    probe_path = root / "20_script" / "tts_duration_probe.json"
    if not probe_path.exists():
        raise GateFail(f"WAIT_TTS_TIMING_RELOCK: tts_duration_probe.json missing: {probe_path}")
    probe = load_json(probe_path, "tts_duration_probe.json")
    probe_status = status_value(probe)
    if probe_status not in {"PASS", "ESTIMATED_ACCEPTED"}:
        raise GateFail(
            f"WAIT_TTS_TIMING_RELOCK: tts_duration_probe status must be PASS or ESTIMATED_ACCEPTED"
        )
    tts_items = probe.get("tts_items", [])
    if tts_items is None:
        tts_items = []
    if not isinstance(tts_items, list):
        raise GateFail("WAIT_TTS_TIMING_RELOCK: tts_duration_probe.tts_items must be list")
    for index, item in enumerate(tts_items):
        if not isinstance(item, dict):
            raise GateFail(f"WAIT_TTS_TIMING_RELOCK: tts_duration_probe.tts_items[{index}] must be object")
        planned = item.get("planned_tts_duration_sec")
        planned_field = "planned_tts_duration_sec"
        if planned in (None, ""):
            planned = item.get("planned_duration_sec")
            planned_field = "planned_duration_sec"
        actual = item.get("actual_tts_duration_sec")
        actual_field = "actual_tts_duration_sec"
        if actual in (None, ""):
            actual = item.get("actual_duration_sec")
            actual_field = "actual_duration_sec"
        action = str(item.get("reconciliation_action") or "").strip()
        if action not in ALLOWED_RECONCILIATION_ACTIONS:
            raise GateFail("WAIT_TTS_TIMING_RELOCK: unsupported reconciliation action")
        if planned not in (None, ""):
            require_number(
                planned,
                f"tts_duration_probe.tts_items[{index}].{planned_field}",
                "WAIT_TTS_TIMING_RELOCK",
            )
        if actual not in (None, ""):
            require_number(
                actual,
                f"tts_duration_probe.tts_items[{index}].{actual_field}",
                "WAIT_TTS_TIMING_RELOCK",
            )
            if (
                planned not in (None, "")
                and actual > planned
                and item.get("within_tolerance") is False
                and action in {"", "none"}
            ):
                raise GateFail(
                    "WAIT_TTS_TIMING_RELOCK: actual TTS duration exceeds planned slot without reconciliation action"
                )

    gate_path = root / "20_script" / "tts_timing_reconciliation_gate.json"
    if not gate_path.exists():
        raise GateFail(
            f"WAIT_TTS_TIMING_RELOCK: tts_timing_reconciliation_gate.json missing: {gate_path}"
        )
    gate = load_json(gate_path, "tts_timing_reconciliation_gate.json")
    if status_value(gate) != "PASS":
        raise GateFail("WAIT_TTS_TIMING_RELOCK: tts_timing_reconciliation_gate status must be PASS")
    if str(gate.get("tts_duration_status") or "") not in READY_TTS_TIMING_STATUSES:
        raise GateFail(
            "WAIT_TTS_TIMING_RELOCK: tts_duration_status must be ESTIMATED_ACCEPTED or ACTUAL_AUDIO_LOCKED"
        )
    action = str(gate.get("reconciliation_action") or "").strip()
    if action not in ALLOWED_RECONCILIATION_ACTIONS:
        raise GateFail("WAIT_TTS_TIMING_RELOCK: unsupported reconciliation action")


def validate_humanize_gate(root: Path) -> dict[str, Any]:
    path = root / "20_script" / "humanize_korean_gate.json"
    data = load_json(path, "humanize_korean_gate.json")
    if status_value(data) != "PASS":
        raise GateFail("WAIT_HUMANIZE_REPAIR: humanize_korean_gate status must be PASS")
    if data.get("structure_changed") is True:
        raise GateFail("WAIT_HUMANIZE_REPAIR: structure_changed must be false")
    if data.get("protected_fields_changed") is True:
        raise GateFail("WAIT_HUMANIZE_REPAIR: protected_fields_changed must be false")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def video_id_from_url(raw_url: str) -> str:
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(str(raw_url or "").strip())
    parts = [part for part in parsed.path.split("/") if part]
    host = parsed.netloc.lower().split(":", 1)[0]
    is_youtube = host in {"youtube.com", "www.youtube.com", "m.youtube.com"}
    if is_youtube and "shorts" in parts:
        index = parts.index("shorts")
        return parts[index + 1] if index + 1 < len(parts) else ""
    if host == "youtu.be" and parts:
        return parts[0]
    if is_youtube:
        return (parse_qs(parsed.query).get("v") or [""])[0]
    return ""


def probe_source_media(source_path: Path) -> dict[str, Any]:
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
                str(source_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise GateFail(f"WAIT_SOURCE_MEDIA_FFPROBE: ffprobe unavailable or timed out: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        suffix = detail[-1] if detail else "unknown ffprobe error"
        raise GateFail(f"WAIT_SOURCE_MEDIA_FFPROBE: ffprobe failed: {suffix}")
    try:
        payload = json.loads(completed.stdout)
        duration_sec = float(payload.get("format", {}).get("duration"))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GateFail("WAIT_SOURCE_MEDIA_FFPROBE: duration missing or invalid") from exc
    streams = payload.get("streams")
    if not isinstance(streams, list) or not any(
        isinstance(stream, dict) and stream.get("codec_type") == "video" for stream in streams
    ):
        raise GateFail("WAIT_SOURCE_MEDIA_FFPROBE: video stream missing")
    if duration_sec <= 0:
        raise GateFail("WAIT_SOURCE_MEDIA_FFPROBE: duration must be positive")
    return {"duration_sec": duration_sec, "has_video_stream": True}


def validate_source_identity_lock(
    root: Path,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fail_token = "WAIT_SOURCE_IDENTITY_LOCK"
    manifest_path = root / "00_source" / "source_manifest.json"
    manifest = load_json(manifest_path, "source_manifest.json")
    if status_value(manifest) != "PASS":
        raise GateFail(f"{fail_token}: source_manifest status must be PASS")

    lock_rel = str(manifest.get("source_identity_lock_path") or "10_analysis/source_identity_lock.json")
    lock_path = as_path(root, lock_rel)
    lock = load_json(lock_path, "source_identity_lock.json")
    if status_value(lock) != "PASS":
        raise GateFail(f"{fail_token}: source_identity_lock status must be PASS")

    required = ("canonical_url", "video_id", "local_source_path", "sha256", "duration_sec")
    missing = [field for field in required if lock.get(field) in (None, "")]
    if missing:
        raise GateFail(f"{fail_token}: source_identity_lock missing {', '.join(missing)}")
    if video_id_from_url(str(lock["canonical_url"])) != str(lock["video_id"]):
        raise GateFail(f"{fail_token}: canonical_url video id mismatch")
    if (
        isinstance(lock["duration_sec"], bool)
        or not isinstance(lock["duration_sec"], (int, float))
        or float(lock["duration_sec"]) <= 0
    ):
        raise GateFail(f"{fail_token}: duration_sec must be positive numeric")

    source_request_path = root / "10_analysis" / "tikitaka_source_request.json"
    source_request = load_json(source_request_path, "tikitaka_source_request.json")
    if status_value(source_request) != "PASS":
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: Tikitaka source request status must be PASS")
    if source_request.get("owner_skill") not in (None, "", "00-tikitaka"):
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: source request owner must be 00-tikitaka")
    requested_url = str(source_request.get("requested_source_url") or "").strip()
    requested_video_id = str(source_request.get("requested_video_id") or "").strip()
    if not requested_url or not requested_video_id:
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: Tikitaka source URL/video id required")
    if video_id_from_url(requested_url) != requested_video_id:
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: Tikitaka URL/video id mismatch")
    if requested_video_id != str(lock["video_id"]):
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: Tikitaka request does not match source lock")
    contract_source_url = str(
        (contract or {}).get("requested_source_url")
        or (contract or {}).get("source_url")
        or ""
    ).strip()
    contract_video_id = video_id_from_url(contract_source_url) if contract_source_url else ""
    if contract_video_id and contract_video_id != requested_video_id:
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: contract source does not match Tikitaka request")
    if contract_video_id and contract_source_url != requested_url:
        raise GateFail("WAIT_SOURCE_REQUEST_BINDING: contract source URL must exactly match Tikitaka request")

    source_path = as_path(root, str(lock["local_source_path"]))
    if not source_path.is_file() or source_path.stat().st_size <= 0:
        raise GateFail(f"{fail_token}: local source media missing or empty: {source_path}")
    actual_sha256 = sha256_file(source_path)
    if actual_sha256.lower() != str(lock["sha256"]).lower():
        raise GateFail(f"{fail_token}: source sha256 mismatch")
    actual_probe = probe_source_media(source_path)
    if abs(float(actual_probe["duration_sec"]) - float(lock["duration_sec"])) > 0.25:
        raise GateFail("WAIT_SOURCE_MEDIA_FFPROBE: source duration does not match identity lock")

    for field in required:
        if manifest.get(field) != lock.get(field):
            raise GateFail(f"{fail_token}: source_manifest {field} mismatch")

    evidence_paths = {
        "source_evidence": str(manifest.get("source_evidence_path") or "10_analysis/source_evidence.json"),
        "crosscheck_report": str(manifest.get("crosscheck_report_path") or "10_analysis/crosscheck_report.json"),
    }
    verified_evidence: dict[str, str] = {}
    for label, relative in evidence_paths.items():
        evidence_path = as_path(root, relative)
        evidence = load_json(evidence_path, f"{label}.json")
        if status_value(evidence) != "PASS":
            raise GateFail(f"WAIT_SOURCE_EVIDENCE_REQUIRED: {label} status must be PASS")
        if str(evidence.get("video_id") or "") != str(lock["video_id"]):
            raise GateFail(f"WAIT_SOURCE_EVIDENCE_REQUIRED: {label} video_id mismatch")
        if str(evidence.get("source_fingerprint_sha256") or "").lower() != actual_sha256.lower():
            raise GateFail(f"WAIT_SOURCE_EVIDENCE_REQUIRED: {label} source fingerprint mismatch")
        if label == "source_evidence":
            stt = evidence.get("stt")
            if (
                not isinstance(stt, dict)
                or status_value(stt) != "PASS"
                or not isinstance(stt.get("verified_ranges"), list)
            ):
                raise GateFail("WAIT_SOURCE_EVIDENCE_REQUIRED: stt verified_ranges are required")
            probed_duration = evidence.get("probed_duration_sec")
            if evidence.get("ffprobe_status") != "PASS" or evidence.get("has_video_stream") is not True:
                raise GateFail(
                    "WAIT_SOURCE_EVIDENCE_PROBE_REQUIRED: ffprobe PASS and video stream evidence required"
                )
            if isinstance(probed_duration, bool) or not isinstance(probed_duration, (int, float)):
                raise GateFail("WAIT_SOURCE_EVIDENCE_PROBE_REQUIRED: probed_duration_sec must be numeric")
            if abs(float(probed_duration) - float(lock["duration_sec"])) > 0.25:
                raise GateFail("WAIT_SOURCE_EVIDENCE_PROBE_REQUIRED: probed duration mismatch")
            if abs(float(probed_duration) - float(actual_probe["duration_sec"])) > 0.25:
                raise GateFail("WAIT_SOURCE_EVIDENCE_PROBE_REQUIRED: evidence does not match actual ffprobe")
        else:
            if evidence.get("hint_vs_evidence_compared") is not True:
                raise GateFail("WAIT_SOURCE_EVIDENCE_REQUIRED: crosscheck comparison is incomplete")
        verified_evidence[label] = str(evidence_path)

    return {
        "source_path": source_path,
        "source_manifest_path": manifest_path,
        "source_identity_lock_path": lock_path,
        "source_sha256": actual_sha256,
        "video_id": str(lock["video_id"]),
        "requested_video_id": requested_video_id,
        "tikitaka_source_request_path": source_request_path,
        "source_probe_duration_sec": actual_probe["duration_sec"],
        **verified_evidence,
    }


def validate_handoff_source_fingerprints(
    report1: dict[str, Any],
    script_handoff: dict[str, Any],
    timeline_design: dict[str, Any],
    expected_sha256: str,
) -> None:
    expected = expected_sha256.lower()
    for label, payload in (
        ("report1_handoff.json", report1),
        ("script_handoff_gate.json", script_handoff),
        ("timeline_design.json", timeline_design),
    ):
        actual = str(payload.get("source_fingerprint_sha256") or "").lower()
        if actual != expected:
            raise GateFail(
                f"WAIT_SOURCE_HANDOFF_FINGERPRINT: {label} source fingerprint mismatch"
            )


def validate_handoff_maps(root: Path, timeline_design: dict[str, Any]) -> dict[str, Any]:
    fail_token = "WAIT_HANDOFF_MAP_COHERENCE"
    role_map_path = root / "20_script" / "block_role_map.json"
    if not role_map_path.exists():
        raise GateFail(f"WAIT_BLOCK_ROLE_MAP_REQUIRED: {fail_token}: block_role_map.json missing")
    try:
        block_map = load_json(root / "20_script" / "block_map.json", "block_map.json")
        role_map = load_json(role_map_path, "block_role_map.json")
        voice_map = load_json(root / "20_script" / "block_voice_switch_map.json", "block_voice_switch_map.json")
    except GateFail as exc:
        raise GateFail(f"{fail_token}: {exc}") from exc

    timeline_segments = [
        item for item in timeline_design.get("segments", []) if isinstance(item, dict)
    ]
    timeline_ids = {str(item.get("edit_id")) for item in timeline_segments}
    sequence = block_map.get("edit_block_sequence")
    blocks = block_map.get("blocks")
    roles = role_map.get("roles")
    switches = voice_map.get("switches")
    if not isinstance(sequence, list) or not isinstance(blocks, list):
        raise GateFail(f"{fail_token}: block_map lists missing")
    if not isinstance(roles, list) or not isinstance(switches, list):
        raise GateFail(f"{fail_token}: role or voice map lists missing")
    for label, items in (("blocks", blocks), ("roles", roles), ("switches", switches)):
        if any(not isinstance(item, dict) or not str(item.get("edit_id") or "") for item in items):
            raise GateFail(f"{fail_token}: {label} contains invalid edit_id")
        edit_ids = [str(item["edit_id"]) for item in items]
        if len(edit_ids) != len(set(edit_ids)):
            raise GateFail(f"{fail_token}: {label} contains duplicate edit_id")
    sequence_values = [str(value) for value in sequence]
    if len(sequence_values) != len(set(sequence_values)):
        raise GateFail(f"{fail_token}: edit_block_sequence contains duplicate edit_id")
    sequence_ids = {str(value) for value in sequence}
    block_ids = {str(item.get("edit_id")) for item in blocks if isinstance(item, dict)}
    role_ids = {str(item.get("edit_id")) for item in roles if isinstance(item, dict)}
    switch_ids = {str(item.get("edit_id")) for item in switches if isinstance(item, dict)}
    if not timeline_ids or not (timeline_ids == sequence_ids == block_ids == role_ids == switch_ids):
        raise GateFail(f"{fail_token}: edit_id coverage mismatch")
    timeline_by_id = {str(item["edit_id"]): item for item in timeline_segments}
    expected_sequence = [
        str(item["edit_id"])
        for item in sorted(
            timeline_segments,
            key=lambda item: (int(item.get("timeline_order", 0)), str(item["edit_id"])),
        )
    ]
    if sequence_values != expected_sequence:
        raise GateFail(f"{fail_token}: edit_block_sequence must match timeline_order")
    for block in blocks:
        segment = timeline_by_id[str(block["edit_id"])]
        expected_source = str(segment.get("source_ref") or "")
        if expected_source and str(block.get("source_block_id") or "") != expected_source:
            raise GateFail(f"{fail_token}: source_block_id mismatch for {block['edit_id']}")
        if "source_order" in block and block.get("source_order") != segment.get("source_order"):
            raise GateFail(f"{fail_token}: source_order mismatch for {block['edit_id']}")
        if "timeline_order" in block and block.get("timeline_order") != segment.get("timeline_order"):
            raise GateFail(f"{fail_token}: timeline_order mismatch for {block['edit_id']}")
    for role in roles:
        edit_id = str(role["edit_id"])
        caption_type = str(role.get("caption_type") or "")
        if not caption_type or caption_type != str(timeline_by_id[edit_id].get("caption_type") or ""):
            raise GateFail(f"{fail_token}: role caption_type mismatch for {edit_id}")
    for switch in switches:
        segment = timeline_by_id[str(switch["edit_id"])]
        caption_type = str(segment.get("caption_type") or "")
        expected_source_audio = "on" if caption_type == "speaker_quote" else "off"
        expected_tts = "on" if segment_uses_narration_audio(segment) else "off"
        if switch.get("source_audio") != expected_source_audio or switch.get("tts") != expected_tts:
            raise GateFail(f"{fail_token}: voice switch semantics mismatch for {switch['edit_id']}")
    return {"handoff_map_edit_ids": sorted(timeline_ids)}


def validate_integrated_blueprint_artifact(root: Path) -> dict[str, Any]:
    validator_path = Path(__file__).with_name("validate_integrated_blueprint.py")
    spec = importlib.util.spec_from_file_location("integrated_blueprint_validator", validator_path)
    if spec is None or spec.loader is None:
        raise GateFail("FAIL_ASSEMBLY_BLUEPRINT_VALIDATOR_MISSING")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.validate_integrated_blueprint(root / "20_script" / "design_blueprint.md", phase="production")
    except module.BlueprintGateFail as exc:
        raise GateFail(str(exc)) from exc


def integrated_blueprint_status(root: Path, *, require_production: bool) -> dict[str, Any]:
    """Validate blueprint only at the stage that owns that contract.

    Stage-2 entry validates source/script handoff. Production completion owns
    the full design+assembly+upload blueprint. Legacy handoff fixtures may not
    have a human-facing blueprint yet, so entry reports NOT_RUN instead of
    masking the handoff failure under a production-only requirement.
    """
    blueprint = root / "20_script" / "design_blueprint.md"
    if require_production:
        return validate_integrated_blueprint_artifact(root)
    if not blueprint.is_file():
        return {"status": "NOT_RUN", "path": str(blueprint)}
    validator_path = Path(__file__).with_name("validate_integrated_blueprint.py")
    spec = importlib.util.spec_from_file_location("integrated_blueprint_design_validator", validator_path)
    if spec is None or spec.loader is None:
        raise GateFail("FAIL_DESIGN_BLUEPRINT_VALIDATOR_MISSING")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.validate_integrated_blueprint(blueprint, phase="design")
    except module.BlueprintGateFail as exc:
        raise GateFail(str(exc)) from exc


def validate_stage2_tikitaka_handoff(
    root: Path,
    contract: dict[str, Any] | None = None,
    *,
    require_production_blueprint: bool = False,
) -> dict[str, Any]:
    root = Path(root)
    report1 = validate_report1_handoff(root, contract)
    script_handoff = validate_script_handoff(root)
    timeline_design, has_narration_audio = validate_timeline_design(root)
    require_status_pass(
        root / "20_script" / "timeline_design_gate.json",
        "timeline_design_gate.json",
        "WAIT_TIMELINE_DESIGN_REPAIR",
    )
    validate_humanize_gate(root)
    map_result = validate_handoff_maps(root, timeline_design)
    if has_narration_audio:
        validate_tts_timing(root, has_narration_audio)
        tts_copy = require_existing_file(
            root / "20_script" / "tts_copy_text.txt",
            "tts_copy_text.txt",
            "WAIT_TTS_COPY_TEXT_REQUIRED",
        )
        if not tts_copy.read_text(encoding="utf-8-sig").strip():
            raise GateFail("WAIT_TTS_COPY_TEXT_REQUIRED: tts_copy_text.txt is empty")
    source_result = validate_source_identity_lock(root, contract)
    source_voice_result = validate_source_voice_separation(root)
    has_speaker_quote = any(
        segment_uses_speaker_quote(item)
        for item in timeline_design.get("segments", [])
    )
    if (
        has_speaker_quote
        and source_voice_result.get("source_voice_separation_status")
        != "PASS"
    ):
        raise GateFail(
            "WAIT_SOURCE_VOICE_Q_PROVENANCE: speaker_quote requires PASS Demucs vocals"
        )
    if has_speaker_quote:
        evidence = load_json(root / "10_analysis" / "source_evidence.json", "source_evidence.json")
        ranges = evidence.get("stt", {}).get("verified_ranges") if isinstance(evidence.get("stt"), dict) else None
        if not isinstance(ranges, list) or not ranges:
            raise GateFail("WAIT_SOURCE_QUOTE_EVIDENCE: verified STT range required")
    blueprint_result = integrated_blueprint_status(
        root,
        require_production=require_production_blueprint,
    )
    validate_handoff_source_fingerprints(
        report1,
        script_handoff,
        timeline_design,
        source_result["source_sha256"],
    )
    return {
        "stage2_tikitaka_handoff_status": "PASS",
        "stage2_tikitaka_source_of_truth": "20_script/timeline_design.json",
        "timeline_design_segment_count": len(timeline_design["segments"]),
        "report1_handoff_next_skill": report1["next_skill"],
        "source_media_or_manifest": str(source_result["source_path"]),
        **source_result,
        **source_voice_result,
        **map_result,
        "integrated_blueprint_status": blueprint_result["status"],
        "integrated_blueprint_path": blueprint_result["path"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--require-production-blueprint",
        action="store_true",
        help="Require the completed design+assembly+upload blueprint.",
    )
    args = parser.parse_args()
    try:
        result = validate_stage2_tikitaka_handoff(
            Path(args.root),
            require_production_blueprint=args.require_production_blueprint,
        )
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
