#!/usr/bin/env python3
"""Validate the structural locks of a derived top5isu CapCut draft."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


EXPECTED_TRACKS = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]


def fail(code: str, detail: str) -> None:
    raise GateFail(f"{code}: {detail}")


def read_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        fail("FAIL_TOP5ISU_DRAFT", f"object required: {path}")
    return data


def validate_top5isu_capcut_draft(
    draft_dir: Path,
    style_profile: str,
    audio_manifest: dict[str, Any] | None,
    manual_edit_expected: bool = False,
) -> dict[str, Any]:
    draft_dir = Path(draft_dir)
    content_path = draft_dir / "draft_content.json"
    if not content_path.is_file():
        fail("FAIL_TOP5ISU_DRAFT", "draft_content.json missing")
    content = read_object(content_path)
    if style_profile not in {"top5", "gunlimbo"}:
        fail("FAIL_TOP5ISU_DRAFT", "unknown style profile")
    tracks = content.get("tracks") or []
    if not isinstance(tracks, list) or not tracks or not all(isinstance(track, dict) for track in tracks):
        fail("FAIL_TOP5ISU_DRAFT", "current draft must contain readable tracks")
    names = [track.get("name") for track in tracks]
    canvas = content.get("canvas_config") or {}

    if manual_edit_expected:
        duration = content.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0 or not isinstance(canvas, dict) or not canvas:
            fail("FAIL_TOP5ISU_DRAFT", "current edited draft is unreadable or missing core metadata")
        return {
            "top5isu_capcut_draft_status": "PASS_MANUAL_EDIT_EXPECTED",
            "style_profile": style_profile,
            "current_draft_reread": True,
            "manual_edit_expected": True,
            "manual_edit_difference_is_failure": False,
            "observed_tracks": names,
            "observed_duration": content.get("duration"),
            "observed_canvas": canvas,
            "note": "Operator CapCut edits are expected; snapshot differences are not failures.",
        }

    if canvas.get("width") != 1080 or canvas.get("height") != 1920:
        fail("FAIL_TOP5ISU_DRAFT", "canvas must be 1080x1920")
    if names != EXPECTED_TRACKS:
        fail("FAIL_TOP5ISU_TRACK_MAPPING", f"unexpected tracks: {names}")

    image_segments = tracks[0].get("segments") or []
    if len(image_segments) != 7:
        fail("FAIL_TOP5ISU_TRACK_MAPPING", "seven image-effect segments required")
    for segment in image_segments:
        y_value = (((segment.get("clip") or {}).get("transform") or {}).get("y"))
        if y_value != -0.15625:
            fail("FAIL_TOP5ISU_COORDINATE_LOCK", f"image JSON y must be -0.15625; got {y_value!r}")
        if not segment.get("extra_material_refs"):
            fail("FAIL_TOP5ISU_TRACK_MAPPING", "image entrance effect missing")

    active_image_ids = {segment.get("material_id") for segment in image_segments}
    videos = content.get("materials", {}).get("videos", [])
    active_paths = [
        str(video.get("path") or "")
        for video in videos
        if video.get("id") in active_image_ids
    ]
    if any(re.search(r"leehaneul_\d+\.png$", path, re.I) for path in active_paths):
        fail("FAIL_TOP5ISU_SAMPLE_MEDIA_REMAINS", "root sample image remains active")

    duration = content.get("duration")
    logo_segments = tracks[-1].get("segments") or []
    logo_duration = ((logo_segments[0].get("target_timerange") or {}).get("duration")) if logo_segments else None
    if not duration or logo_duration != duration:
        fail("FAIL_TOP5ISU_LOGO_DURATION", "logo must span project duration")

    if style_profile == "gunlimbo":
        speaker_segments = (audio_manifest or {}).get("speaker_segments")
        if not isinstance(speaker_segments, list) or not speaker_segments:
            fail("FAIL_SPEAKER_SEGMENT_MUTED", "gunlimbo speaker_segments missing")
        for segment in speaker_segments:
            if not isinstance(segment, dict) or segment.get("muted") is not False:
                fail("FAIL_SPEAKER_SEGMENT_MUTED", "approved speaker segment is muted")
            if segment.get("volume", 1) <= 0:
                fail("FAIL_SPEAKER_SEGMENT_MUTED", "approved speaker segment volume is zero")

    return {
        "top5isu_capcut_draft_status": "PASS",
        "style_profile": style_profile,
        "tracks": list(EXPECTED_TRACKS),
        "image_effect_segments": 7,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft_dir")
    parser.add_argument("--style-profile", required=True, choices=("top5", "gunlimbo"))
    parser.add_argument("--audio-manifest", default="")
    parser.add_argument("--manual-edit-expected", action="store_true")
    args = parser.parse_args()
    try:
        audio_manifest = read_object(Path(args.audio_manifest)) if args.audio_manifest else None
        result = validate_top5isu_capcut_draft(
            Path(args.draft_dir),
            args.style_profile,
            audio_manifest,
            manual_edit_expected=args.manual_edit_expected,
        )
    except (GateFail, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
