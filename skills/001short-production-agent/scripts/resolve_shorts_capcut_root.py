#!/usr/bin/env python3
"""Resolve a portable 001 Shorts CapCut root from an OneDrive contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from track_template_matrix import (
    layout_contract_roles,
    track_template_profile,
    track_types_for_layout,
)


CONTRACT_RELATIVE_PATH = "00_asset_tools/templates/capcut/shorts_capcut_root_contract_v1.json"
LEGACY_LAYOUT_OPTIONAL_TEMPLATE_PROFILES = frozenset({
    "shrt_white_base_v1",
    "shrt_white_macmini_base_v1",
    "gunlimbo_london_bagel_layered_v2",
})


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


def _archive_root_tracks(archive: Path) -> list[dict[str, Any]]:
    try:
        with zipfile.ZipFile(archive) as bundle:
            candidates = []
            for name in bundle.namelist():
                parts = name.replace("\\", "/").split("/")
                if (
                    parts[-1] == "draft_content.json"
                    and "Timelines" not in parts
                    and "subdraft" not in parts
                ):
                    candidates.append(name)
            if len(candidates) != 1:
                raise ValueError(
                    f"ROOT_CONTRACT_LAYOUT_ARCHIVE_ROOT_AMBIGUOUS:{len(candidates)}"
                )
            payload = json.loads(bundle.read(candidates[0]).decode("utf-8"))
    except ValueError:
        raise
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("ROOT_CONTRACT_LAYOUT_ARCHIVE_INVALID") from exc
    tracks = payload.get("tracks") if isinstance(payload, dict) else None
    if not isinstance(tracks, list):
        raise ValueError("ROOT_CONTRACT_LAYOUT_ARCHIVE_TRACKS_INVALID")
    return tracks


def _validate_layout_contract(
    layout: Path,
    archive: Path,
    archive_sha: str,
    template_profile: str,
) -> tuple[str, int]:
    try:
        payload = json.loads(layout.read_text(encoding="utf-8"))
        profile = track_template_profile(template_profile)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("ROOT_CONTRACT_LAYOUT_INVALID") from exc
    except ValueError as exc:
        raise ValueError("ROOT_CONTRACT_TEMPLATE_PROFILE_UNKNOWN") from exc
    if payload.get("template_profile") != template_profile:
        raise ValueError("ROOT_CONTRACT_LAYOUT_PROFILE_MISMATCH")
    if str(payload.get("archive_sha256", "")).casefold() != archive_sha.casefold():
        raise ValueError("ROOT_CONTRACT_LAYOUT_SHA_MISMATCH")
    contract_version = payload.get("contract_version")
    if not isinstance(contract_version, str) or not contract_version:
        raise ValueError("ROOT_CONTRACT_LAYOUT_VERSION_INVALID")
    layout_tracks = payload.get("tracks")
    archive_tracks = _archive_root_tracks(archive)
    expected_count = len(profile.physical_tracks)
    expected_roles = layout_contract_roles(profile.track_layout)
    expected_types = track_types_for_layout(profile.track_layout)
    if (
        not isinstance(layout_tracks, list)
        or len(layout_tracks) != expected_count
        or len(archive_tracks) != expected_count
    ):
        raise ValueError("ROOT_CONTRACT_LAYOUT_TRACK_COUNT_MISMATCH")

    track_ids: set[str] = set()
    for index, (declared, actual) in enumerate(zip(layout_tracks, archive_tracks)):
        if not isinstance(declared, dict) or not isinstance(actual, dict):
            raise ValueError("ROOT_CONTRACT_LAYOUT_TRACK_IDENTITY_INVALID")
        identity = declared.get("identity")
        track_id = declared.get("track_id")
        track_type = declared.get("type")
        role = declared.get("role")
        if (
            declared.get("index") != index
            or not isinstance(identity, dict)
            or not isinstance(track_id, str)
            or not track_id
            or track_id in track_ids
            or not isinstance(track_type, str)
            or not track_type
            or not isinstance(role, str)
            or not role
        ):
            raise ValueError("ROOT_CONTRACT_LAYOUT_TRACK_IDENTITY_INVALID")
        track_ids.add(track_id)
        if role != expected_roles[index]:
            raise ValueError("ROOT_CONTRACT_LAYOUT_TRACK_ROLE_MISMATCH")
        if track_type != expected_types[index]:
            raise ValueError("ROOT_CONTRACT_LAYOUT_TRACK_TYPE_MISMATCH")
        if (
            str(identity.get("archive_sha256", "")).casefold()
            != archive_sha.casefold()
            or identity.get("track_id") != track_id
            or identity.get("type") != track_type
            or actual.get("id") != track_id
            or actual.get("type") != track_type
        ):
            raise ValueError("ROOT_CONTRACT_LAYOUT_TRACK_IDENTITY_MISMATCH")
    return contract_version, expected_count


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
    template_profile = selected.get("template_profile")
    if not isinstance(template_profile, str) or not template_profile:
        raise ValueError("ROOT_CONTRACT_TEMPLATE_PROFILE_MISSING")
    layout_raw = selected.get("layout_contract_relative_path")
    legacy_layout_unbound = (
        layout_raw is None
        and template_profile in LEGACY_LAYOUT_OPTIONAL_TEMPLATE_PROFILES
    )
    if legacy_layout_unbound:
        layout = None
        layout_version = "LEGACY_UNBOUND"
        track_count = len(_archive_root_tracks(archive))
    else:
        layout = _relative_file(workspace_root, layout_raw, "layout")
        layout_version, track_count = _validate_layout_contract(
            layout,
            archive,
            actual_sha,
            template_profile,
        )
    return {
        "status": "PASS_ROOT_CONTRACT",
        "workspace_root": str(workspace_root),
        "profile": profile,
        "contract_path": str(contract_path),
        "template_profile": template_profile,
        "archive": str(archive),
        "archive_sha256": actual_sha,
        "manifest": str(manifest),
        "layout_contract": str(layout) if layout is not None else None,
        "layout_contract_version": layout_version,
        "track_count": track_count,
        "legacy_layout_unbound": legacy_layout_unbound,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    print(json.dumps(resolve_root_contract(args.workspace_root, args.profile, args.contract), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
