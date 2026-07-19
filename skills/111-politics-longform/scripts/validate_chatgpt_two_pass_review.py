#!/usr/bin/env python3
"""Validate the politics-longform ChatGPT two-pass master review chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


GATE = "MASTER_COMMENTARY_REVIEW_GATE"
REQUIRED_FILES = (
    "round1_packet_sent.md",
    "round1_manifest.json",
    "round1_returned.md",
    "round1_receipt.json",
    "round1_codex_decisions.json",
    "round2_packet_sent.md",
    "round2_manifest.json",
    "round2_returned.md",
    "round2_receipt.json",
)
ALLOWED_DECISIONS = {
    "ADOPTED",
    "PARTIALLY_ADOPTED",
    "REJECTED",
    "PENDING_EVIDENCE",
}
ROUND2_REQUIRED_SECTIONS = {
    "round1_review",
    "decision_table",
    "revised_script",
    "revised_fact_map",
    "change_summary",
}
ROUND2_LEGACY_SECTIONS = {
    "round1_return_full",
    "codex_decisions_full",
    "revised_master_script_full",
    "revised_fact_map_full",
    "timeline_order_full",
    "core_question",
}
FORBIDDEN_EXTERNAL_APPROVAL = re.compile(
    r"(?im)^\s*(?:final_state|approval_status)\s*:\s*"
    r"(?:PASS|FINAL|ADOPTED)\s*$"
)
SUGGESTION_ID_PATTERN = re.compile(
    r"(?im)^\s*(?:suggestion_id\s*:\s*|제안\s+|#{2,4}\s+)"
    r"([A-Za-z]+\d+(?:-\d+)?)\s*$"
)
TEXT_HYGIENE_PATTERNS = (
    ("U+FFFD replacement character", re.compile("\ufffd")),
    ("isolated Hangul jamo", re.compile(r"[\u3131-\u318e]")),
    ("editor artifact", re.compile(r"<<|>>|<\s*[A-Za-z]\s*>", re.IGNORECASE)),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_json(path: Path, errors: list[dict[str, str]]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(
            {
                "code": "INVALID_JSON",
                "severity": "FAIL",
                "message": f"{path.name}: {exc}",
            }
        )
        return {}
    if not isinstance(payload, dict):
        errors.append(
            {
                "code": "INVALID_JSON",
                "severity": "FAIL",
                "message": f"{path.name}: top level must be an object",
            }
        )
        return {}
    return payload


def _add_error(
    errors: list[dict[str, str]],
    code: str,
    message: str,
    severity: str = "FAIL",
) -> None:
    errors.append({"code": code, "severity": severity, "message": message})


def _resolve(review_dir: Path, relative: Any) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        return None
    return (review_dir / relative).resolve()


def _verify_file_hash(
    review_dir: Path,
    payload: dict[str, Any],
    file_key: str,
    hash_key: str,
    label: str,
    errors: list[dict[str, str]],
) -> Path | None:
    path = _resolve(review_dir, payload.get(file_key))
    expected = payload.get(hash_key)
    if path is None or not isinstance(expected, str) or not expected:
        _add_error(
            errors,
            "MISSING_HASH_BINDING",
            f"{label}: {file_key} and {hash_key} are required",
        )
        return None
    if not path.is_file():
        _add_error(errors, "MISSING_ARTIFACT", f"{label}: missing {path}")
        return None
    actual = _sha256(path)
    if actual != expected.upper():
        _add_error(
            errors,
            "HASH_MISMATCH",
            f"{label}: expected {expected.upper()}, actual {actual}",
        )
    return path


def _clean_id_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) and item.strip() for item in value):
        return None
    return value


def _check_round_number(
    payload: dict[str, Any],
    expected: int,
    label: str,
    errors: list[dict[str, str]],
) -> None:
    if payload.get("review_round") != expected:
        _add_error(
            errors,
            "REVIEW_ROUND_MISMATCH",
            f"{label}: expected review_round={expected}",
        )


def _check_external_return(
    receipt: dict[str, Any],
    returned_path: Path | None,
    label: str,
    errors: list[dict[str, str]],
) -> None:
    if receipt.get("external_review_status") != "PENDING_CODEX_REVIEW":
        _add_error(
            errors,
            "FORBIDDEN_EXTERNAL_APPROVAL",
            f"{label}: external_review_status must be PENDING_CODEX_REVIEW",
        )
    if returned_path is None:
        return
    try:
        text = returned_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        _add_error(errors, "INVALID_RETURN_TEXT", f"{label}: {exc}")
        return
    if FORBIDDEN_EXTERNAL_APPROVAL.search(text):
        _add_error(
            errors,
            "FORBIDDEN_EXTERNAL_APPROVAL",
            f"{label}: external response claims final approval",
        )


def _check_text_hygiene(
    script_path: Path | None,
    errors: list[dict[str, str]],
) -> None:
    if script_path is None:
        return
    try:
        text = script_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        _add_error(errors, "FAIL_TEXT_HYGIENE", f"revised script: {exc}")
        return
    audience_text = "\n".join(
        line
        for line in text.splitlines()
        if not re.match(r"^\s*원문 근거(?:\s|\()", line)
    )
    findings = [
        label
        for label, pattern in TEXT_HYGIENE_PATTERNS
        if pattern.search(audience_text)
    ]
    if findings:
        _add_error(
            errors,
            "FAIL_TEXT_HYGIENE",
            "revised script contains audience-visible text corruption: "
            + ", ".join(findings),
        )


def _validate_human_readable_review(
    review_dir: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    """Validate the compact Markdown-first two-pass review contract."""
    errors: list[dict[str, str]] = []
    manifest = _load_json(manifest_path, errors)
    expected_schema = "politics-chatgpt-two-pass-human-readable-v1"
    if manifest.get("schema_version") != expected_schema:
        _add_error(
            errors,
            "INVALID_SCHEMA",
            f"review_manifest.json schema_version must be {expected_schema}",
        )

    bindings = (
        ("round1_returned_file", "round1_returned_sha256", "Round 1 return"),
        ("decisions_file", "decisions_sha256", "Codex decisions"),
        ("round2_returned_file", "round2_returned_sha256", "Round 2 return"),
        ("revised_script_file", "revised_script_sha256", "revised script"),
        ("revised_fact_map_file", "revised_fact_map_sha256", "revised fact map"),
        ("timeline_file", "timeline_sha256", "timeline"),
    )
    resolved: dict[str, Path | None] = {}
    for file_key, hash_key, label in bindings:
        resolved[file_key] = _verify_file_hash(
            review_dir,
            manifest,
            file_key,
            hash_key,
            label,
            errors,
        )
    if (
        manifest.get("round2_repair_returned_file") is not None
        or manifest.get("round2_repair_returned_sha256") is not None
    ):
        resolved["round2_repair_returned_file"] = _verify_file_hash(
            review_dir,
            manifest,
            "round2_repair_returned_file",
            "round2_repair_returned_sha256",
            "Round 2 repair return",
            errors,
        )

    conversation_id = manifest.get("conversation_id")
    if not isinstance(conversation_id, str) or not conversation_id.strip():
        _add_error(
            errors,
            "SAME_CONVERSATION_REQUIRED",
            "one nonblank ChatGPT conversation_id is required",
        )

    for key, label in (
        ("round1_returned_file", "Round 1 return"),
        ("round2_returned_file", "Round 2 return"),
        ("round2_repair_returned_file", "Round 2 repair return"),
    ):
        path = resolved.get(key)
        if path is not None:
            _check_external_return(
                {"external_review_status": "PENDING_CODEX_REVIEW"},
                path,
                label,
                errors,
            )

    script_path = resolved.get("revised_script_file")
    _check_text_hygiene(script_path, errors)
    ordered_segment_ids = _clean_id_list(manifest.get("ordered_segment_ids"))
    if ordered_segment_ids is None or not ordered_segment_ids:
        _add_error(
            errors,
            "SEGMENT_ORDER_DRIFT",
            "ordered_segment_ids must be a nonempty string list",
        )
        ordered_segment_ids = []
    elif len(ordered_segment_ids) != len(set(ordered_segment_ids)):
        _add_error(
            errors,
            "SEGMENT_ORDER_DRIFT",
            "ordered_segment_ids contains duplicates",
        )
    if script_path is not None:
        try:
            script_text = script_path.read_text(encoding="utf-8-sig")
            actual_order = re.findall(r"(?m)^##\s+([A-Za-z]+\d+)\.", script_text)
        except (OSError, UnicodeError) as exc:
            actual_order = []
            _add_error(errors, "INVALID_RETURN_TEXT", f"revised script: {exc}")
        if actual_order != ordered_segment_ids:
            _add_error(
                errors,
                "SEGMENT_ORDER_DRIFT",
                "revised script section order differs from ordered_segment_ids",
            )

    decisions_path = resolved.get("decisions_file")
    round1_path = resolved.get("round1_returned_file")
    decisions = _load_json(decisions_path, errors) if decisions_path else {}
    decision_rows = decisions.get("decisions")
    if not isinstance(decision_rows, list):
        _add_error(
            errors,
            "INCOMPLETE_CODEX_DECISIONS",
            "Codex decisions must be a list",
        )
        decision_rows = []
    decision_ids: list[str] = []
    for index, row in enumerate(decision_rows):
        if not isinstance(row, dict):
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                f"decision row {index} must be an object",
            )
            continue
        suggestion_id = row.get("suggestion_id")
        decision = row.get("decision")
        reason = row.get("decision_reason")
        if not isinstance(suggestion_id, str) or not suggestion_id.strip():
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                f"decision row {index} has no suggestion_id",
            )
            continue
        decision_ids.append(suggestion_id)
        if decision not in ALLOWED_DECISIONS:
            _add_error(
                errors,
                "INVALID_CODEX_DECISION",
                f"{suggestion_id}: invalid decision {decision!r}",
            )
        if not isinstance(reason, str) or not reason.strip():
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                f"{suggestion_id}: decision_reason is required",
            )
        if decision == "PENDING_EVIDENCE":
            _add_error(
                errors,
                "PENDING_EVIDENCE",
                f"{suggestion_id}: evidence is still pending",
                severity="WAIT",
            )
    if len(decision_ids) != len(set(decision_ids)):
        _add_error(
            errors,
            "INCOMPLETE_CODEX_DECISIONS",
            "Codex decision suggestion IDs must be unique",
        )
    if round1_path is not None:
        try:
            suggestion_ids = SUGGESTION_ID_PATTERN.findall(
                round1_path.read_text(encoding="utf-8-sig")
            )
        except (OSError, UnicodeError) as exc:
            suggestion_ids = []
            _add_error(errors, "INVALID_RETURN_TEXT", f"Round 1 return: {exc}")
        if suggestion_ids != decision_ids:
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                "Round 1 suggestions and Codex decisions must be exactly one-to-one",
            )

    blockers = manifest.get("remaining_blockers")
    if not isinstance(blockers, list):
        _add_error(
            errors,
            "INVALID_ROUND2_BLOCKERS",
            "remaining_blockers must be a list",
        )
        blockers = ["invalid"]
    if (
        manifest.get("recommendation") != "PASS_RECOMMENDED"
        or manifest.get("flow_continuity_status") != "PASS"
        or manifest.get("text_hygiene_status") != "PASS"
        or bool(blockers)
    ):
        _add_error(
            errors,
            "WAIT_CHATGPT_REVIEW_REPAIR",
            "Round 2 recommendation, flow, text hygiene, or blockers require repair",
            severity="WAIT",
        )

    fail_count = sum(item["severity"] == "FAIL" for item in errors)
    wait_count = sum(item["severity"] == "WAIT" for item in errors)
    status = "FAIL" if fail_count else "WAIT" if wait_count else "PASS"
    return {
        "gate": GATE,
        "status": status,
        "stop_code": None if status == "PASS" else "WAIT_CHATGPT_REVIEW_REPAIR",
        "review_dir": str(review_dir),
        "contract": expected_schema,
        "conversation_id": conversation_id if status == "PASS" else None,
        "ordered_segment_ids": ordered_segment_ids if status == "PASS" else [],
        "errors": errors,
    }


def validate_review(review_dir: Path | str) -> dict[str, Any]:
    review_dir = Path(review_dir).resolve()
    errors: list[dict[str, str]] = []

    if not review_dir.is_dir():
        _add_error(errors, "MISSING_REVIEW_DIR", f"missing review dir: {review_dir}")
        return {
            "gate": GATE,
            "status": "FAIL",
            "stop_code": "WAIT_CHATGPT_REVIEW_REPAIR",
            "review_dir": str(review_dir),
            "errors": errors,
        }

    compact_manifest = review_dir / "review_manifest.json"
    if compact_manifest.is_file():
        return _validate_human_readable_review(review_dir, compact_manifest)

    missing = [name for name in REQUIRED_FILES if not (review_dir / name).is_file()]
    for name in missing:
        _add_error(errors, "MISSING_ARTIFACT", f"missing {name}")
    if missing:
        return {
            "gate": GATE,
            "status": "FAIL",
            "stop_code": "WAIT_CHATGPT_REVIEW_REPAIR",
            "review_dir": str(review_dir),
            "errors": errors,
        }

    round1_manifest = _load_json(review_dir / "round1_manifest.json", errors)
    round1_receipt = _load_json(review_dir / "round1_receipt.json", errors)
    decisions = _load_json(review_dir / "round1_codex_decisions.json", errors)
    round2_manifest = _load_json(review_dir / "round2_manifest.json", errors)
    round2_receipt = _load_json(review_dir / "round2_receipt.json", errors)

    _check_round_number(round1_manifest, 1, "round1_manifest", errors)
    _check_round_number(round1_receipt, 1, "round1_receipt", errors)
    _check_round_number(round2_manifest, 2, "round2_manifest", errors)
    _check_round_number(round2_receipt, 2, "round2_receipt", errors)

    if round1_manifest.get("packet_id") != round1_receipt.get("packet_id"):
        _add_error(errors, "PACKET_ID_MISMATCH", "Round 1 packet_id mismatch")
    if round2_manifest.get("packet_id") != round2_receipt.get("packet_id"):
        _add_error(errors, "PACKET_ID_MISMATCH", "Round 2 packet_id mismatch")

    _verify_file_hash(
        review_dir,
        round1_manifest,
        "sent_file",
        "sent_sha256",
        "Round 1 sent packet",
        errors,
    )
    round1_returned = _verify_file_hash(
        review_dir,
        round1_receipt,
        "returned_file",
        "returned_sha256",
        "Round 1 returned response",
        errors,
    )
    _check_external_return(
        round1_receipt, round1_returned, "Round 1 returned response", errors
    )

    _verify_file_hash(
        review_dir,
        round2_manifest,
        "sent_file",
        "sent_sha256",
        "Round 2 sent packet",
        errors,
    )
    revised_script = _verify_file_hash(
        review_dir,
        round2_manifest,
        "revised_script_file",
        "revised_script_sha256",
        "Round 2 revised script",
        errors,
    )
    _check_text_hygiene(revised_script, errors)
    for file_key, hash_key, label in (
        ("revised_fact_map_file", "revised_fact_map_sha256", "Round 2 fact map"),
        ("timeline_file", "timeline_sha256", "Round 2 timeline"),
    ):
        _verify_file_hash(
            review_dir, round2_manifest, file_key, hash_key, label, errors
        )
    round2_returned = _verify_file_hash(
        review_dir,
        round2_receipt,
        "returned_file",
        "returned_sha256",
        "Round 2 returned response",
        errors,
    )
    _check_external_return(
        round2_receipt, round2_returned, "Round 2 returned response", errors
    )

    conversation_ids = (
        round1_receipt.get("conversation_id"),
        round2_manifest.get("conversation_id"),
        round2_receipt.get("conversation_id"),
    )
    if (
        not all(isinstance(item, str) and item.strip() for item in conversation_ids)
        or len(set(conversation_ids)) != 1
    ):
        _add_error(
            errors,
            "SAME_CONVERSATION_REQUIRED",
            "Round 1 receipt, Round 2 manifest, and Round 2 receipt "
            "must use one conversation_id",
        )

    round1_return_hash = _sha256(review_dir / "round1_returned.md")
    if round2_manifest.get("round1_return_sha256", "").upper() != round1_return_hash:
        _add_error(
            errors,
            "HASH_MISMATCH",
            "Round 2 parent Round 1 return hash mismatch",
        )
    if decisions.get("round1_return_sha256", "").upper() != round1_return_hash:
        _add_error(
            errors,
            "HASH_MISMATCH",
            "Codex decisions are not bound to the Round 1 return",
        )

    decisions_hash = _sha256(review_dir / "round1_codex_decisions.json")
    if round2_manifest.get("round1_decisions_sha256", "").upper() != decisions_hash:
        _add_error(
            errors,
            "HASH_MISMATCH",
            "Round 2 parent Codex decisions hash mismatch",
        )

    suggestion_ids = _clean_id_list(round1_receipt.get("suggestion_ids"))
    decision_rows = decisions.get("decisions")
    if suggestion_ids is None or len(suggestion_ids) != len(set(suggestion_ids)):
        _add_error(
            errors,
            "INVALID_SUGGESTION_IDS",
            "Round 1 suggestion_ids must be a unique nonempty string list",
        )
        suggestion_ids = []
    if round1_returned is not None:
        try:
            returned_text = round1_returned.read_text(encoding="utf-8-sig")
            returned_suggestion_ids = SUGGESTION_ID_PATTERN.findall(returned_text)
        except (OSError, UnicodeError) as exc:
            returned_suggestion_ids = []
            _add_error(errors, "INVALID_RETURN_TEXT", f"Round 1: {exc}")
        if returned_suggestion_ids != suggestion_ids:
            _add_error(
                errors,
                "SUGGESTION_ID_MISMATCH",
                "Round 1 receipt suggestion_ids must exactly match the returned response",
            )
    if not isinstance(decision_rows, list):
        _add_error(
            errors,
            "INCOMPLETE_CODEX_DECISIONS",
            "Codex decisions must be a list",
        )
        decision_rows = []

    decision_ids: list[str] = []
    for index, row in enumerate(decision_rows):
        if not isinstance(row, dict):
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                f"decision row {index} must be an object",
            )
            continue
        suggestion_id = row.get("suggestion_id")
        decision = row.get("decision")
        reason = row.get("decision_reason")
        if not isinstance(suggestion_id, str) or not suggestion_id:
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                f"decision row {index} has no suggestion_id",
            )
            continue
        decision_ids.append(suggestion_id)
        if decision not in ALLOWED_DECISIONS:
            _add_error(
                errors,
                "INVALID_CODEX_DECISION",
                f"{suggestion_id}: invalid decision {decision!r}",
            )
        if not isinstance(reason, str) or not reason.strip():
            _add_error(
                errors,
                "INCOMPLETE_CODEX_DECISIONS",
                f"{suggestion_id}: decision_reason is required",
            )
        if decision == "PENDING_EVIDENCE":
            _add_error(
                errors,
                "PENDING_EVIDENCE",
                f"{suggestion_id}: evidence is still pending",
                severity="WAIT",
            )

    if (
        len(decision_ids) != len(set(decision_ids))
        or set(decision_ids) != set(suggestion_ids)
    ):
        _add_error(
            errors,
            "INCOMPLETE_CODEX_DECISIONS",
            "Round 1 suggestions and Codex decisions must be exactly one-to-one",
        )

    included_sections = round2_manifest.get("included_sections")
    included_set = set(included_sections) if isinstance(included_sections, list) else set()
    has_current_sections = ROUND2_REQUIRED_SECTIONS.issubset(included_set)
    has_legacy_sections = ROUND2_LEGACY_SECTIONS.issubset(included_set)
    if not (has_current_sections or has_legacy_sections):
        _add_error(
            errors,
            "ROUND2_PACKET_INCOMPLETE",
            "Round 2 manifest does not include the current human-readable "
            "bundles or the complete legacy self-contained bundle",
        )

    order_values = (
        _clean_id_list(round1_manifest.get("ordered_segment_ids")),
        _clean_id_list(round2_manifest.get("ordered_segment_ids")),
        _clean_id_list(round2_receipt.get("ordered_segment_ids")),
    )
    if (
        any(value is None or not value for value in order_values)
        or not (order_values[0] == order_values[1] == order_values[2])
    ):
        _add_error(
            errors,
            "SEGMENT_ORDER_DRIFT",
            "Round 1, Round 2 packet, and Round 2 return segment order must match",
        )

    recommendation = round2_receipt.get("recommendation")
    flow_status = round2_receipt.get("flow_continuity_status")
    text_hygiene_status = round2_receipt.get("text_hygiene_status")
    if text_hygiene_status is None:
        text_hygiene_status = (
            "FAIL"
            if any(item.get("code") == "FAIL_TEXT_HYGIENE" for item in errors)
            else "PASS"
        )
    blockers = round2_receipt.get("remaining_blockers")
    if recommendation not in {
        "PASS_RECOMMENDED",
        "REVISE_REQUIRED",
        "EVIDENCE_REQUIRED",
    }:
        _add_error(
            errors,
            "INVALID_ROUND2_RECOMMENDATION",
            f"invalid recommendation: {recommendation!r}",
        )
    if not isinstance(blockers, list):
        _add_error(
            errors,
            "INVALID_ROUND2_BLOCKERS",
            "remaining_blockers must be a list",
        )
        blockers = ["invalid"]
    if text_hygiene_status != "PASS":
        _add_error(
            errors,
            "WAIT_TEXT_HYGIENE_REPAIR",
            "Round 2 text hygiene audit must pass before the review gate",
            severity="WAIT",
        )
    if (
        recommendation != "PASS_RECOMMENDED"
        or flow_status != "PASS"
        or text_hygiene_status != "PASS"
        or bool(blockers)
    ):
        _add_error(
            errors,
            "WAIT_CHATGPT_REVIEW_REPAIR",
            "Round 2 requested revision/evidence, flow failed, or blockers remain",
            severity="WAIT",
        )

    fail_count = sum(item["severity"] == "FAIL" for item in errors)
    wait_count = sum(item["severity"] == "WAIT" for item in errors)
    status = "FAIL" if fail_count else "WAIT" if wait_count else "PASS"
    return {
        "gate": GATE,
        "status": status,
        "stop_code": None if status == "PASS" else "WAIT_CHATGPT_REVIEW_REPAIR",
        "review_dir": str(review_dir),
        "conversation_id": conversation_ids[0]
        if status == "PASS" and conversation_ids
        else None,
        "ordered_segment_ids": order_values[0]
        if status == "PASS" and order_values
        else [],
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the politics-longform ChatGPT two-pass review chain."
    )
    parser.add_argument("--review-dir", required=True, type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Gate JSON path. Defaults to master_commentary_review_gate.json.",
    )
    args = parser.parse_args(argv)

    result = validate_review(args.review_dir)
    output = args.output or (
        args.review_dir.resolve() / "master_commentary_review_gate.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
