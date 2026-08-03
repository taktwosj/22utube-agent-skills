"""Episode-local root staging and the single shared CapCut materialization queue.

This module deliberately knows nothing about the CapCut UI.  A caller must prove
the app is closed before it obtains the shared-root lock; no failure path kills an
app or modifies another episode's package.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Callable, Iterator


CANONICAL_IDENTITY_FIELDS = ("project_folder", "draft_manifest_sha", "draft_id")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def stage_episode_root_authority(template_zip: Path, episode_root: Path, episode_id: str) -> dict:
    """Copy exactly one verified root ZIP into an episode-owned immutable location."""
    template_zip = Path(template_zip).resolve()
    episode_root = Path(episode_root).resolve()
    if not template_zip.is_file():
        raise RuntimeError("ROOT_AUTHORITY_ZIP_MISSING")
    source_sha = _sha256(template_zip)
    authority_dir = episode_root / "50_capcut_project" / "root_authority"
    copied_zip = authority_dir / "root.zip"
    if copied_zip.exists() and _sha256(copied_zip) != source_sha:
        raise RuntimeError("ROOT_AUTHORITY_EPISODE_CONFLICT")
    if not copied_zip.exists():
        authority_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_zip, copied_zip)
    copied_zip.chmod(0o444)
    contract = {
        "schema_version": "001short-root-contract-v1",
        "episode_id": episode_id,
        "root_zip_sha256": source_sha,
        "episode_root_zip_path": str(copied_zip),
        "root_authority": "ONE_VERIFIED_ZIP",
        "immutable_episode_local_copy": True,
    }
    contract_path = episode_root / "90_workflow" / "root_contract.json"
    if contract_path.exists():
        existing = json.loads(contract_path.read_text(encoding="utf-8"))
        if existing != contract:
            raise RuntimeError("ROOT_CONTRACT_EPISODE_CONFLICT")
    else:
        _write_json(contract_path, contract)
    return contract


@contextlib.contextmanager
def global_materialization_lock(capcut_root: Path, observe: Callable[[str, str], None] | None = None) -> Iterator[None]:
    """Serialize writes to the one Mac CapCut root using an advisory file lock."""
    capcut_root = Path(capcut_root).resolve()
    capcut_root.mkdir(parents=True, exist_ok=True)
    lock_path = capcut_root / ".Mac_CapCut_global_root.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        if os.name == "nt":
            import msvcrt
            while True:
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        if observe:
            observe("acquired", lock_path.name)
        try:
            yield
        finally:
            if observe:
                observe("released", lock_path.name)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_canonical_identity(identity: dict, ui_receipt: dict | None = None) -> dict:
    """Only project folder, manifest SHA and draft ID define a CapCut project."""
    if set(identity) != set(CANONICAL_IDENTITY_FIELDS):
        return {"status": "FAIL", "errors": [{"code": "CANONICAL_IDENTITY_FIELDS_INVALID"}]}
    if (
        not isinstance(identity["project_folder"], str) or not identity["project_folder"]
        or not isinstance(identity["draft_id"], str) or not identity["draft_id"]
        or not isinstance(identity["draft_manifest_sha"], str)
        or len(identity["draft_manifest_sha"]) != 64
    ):
        return {"status": "FAIL", "errors": [{"code": "CANONICAL_IDENTITY_VALUE_INVALID"}]}
    # Home/editor cards are deliberately auxiliary receipts.  They cannot make a
    # valid project invalid while CapCut refreshes its UI identifiers.
    del ui_receipt
    return {"status": "PASS", "errors": [], "canonical_identity": identity}


def _register_project(project: Path, capcut_root: Path, identity: dict) -> None:
    root_meta = capcut_root / "root_meta_info.json"
    if not root_meta.is_file():
        raise RuntimeError("MATERIALIZATION_ROOT_META_MISSING")
    root = json.loads(root_meta.read_text(encoding="utf-8"))
    meta_path = project / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("draft_id") != identity["draft_id"]:
        raise RuntimeError("MATERIALIZATION_DRAFT_ID_MISMATCH")
    rows = root.setdefault("all_draft_store", [])
    rows[:] = [
        row for row in rows
        if row.get("draft_name") != project.name and row.get("draft_id") != identity["draft_id"]
    ]
    row = dict(meta)
    row["draft_json_file"] = str(project / "draft_content.json")
    row["draft_timeline_materials_size"] = sum(
        path.stat().st_size for path in project.rglob("*") if path.is_file()
    )
    rows.append(row)
    root["root_path"] = str(capcut_root)
    _write_json(root_meta, root)


def materialize_validated_package(
    package: Path,
    capcut_root: Path,
    project_folder: str,
    episode_id: str,
    *,
    assert_closed: Callable[[], None],
    observe: Callable[[str, str], None] | None = None,
    graceful_close: Callable[[], None] | None = None,
) -> dict:
    """Copy one already-validated episode package while holding the global lock."""
    package = Path(package).resolve()
    capcut_root = Path(capcut_root).resolve()
    if not package.is_dir() or not (package / "draft_content.json").is_file():
        return {"status": "FAIL", "errors": [{"code": "MATERIALIZATION_PACKAGE_INVALID"}]}
    with global_materialization_lock(capcut_root, observe):
        try:
            assert_closed()
        except Exception as exc:
            return {"status": "FAIL", "errors": [{"code": "CAPCUT_PROCESS_OPEN", "detail": str(exc)}]}
        target = capcut_root / project_folder
        if target.exists():
            return {"status": "FAIL", "errors": [{"code": "LOCAL_CAPCUT_PROJECT_EXISTS"}]}
        try:
            shutil.copytree(package, target)
            draft_id = json.loads((target / "draft_meta_info.json").read_text(encoding="utf-8"))["draft_id"]
            identity = {
                "project_folder": target.name,
                "draft_manifest_sha": _sha256(target / "draft_content.json"),
                "draft_id": draft_id,
            }
            checked = validate_canonical_identity(identity, {"status": "UI_PENDING"})
            if checked["status"] != "PASS":
                raise RuntimeError(checked["errors"][0]["code"])
            _register_project(target, capcut_root, identity)
        except Exception as exc:
            if target.exists():
                shutil.rmtree(target)
            return {"status": "FAIL", "errors": [{"code": "MATERIALIZATION_FAILED", "detail": str(exc)}]}
        graceful = {"status": "NOT_REQUIRED_ALREADY_CLOSED"}
        if graceful_close is not None:
            try:
                graceful_close()
                graceful = {"status": "PASS"}
            except Exception as exc:
                graceful = {"status": "WAIT_CAPCUT_GRACEFUL_CLOSE_FAILED", "detail": str(exc)}
        return {
            "status": graceful["status"] if graceful["status"].startswith("WAIT_") else "PASS",
            "episode_id": episode_id,
            "canonical_identity": identity,
            "ui_receipt": {"status": "UI_PENDING"},
            "graceful_close_receipt": graceful,
            "errors": [],
        }
