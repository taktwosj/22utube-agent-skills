#!/usr/bin/env python3
"""Validate a Vmake clean visual against the locked original Shorts source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


class GateFail(Exception):
    pass


MANIFEST_RELATIVE_PATH = Path("10_analysis/vmake_clean_source.json")
LOCK_RELATIVE_PATH = Path("10_analysis/source_identity_lock.json")
EXPECTED_CLEAN_PATH = "00_source/clean_source.mp4"
VMAKE_PAGE_URL = "https://vmake.ai/video-watermark-remover/upload"
MAX_DURATION_TOLERANCE_SEC = 0.5
MAX_ASPECT_RATIO_DELTA = 0.02


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


def require_number(data: dict[str, Any], field: str) -> float:
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {field} must be numeric")
    return float(value)


def relative_artifact(root: Path, raw_path: Any, field: str) -> Path:
    value = str(raw_path or "").strip()
    path = Path(value)
    if not value or path.is_absolute():
        raise GateFail(
            f"WAIT_VMAKE_CLEAN_SOURCE: {field} must be an episode-root-relative path"
        )
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {field} escapes episode root") from exc
    if not resolved.is_file() or resolved.stat().st_size <= 0:
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {field} missing: {resolved}")
    return resolved


def extract_video_id(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/").split("/", 1)[0]
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1]
        query_id = parse_qs(parsed.query).get("v")
        if query_id:
            return query_id[0]
    return ""


def probe_media(path: Path, ffprobe: str | None = None) -> dict[str, Any]:
    executable = ffprobe or shutil.which("ffprobe")
    if not executable:
        raise GateFail("WAIT_FFPROBE_AVAILABLE: ffprobe not found")
    try:
        completed = subprocess.run(
            [
                executable,
                "-v",
                "error",
                "-show_entries",
                (
                    "format=duration:"
                    "stream=codec_type,codec_name,width,height,sample_rate,channels"
                ),
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: ffprobe failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()
        message = detail[-1] if detail else f"exit={completed.returncode}"
        raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: ffprobe failed: {message}")
    try:
        payload = json.loads(completed.stdout)
        duration_sec = float(payload.get("format", {}).get("duration"))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: media duration missing") from exc
    streams = payload.get("streams")
    if not isinstance(streams, list):
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: media streams missing")
    video_streams = [
        stream
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "video"
    ]
    audio_streams = [
        stream
        for stream in streams
        if isinstance(stream, dict) and stream.get("codec_type") == "audio"
    ]
    if duration_sec <= 0 or not video_streams:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: playable video stream required")
    try:
        width = int(video_streams[0].get("width") or 0)
        height = int(video_streams[0].get("height") or 0)
    except (TypeError, ValueError) as exc:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: invalid video dimensions") from exc
    if width <= 0 or height <= 0:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: positive video dimensions required")
    return {
        "duration_sec": duration_sec,
        "width": width,
        "height": height,
        "aspect_ratio": width / height,
        "video_streams": len(video_streams),
        "audio_streams": len(audio_streams),
        "video_codec": str(video_streams[0].get("codec_name") or ""),
        "audio_codec": (
            str(audio_streams[0].get("codec_name") or "") if audio_streams else ""
        ),
    }


def validate_vmake_clean_source(
    root: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest_file = (
        root / MANIFEST_RELATIVE_PATH
        if manifest_path is None
        else (
            Path(manifest_path)
            if Path(manifest_path).is_absolute()
            else root / Path(manifest_path)
        )
    )
    manifest = load_json(manifest_file, "vmake_clean_source.json")
    lock = load_json(root / LOCK_RELATIVE_PATH, "source_identity_lock.json")

    expected_values = {
        "gate_name": "VMAKE_CLEAN_SOURCE_GATE",
        "status": "PASS",
        "owner_skill": "00-tikitaka",
        "provider": "vmake.ai",
        "provider_page": VMAKE_PAGE_URL,
        "provider_operation": "video_watermark_remover_auto",
        "clean_visual_path": EXPECTED_CLEAN_PATH,
        "rights_confirmed": True,
        "confirmation_source": "user",
        "analysis_video_path": "00_source/source.mp4",
        "analysis_source_role": "original_source_only",
        "production_visual_role": "vmake_clean_visual",
        "embedded_audio_policy": "muted_always",
        "source_voice_policy": "separate_demucs_q_only",
        "created_by": "register_vmake_clean_source.py",
    }
    for field, expected in expected_values.items():
        if manifest.get(field) != expected:
            token = (
                "WAIT_VMAKE_RIGHTS_CONFIRMATION"
                if field in {"rights_confirmed", "confirmation_source"}
                else "WAIT_VMAKE_CLEAN_SOURCE"
            )
            raise GateFail(f"{token}: {field} must be {expected!r}")

    if manifest.get("download_method") not in {
        "browser_download",
        "idm",
        "direct_signed_url_fallback",
    }:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: unsupported download_method")

    source_sha = str(lock.get("sha256") or "").strip().lower()
    manifest_source_sha = str(
        manifest.get("source_fingerprint_sha256") or ""
    ).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha) or manifest_source_sha != source_sha:
        raise GateFail("WAIT_VMAKE_SOURCE_IDENTITY: source fingerprint mismatch")

    locked_video_id = str(lock.get("video_id") or "").strip()
    requested_video_id = str(manifest.get("requested_video_id") or "").strip()
    requested_url_id = extract_video_id(str(manifest.get("requested_source_url") or ""))
    locked_url_id = extract_video_id(str(lock.get("canonical_url") or ""))
    if (
        not locked_video_id
        or requested_video_id != locked_video_id
        or requested_url_id != locked_video_id
        or (locked_url_id and locked_url_id != locked_video_id)
    ):
        raise GateFail("WAIT_VMAKE_SOURCE_IDENTITY: URL/video id mismatch")

    job_id = str(manifest.get("vmake_job_id") or "").strip()
    filename = str(manifest.get("downloaded_filename") or "").strip()
    if (
        not job_id
        or not filename.lower().startswith("file_from_link_")
        or job_id not in filename
    ):
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: Vmake job/download binding missing")

    source_path_value = (
        lock.get("local_source_path")
        or lock.get("local_source_relative_path")
        or "00_source/source.mp4"
    )
    source_path = relative_artifact(root, source_path_value, "local_source_path")
    clean_path = relative_artifact(
        root,
        manifest.get("clean_visual_path"),
        "clean_visual_path",
    )
    if sha256_file(source_path) != source_sha:
        raise GateFail("WAIT_VMAKE_SOURCE_IDENTITY: locked source hash mismatch")
    clean_sha = sha256_file(clean_path)
    if str(manifest.get("clean_visual_sha256") or "").lower() != clean_sha:
        raise GateFail("WAIT_VMAKE_CLEAN_SOURCE: clean visual hash mismatch")

    source_probe = probe_media(source_path)
    clean_probe = probe_media(clean_path)
    tolerance = require_number(manifest, "duration_tolerance_sec")
    if tolerance < 0 or tolerance > MAX_DURATION_TOLERANCE_SEC:
        raise GateFail("WAIT_VMAKE_DURATION_PARITY: tolerance must be 0..0.5")
    observed_durations = (
        require_number(lock, "duration_sec"),
        require_number(manifest, "source_duration_sec"),
        require_number(manifest, "clean_duration_sec"),
        source_probe["duration_sec"],
        clean_probe["duration_sec"],
    )
    if max(observed_durations) - min(observed_durations) > tolerance:
        raise GateFail("WAIT_VMAKE_DURATION_PARITY: original and clean duration mismatch")

    declared_dimensions = {
        "source_width": source_probe["width"],
        "source_height": source_probe["height"],
        "clean_width": clean_probe["width"],
        "clean_height": clean_probe["height"],
    }
    for field, actual in declared_dimensions.items():
        if manifest.get(field) != actual:
            raise GateFail(f"WAIT_VMAKE_CLEAN_SOURCE: {field} mismatch")
    if abs(source_probe["aspect_ratio"] - clean_probe["aspect_ratio"]) > MAX_ASPECT_RATIO_DELTA:
        raise GateFail("WAIT_VMAKE_ASPECT_RATIO: original and clean aspect ratio mismatch")

    return {
        "vmake_clean_source_status": "PASS",
        "vmake_clean_source_manifest_path": str(manifest_file),
        "vmake_clean_visual_path": str(clean_path),
        "vmake_clean_visual_sha256": clean_sha,
        "vmake_job_id": job_id,
        "source_video_id": locked_video_id,
        "source_video_audio_policy": "muted_always",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default=str(MANIFEST_RELATIVE_PATH))
    args = parser.parse_args()
    try:
        result = validate_vmake_clean_source(Path(args.root), Path(args.manifest))
    except GateFail as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
