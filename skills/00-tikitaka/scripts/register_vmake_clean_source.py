#!/usr/bin/env python3
"""Register a downloaded Vmake result as the episode clean visual."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


MANIFEST_RELATIVE_PATH = Path("10_analysis/vmake_clean_source.json")
LOCK_RELATIVE_PATH = Path("10_analysis/source_identity_lock.json")
CLEAN_RELATIVE_PATH = Path("00_source/clean_source.mp4")
VMAKE_PAGE_URL = "https://vmake.ai/video-watermark-remover/upload"
DURATION_TOLERANCE_SEC = 0.5


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {label} missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {label} parse failed") from exc
    if not isinstance(payload, dict):
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {label} root must be object")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_validator() -> Any:
    validator_path = Path(__file__).with_name("validate_vmake_clean_source.py")
    spec = importlib.util.spec_from_file_location(
        "tikitaka_vmake_clean_source_validator",
        validator_path,
    )
    if spec is None or spec.loader is None:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path = root / MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def register_vmake_clean_source(
    root: Path,
    download_path: Path,
    *,
    source_url: str,
    job_id: str,
    rights_confirmed: bool,
    confirmation_source: str,
    download_method: str = "browser_download",
) -> dict[str, Any]:
    root = Path(root).resolve()
    download = Path(download_path).resolve()
    if download_method not in {
        "browser_download",
        "idm",
        "direct_signed_url_fallback",
    }:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: unsupported download_method")
    if rights_confirmed is not True or confirmation_source != "user":
        raise GateFail(
            "WAIT_VMAKE_RIGHTS_CONFIRMATION: current source URL requires explicit user confirmation"
        )
    if not download.is_file() or download.stat().st_size <= 0:
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: downloaded file missing: {download}")
    if not str(job_id or "").strip():
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: Vmake job id missing")
    if (
        not download.name.lower().startswith("file_from_link_")
        or str(job_id).strip() not in download.name
    ):
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: download filename is not bound to Vmake job id")

    lock = load_json(root / LOCK_RELATIVE_PATH, "source_identity_lock.json")
    validator = load_validator()
    locked_video_id = str(lock.get("video_id") or "").strip()
    requested_video_id = validator.extract_video_id(source_url)
    if not locked_video_id or requested_video_id != locked_video_id:
        raise GateFail("WAIT_VMAKE_SOURCE_IDENTITY: source URL/video id mismatch")

    source_relative = str(
        lock.get("local_source_path")
        or lock.get("local_source_relative_path")
        or "00_source/source.mp4"
    )
    source_path = validator.relative_artifact(
        root,
        source_relative,
        "local_source_path",
    )
    source_sha = str(lock.get("sha256") or "").strip().lower()
    if sha256_file(source_path) != source_sha:
        raise GateFail("WAIT_VMAKE_SOURCE_IDENTITY: locked source hash mismatch")

    clean_path = root / CLEAN_RELATIVE_PATH
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".clean_source-",
            suffix=".mp4",
            dir=str(clean_path.parent),
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        shutil.copyfile(download, temporary_path)
        if temporary_path.stat().st_size != download.stat().st_size:
            raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: clean visual copy size mismatch")
        os.replace(temporary_path, clean_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    source_probe = validator.probe_media(source_path)
    clean_probe = validator.probe_media(clean_path)
    locked_duration = lock.get("duration_sec")
    if isinstance(locked_duration, bool) or not isinstance(locked_duration, (int, float)):
        raise GateFail("WAIT_VMAKE_DURATION_PARITY: locked duration must be numeric")
    observed_durations = (
        float(locked_duration),
        float(source_probe["duration_sec"]),
        float(clean_probe["duration_sec"]),
    )
    if max(observed_durations) - min(observed_durations) > DURATION_TOLERANCE_SEC:
        raise GateFail("WAIT_VMAKE_DURATION_PARITY: original and clean duration mismatch")
    if abs(source_probe["aspect_ratio"] - clean_probe["aspect_ratio"]) > 0.02:
        raise GateFail("WAIT_VMAKE_ASPECT_RATIO: original and clean aspect ratio mismatch")

    payload = {
        "gate_name": "VMAKE_CLEAN_SOURCE_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "provider": "vmake.ai",
        "provider_page": VMAKE_PAGE_URL,
        "provider_operation": "video_watermark_remover_auto",
        "requested_source_url": source_url,
        "requested_video_id": requested_video_id,
        "source_fingerprint_sha256": source_sha,
        "analysis_video_path": "00_source/source.mp4",
        "analysis_source_role": "original_source_only",
        "clean_visual_path": CLEAN_RELATIVE_PATH.as_posix(),
        "clean_visual_sha256": sha256_file(clean_path),
        "production_visual_role": "vmake_clean_visual",
        "vmake_job_id": str(job_id).strip(),
        "downloaded_filename": download.name,
        "download_method": download_method,
        "rights_confirmed": True,
        "confirmation_source": "user",
        "source_duration_sec": source_probe["duration_sec"],
        "clean_duration_sec": clean_probe["duration_sec"],
        "duration_tolerance_sec": DURATION_TOLERANCE_SEC,
        "source_width": source_probe["width"],
        "source_height": source_probe["height"],
        "clean_width": clean_probe["width"],
        "clean_height": clean_probe["height"],
        "embedded_audio_policy": "muted_always",
        "source_voice_policy": "separate_demucs_q_only",
        "no_vocals_used": False,
        "created_by": "register_vmake_clean_source.py",
    }
    write_manifest(root, payload)
    try:
        validator.validate_vmake_clean_source(root)
    except validator.GateFail as exc:
        raise GateFail(str(exc)) from exc
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--download", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--rights-confirmed", action="store_true")
    parser.add_argument("--confirmation-source", choices=["user"], default="")
    parser.add_argument(
        "--download-method",
        choices=["browser_download", "idm", "direct_signed_url_fallback"],
        default="browser_download",
    )
    args = parser.parse_args()
    try:
        result = register_vmake_clean_source(
            Path(args.root),
            Path(args.download),
            source_url=args.source_url,
            job_id=args.job_id,
            rights_confirmed=args.rights_confirmed,
            confirmation_source=args.confirmation_source,
            download_method=args.download_method,
        )
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
