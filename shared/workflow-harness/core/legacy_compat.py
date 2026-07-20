"""Read-only legacy adapters and deterministic rewind planning.

Legacy artifacts are inputs only. Canonical V2 artifacts always win when
present, and this module never rewrites an episode or deletes a build.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


CANONICAL_SHORTS_HANDOFF = Path("20_script/design_handoff.json")
LEGACY_SHORTS_HANDOFFS = (
    Path("20_script/script_handoff_gate.json"),
    Path("20_script/report1_handoff.json"),
)
_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
_EVENT_ID_RE = re.compile(r"^evt-(\d{6})$")


class LegacyCompatibilityError(Exception):
    """Raised when a legacy artifact cannot be read without guessing."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _read_json(path: Path) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LegacyCompatibilityError(
            f"LEGACY_ARTIFACT_UNREADABLE path={path}"
        ) from exc
    if not isinstance(value, dict):
        raise LegacyCompatibilityError(
            f"LEGACY_ARTIFACT_NOT_OBJECT path={path}"
        )
    return value, _sha256_bytes(raw)


def _resolve_inside(root: Path, relative_path: str | Path) -> Path:
    root = root.resolve()
    candidate = (root / Path(relative_path)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise LegacyCompatibilityError(
            f"LEGACY_PATH_OUTSIDE_EPISODE path={relative_path}"
        ) from exc
    return candidate


def _pointer_target(
    episode_root: Path,
    pointer: dict,
) -> tuple[dict, str, str] | None:
    if pointer.get("schema_version") != "handoff-compat-v1":
        return None
    relative = pointer.get("canonical_handoff_path")
    expected_sha = pointer.get("canonical_handoff_sha256")
    if not isinstance(relative, str) or not _SHA256_RE.fullmatch(
        str(expected_sha or "")
    ):
        raise LegacyCompatibilityError("INVALID_LEGACY_COMPAT_POINTER")
    target = _resolve_inside(episode_root, relative)
    if not target.is_file():
        raise LegacyCompatibilityError(
            f"LEGACY_COMPAT_TARGET_MISSING path={relative}"
        )
    payload, actual_sha = _read_json(target)
    if actual_sha.upper() != str(expected_sha).upper():
        raise LegacyCompatibilityError(
            "STALE_LEGACY_CANONICAL_SHA "
            f"expected={expected_sha} actual={actual_sha}"
        )
    return payload, actual_sha, Path(relative).as_posix()


def load_shorts_handoff(episode_root: str | Path) -> dict:
    """Load the authoritative Shorts handoff without rewriting the episode.

    If the V2 canonical file exists, it is selected. Any direct legacy payload
    that differs is rejected as stale evidence rather than used. Without a
    canonical file, the first readable legacy payload (or valid compatibility
    pointer target) is returned under ``contract_mode=LEGACY_COMPAT``.
    """
    root = Path(episode_root)
    canonical_path = _resolve_inside(root, CANONICAL_SHORTS_HANDOFF)
    legacy_found: list[tuple[Path, dict, str]] = []
    for relative in LEGACY_SHORTS_HANDOFFS:
        path = _resolve_inside(root, relative)
        if path.is_file():
            payload, sha = _read_json(path)
            legacy_found.append((relative, payload, sha))

    if canonical_path.is_file():
        canonical, canonical_sha = _read_json(canonical_path)
        rejected = []
        for relative, payload, payload_sha in legacy_found:
            if payload.get("schema_version") == "handoff-compat-v1":
                agrees = (
                    payload.get("canonical_handoff_path")
                    == CANONICAL_SHORTS_HANDOFF.as_posix()
                    and str(payload.get("canonical_handoff_sha256", "")).upper()
                    == canonical_sha
                )
            else:
                agrees = payload == canonical
            if not agrees:
                rejected.append(
                    {
                        "path": relative.as_posix(),
                        "sha256": payload_sha,
                        "reason": "STALE_LEGACY_PAYLOAD",
                    }
                )
        return {
            "contract_mode": "V2_CANONICAL",
            "source_path": CANONICAL_SHORTS_HANDOFF.as_posix(),
            "source_sha256": canonical_sha,
            "payload": canonical,
            "rejected_legacy": rejected,
        }

    if not legacy_found:
        raise LegacyCompatibilityError("SHORTS_HANDOFF_NOT_FOUND")

    relative, legacy, legacy_sha = legacy_found[0]
    pointer = _pointer_target(root, legacy)
    if pointer is not None:
        payload, source_sha, source_path = pointer
    else:
        payload, source_sha, source_path = (
            legacy,
            legacy_sha,
            relative.as_posix(),
        )
    return {
        "contract_mode": "LEGACY_COMPAT",
        "source_path": source_path,
        "source_sha256": source_sha,
        "payload": payload,
        "rejected_legacy": [],
    }


def load_legacy_politics_episode(
    episode_root: str | Path,
    artifact_paths: list[str],
) -> dict:
    """Read requested legacy politics artifacts byte-for-byte, without writes."""
    root = Path(episode_root)
    artifacts = []
    for relative in artifact_paths:
        path = _resolve_inside(root, relative)
        if not path.is_file():
            raise LegacyCompatibilityError(
                f"LEGACY_POLITICS_ARTIFACT_MISSING path={relative}"
            )
        raw = path.read_bytes()
        artifacts.append(
            {
                "path": Path(relative).as_posix(),
                "sha256": _sha256_bytes(raw),
                "bytes": raw,
            }
        )
    return {
        "contract_mode": "LEGACY_COMPAT",
        "artifacts": artifacts,
    }


def append_rewind_event(
    ledger_store,
    *,
    timestamp: str,
    episode_id: str,
    lane: str,
    rewind_to_gate: str,
    reason: str,
    affected_sha256: list[str],
) -> dict:
    """Append the required LOCK_INVALIDATED evidence for one rewind."""
    if not reason.strip():
        raise LegacyCompatibilityError("REWIND_REASON_REQUIRED")
    normalized_shas = [str(value).upper() for value in affected_sha256]
    if not normalized_shas or any(
        not _SHA256_RE.fullmatch(value) for value in normalized_shas
    ):
        raise LegacyCompatibilityError("REWIND_AFFECTED_SHA256_REQUIRED")
    previous = ledger_store.latest_event_id()
    match = _EVENT_ID_RE.fullmatch(str(previous or ""))
    if match is None:
        raise LegacyCompatibilityError("REWIND_REQUIRES_EXISTING_LEDGER")
    event = {
        "event_id": f"evt-{int(match.group(1)) + 1:06d}",
        "timestamp": timestamp,
        "episode_id": episode_id,
        "lane": lane,
        "gate": rewind_to_gate,
        "event_type": "LOCK_INVALIDATED",
        "actor": "CODEX",
        "previous_event_id": previous,
        "reason": reason,
        "affected_sha256": normalized_shas,
    }
    return ledger_store.append(event)


def plan_structural_contamination_rebuild(
    *,
    structural_contamination: bool,
    target_build_path: str,
    pinned_root_path: str,
) -> dict:
    """Return a safe deterministic plan; callers own actual filesystem work."""
    if not structural_contamination:
        return {
            "status": "NO_REBUILD_REQUIRED",
            "discard_target": None,
            "rebuild_from": None,
            "partial_patch_allowed": False,
        }
    target = Path(target_build_path)
    pinned = Path(pinned_root_path)
    if target == pinned:
        raise LegacyCompatibilityError("TARGET_BUILD_MUST_NOT_BE_PINNED_ROOT")
    return {
        "status": "CLEAN_REBUILD_REQUIRED",
        "discard_target": target.as_posix(),
        "rebuild_from": pinned.as_posix(),
        "partial_patch_allowed": False,
    }
