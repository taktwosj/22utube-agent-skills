#!/usr/bin/env python3
"""Validate PRE-119 routing and bind editorial approval to external evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


HANDOFF_PATH = Path("20_script/pre119_handoff.json")
SCRIPT_PATH = Path("20_script/119_final_script.md")
REPORT_PATH = Path("90_reports/pre119_handoff_validation.json")
STRONG_TEXT_MARKERS = {
    "togun-pre119-handoff-v3",
    "TOGUN_PRE119_TO_119_DIRECT",
    "EDITORIAL_OWNER=TOGUN_PRE119",
    "TOGUN_PRE119",
    "PRE119_SOURCE_CANDIDATE",
}
AUXILIARY_PATHS = (
    Path("20_script/119_final_script.md"),
    Path("10_analysis/pre119_editorial_packet.md"),
    Path("00_source/source_packet.md"),
    Path("90_reports/source_gap_and_status.md"),
    Path("00_README.md"),
)
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
SEED_MARKER = "[ASSEMBLY_ONLY_SEED]"
CARD_MARKER = "[CARD]"
SEED_ASSIGNMENT_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*(?:=|:)\s*(.*)$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def assembly_seed_sha256(seed: dict[str, Any]) -> str:
    canonical = json.dumps(seed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def _seed_value(text: str) -> Any:
    if not text:
        return ""
    if text[0] in '[{"' or text in {"true", "false", "null"}:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return text


def _store_seed_assignment(target: dict[str, Any], line: str, line_number: int) -> None:
    match = SEED_ASSIGNMENT_RE.fullmatch(line)
    if match is None:
        raise ValueError(f"LINE_{line_number}_ASSIGNMENT_REQUIRED")
    key = match.group(1).lower()
    if key in target:
        raise ValueError(f"LINE_{line_number}_DUPLICATE_FIELD:{key}")
    target[key] = _seed_value(match.group(2).strip())


def parse_assembly_only_seed(script_path: Path) -> dict[str, Any]:
    lines = script_path.read_text(encoding="utf-8").splitlines()
    marker_lines = [index for index, line in enumerate(lines) if line.strip() == SEED_MARKER]
    if not marker_lines:
        raise ValueError("ASSEMBLY_ONLY_SEED_REQUIRED")
    if len(marker_lines) != 1:
        raise ValueError("ASSEMBLY_ONLY_SEED_DUPLICATE")

    policy: dict[str, Any] = {}
    cards: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    closed = False
    for index in range(marker_lines[0] + 1, len(lines)):
        line_number = index + 1
        line = lines[index].strip()
        if not line or line in {"```", "```text"}:
            continue
        if line == "[/ASSEMBLY_ONLY_SEED]":
            closed = True
            break
        if line == CARD_MARKER:
            current = {}
            cards.append(current)
            continue
        if line == "[/CARD]":
            if current is None:
                raise ValueError(f"LINE_{line_number}_CARD_CLOSE_WITHOUT_CARD")
            current = None
            continue
        _store_seed_assignment(policy if current is None else current, line, line_number)

    if not cards:
        raise ValueError("ASSEMBLY_ONLY_SEED_CARDS_REQUIRED")
    if closed and any(line.strip() == SEED_MARKER for line in lines[index + 1 :]):
        raise ValueError("ASSEMBLY_ONLY_SEED_DUPLICATE")
    if str(policy.get("execution_mode", "")).strip().upper() != "ASSEMBLY_ONLY":
        raise ValueError("ASSEMBLY_ONLY_SEED_EXECUTION_MODE_INVALID")

    card_order: list[str] = []
    for position, card in enumerate(cards, start=1):
        card_id = str(card.get("card_id", "")).strip()
        card_type = str(card.get("card_type", "")).strip()
        if not card_id:
            raise ValueError(f"CARD_{position}_ID_REQUIRED")
        if not card_type:
            raise ValueError(f"CARD_{position}_TYPE_REQUIRED:{card_id}")
        if card_id in card_order:
            raise ValueError(f"CARD_ID_DUPLICATE:{card_id}")
        card["card_id"] = card_id
        card["card_type"] = card_type
        if card_type != "INTRO":
            chapter_title = card.get("chapter_title")
            chapter_label = card.get("chapter_label")
            if not isinstance(chapter_title, str) or not chapter_title.strip():
                raise ValueError(f"CARD_{position}_CHAPTER_TITLE_REQUIRED:{card_id}")
            if not isinstance(chapter_label, str) or not chapter_label.strip():
                raise ValueError(f"CARD_{position}_CHAPTER_LABEL_REQUIRED:{card_id}")
            card["chapter_title"] = chapter_title.strip()
            card["chapter_label"] = chapter_label.strip()
        card_order.append(card_id)
    return {"policy": policy, "card_order": card_order, "cards": cards}


def write_report(package_root: Path, payload: dict[str, Any]) -> None:
    path = package_root / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_handoff(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("handoff must be an object")
    return value


def _marker_text(package_root: Path, handoff: dict[str, Any] | None) -> str:
    values: list[str] = []
    if handoff is not None:
        values.append(json.dumps(handoff, ensure_ascii=False))
    for relative in AUXILIARY_PATHS:
        path = package_root / relative
        if path.is_file():
            try:
                values.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    return "\n".join(values)


def detect_route(package_root: Path, handoff: dict[str, Any] | None) -> tuple[str, list[str]]:
    strong: list[str] = []
    if (package_root / HANDOFF_PATH).is_file():
        strong.append(HANDOFF_PATH.as_posix())
    marker_text = _marker_text(package_root, handoff)
    strong.extend(sorted(marker for marker in STRONG_TEXT_MARKERS if marker in marker_text))
    auxiliary = [relative.as_posix() for relative in AUXILIARY_PATHS if (package_root / relative).is_file()]
    if strong or len(auxiliary) >= 2:
        return "PRE119", strong + auxiliary
    return "DIRECT_SCRIPT", auxiliary


def _unsafe_path_fields(value: Any, prefix: str = "") -> list[str]:
    unsafe: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            if "path" in str(key).lower() and isinstance(child, str):
                normalized = child.replace("\\", "/")
                posix = PurePosixPath(normalized)
                windows = PureWindowsPath(child)
                if (
                    not child.strip()
                    or posix.is_absolute()
                    or windows.is_absolute()
                    or ".." in posix.parts
                    or re.match(r"^[A-Za-z]:", normalized)
                ):
                    unsafe.append(child_prefix)
            unsafe.extend(_unsafe_path_fields(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            unsafe.extend(_unsafe_path_fields(child, f"{prefix}[{index}]"))
    return unsafe


def _required_text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(code)
    return value.strip()


def validate_publication_report(value: Any) -> dict[str, Any]:
    """Validate editorial metadata that 119 copies into the delivery report."""
    if not isinstance(value, dict):
        raise ValueError("PUBLICATION_REPORT_REQUIRED")
    title = _required_text(value.get("title"), "PUBLICATION_TITLE_REQUIRED")
    content = value.get("content")
    if not isinstance(content, dict):
        raise ValueError("PUBLICATION_CONTENT_REQUIRED")
    summary = _required_text(content.get("simple_summary"), "PUBLICATION_SIMPLE_SUMMARY_REQUIRED")

    timeline_raw = content.get("timeline")
    if not isinstance(timeline_raw, list) or not timeline_raw:
        raise ValueError("PUBLICATION_TIMELINE_REQUIRED")
    timeline: list[dict[str, str]] = []
    for index, item in enumerate(timeline_raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"PUBLICATION_TIMELINE_ITEM_INVALID:{index}")
        at = _required_text(item.get("at"), f"PUBLICATION_TIMELINE_AT_REQUIRED:{index}")
        label = _required_text(item.get("label"), f"PUBLICATION_TIMELINE_LABEL_REQUIRED:{index}")
        if re.fullmatch(r"(?:\d{2}:)?[0-5]\d:[0-5]\d", at) is None:
            raise ValueError(f"PUBLICATION_TIMELINE_AT_INVALID:{index}")
        timeline.append({"at": at, "label": label})

    sources_raw = content.get("sources")
    if not isinstance(sources_raw, list) or not sources_raw:
        raise ValueError("PUBLICATION_SOURCES_REQUIRED")
    sources: list[dict[str, str | None]] = []
    for index, item in enumerate(sources_raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"PUBLICATION_SOURCE_ITEM_INVALID:{index}")
        label = _required_text(item.get("label"), f"PUBLICATION_SOURCE_LABEL_REQUIRED:{index}")
        url = item.get("url")
        if url is not None and not isinstance(url, str):
            raise ValueError(f"PUBLICATION_SOURCE_URL_INVALID:{index}")
        sources.append({"label": label, "url": url.strip() if isinstance(url, str) and url.strip() else None})

    thumbnail = value.get("thumbnail")
    if not isinstance(thumbnail, dict):
        raise ValueError("THUMBNAIL_COPY_REQUIRED")
    words_raw = thumbnail.get("words")
    if not isinstance(words_raw, list) or len(words_raw) != 3:
        raise ValueError("THUMBNAIL_WORDS_EXACTLY_3_REQUIRED")
    words: list[str] = []
    for index, word in enumerate(words_raw, start=1):
        text = _required_text(word, f"THUMBNAIL_WORD_REQUIRED:{index}")
        if any(character.isspace() for character in text) or len(text) > 5:
            raise ValueError(f"THUMBNAIL_WORD_MAX_5_REQUIRED:{index}")
        words.append(text)
    sentences_raw = thumbnail.get("sentences")
    if not isinstance(sentences_raw, list) or len(sentences_raw) != 3:
        raise ValueError("THUMBNAIL_SENTENCES_EXACTLY_3_REQUIRED")
    sentences = [
        _required_text(sentence, f"THUMBNAIL_SENTENCE_REQUIRED:{index}")
        for index, sentence in enumerate(sentences_raw, start=1)
    ]
    return {
        "title": title,
        "content": {"simple_summary": summary, "timeline": timeline, "sources": sources},
        "thumbnail": {"words": words, "sentences": sentences},
    }


def blocked_report(status: str, markers: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "schema": "politics-pre119-handoff-validation.v1",
        "status": status,
        "route": "PRE119",
        "markers": markers,
        **extra,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--approved-script-sha256", default="")
    parser.add_argument("--approval-evidence", default="")
    args = parser.parse_args()
    package_root = args.package_root.resolve()

    handoff_path = package_root / HANDOFF_PATH
    handoff: dict[str, Any] | None = None
    if handoff_path.is_file():
        try:
            handoff = load_handoff(handoff_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            write_report(package_root, blocked_report("FAIL_PRE119_HANDOFF_JSON", [HANDOFF_PATH.as_posix()]))
            return 2

    route, markers = detect_route(package_root, handoff)
    if route == "DIRECT_SCRIPT":
        write_report(
            package_root,
            {
                "schema": "politics-pre119-handoff-validation.v1",
                "status": "NOT_PRE119",
                "route": "DIRECT_SCRIPT",
                "markers": markers,
            },
        )
        return 0
    if handoff is None:
        write_report(package_root, blocked_report("WAIT_PRE119_HANDOFF_REQUIRED", markers))
        return 2

    unsafe = _unsafe_path_fields(handoff)
    if unsafe:
        write_report(package_root, blocked_report("FAIL_PACKET_PATH_UNSAFE", markers, unsafe_path_fields=unsafe))
        return 2

    editorial_owner = handoff.get("editorial_owner", handoff.get("EDITORIAL_OWNER"))
    source_state = handoff.get("source_state", handoff.get("PRE119_SOURCE_STATE"))
    if (
        handoff.get("schema") != "togun-pre119-handoff-v3"
        or handoff.get("route") != "TOGUN_PRE119_TO_119_DIRECT"
        or editorial_owner != "TOGUN_PRE119"
        or source_state != "PRE119_SOURCE_CANDIDATE"
    ):
        write_report(package_root, blocked_report("FAIL_PRE119_HANDOFF_IDENTITY", markers))
        return 2

    approved_sha = args.approved_script_sha256.strip().upper()
    approval_evidence = args.approval_evidence.strip()
    if not approved_sha or not approval_evidence:
        write_report(package_root, blocked_report("WAIT_EXTERNAL_APPROVAL_REQUIRED", markers))
        return 2
    if not SHA256_RE.fullmatch(approved_sha) or not approval_evidence.startswith(("user_message:", "runtime_approval:")):
        write_report(package_root, blocked_report("FAIL_EXTERNAL_APPROVAL_EVIDENCE", markers))
        return 2

    script_path = package_root / SCRIPT_PATH
    if not script_path.is_file():
        write_report(package_root, blocked_report("WAIT_FINAL_SCRIPT_REQUIRED", markers))
        return 2
    actual_sha = sha256(script_path)
    script_lock = handoff.get("script_lock")
    packet_sha = "" if not isinstance(script_lock, dict) else str(script_lock.get("current_final_script_sha256", "")).strip().upper()
    lock_report = {
        "actual_final_script_sha256": actual_sha,
        "packet_current_final_script_sha256": packet_sha,
        "external_approved_script_sha256": approved_sha,
    }
    if not SHA256_RE.fullmatch(packet_sha) or len({actual_sha, packet_sha, approved_sha}) != 1:
        write_report(package_root, blocked_report("WAIT_APPROVAL_HASH_MISMATCH", markers, script_lock=lock_report))
        return 2

    try:
        assembly_seed = parse_assembly_only_seed(script_path)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        detail = str(error)
        status = (
            "FAIL_PRE119_ASSEMBLY_SEED_REQUIRED"
            if detail == "ASSEMBLY_ONLY_SEED_REQUIRED"
            else "FAIL_PRE119_ASSEMBLY_SEED_INVALID"
        )
        write_report(
            package_root,
            blocked_report(status, markers, script_lock=lock_report, seed_error=detail),
        )
        return 2

    minimal_edit_plan = handoff.get("minimal_edit_plan")
    if not isinstance(minimal_edit_plan, dict):
        minimal_edit_plan = {}
    required = {
        "episode_id": handoff.get("episode_id"),
        "project_name": handoff.get("project_name"),
        "central_question": handoff.get("central_question"),
        "selected_thesis": handoff.get("selected_thesis"),
        "chapter_order": handoff.get("chapter_order"),
        "between_image": handoff.get("between_image"),
        "between_narration": handoff.get("between_narration"),
        "lower_mode": handoff.get("lower_mode"),
        "execution_mode": handoff.get("execution_mode", "ASSEMBLY_ONLY"),
        "cta_like_subscribe": handoff.get(
            "cta_like_subscribe", minimal_edit_plan.get("cta_like_subscribe", "ON")
        ),
    }
    if any(value in (None, "", []) for value in required.values()):
        write_report(package_root, blocked_report("WAIT_PRE119_PLAN_FIELDS_REQUIRED", markers))
        return 2
    if required["lower_mode"] not in {"SRT", "COMMENTARY_2LINE", "NONE", "MIXED"}:
        write_report(package_root, blocked_report("FAIL_PRE119_LOWER_MODE", markers))
        return 2
    if required["execution_mode"] != "ASSEMBLY_ONLY":
        write_report(package_root, blocked_report("FAIL_PRE119_EXECUTION_MODE", markers))
        return 2
    if str(required["cta_like_subscribe"]).strip().upper() not in {"ON", "OFF"}:
        write_report(package_root, blocked_report("FAIL_PRE119_CTA_POLICY", markers))
        return 2
    required["cta_like_subscribe"] = str(required["cta_like_subscribe"]).strip().upper()
    try:
        required["publication_report"] = validate_publication_report(handoff.get("publication_report"))
    except ValueError as error:
        detail = str(error)
        status = "WAIT_PRE119_PUBLICATION_REPORT_REQUIRED" if detail == "PUBLICATION_REPORT_REQUIRED" else "FAIL_PRE119_PUBLICATION_REPORT_INVALID"
        write_report(package_root, blocked_report(status, markers, publication_report_error=detail))
        return 2

    seed_policy = assembly_seed["policy"]
    policy_mismatches = [
        key
        for key in (
            "episode_id",
            "project_name",
            "central_question",
            "selected_thesis",
            "chapter_order",
            "between_image",
            "between_narration",
            "lower_mode",
            "execution_mode",
            "cta_like_subscribe",
        )
        if key in seed_policy and seed_policy[key] != required[key]
    ]
    if policy_mismatches:
        write_report(
            package_root,
            blocked_report(
                "FAIL_PRE119_SEED_POLICY_MISMATCH",
                markers,
                script_lock=lock_report,
                seed_policy_mismatches=policy_mismatches,
            ),
        )
        return 2

    report = {
        "schema": "politics-pre119-handoff-validation.v1",
        "status": "PASS",
        "route": "PRE119",
        "markers": markers,
        "handoff_path": HANDOFF_PATH.as_posix(),
        "handoff_sha256": sha256(handoff_path),
        "approval_evidence": approval_evidence,
        "script_lock": lock_report,
        "validated_plan": required,
        "assembly_only_seed": assembly_seed,
        "assembly_only_seed_sha256": assembly_seed_sha256(assembly_seed),
        "next": "Run A and D plus requested B/C, then compile cards from actual asset evidence.",
    }
    write_report(package_root, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
