#!/usr/bin/env python3
"""Resolve the active, immutable politics-longform CapCut root bundle."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any


DEFAULT_ACTIVE_POINTER = Path(
    "00_asset_tools/templates/capcut/jungchilong/capcut_active_root_v1.json"
)
_VERSION_RE = re.compile(r"^v([1-9][0-9]*)$")


@dataclass(frozen=True)
class ResolvedRoot:
    root_version: str
    root_profile: str
    base_layout_profile: str
    contract_path: Path
    contract_sha256: str
    archive_path: Path
    archive_sha256: str
    archive_root: str
    manifest_path: Path
    manifest_sha256: str
    layout_path: Path
    layout_sha256: str
    evidence_path: Path
    evidence_sha256: str
    activation_mode: str
    root_visual_gate: str
    root_post_open_validation: str
    episode_visual_gate_inherited: bool
    _workspace_root: Path = field(repr=False, compare=False)

    def _report_path(self, path: Path) -> str:
        return path.relative_to(self._workspace_root).as_posix()

    def to_report(self) -> dict[str, Any]:
        return {
            "status": "PASS_ROOT_CONTRACT",
            "root_version": self.root_version,
            "root_profile": self.root_profile,
            "base_layout_profile": self.base_layout_profile,
            "contract_path": self._report_path(self.contract_path),
            "contract_sha256": self.contract_sha256,
            "archive_path": self._report_path(self.archive_path),
            "archive_sha256": self.archive_sha256,
            "archive_root": self.archive_root,
            "manifest_path": self._report_path(self.manifest_path),
            "manifest_sha256": self.manifest_sha256,
            "layout_path": self._report_path(self.layout_path),
            "layout_sha256": self.layout_sha256,
            "evidence_path": self._report_path(self.evidence_path),
            "evidence_sha256": self.evidence_sha256,
            "activation_mode": self.activation_mode,
            "root_visual_gate": self.root_visual_gate,
            "root_post_open_validation": self.root_post_open_validation,
            "episode_visual_gate_inherited": self.episode_visual_gate_inherited,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("FAIL_ROOT_BUNDLE_JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError("FAIL_ROOT_BUNDLE_JSON")
    return value


def workspace_relative_path(workspace_root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("FAIL_ROOT_BUNDLE_PATH")
    normalized = value.replace("\\", "/")
    relative = PurePosixPath(normalized)
    if relative.is_absolute() or ":" in normalized or ".." in relative.parts:
        raise RuntimeError("FAIL_ROOT_BUNDLE_PATH")
    workspace = workspace_root.resolve()
    candidate = (workspace / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as error:
        raise RuntimeError("FAIL_ROOT_BUNDLE_PATH") from error
    return candidate


def _required_object(parent: dict[str, Any], field: str) -> dict[str, Any]:
    value = parent.get(field)
    if not isinstance(value, dict):
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    return value


def _required_text(parent: dict[str, Any], field: str) -> str:
    value = parent.get(field)
    if not isinstance(value, str) or not value:
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    return value


def _bound_artifact(
    workspace: Path,
    binding: dict[str, Any],
    *,
    missing_code: str,
    hash_code: str,
) -> tuple[Path, str]:
    path = workspace_relative_path(workspace, binding.get("relative_path"))
    if not path.is_file():
        raise RuntimeError(missing_code)
    expected = str(binding.get("sha256", "")).upper()
    actual = sha256_file(path)
    if not expected or actual != expected:
        raise RuntimeError(hash_code)
    return path, actual


def validate_archive_inventory(
    archive_path: Path,
    archive_root: str,
    file_count: int,
    manifest: dict[str, Any],
) -> None:
    if not archive_root.endswith("/") or PurePosixPath(archive_root.rstrip("/")).name != archive_root.rstrip("/"):
        raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list):
        raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
    expected: dict[str, tuple[int, str]] = {}
    for item in manifest_files:
        if not isinstance(item, dict):
            raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
        path = item.get("path")
        if not isinstance(path, str) or not path or path in expected:
            raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
        byte_count = item.get("bytes")
        sha256 = item.get("sha256")
        if (
            type(byte_count) is not int
            or byte_count < 0
            or not isinstance(sha256, str)
            or re.fullmatch(r"[0-9A-Fa-f]{64}", sha256) is None
        ):
            raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
        expected[path] = (byte_count, sha256.upper())
    try:
        with zipfile.ZipFile(archive_path) as package:
            entries = package.infolist()
            if len(entries) != file_count or any(entry.is_dir() for entry in entries):
                raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
            actual: dict[str, tuple[int, str]] = {}
            root = PurePosixPath(archive_root.rstrip("/"))
            for entry in entries:
                name = PurePosixPath(entry.filename)
                if name.is_absolute() or ".." in name.parts:
                    raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
                try:
                    relative = name.relative_to(root).as_posix()
                except ValueError as error:
                    raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY") from error
                if not relative or relative in actual:
                    raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")
                content = package.read(entry)
                actual[relative] = (len(content), hashlib.sha256(content).hexdigest().upper())
    except (OSError, zipfile.BadZipFile) as error:
        raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY") from error
    if actual != expected:
        raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY")


def _material_text(material: dict[str, Any]) -> str:
    try:
        content = json.loads(material["content"])
        return str(content["text"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT") from error


def _role_segment(draft: dict[str, Any], track: dict[str, Any], selector: dict[str, Any]) -> dict[str, Any]:
    kind = selector.get("kind")
    value = selector.get("value")
    if kind == "material_id":
        matches = [segment for segment in track.get("segments", []) if segment.get("material_id") == value]
    else:
        texts = {
            material.get("id"): _material_text(material)
            for material in draft.get("materials", {}).get("texts", [])
            if isinstance(material, dict)
        }
        if kind == "text_exact":
            matches = [segment for segment in track.get("segments", []) if texts.get(segment.get("material_id")) == value]
        elif kind == "text_prefix":
            matches = [
                segment
                for segment in track.get("segments", [])
                if texts.get(segment.get("material_id"), "").startswith(str(value))
            ]
        else:
            raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    if len(matches) != 1:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    return matches[0]


def _layout_timerange(value: object) -> tuple[int, int]:
    if not isinstance(value, dict) or set(value) != {"start", "duration"}:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    start = value["start"]
    duration = value["duration"]
    if type(start) is not int or type(duration) is not int:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    return start, duration


def validate_layout_against_archive(
    archive_path: Path,
    archive_root: str,
    layout: dict[str, Any],
) -> None:
    try:
        with zipfile.ZipFile(archive_path) as package:
            draft = json.loads(package.read(f"{archive_root}draft_content.json").decode("utf-8"))
    except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT") from error
    if not isinstance(draft, dict):
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    tracks = draft.get("tracks")
    if not isinstance(tracks, list):
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    canvas_config = draft.get("canvas_config", {})
    canvas = {
        "width": canvas_config.get("width"),
        "height": canvas_config.get("height"),
    }
    if (
        draft.get("duration") != layout.get("duration_us")
        or canvas != layout.get("canvas")
        or len(tracks) != layout.get("track_count")
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    roles = layout.get("roles")
    if not isinstance(roles, list) or not roles:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    content_starts: list[int] = []
    intro_ends: list[int] = []
    for role in roles:
        try:
            track = tracks[int(role["track_index"])]
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT") from error
        if track.get("id") != role.get("track_id") or track.get("type") != role.get("track_type"):
            raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
        segment = _role_segment(draft, track, _required_object(role, "material_selector"))
        target_range = segment.get("target_timerange")
        seed_range = role.get("seed_target_range_us")
        start, duration = _layout_timerange(target_range)
        seed_start, seed_duration = _layout_timerange(seed_range)
        if (start, duration) != (seed_start, seed_duration):
            raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
        if role.get("role") in {"ROOT_INTRO_BACKGROUND", "INTRO_HOOK"}:
            intro_ends.append(start + duration)
        else:
            content_starts.append(start)
        clip = segment.get("clip", {})
        expected_clip = _required_object(role, "clip")
        for field in ("scale", "rotation", "transform", "alpha"):
            if clip.get(field) != expected_clip.get(field):
                raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    if not content_starts:
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")
    content_boundary = min(content_starts)
    if layout.get("content_start_us") != content_boundary or any(
        intro_end != content_boundary for intro_end in intro_ends
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_LAYOUT")


def validate_activation_policy(
    root_version: str,
    pointer: dict[str, Any],
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[str, str, str, bool]:
    match = _VERSION_RE.fullmatch(root_version)
    if match is None:
        raise RuntimeError("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY")
    activation_basis = _required_object(pointer, "activation_basis")
    policy = _required_object(contract, "activation_policy")
    mode = _required_text(policy, "mode")
    inherited = policy.get("episode_visual_gate_inherited")
    evidence_inherited = evidence.get("episode_visual_gate_inherited")
    visual = _required_text(evidence, "visual_gate")
    post_open = _required_text(evidence, "post_open_validation")
    if activation_basis.get("mode") != mode or inherited is not False or evidence_inherited is not False:
        raise RuntimeError("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY")
    version_number = int(match.group(1))
    if version_number == 5:
        if (
            mode != "LEGACY_V5_STATIC_LOCK"
            or policy.get("allows_historical_visual_wait") is not True
            or policy.get("allows_historical_post_open_wait") is not True
            or visual != "WAIT_USER_VISUAL_GATE"
            or post_open != "WAIT_CAPCUT_OPEN_CLOSE"
        ):
            raise RuntimeError("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY")
    elif (
        mode != "VERIFIED_VISUAL_AND_POST_OPEN"
        or policy.get("allows_historical_visual_wait") is not False
        or policy.get("allows_historical_post_open_wait") is not False
        or visual != "PASS_USER_VISUAL_GATE"
        or post_open != "PASS_CAPCUT_OPEN_CLOSE"
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY")
    return mode, visual, post_open, False


def _resolve_root(
    workspace_root: Path,
    active_pointer_relative: Path = DEFAULT_ACTIVE_POINTER,
    candidate_contract_relative: Path | None = None,
) -> ResolvedRoot:
    workspace = workspace_root.resolve()
    if not workspace.is_dir():
        raise RuntimeError("WAIT_ROOT_BUNDLE_WORKSPACE_NOT_FOUND")
    if candidate_contract_relative is None:
        pointer_path = workspace_relative_path(workspace, active_pointer_relative.as_posix())
        if not pointer_path.is_file():
            raise RuntimeError("WAIT_ROOT_BUNDLE_POINTER_NOT_FOUND")
        pointer = load_json_object(pointer_path)
        if pointer.get("schema") != "politics-longform-capcut-active-root.v1":
            raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
        contract_binding = _required_object(pointer, "contract")
        contract_path = workspace_relative_path(workspace, contract_binding.get("relative_path"))
        if not contract_path.is_file():
            raise RuntimeError("WAIT_ROOT_BUNDLE_CONTRACT_NOT_FOUND")
        contract_sha256 = sha256_file(contract_path)
        if contract_sha256 != str(contract_binding.get("sha256", "")).upper():
            raise RuntimeError("FAIL_ROOT_BUNDLE_CONTRACT_HASH")
    else:
        contract_path = workspace_relative_path(workspace, candidate_contract_relative.as_posix())
        if not contract_path.is_file():
            raise RuntimeError("WAIT_ROOT_BUNDLE_CONTRACT_NOT_FOUND")
        contract_sha256 = sha256_file(contract_path)
        candidate_contract = load_json_object(contract_path)
        policy = _required_object(candidate_contract, "activation_policy")
        pointer = {
            "schema": "politics-longform-capcut-active-root.v1",
            "active_root_version": candidate_contract.get("root_version"),
            "activation_basis": {"mode": policy.get("mode")},
        }
    contract = load_json_object(contract_path)
    if contract.get("schema") != "politics-longform-capcut-root-bundle.v1":
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")

    root_version = _required_text(contract, "root_version")
    root_profile = _required_text(contract, "root_profile")
    base_layout_profile = _required_text(contract, "base_layout_profile")
    if (
        pointer.get("active_root_version") != root_version
        or root_profile == base_layout_profile
        or contract.get("immutable") is not True
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_PROFILE_RELATION")
    version_match = _VERSION_RE.fullmatch(root_version)
    parent_match = _VERSION_RE.fullmatch(str(contract.get("parent_root_version", "")))
    if version_match is None or parent_match is None or int(parent_match.group(1)) != int(version_match.group(1)) - 1:
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")

    archive_binding = _required_object(contract, "archive")
    manifest_binding = _required_object(contract, "manifest")
    layout_binding = _required_object(contract, "layout_contract")
    evidence_binding = _required_object(contract, "promotion_evidence")
    archive_path, archive_sha256 = _bound_artifact(
        workspace, archive_binding, missing_code="WAIT_ROOT_BUNDLE_ARCHIVE_NOT_FOUND", hash_code="FAIL_ROOT_BUNDLE_ARCHIVE_HASH"
    )
    manifest_path, manifest_sha256 = _bound_artifact(
        workspace, manifest_binding, missing_code="WAIT_ROOT_BUNDLE_MANIFEST_NOT_FOUND", hash_code="FAIL_ROOT_BUNDLE_MANIFEST_HASH"
    )
    layout_path, layout_sha256 = _bound_artifact(
        workspace, layout_binding, missing_code="WAIT_ROOT_BUNDLE_LAYOUT_NOT_FOUND", hash_code="FAIL_ROOT_BUNDLE_LAYOUT_HASH"
    )
    evidence_path, evidence_sha256 = _bound_artifact(
        workspace, evidence_binding, missing_code="WAIT_ROOT_BUNDLE_EVIDENCE_NOT_FOUND", hash_code="FAIL_ROOT_BUNDLE_EVIDENCE_HASH"
    )
    manifest = load_json_object(manifest_path)
    layout = load_json_object(layout_path)
    evidence = load_json_object(evidence_path)
    archive_root = _required_text(archive_binding, "archive_root")

    if (
        manifest.get("status") != manifest_binding.get("required_status")
        or str(manifest.get("archive_sha256", "")).upper() != archive_sha256
        or manifest.get("archive_root") != archive_root
        or manifest.get("template_profile") != base_layout_profile
        or manifest.get("source_candidate") != contract.get("source_candidate")
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    if int(version_match.group(1)) >= 6 and (
        manifest.get("root_version") != root_version
        or manifest.get("root_profile") != root_profile
        or manifest.get("base_layout_profile") != base_layout_profile
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_PROFILE_RELATION")
    if (
        layout.get("schema") != layout_binding.get("required_schema")
        or layout.get("root_version") != root_version
        or layout.get("root_profile") != root_profile
        or layout.get("base_layout_profile") != base_layout_profile
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_PROFILE_RELATION")
    if (
        evidence.get("schema") != "politics-longform-capcut-root-evidence.v1"
        or evidence.get("root_version") != root_version
        or evidence.get("root_profile") != root_profile
        or evidence.get("source_candidate") != contract.get("source_candidate")
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    for field, expected_path, expected_hash in (
        ("archive", archive_path, archive_sha256),
        ("manifest", manifest_path, manifest_sha256),
    ):
        binding = _required_object(evidence, field)
        if workspace_relative_path(workspace, binding.get("relative_path")) != expected_path or str(binding.get("sha256", "")).upper() != expected_hash:
            raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    promotion_binding = _required_object(evidence, "promotion_report")
    promotion_path, _ = _bound_artifact(
        workspace,
        promotion_binding,
        missing_code="WAIT_ROOT_BUNDLE_EVIDENCE_NOT_FOUND",
        hash_code="FAIL_ROOT_BUNDLE_EVIDENCE_HASH",
    )
    promotion = load_json_object(promotion_path)
    source_candidate = _required_text(contract, "source_candidate")
    promotion_source = _required_text(promotion, "source_root")
    promotion_candidate = promotion_source.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    if promotion_candidate != source_candidate:
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    if (
        evidence.get("static_gate") != evidence_binding.get("required_static_gate")
        or promotion.get("status") != evidence.get("static_gate")
        or promotion.get("visual_gate") != evidence.get("visual_gate")
        or promotion.get("post_open_validation") != evidence.get("post_open_validation")
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_RELATION")
    if (
        evidence_binding.get("required_static_gate") != "PASS_ROOT_PROMOTION_STATIC"
        or evidence.get("static_gate") != "PASS_ROOT_PROMOTION_STATIC"
        or promotion.get("status") != "PASS_ROOT_PROMOTION_STATIC"
    ):
        raise RuntimeError("FAIL_ROOT_BUNDLE_ACTIVATION_POLICY")

    try:
        file_count = int(archive_binding.get("file_count"))
    except (TypeError, ValueError) as error:
        raise RuntimeError("FAIL_ROOT_BUNDLE_INVENTORY") from error
    validate_archive_inventory(archive_path, archive_root, file_count, manifest)
    validate_layout_against_archive(archive_path, archive_root, layout)
    activation_mode, visual, post_open, inherited = validate_activation_policy(
        root_version, pointer, contract, evidence
    )
    return ResolvedRoot(
        root_version=root_version,
        root_profile=root_profile,
        base_layout_profile=base_layout_profile,
        contract_path=contract_path,
        contract_sha256=contract_sha256,
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        archive_root=archive_root,
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
        layout_path=layout_path,
        layout_sha256=layout_sha256,
        evidence_path=evidence_path,
        evidence_sha256=evidence_sha256,
        activation_mode=activation_mode,
        root_visual_gate=visual,
        root_post_open_validation=post_open,
        episode_visual_gate_inherited=inherited,
        _workspace_root=workspace,
    )


def resolve_active_root(
    workspace_root: Path,
    active_pointer_relative: Path = DEFAULT_ACTIVE_POINTER,
) -> ResolvedRoot:
    return _resolve_root(workspace_root, active_pointer_relative)


def resolve_candidate_root(
    workspace_root: Path,
    contract_relative_path: Path,
) -> ResolvedRoot:
    return _resolve_root(
        workspace_root,
        DEFAULT_ACTIVE_POINTER,
        candidate_contract_relative=contract_relative_path,
    )
