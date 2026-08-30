#!/usr/bin/env python3
"""Resolve a portable 001 Shorts CapCut root from an OneDrive contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CONTRACT_RELATIVE_PATH = "00_asset_tools/templates/capcut/shorts_capcut_root_contract_v1.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_file(workspace_root: Path, raw: object, field: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"ROOT_CONTRACT_{field.upper()}_MISSING")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError(f"ROOT_CONTRACT_{field.upper()}_MUST_BE_RELATIVE")
    resolved = (workspace_root / candidate).resolve()
    try:
        resolved.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError(f"ROOT_CONTRACT_{field.upper()}_OUT_OF_WORKSPACE") from exc
    if not resolved.is_file():
        raise FileNotFoundError(f"ROOT_CONTRACT_{field.upper()}_MISSING:{resolved}")
    return resolved


def resolve_root_contract(
    workspace_root: Path, profile: str, contract_path: Path | None = None
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    if not workspace_root.is_dir():
        raise FileNotFoundError(f"WORKSPACE_ROOT_MISSING:{workspace_root}")
    contract_path = (contract_path or workspace_root / CONTRACT_RELATIVE_PATH).resolve()
    try:
        contract_path.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError("ROOT_CONTRACT_OUT_OF_WORKSPACE") from exc
    if not contract_path.is_file():
        raise FileNotFoundError(f"ROOT_CONTRACT_MISSING:{contract_path}")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "shorts-capcut-root-contract-v1":
        raise ValueError("ROOT_CONTRACT_SCHEMA_INVALID")
    if contract.get("workspace_relative") is not True:
        raise ValueError("ROOT_CONTRACT_NOT_PORTABLE")
    if contract.get("assembly_mode") != "clean_staging_copy":
        raise ValueError("ROOT_CONTRACT_ASSEMBLY_MODE_INVALID")
    profiles = contract.get("profiles")
    if not isinstance(profiles, dict) or profile not in profiles:
        raise ValueError(f"ROOT_CONTRACT_PROFILE_UNKNOWN:{profile}")
    selected = profiles[profile]
    if not isinstance(selected, dict):
        raise ValueError("ROOT_CONTRACT_PROFILE_INVALID")
    archive = _relative_file(workspace_root, selected.get("archive_relative_path"), "archive")
    manifest = _relative_file(workspace_root, selected.get("manifest_relative_path"), "manifest")
    expected_sha = selected.get("archive_sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValueError("ROOT_CONTRACT_ARCHIVE_SHA_INVALID")
    actual_sha = _sha256(archive)
    if actual_sha.casefold() != expected_sha.casefold():
        raise ValueError("ROOT_CONTRACT_ARCHIVE_SHA_MISMATCH")
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    if manifest_payload.get("sha256", "").casefold() != expected_sha.casefold():
        raise ValueError("ROOT_CONTRACT_MANIFEST_SHA_MISMATCH")
    if manifest_payload.get("template_profile") != selected.get("template_profile"):
        raise ValueError("ROOT_CONTRACT_MANIFEST_PROFILE_MISMATCH")
    return {
        "status": "PASS_ROOT_CONTRACT",
        "workspace_root": str(workspace_root),
        "profile": profile,
        "contract_path": str(contract_path),
        "template_profile": selected["template_profile"],
        "archive": str(archive),
        "archive_sha256": actual_sha,
        "manifest": str(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--profile", choices=("home_windows", "macmini"), required=True)
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    print(json.dumps(resolve_root_contract(args.workspace_root, args.profile, args.contract), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
