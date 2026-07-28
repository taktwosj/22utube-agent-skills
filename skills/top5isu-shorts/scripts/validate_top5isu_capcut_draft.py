#!/usr/bin/env python3
"""Validate the structural locks of a derived top5isu CapCut draft."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, NoReturn


class GateFail(Exception):
    pass


EXPECTED_TRACKS_V1 = ["IMAGE_EFFECT_PRESETS", "TTS", "T2", "T1", "LOGO"]
EXPECTED_TRACKS_V2 = ["IMAGE_EFFECT_PRESETS", "FRAME", "LOGO", "TTS_TEXT", "SOURCE_TEXT", "T2", "T1"]
ALLOWED_AUDIO_TRACKS = {"A_TTS", "A_SOURCE", "A_SFX", "A_BGM"}
HIGH_IMPACT_EFFECTS = {"불꽃 회오리", "불꽃 스와이프", "불꽃 마법"}


def fail(code: str, detail: str) -> NoReturn:
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
    for mirror in sorted((draft_dir / "subdraft").glob("*/draft_content.json")):
        if read_object(mirror) != content:
            fail(
                "FAIL_TOP5ISU_CONTENT_MIRROR",
                f"stale subdraft content: {mirror.relative_to(draft_dir)}",
            )
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
    if names == EXPECTED_TRACKS_V1:
        template_profile = "top5isu_v1"
        expected_tracks = EXPECTED_TRACKS_V1
    elif names[: len(EXPECTED_TRACKS_V2)] == EXPECTED_TRACKS_V2 and all(
        name in ALLOWED_AUDIO_TRACKS for name in names[len(EXPECTED_TRACKS_V2):]
    ):
        template_profile = "top5isu_v2_top55"
        expected_tracks = EXPECTED_TRACKS_V2
    else:
        fail("FAIL_TOP5ISU_TRACK_MAPPING", f"unexpected tracks: {names}")

    image_segments = tracks[0].get("segments") or []
    if template_profile == "top5isu_v1":
        if len(image_segments) != 7:
            fail("FAIL_TOP5ISU_TRACK_MAPPING", "seven image-effect segments required")
        for segment in image_segments:
            y_value = (((segment.get("clip") or {}).get("transform") or {}).get("y"))
            if y_value != -0.15625:
                fail("FAIL_TOP5ISU_COORDINATE_LOCK", f"image JSON y must be -0.15625; got {y_value!r}")
            if not segment.get("extra_material_refs"):
                fail("FAIL_TOP5ISU_TRACK_MAPPING", "image entrance effect missing")
        high_impact_count = 0
    else:
        if not image_segments:
            fail("FAIL_TOP5ISU_TRACK_MAPPING", "one or more image segments required")
        animation_lookup = {
            str(item.get("id")): item
            for item in ((content.get("materials") or {}).get("material_animations") or [])
            if isinstance(item, dict)
        }
        animation_names: list[str] = []
        for segment in image_segments:
            y_value = (((segment.get("clip") or {}).get("transform") or {}).get("y"))
            if y_value != 0.0:
                fail("FAIL_TOP5ISU_COORDINATE_LOCK", f"TOP55 image JSON y must be 0.0; got {y_value!r}")
            names_for_segment: list[str] = []
            for ref in segment.get("extra_material_refs") or []:
                for animation in (animation_lookup.get(str(ref)) or {}).get("animations") or []:
                    name = str(animation.get("name") or "").strip()
                    if name:
                        names_for_segment.append(name)
            if len(names_for_segment) != 1:
                fail(
                    "FAIL_TOP5ISU_IMAGE_TRANSITION_REQUIRED",
                    f"each image requires exactly one transition animation; got {names_for_segment}",
                )
            animation_names.extend(names_for_segment)
        high_impact_count = sum(name in HIGH_IMPACT_EFFECTS for name in animation_names)
        if not 1 <= high_impact_count <= 2:
            fail(
                "FAIL_TOP5ISU_HIGH_IMPACT_EFFECT",
                f"one or two high-impact fire animations required; got {high_impact_count}",
            )

    active_image_ids = {segment.get("material_id") for segment in image_segments}
    videos = content.get("materials", {}).get("videos", [])
    videos_by_id = {str(video.get("id")): video for video in videos if isinstance(video, dict)}
    active_paths = [
        str(video.get("path") or "")
        for video in videos
        if video.get("id") in active_image_ids
    ]
    active_video_segments = 0
    for segment in image_segments:
        material = videos_by_id.get(str(segment.get("material_id"))) or {}
        if str(material.get("type") or "") != "video":
            continue
        active_video_segments += 1
        if material.get("has_audio") is not False:
            fail("FAIL_TOP5ISU_VIDEO_AUDIO_MUTE", "mixed visual video material must have has_audio=false")
        flip = ((segment.get("clip") or {}).get("flip") or {})
        if flip.get("horizontal") is not True:
            fail("FAIL_TOP5ISU_VIDEO_MIRROR", "mixed visual video segment must set clip.flip.horizontal=true")
    if any(
        re.search(r"leehaneul_\d+\.png$", path, re.I) or "top55_sample_image" in path
        for path in active_paths
    ):
        fail("FAIL_TOP5ISU_SAMPLE_MEDIA_REMAINS", "root sample image remains active")

    duration = content.get("duration")
    full_duration_names = ["LOGO"] if template_profile == "top5isu_v1" else ["FRAME", "LOGO"]
    for full_name in full_duration_names:
        full_track = next(track for track in tracks if track.get("name") == full_name)
        full_segments = full_track.get("segments") or []
        observed_duration = ((full_segments[0].get("target_timerange") or {}).get("duration")) if full_segments else None
        if not duration or observed_duration != duration:
            fail("FAIL_TOP5ISU_LOGO_DURATION", f"{full_name} must span project duration")

    speaker_mode = ""
    vocal_isolation_status = ""
    if style_profile == "gunlimbo":
        audio_manifest = audio_manifest or {}
        speaker_mode = str(audio_manifest.get("source_speaker_mode") or "").strip()
        speaker_segments = audio_manifest.get("speaker_segments")
        if speaker_mode == "no_meaningful_source_speech":
            if speaker_segments != []:
                fail("FAIL_SPEAKER_SEGMENT_MUTED", "verified no-speech mode requires an empty speaker_segments list")
            if str(audio_manifest.get("source_dialogue_analysis_status") or "").upper() not in {"NO_DIALOGUE", "NO_SOURCE_DIALOGUE"}:
                fail("FAIL_SPEAKER_SEGMENT_MUTED", "verified no-speech mode requires NO_DIALOGUE analysis")
            if audio_manifest.get("source_cta_reuse") is not False:
                fail("FAIL_SPEAKER_SEGMENT_MUTED", "unapproved source CTA must not be reused")
        else:
            if not isinstance(speaker_segments, list) or not speaker_segments:
                fail("FAIL_SPEAKER_SEGMENT_MUTED", "gunlimbo speaker_segments missing")
            isolation = audio_manifest.get("source_vocal_isolation")
            if not isinstance(isolation, dict):
                fail(
                    "FAIL_VOCAL_ISOLATION_REQUIRED",
                    "meaningful source speech requires full-source vocal isolation before Q clipping",
                )
            assert isinstance(isolation, dict)
            vocal_isolation_status = str(isolation.get("status") or "").upper()
            if vocal_isolation_status != "PASS" or str(isolation.get("policy") or "") != "REQUIRED_WHEN_MIXED_AUDIO":
                fail("FAIL_VOCAL_ISOLATION_REQUIRED", "source vocal isolation policy/status must be locked PASS")
            if str(isolation.get("method") or "") not in {
                "demucs_two_stems",
                "demucs_htdemucs_ft",
                "bs_roformer_vocals",
            }:
                fail("FAIL_VOCAL_ISOLATION_REQUIRED", "approved full-source vocal isolation method required")
            if isolation.get("processed_before_speaker_clip_cut") is not True:
                fail("FAIL_VOCAL_ISOLATION_ORDER", "separate the full source before cutting Q clips")
            if str(isolation.get("q_clips_source") or "") != "vocals_stem":
                fail("FAIL_VOCAL_ISOLATION_Q_SOURCE", "Q clips must be cut only from the vocals stem")
            if isolation.get("original_video_audio_muted") is not True:
                fail("FAIL_VOCAL_ISOLATION_REQUIRED", "original mixed video audio must be muted")
            if str(isolation.get("residual_music_review") or "").upper() != "PASS":
                fail("FAIL_VOCAL_ISOLATION_REQUIRED", "residual music review must pass")
            if str(isolation.get("voice_artifact_review") or "").upper() != "PASS":
                fail("FAIL_VOCAL_ISOLATION_REQUIRED", "voice artifact review must pass")
            assert isinstance(speaker_segments, list)
            for segment in speaker_segments:
                if not isinstance(segment, dict) or segment.get("muted") is not False:
                    fail("FAIL_SPEAKER_SEGMENT_MUTED", "approved speaker segment is muted")
                if segment.get("volume", 1) <= 0:
                    fail("FAIL_SPEAKER_SEGMENT_MUTED", "approved speaker segment volume is zero")
                if str(segment.get("source_stem") or "") != "vocals_stem":
                    fail("FAIL_VOCAL_ISOLATION_Q_SOURCE", "speaker segment must reference vocals_stem")

    return {
        "top5isu_capcut_draft_status": "PASS",
        "template_profile": template_profile,
        "style_profile": style_profile,
        "tracks": list(expected_tracks),
        "image_effect_segments": len(image_segments),
        "high_impact_effect_segments": high_impact_count,
        "source_speaker_mode": speaker_mode,
        "source_vocal_isolation": vocal_isolation_status,
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
