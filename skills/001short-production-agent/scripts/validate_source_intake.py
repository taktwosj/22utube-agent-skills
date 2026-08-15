#!/usr/bin/env python3
"""Validate a local 001 source-intake receipt without any network action."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from common import sha256_file


ALLOWED_KINDS = {"GOOGLE_DRIVE", "URL", "DESKTOP"}
RECEIPT_VERSIONS = {
    "001short-source-intake-receipt-v1",
    "001short-source-intake-receipt-v2",
}
ORIGINAL_ANALYSIS_CONTRACT_VERSION = "001short-original-source-transcript-v1"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def _declared_file(base: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else base / candidate


def _locator_source_id(kind: str, locator: Any) -> str | None:
    if not isinstance(locator, str) or not locator.strip():
        return None
    if kind == "GOOGLE_DRIVE":
        parsed = urlparse(locator)
        if not parsed.scheme:
            return locator.strip() if "/" not in locator and "\\" not in locator else None
        if parsed.scheme not in {"http", "https"} or parsed.netloc not in {"drive.google.com", "www.drive.google.com"}:
            return None
        match = re.search(r"/(?:d|folders)/([^/?#]+)", parsed.path)
        return match.group(1) if match else parse_qs(parsed.query).get("id", [None])[0]
    if kind == "URL":
        parsed = urlparse(locator)
        if parsed.scheme not in {"http", "https"} or parsed.netloc not in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
            return None
        return parse_qs(parsed.query).get("v", [None])[0] or next((part for part in reversed(parsed.path.split("/")) if part), None)
    return str(Path(locator).resolve()) if Path(locator).is_absolute() else None


def _probe_duration_us(path: Path) -> int | None:
    try:
        completed = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True, check=False)
        duration = float(completed.stdout.strip()) if completed.returncode == 0 else 0
        return round(duration * 1_000_000) if duration > 0 else None
    except (OSError, ValueError):
        return None


def validate_receipt(receipt_path: Path) -> list[str]:
    path = Path(receipt_path).resolve()
    try:
        receipt = _load(path)
    except Exception as exc:
        return [f"INTAKE_RECEIPT_READ:{exc}"]
    errors: list[str] = []
    receipt_version = receipt.get("schema_version")
    if receipt_version not in RECEIPT_VERSIONS:
        errors.append("INTAKE_RECEIPT_SCHEMA_VERSION_INVALID")
    if receipt_version == "001short-source-intake-receipt-v2":
        if receipt.get("original_analysis_contract_version") != ORIGINAL_ANALYSIS_CONTRACT_VERSION:
            errors.append("INTAKE_RECEIPT_ORIGINAL_ANALYSIS_CONTRACT_REQUIRED")
    elif receipt.get("original_analysis_contract_version") is not None:
        errors.append("INTAKE_RECEIPT_ORIGINAL_ANALYSIS_CONTRACT_VERSION_INVALID")
    for field in ("episode_id", "source_id", "source_locator", "local_media_path", "local_media_sha256", "source_identity_path", "source_identity_sha256"):
        if not isinstance(receipt.get(field), str) or not receipt[field].strip():
            errors.append(f"INTAKE_RECEIPT_FIELD_REQUIRED:{field}")
    if not isinstance(receipt.get("local_media_duration_us"), int) or isinstance(receipt.get("local_media_duration_us"), bool) or receipt["local_media_duration_us"] <= 0:
        errors.append("INTAKE_RECEIPT_FIELD_REQUIRED:local_media_duration_us")
    kind = receipt.get("intake_kind")
    if kind not in ALLOWED_KINDS:
        errors.append("INTAKE_RECEIPT_KIND_INVALID")
    else:
        locator_id = _locator_source_id(kind, receipt.get("source_locator"))
        if locator_id is None:
            errors.append("INTAKE_RECEIPT_LOCATOR_INVALID")
        elif kind != "DESKTOP" and locator_id != receipt.get("source_id"):
            errors.append("INTAKE_RECEIPT_LOCATOR_SOURCE_ID_MISMATCH")

    raw_media_path = receipt.get("local_media_path")
    if not isinstance(raw_media_path, str) or Path(raw_media_path).is_absolute() or ".." in Path(raw_media_path).parts:
        errors.append("INTAKE_RECEIPT_MEDIA_PATH_INVALID")
    media = _declared_file(path.parent, raw_media_path)
    if media is None or not media.is_file():
        errors.append("INTAKE_RECEIPT_MEDIA_MISSING")
    elif sha256_file(media).lower() != str(receipt.get("local_media_sha256", "")).lower():
        errors.append("INTAKE_RECEIPT_MEDIA_SHA_MISMATCH")
    else:
        measured = _probe_duration_us(media)
        declared = receipt.get("local_media_duration_us")
        if not isinstance(declared, int) or isinstance(declared, bool) or declared <= 0:
            errors.append("INTAKE_RECEIPT_MEDIA_DURATION_INVALID")
        elif measured is None or abs(declared - measured) > 100_000:
            errors.append("INTAKE_RECEIPT_MEDIA_DURATION_MISMATCH")

    identity_path = _declared_file(path.parent, receipt.get("source_identity_path"))
    if identity_path is None or not identity_path.is_file():
        errors.append("INTAKE_RECEIPT_IDENTITY_MISSING")
        return errors
    if sha256_file(identity_path).lower() != str(receipt.get("source_identity_sha256", "")).lower():
        errors.append("INTAKE_RECEIPT_IDENTITY_SHA_MISMATCH")
    try:
        identity = _load(identity_path)
    except Exception as exc:
        return errors + [f"INTAKE_RECEIPT_IDENTITY_READ:{exc}"]
    if identity.get("schema_version") != "source-identity-v1":
        errors.append("INTAKE_RECEIPT_IDENTITY_SCHEMA_INVALID")
    if identity.get("episode_id") != receipt.get("episode_id"):
        errors.append("INTAKE_RECEIPT_EPISODE_ID_MISMATCH")
    if identity.get("source_id") != receipt.get("source_id"):
        errors.append("INTAKE_RECEIPT_SOURCE_ID_MISMATCH")
    identity_media = _declared_file(identity_path.parent, identity.get("media_path"))
    if media is not None and identity_media is not None and identity_media.resolve() != media.resolve():
        errors.append("INTAKE_RECEIPT_MEDIA_PATH_MISMATCH")
    if identity.get("media_path") != receipt.get("local_media_path"):
        errors.append("INTAKE_RECEIPT_MEDIA_RELATIVE_PATH_MISMATCH")
    if identity.get("media_sha256", "").lower() != str(receipt.get("local_media_sha256", "")).lower():
        errors.append("INTAKE_RECEIPT_MEDIA_IDENTITY_SHA_MISMATCH")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    errors = validate_receipt(args.receipt)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
