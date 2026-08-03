#!/usr/bin/env python3
"""Resolve and verify the portable politics-longform CapCut root contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONTRACT = Path(
    "00_asset_tools/templates/capcut/jungchilong/capcut_root_contract_v1.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def relative_path(value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"ROOT_CONTRACT_{field}_MISSING")
    candidate = Path(value)
    if candidate.is_absolute() or ":" in value or ".." in candidate.parts:
        raise RuntimeError(f"ROOT_CONTRACT_{field}_NOT_WORKSPACE_RELATIVE")
    return candidate


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"ROOT_CONTRACT_INVALID:{error}") from error
    if not isinstance(value, dict):
        raise RuntimeError("ROOT_CONTRACT_OBJECT_REQUIRED")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--contract-relative-path", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()

    workspace = args.workspace_root.resolve()
    contract_path = workspace / relative_path(args.contract_relative_path.as_posix(), "PATH")
    if not workspace.is_dir() or not contract_path.is_file():
        raise RuntimeError("WAIT_ROOT_CONTRACT_NOT_FOUND")
    contract = load_json(contract_path)
    if contract.get("status") != "PASS_ARCHIVE_INTEGRITY":
        raise RuntimeError("WAIT_ROOT_CONTRACT_NOT_APPROVED")

    archive_data = contract.get("archive")
    manifest_data = contract.get("manifest")
    if not isinstance(archive_data, dict) or not isinstance(manifest_data, dict):
        raise RuntimeError("ROOT_CONTRACT_ARCHIVE_OR_MANIFEST_MISSING")
    archive = workspace / relative_path(archive_data.get("relative_path"), "ARCHIVE_PATH")
    manifest = workspace / relative_path(manifest_data.get("relative_path"), "MANIFEST_PATH")
    if not archive.is_file() or not manifest.is_file():
        raise RuntimeError("WAIT_ROOT_ARCHIVE_OR_MANIFEST_NOT_FOUND")
    expected_hash = str(archive_data.get("sha256", "")).upper()
    actual_hash = sha256(archive)
    if actual_hash != expected_hash:
        raise RuntimeError("FAIL_ROOT_ARCHIVE_INTEGRITY")
    manifest_json = load_json(manifest)
    if manifest_json.get("status") != manifest_data.get("required_status"):
        raise RuntimeError("FAIL_ROOT_MANIFEST_STATUS")
    if str(manifest_json.get("archive_sha256", "")).upper() != actual_hash:
        raise RuntimeError("FAIL_ROOT_MANIFEST_ARCHIVE_BINDING")

    print(
        json.dumps(
            {
                "status": "PASS_ROOT_CONTRACT",
                "workspace_root": str(workspace),
                "contract_relative_path": DEFAULT_CONTRACT.as_posix(),
                "archive": str(archive),
                "archive_sha256": actual_hash,
                "manifest": str(manifest),
                "template_profile": contract.get("template_profile"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
