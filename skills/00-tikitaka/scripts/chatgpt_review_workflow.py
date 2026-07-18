#!/usr/bin/env python3
"""Build and validate Tikitaka ChatGPT Project two-pass review artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ID = "g-p-6a245b804c2c8191907088f317842a55-syoceudaebonbunseog"
ROUND1_PACKET = Path("chatgpt_review/round1_review_packet.md")
ROUND1_RESPONSE = Path("chatgpt_review/round1_chatgpt_raw.md")
ROUND1_DECISIONS = Path("chatgpt_review/round1_codex_decisions.json")
ROUND2_PACKET = Path("chatgpt_review/round2_audit_packet.md")
ROUND2_RESPONSE = Path("chatgpt_review/round2_chatgpt_raw.md")
REVIEW_GATE = Path("chatgpt_review_gate.json")
ROUND1_REQUIRED_FILES = (
    "design_blueprint.md",
    "timeline_design.json",
    "timeline_design_gate.json",
    "caption_beat_map.json",
)
SOURCE_FINGERPRINT_PATTERN = re.compile(r"^[A-Fa-f0-9]{64}$")
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
RECOMMENDATIONS = {
    "PASS_RECOMMENDED",
    "REVISE_REQUIRED",
    "EVIDENCE_REQUIRED",
}
DECISION_VALUES = {
    "ADOPTED",
    "PARTIALLY_ADOPTED",
    "REJECTED",
    "PENDING_EVIDENCE",
}
PROTECTED_FIELDS = (
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
)
ROUND2_REQUIRED_FILES = (
    "design_blueprint.md",
    "timeline_design.json",
    "timeline_design_gate.json",
    "caption_beat_map.json",
    "humanize_korean_gate.json",
    "block_map.json",
    "block_role_map.json",
    "block_voice_switch_map.json",
    "tts_copy_text.txt",
)


class ReviewWorkflowError(RuntimeError):
    """Raised when a review artifact cannot be created or trusted."""


def normalize_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def canonical_packet_sha256(text: str) -> str:
    normalized = normalize_lf(text)
    output: list[str] = []
    removed = False
    for line in normalized.splitlines(keepends=True):
        candidate = line[:-1] if line.endswith("\n") else line
        if not removed and candidate.startswith("sent_packet_sha256:"):
            removed = True
            continue
        output.append(line)
    if not removed:
        raise ReviewWorkflowError("sent_packet_sha256 top-level metadata line missing")
    return hashlib.sha256("".join(output).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_text(path: Path) -> str:
    if not path.is_file() or path.stat().st_size == 0:
        raise ReviewWorkflowError(f"required file missing or empty: {path.name}")
    return normalize_lf(path.read_text(encoding="utf-8-sig"))


def _read_json_object(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewWorkflowError(f"invalid JSON: {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReviewWorkflowError(f"JSON root must be an object: {path.name}")
    return payload


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_lf(text)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(normalized, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    _write_text_atomic(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def _validate_id(value: str, field: str) -> str:
    normalized = str(value or "").strip()
    if not normalized or not SAFE_ID_PATTERN.fullmatch(normalized):
        raise ReviewWorkflowError(f"{field} must match {SAFE_ID_PATTERN.pattern}")
    return normalized


def _source_lock_path(work_dir: Path) -> tuple[str, Path]:
    candidates = (
        ("source_identity_lock.json", work_dir / "source_identity_lock.json"),
        (
            "10_analysis/source_identity_lock.json",
            work_dir / "10_analysis" / "source_identity_lock.json",
        ),
        (
            "10_analysis/source_identity_lock.json",
            work_dir.parent / "10_analysis" / "source_identity_lock.json",
        ),
    )
    for packet_title, path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return packet_title, path
    raise ReviewWorkflowError(
        "required file missing or empty: 10_analysis/source_identity_lock.json"
    )


def _source_fingerprint(work_dir: Path) -> str:
    timeline = _read_json_object(work_dir / "timeline_design.json")
    fingerprint = str(timeline.get("source_fingerprint_sha256") or "").strip().lower()
    if not SOURCE_FINGERPRINT_PATTERN.fullmatch(fingerprint):
        raise ReviewWorkflowError(
            "timeline_design.json source_fingerprint_sha256 missing or invalid"
        )

    _, source_lock_path = _source_lock_path(work_dir)
    source_lock = _read_json_object(source_lock_path)
    locked = str(
        source_lock.get("sha256")
        or source_lock.get("source_fingerprint_sha256")
        or ""
    ).strip().lower()
    if locked != fingerprint:
        raise ReviewWorkflowError("source identity fingerprint mismatch")
    return fingerprint


def _require_round1_inputs(work_dir: Path) -> None:
    _source_lock_path(work_dir)
    for relative in ROUND1_REQUIRED_FILES:
        _read_text(work_dir / relative)
    timeline_gate = _read_json_object(work_dir / "timeline_design_gate.json")
    if str(timeline_gate.get("status") or "").upper() != "PASS":
        raise ReviewWorkflowError("timeline_design_gate.json status must be PASS")


def _episode_id(work_dir: Path) -> str:
    candidate = work_dir.parent.name if work_dir.name == "20_script" else work_dir.name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate).strip("-")
    return safe or "episode"


def _section(title: str, text: str) -> str:
    body = normalize_lf(text)
    if not body.endswith("\n"):
        body += "\n"
    return f"## {title}\n\n```text\n{body}```\n\n"


def _first_metadata_value(text: str, key: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*?)\s*$", re.MULTILINE)
    match = pattern.search(normalize_lf(text))
    if not match:
        raise ReviewWorkflowError(f"{key} missing")
    return match.group(1)


def _packet_metadata(packet_text: str) -> dict[str, str]:
    normalized = normalize_lf(packet_text)
    header = normalized.split("\n\n", 1)[0]
    content_type = _first_metadata_value(header, "content_type")
    if content_type != "shorts":
        raise ReviewWorkflowError("packet content_type must be shorts")
    sent_hash = _first_metadata_value(header, "sent_packet_sha256").lower()
    if not SOURCE_FINGERPRINT_PATTERN.fullmatch(sent_hash):
        raise ReviewWorkflowError("packet sent_packet_sha256 missing or invalid")
    if sent_hash != canonical_packet_sha256(normalized):
        raise ReviewWorkflowError("packet sent_packet_sha256 is not canonical")
    return {
        "content_type": content_type,
        "review_round": _first_metadata_value(header, "review_round"),
        "review_cycle_id": _first_metadata_value(header, "review_cycle_id"),
        "packet_id": _first_metadata_value(header, "packet_id"),
        "sent_packet_sha256": sent_hash,
    }


def _response_recommendation(response_text: str, round_number: int) -> str | None:
    normalized = normalize_lf(response_text)
    found: list[str] = []
    for line in normalized.splitlines():
        stripped = line.strip()
        if stripped in RECOMMENDATIONS:
            found.append(stripped)
            continue
        if stripped.startswith("recommendation:"):
            value = stripped.split(":", 1)[1].strip()
            if value in RECOMMENDATIONS:
                found.append(value)
    unique = list(dict.fromkeys(found))
    if round_number == 1:
        if unique:
            raise ReviewWorkflowError("Round 1 response must not make a recommendation")
        return None
    if len(unique) != 1:
        raise ReviewWorkflowError("Round 2 response must contain one recommendation")
    return unique[0]


def validate_response(
    packet_path: Path,
    response_path: Path,
    round_number: int,
) -> dict[str, object]:
    if round_number not in {1, 2}:
        raise ReviewWorkflowError("round_number must be 1 or 2")

    packet = _read_text(Path(packet_path))
    response = _read_text(Path(response_path))
    packet_metadata = _packet_metadata(packet)
    response_lines = [line.strip() for line in response.splitlines() if line.strip()]
    if not response_lines or response_lines[0] != "ROUTE=SHORTS":
        raise ReviewWorkflowError("response first line must be ROUTE=SHORTS")
    if response_lines[-1] != "external_review_status: PENDING_CODEX_REVIEW":
        raise ReviewWorkflowError(
            "response final line must be external_review_status: PENDING_CODEX_REVIEW"
        )

    response_metadata = {
        "review_round": _first_metadata_value(response, "review_round"),
        "review_cycle_id": _first_metadata_value(response, "review_cycle_id"),
        "packet_id": _first_metadata_value(response, "packet_id"),
        "sent_packet_sha256": _first_metadata_value(
            response,
            "sent_packet_sha256",
        ).lower(),
    }
    expected = {
        "review_round": str(round_number),
        "review_cycle_id": packet_metadata["review_cycle_id"],
        "packet_id": packet_metadata["packet_id"],
        "sent_packet_sha256": packet_metadata["sent_packet_sha256"],
    }
    for key, expected_value in expected.items():
        if response_metadata[key] != expected_value:
            raise ReviewWorkflowError(f"{key} mismatch")

    return {
        "status": "VALID",
        "review_round": round_number,
        "review_cycle_id": response_metadata["review_cycle_id"],
        "packet_id": response_metadata["packet_id"],
        "sent_packet_sha256": response_metadata["sent_packet_sha256"],
        "recommendation": _response_recommendation(response, round_number),
        "packet_sha256": sha256_file(Path(packet_path)),
        "response_sha256": sha256_file(Path(response_path)),
        "external_review_status": "PENDING_CODEX_REVIEW",
    }


def _suggestion_ids(response_text: str) -> list[str]:
    found = re.findall(
        r"^suggestion_id:\s*([A-Za-z0-9._-]+)\s*$",
        normalize_lf(response_text),
        flags=re.MULTILINE,
    )
    return list(dict.fromkeys(found))


def validate_codex_decisions(
    decisions_path: Path,
    round1_response_path: Path,
) -> dict[str, object]:
    decisions_payload = _read_json_object(Path(decisions_path))
    if str(decisions_payload.get("status") or "").upper() != "PASS":
        raise ReviewWorkflowError("Codex decisions status must be PASS")
    if decisions_payload.get("all_suggestions_dispositioned") is not True:
        raise ReviewWorkflowError("not all Round 1 suggestions were dispositioned")
    decisions = decisions_payload.get("decisions")
    if not isinstance(decisions, list):
        raise ReviewWorkflowError("Codex decisions list missing")

    expected_ids = _suggestion_ids(_read_text(Path(round1_response_path)))
    actual_ids: list[str] = []
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            raise ReviewWorkflowError(f"Codex decision {index} must be an object")
        suggestion_id = str(decision.get("suggestion_id") or "").strip()
        disposition = str(
            decision.get("disposition")
            or decision.get("decision")
            or ""
        ).strip()
        if not suggestion_id:
            raise ReviewWorkflowError(f"Codex decision {index} suggestion_id missing")
        if disposition not in DECISION_VALUES:
            raise ReviewWorkflowError(
                f"Codex decision {suggestion_id} has invalid disposition"
            )
        if disposition == "PENDING_EVIDENCE":
            raise ReviewWorkflowError(
                f"PENDING_EVIDENCE remains for suggestion {suggestion_id}"
            )
        actual_ids.append(suggestion_id)

    if len(actual_ids) != len(set(actual_ids)):
        raise ReviewWorkflowError("duplicate Codex decision suggestion_id")
    if set(actual_ids) != set(expected_ids):
        raise ReviewWorkflowError(
            "Codex decision IDs do not match Round 1 suggestion IDs"
        )
    return {
        "status": "PASS",
        "all_suggestions_dispositioned": True,
        "suggestion_count": len(expected_ids),
        "decision_count": len(actual_ids),
    }


def _protected_fields_payload(work_dir: Path) -> list[dict[str, Any]]:
    timeline = _read_json_object(work_dir / "timeline_design.json")
    segments = timeline.get("segments") or timeline.get("timeline_segments")
    if not isinstance(segments, list) or not segments:
        raise ReviewWorkflowError("timeline_design.json segments missing")
    protected: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ReviewWorkflowError(f"timeline segment {index} must be an object")
        protected.append({key: segment.get(key) for key in PROTECTED_FIELDS})
    return protected


def protected_fields_sha256(work_dir: Path) -> str:
    canonical = json.dumps(
        _protected_fields_payload(Path(work_dir)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _timeline_uses_narration(work_dir: Path) -> bool:
    timeline = _read_json_object(work_dir / "timeline_design.json")
    segments = timeline.get("segments") or timeline.get("timeline_segments") or []
    return any(
        isinstance(segment, dict)
        and (
            segment.get("caption_type") == "tts_narration"
            or segment.get("audio_role") == "audio.narration_tts"
        )
        for segment in segments
    )


def _require_round2_inputs(work_dir: Path) -> None:
    for relative in ROUND2_REQUIRED_FILES:
        _read_text(work_dir / relative)
    timeline_gate = _read_json_object(work_dir / "timeline_design_gate.json")
    if str(timeline_gate.get("status") or "").upper() != "PASS":
        raise ReviewWorkflowError("timeline_design_gate.json status must be PASS")
    humanize = _read_json_object(work_dir / "humanize_korean_gate.json")
    if str(humanize.get("status") or "").upper() != "PASS":
        raise ReviewWorkflowError("humanize_korean_gate.json status must be PASS")
    if (
        humanize.get("structure_changed") is True
        or humanize.get("protected_fields_changed") is True
    ):
        raise ReviewWorkflowError("Humanize changed protected timeline structure")
    if _timeline_uses_narration(work_dir):
        for relative in (
            "tts_duration_probe.json",
            "tts_timing_reconciliation_gate.json",
        ):
            payload = _read_json_object(work_dir / relative)
            if str(payload.get("status") or "").upper() != "PASS":
                raise ReviewWorkflowError(f"{relative} status must be PASS")


def build_round2(
    work_dir: Path,
    review_cycle_id: str,
    *,
    packet_id: str | None = None,
) -> dict[str, object]:
    root = Path(work_dir).resolve()
    cycle_id = _validate_id(review_cycle_id, "review_cycle_id")
    resolved_packet_id = _validate_id(
        packet_id or f"{cycle_id}-round2",
        "packet_id",
    )
    round1 = validate_response(
        root / ROUND1_PACKET,
        root / ROUND1_RESPONSE,
        1,
    )
    if round1["review_cycle_id"] != cycle_id:
        raise ReviewWorkflowError("Round 1 review_cycle_id mismatch")
    decisions = validate_codex_decisions(
        root / ROUND1_DECISIONS,
        root / ROUND1_RESPONSE,
    )
    _require_round2_inputs(root)
    fingerprint = _source_fingerprint(root)
    protected_hash = protected_fields_sha256(root)
    timeline = _read_json_object(root / "timeline_design.json")
    truth_mode = str(timeline.get("truth_mode") or "fact_first").strip()
    if truth_mode not in {"fact_first", "hook_first_writer_premise"}:
        raise ReviewWorkflowError(f"unsupported truth_mode: {truth_mode}")

    header = (
        "content_type: shorts\n"
        "review_round: 2\n"
        f"review_cycle_id: {cycle_id}\n"
        f"packet_id: {resolved_packet_id}\n"
        "sent_packet_sha256: __PENDING__\n"
        f"episode_id: {_episode_id(root)}\n"
        f"source_fingerprint_sha256: {fingerprint}\n"
        f"truth_mode: {truth_mode}\n"
        f"protected_fields_sha256: {protected_hash}\n"
        f"project_id: {PROJECT_ID}\n\n"
    )
    body = (
        "# Tikitaka Shorts Round 2 Evidence Audit Packet\n\n"
        "Perform EVIDENCE_AUDIT only. Audit the revised candidate and Round 1 "
        "resolution; do not start a new creative rewrite.\n\n"
        f"Round 1 suggestion count: {decisions['suggestion_count']}\n\n"
    )
    sections = (
        ("round1_review_packet.md", root / ROUND1_PACKET),
        ("round1_chatgpt_raw.md", root / ROUND1_RESPONSE),
        ("round1_codex_decisions.json", root / ROUND1_DECISIONS),
        ("revised design_blueprint.md", root / "design_blueprint.md"),
        ("revised timeline_design.json", root / "timeline_design.json"),
        ("timeline_design_gate.json", root / "timeline_design_gate.json"),
        ("caption_beat_map.json", root / "caption_beat_map.json"),
        ("humanize_korean_gate.json", root / "humanize_korean_gate.json"),
        ("block_map.json", root / "block_map.json"),
        ("block_role_map.json", root / "block_role_map.json"),
        ("block_voice_switch_map.json", root / "block_voice_switch_map.json"),
        ("tts_copy_text.txt", root / "tts_copy_text.txt"),
    )
    for title, path in sections:
        body += _section(title, _read_text(path))
    if _timeline_uses_narration(root):
        body += _section(
            "tts_duration_probe.json",
            _read_text(root / "tts_duration_probe.json"),
        )
        body += _section(
            "tts_timing_reconciliation_gate.json",
            _read_text(root / "tts_timing_reconciliation_gate.json"),
        )

    packet_with_placeholder = header + body
    sent_hash = canonical_packet_sha256(packet_with_placeholder)
    packet = packet_with_placeholder.replace(
        "sent_packet_sha256: __PENDING__",
        f"sent_packet_sha256: {sent_hash}",
        1,
    )
    packet_path = root / ROUND2_PACKET
    _write_text_atomic(packet_path, packet)
    return {
        "status": "READY",
        "review_round": 2,
        "review_cycle_id": cycle_id,
        "packet_id": resolved_packet_id,
        "sent_packet_sha256": sent_hash,
        "packet_sha256": sha256_file(packet_path),
        "packet_path": str(packet_path),
        "project_id": PROJECT_ID,
        "source_fingerprint_sha256": fingerprint,
        "protected_fields_sha256": protected_hash,
    }


def finalize_gate(work_dir: Path) -> dict[str, Any]:
    root = Path(work_dir).resolve()
    round1 = validate_response(
        root / ROUND1_PACKET,
        root / ROUND1_RESPONSE,
        1,
    )
    decisions = validate_codex_decisions(
        root / ROUND1_DECISIONS,
        root / ROUND1_RESPONSE,
    )
    round2 = validate_response(
        root / ROUND2_PACKET,
        root / ROUND2_RESPONSE,
        2,
    )
    if round1["review_cycle_id"] != round2["review_cycle_id"]:
        raise ReviewWorkflowError("review_cycle_id differs between rounds")
    if round2["recommendation"] != "PASS_RECOMMENDED":
        raise ReviewWorkflowError(
            f"Round 2 recommendation is {round2['recommendation']}"
        )

    round2_packet = _read_text(root / ROUND2_PACKET)
    packet_protected_hash = _first_metadata_value(
        round2_packet.split("\n\n", 1)[0],
        "protected_fields_sha256",
    ).lower()
    current_protected_hash = protected_fields_sha256(root)
    if packet_protected_hash != current_protected_hash:
        raise ReviewWorkflowError("protected fields changed after Round 2 packet")

    source_fingerprint = _source_fingerprint(root)
    packet_fingerprint = _first_metadata_value(
        round2_packet.split("\n\n", 1)[0],
        "source_fingerprint_sha256",
    ).lower()
    if packet_fingerprint != source_fingerprint:
        raise ReviewWorkflowError("source fingerprint changed after Round 2 packet")

    gate: dict[str, Any] = {
        "gate_name": "CHATGPT_PROJECT_TWO_PASS_REVIEW_GATE",
        "status": "PASS",
        "project_id": PROJECT_ID,
        "content_type": "shorts",
        "review_cycle_id": round1["review_cycle_id"],
        "source_fingerprint_sha256": source_fingerprint,
        "round1": {
            "review_round": 1,
            "review_cycle_id": round1["review_cycle_id"],
            "packet_id": round1["packet_id"],
            "sent_packet_sha256": round1["sent_packet_sha256"],
            "external_review_status": "PENDING_CODEX_REVIEW",
            "packet_sha256": round1["packet_sha256"],
            "response_sha256": round1["response_sha256"],
        },
        "codex_decisions": decisions,
        "round2": {
            "review_round": 2,
            "review_cycle_id": round2["review_cycle_id"],
            "packet_id": round2["packet_id"],
            "sent_packet_sha256": round2["sent_packet_sha256"],
            "external_review_status": "PENDING_CODEX_REVIEW",
            "recommendation": round2["recommendation"],
            "packet_sha256": round2["packet_sha256"],
            "response_sha256": round2["response_sha256"],
        },
        "protected_fields_sha256": current_protected_hash,
        "protected_fields_changed_after_round2": False,
        "final_decision_owner": "Codex",
    }
    _write_json_atomic(root / REVIEW_GATE, gate)
    return gate


def record_response(
    work_dir: Path,
    round_number: int,
    input_path: Path,
) -> dict[str, object]:
    root = Path(work_dir).resolve()
    source = Path(input_path).resolve()
    raw = _read_text(source)
    if round_number == 1:
        packet_path = root / ROUND1_PACKET
        response_path = root / ROUND1_RESPONSE
    elif round_number == 2:
        packet_path = root / ROUND2_PACKET
        response_path = root / ROUND2_RESPONSE
    else:
        raise ReviewWorkflowError("round_number must be 1 or 2")
    _write_text_atomic(response_path, raw)
    result = validate_response(packet_path, response_path, round_number)
    result["response_path"] = str(response_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and validate Tikitaka ChatGPT Project review artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("build-round1", "build-round2"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--work-dir", required=True)
        subparser.add_argument("--review-cycle-id", required=True)
        subparser.add_argument("--packet-id", default="")

    record = subparsers.add_parser("record-response")
    record.add_argument("--work-dir", required=True)
    record.add_argument("--round", type=int, choices=(1, 2), required=True)
    record.add_argument("--input", required=True)

    finalize = subparsers.add_parser("finalize-gate")
    finalize.add_argument("--work-dir", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "build-round1":
            result = build_round1(
                Path(args.work_dir),
                args.review_cycle_id,
                packet_id=args.packet_id or None,
            )
        elif args.command == "build-round2":
            result = build_round2(
                Path(args.work_dir),
                args.review_cycle_id,
                packet_id=args.packet_id or None,
            )
        elif args.command == "record-response":
            result = record_response(
                Path(args.work_dir),
                args.round,
                Path(args.input),
            )
        else:
            result = finalize_gate(Path(args.work_dir))
    except ReviewWorkflowError as exc:
        print(
            json.dumps(
                {"status": "FAIL", "reason": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_round1(
    work_dir: Path,
    review_cycle_id: str,
    *,
    packet_id: str | None = None,
) -> dict[str, object]:
    root = Path(work_dir).resolve()
    cycle_id = _validate_id(review_cycle_id, "review_cycle_id")
    resolved_packet_id = _validate_id(
        packet_id or f"{cycle_id}-round1",
        "packet_id",
    )
    _require_round1_inputs(root)
    fingerprint = _source_fingerprint(root)

    timeline = _read_json_object(root / "timeline_design.json")
    truth_mode = str(timeline.get("truth_mode") or "fact_first").strip()
    if truth_mode not in {"fact_first", "hook_first_writer_premise"}:
        raise ReviewWorkflowError(f"unsupported truth_mode: {truth_mode}")

    header = (
        "content_type: shorts\n"
        "review_round: 1\n"
        f"review_cycle_id: {cycle_id}\n"
        f"packet_id: {resolved_packet_id}\n"
        "sent_packet_sha256: __PENDING__\n"
        f"episode_id: {_episode_id(root)}\n"
        f"source_fingerprint_sha256: {fingerprint}\n"
        f"truth_mode: {truth_mode}\n"
        f"project_id: {PROJECT_ID}\n\n"
    )
    body = (
        "# Tikitaka Shorts Round 1 Review Packet\n\n"
        "Perform INDEPENDENT_REVIEW and REVISION_PROPOSAL only. "
        "Do not make a final adoption or production decision.\n\n"
    )
    source_lock_title, source_lock_path = _source_lock_path(root)
    body += _section(source_lock_title, _read_text(source_lock_path))
    for relative in ROUND1_REQUIRED_FILES:
        body += _section(relative, _read_text(root / relative))

    packet_with_placeholder = header + body
    sent_hash = canonical_packet_sha256(packet_with_placeholder)
    packet = packet_with_placeholder.replace(
        "sent_packet_sha256: __PENDING__",
        f"sent_packet_sha256: {sent_hash}",
        1,
    )
    packet_path = root / ROUND1_PACKET
    _write_text_atomic(packet_path, packet)

    return {
        "status": "READY",
        "review_round": 1,
        "review_cycle_id": cycle_id,
        "packet_id": resolved_packet_id,
        "sent_packet_sha256": sent_hash,
        "packet_sha256": sha256_file(packet_path),
        "packet_path": str(packet_path),
        "project_id": PROJECT_ID,
        "source_fingerprint_sha256": fingerprint,
    }


if __name__ == "__main__":
    raise SystemExit(main())
