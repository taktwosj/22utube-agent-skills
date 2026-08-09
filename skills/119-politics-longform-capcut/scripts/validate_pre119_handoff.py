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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


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

    required = {
        "episode_id": handoff.get("episode_id"),
        "project_name": handoff.get("project_name"),
        "central_question": handoff.get("central_question"),
        "selected_thesis": handoff.get("selected_thesis"),
        "chapter_order": handoff.get("chapter_order"),
        "between_image": handoff.get("between_image"),
        "between_narration": handoff.get("between_narration"),
        "lower_mode": handoff.get("lower_mode"),
    }
    if any(value in (None, "", []) for value in required.values()):
        write_report(package_root, blocked_report("WAIT_PRE119_PLAN_FIELDS_REQUIRED", markers))
        return 2
    if required["lower_mode"] not in {"SRT", "COMMENTARY_2LINE", "NONE"}:
        write_report(package_root, blocked_report("FAIL_PRE119_LOWER_MODE", markers))
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
        "next": "Run A and D plus requested B/C, then compile cards from actual asset evidence.",
    }
    write_report(package_root, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
