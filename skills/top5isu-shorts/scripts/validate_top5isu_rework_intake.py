#!/usr/bin/env python3
"""Validate clean-video rework intake for top5isu Shorts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Callable


class GateFail(Exception):
    pass


def probe_media(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "format=duration:stream=codec_type,width,height",
        "-of",
        "json",
        str(path),
    ]
    try:
        process = subprocess.run(command, text=True, capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GateFail(f"WAIT_CLEAN_VIDEO_MEDIA_PROBE: {exc}") from exc
    if process.returncode != 0:
        raise GateFail("WAIT_CLEAN_VIDEO_MEDIA_PROBE: ffprobe could not read clean video")
    try:
        data = json.loads(process.stdout)
        duration = float((data.get("format") or {}).get("duration") or 0)
        streams = data.get("streams") or []
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise GateFail("WAIT_CLEAN_VIDEO_MEDIA_PROBE: invalid ffprobe output") from exc
    if duration <= 0 or not any(stream.get("codec_type") == "video" for stream in streams):
        raise GateFail("WAIT_CLEAN_VIDEO_MEDIA_PROBE: playable video stream required")
    return {"status": "PASS", "duration_sec": duration}


def validate_rework_intake(
    data: dict[str, Any],
    base_dir: Path,
    media_probe: Callable[[Path], dict[str, Any]] = probe_media,
) -> dict[str, Any]:
    if data.get("intake_mode") != "clean_video_rework":
        raise GateFail("FAIL_CLEAN_VIDEO_REWORK_INTAKE: intake_mode must be clean_video_rework")
    source_ref = str(data.get("source_short_ref") or "").strip()
    if not source_ref or data.get("derived_from_existing_short") is not True:
        raise GateFail("FAIL_CLEAN_VIDEO_PROVENANCE: existing Short provenance is required")
    raw_path = str(data.get("clean_video_path") or "").strip()
    if not raw_path:
        raise GateFail("FAIL_CLEAN_VIDEO_REWORK_INTAKE: clean_video_path missing")
    supplied = Path(raw_path).expanduser()
    video_path = supplied.resolve() if supplied.is_absolute() else (Path(base_dir) / supplied).resolve()
    if not video_path.is_file() or video_path.stat().st_size <= 0:
        raise GateFail("WAIT_CLEAN_VIDEO_FILE: clean video file missing or empty")
    if video_path.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm"}:
        raise GateFail("FAIL_CLEAN_VIDEO_REWORK_INTAKE: unsupported video extension")
    if data.get("captions_removed") is not True or data.get("text_overlays_removed") is not True:
        raise GateFail("WAIT_CLEAN_VIDEO_REVIEW: caption/text removal is not confirmed")
    if data.get("clean_visual_review_status") != "PASS" or data.get("ocr_overlay_check_status") != "PASS":
        raise GateFail("WAIT_CLEAN_VIDEO_REVIEW: visual and OCR clean checks must PASS")
    probe = media_probe(video_path)
    if not isinstance(probe, dict) or probe.get("status") != "PASS" or float(probe.get("duration_sec") or 0) <= 0:
        raise GateFail("WAIT_CLEAN_VIDEO_MEDIA_PROBE: playable clean video required")
    return {
        "rework_intake_status": "PASS",
        "source_role": "clean_video_rework",
        "source_short_ref": source_ref,
        "clean_video_path": str(video_path),
        "duration_sec": float(probe["duration_sec"]),
        "provenance_preserved": True,
        "rework_allowed": True,
        "treat_as_unrelated_new_source": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--base-dir", default="")
    args = parser.parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    base_dir = Path(args.base_dir).expanduser().resolve() if args.base_dir else manifest_path.parent
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise GateFail("FAIL_CLEAN_VIDEO_REWORK_INTAKE: manifest root must be object")
        result = validate_rework_intake(data, base_dir)
    except (GateFail, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
