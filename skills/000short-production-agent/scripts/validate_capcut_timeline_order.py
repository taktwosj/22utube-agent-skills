#!/usr/bin/env python3
"""Fail-closed post-CapCut timeline order gate for 11short remake jobs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


SCENARIO_FIRST_MODES = {
    "scenario_first_montage",
    "scenario_montage",
    "scenario_first",
}

SCENARIO_LIST_KEYS = ("scenario_timeline", "scenario_beats")
CLIP_ASSIGNMENT_KEYS = ("clip_assignments", "visual_assignments", "assignments")
UNUSED_SPLIT_KEYS = ("unused_split_clips", "unused_source_beats", "spare_clips")
FRAMING_ADJUSTMENT_KEYS = ("framing_adjustments", "crop_pan_zoom_plan", "reframe_plan")
SFX_TIMELINE_KEYS = ("sfx_timeline", "sfx_cues", "sfx_assignments")
SFX_MEDIA_BIN_KEYS = ("sfx_media_bin", "sfx_media", "sfx_materials")
ALLOWED_NON_SOURCE_ASSETS = {
    "blank",
    "caption_only",
    "neutral",
    "black",
    "color",
    "still",
    "generated",
}
VIDEO_SOURCE_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
MANDATORY_EFFECT_RANGES = {
    "smart_color_adjust": (0.30, 0.50),
    "clear": (0.30, 0.50),
    "sharpen": (0.30, 0.50),
    "particle": (0.05, 0.30),
}
PARTICLE_CAPCUT_ENCODED_RANGE = (0.008, 0.0505)
MANDATORY_ADJACENT_DIFF_EFFECTS = ("smart_color_adjust", "clear", "sharpen")
MANDATORY_ADJACENT_VALUE_DIFF = 0.05
MANDATORY_LOUDNESS_TARGET = -14.0
MOJIBAKE_PATTERNS = ("????", "\ufffd")
SEMANTIC_VIDEO_TRACK_CONTRACT = "caption_video_plus_situation_speaker_video"
ALLOWED_SEMANTIC_VIDEO_TRACKS = {
    "caption_video",
    "situation_speaker_video",
}
TTS_MIDDLE_TYPES = {
    "tts_script",
    "tts_dialogue",
    "voice_line",
    "narration",
    "plain_caption",
    "verified_speech",
    "source_speech",
}
VISUAL_ONLY_MIDDLE_TYPES = {
    "situation_caption",
    "reaction_caption",
    "emotion_caption",
    "sfx_caption",
    "caption_only",
    "non_script_caption",
    "visual_caption",
}
SCRIPT_ALIGNED_TIMELINE_KEYS = (
    "script_aligned_timeline_structure",
    "script_aligned_timeline",
    "beat_audio_video_map",
    "beat_timeline_map",
)
AUDIO_NORMALIZATION_STATUS_KEYS = (
    "audio_normalization_status",
    "audio_normalize_status",
    "loudness_normalization_status",
)
NORMALIZED_AUDIO_ASSET_KEYS = (
    "normalized_audio_assets",
    "audio_normalized_assets",
    "loudness_normalized_assets",
    "active_normalized_audio_segments",
)
TIMELINE_CONTENT_START_KEYS = (
    "timeline_content_start_sec",
    "content_start_sec",
    "first_content_start_sec",
    "timeline_start_sec",
)
TTS_VISUAL_FILL_STATUS_KEYS = (
    "tts_visual_fill_status",
    "tts_video_fill_status",
    "voice_visual_fill_status",
)
TTS_VISUAL_COVERAGE_KEYS = (
    "visual_coverage_segments",
    "tts_visual_coverage_segments",
    "voice_visual_coverage_segments",
)
THREE_LINE_TEXT_LAYOUT_STATUS_KEYS = (
    "three_line_text_layout_status",
    "three_text_layer_layout_status",
    "text_role_rows_status",
)
TEXT_LAYER_ROLE_KEYS = (
    "text_layer_role",
    "display_text_layer_role",
    "caption_layer_role",
    "text_row_role",
)
TEXT_LAYER_INDEX_KEYS = (
    "text_layer_index",
    "display_text_layer_index",
    "caption_layer_index",
    "text_row_index",
)
TEXT_LAYER_ROLE_TO_INDEX = {
    "line1": 1,
    "line_1": 1,
    "display_line_1": 1,
    "hook_line": 1,
    "dialogue_hook": 1,
    "line1_hook": 1,
    "speaker_quote": 1,
    "source_speech": 1,
    "speaker_dialogue": 1,
    "line2": 2,
    "line_2": 2,
    "display_line_2": 2,
    "situation_line": 2,
    "emotion_line": 2,
    "line2_situation": 2,
    "emotion_situation": 2,
    "situation_emotion": 2,
    "reaction_situation": 2,
    "line3": 3,
    "line_3": 3,
    "display_line_3": 3,
    "tts_line": 3,
    "line3_tts": 3,
    "tts_caption": 3,
    "tts_narration": 3,
    "caption_voice": 3,
}
DISPLAY_TEXT_LINES_KEYS = (
    "display_text_lines",
    "three_line_display",
    "visible_text_lines",
    "onscreen_text_lines",
)
TEXT_TRACK_ORDER_KEYS = (
    "middle_text_track_order_top_to_bottom",
    "text_track_order_top_to_bottom",
    "capcut_text_track_order_top_to_bottom",
)
VIDEO_TRACK_ORDER_KEYS = (
    "video_track_order_top_to_bottom",
    "capcut_video_track_order_top_to_bottom",
)
REQUIRED_TEXT_TRACK_ORDER = (
    "tts",
    "source_speech",
    "situation_emotion",
)
REQUIRED_VIDEO_TRACK_ORDER = (
    "caption_video",
    "situation_speaker_video",
)
TRACK_ROLE_ALIASES = {
    "tts": "tts",
    "tts_caption": "tts",
    "tts_line": "tts",
    "tts_narration": "tts",
    "plain_tts": "tts",
    "plain_caption": "tts",
    "narration": "tts",
    "caption_voice": "tts",
    "middle_script_tts_plain": "tts",
    "source_speech": "source_speech",
    "speaker_quote": "source_speech",
    "source_quote": "source_speech",
    "quoted_source_speech": "source_speech",
    "source_dialogue": "source_speech",
    "speaker_dialogue": "source_speech",
    "verified_speech": "source_speech",
    "situation_emotion": "situation_emotion",
    "situation_caption": "situation_emotion",
    "emotion_caption": "situation_emotion",
    "reaction_caption": "situation_emotion",
    "visual_caption": "situation_emotion",
    "situation_line": "situation_emotion",
    "emotion_line": "situation_emotion",
    "caption_video": "caption_video",
    "tts_video": "caption_video",
    "tts_visual": "caption_video",
    "caption_tts_video": "caption_video",
    "situation_speaker_video": "situation_speaker_video",
    "source_speech_video": "situation_speaker_video",
    "source_dialogue_video": "situation_speaker_video",
    "situation_video": "situation_speaker_video",
    "emotion_video": "situation_speaker_video",
    "speaker_video": "situation_speaker_video",
}
CATCUP_TEMPLATE_MASTERS = {
    "shrt_white_base_v1": {
        "reference_project": "shrt white",
        "accepted_reference_projects": {
            "shrt white",
            "short white",
        },
        "rejected_reference_projects": {
            "260708 short",
            "260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1",
        },
        "track_count": 12,
        "text_track_count": 5,
        "required_role_order": (
            "top_title_1",
            "top_title_2",
            "tts",
            "source_speech_1",
            "situation_emotion",
        ),
        "required_active_roles": {
            "top_title_1",
            "top_title_2",
            "tts",
            "source_speech_1",
            "situation_emotion",
        },
        "draft_text_track_index_order": "descending",
        "frame_keywords": ("white",),
    },
    "insta_white_template_master_v1": {
        "reference_project": "insta white",
        "accepted_reference_projects": {
            "insta white",
            "260625-ig-contortion-top3-urakkai-instagram-tts",
        },
        "rejected_reference_projects": {
            "260625-ig-contortion-top3-urakkai-instagram-tts-fixed",
        },
        "track_count": 10,
        "text_track_count": 4,
        "frame_keywords": ("insta", "white"),
    },
    "insta_white_audio_split_v1": {
        "reference_project": "insta white",
        "accepted_reference_projects": {
            "insta white",
            "260625-ig-contortion-top3-urakkai-instagram-tts",
        },
        "rejected_reference_projects": {
            "260625-ig-contortion-top3-urakkai-instagram-tts-fixed",
        },
        "track_count": 9,
        "text_track_count": 4,
        "frame_keywords": ("insta", "white"),
    },
    "black_template_master_v1": {
        "reference_project": "black",
        "accepted_reference_projects": {"black"},
        "rejected_reference_projects": set(),
        "track_count": 10,
        "text_track_count": 4,
        "frame_keywords": ("black",),
    },
}
CATCUP_LAYOUT_PROFILE_KEYS = (
    "catcup_reference_layout_profile",
    "catcup_layout_profile",
    "catcup_text_template_profile",
)
CATCUP_REFERENCE_PROJECT_KEYS = (
    "catcup_reference_project",
    "catcup_reference_draft_name",
    "reference_capcut_project",
    "instagram_template_master_draft_name",
    "black_template_master_draft_name",
)
CATCUP_TEXT_ROLE_ROWS_KEYS = (
    "catcup_text_role_rows",
    "catcup_text_track_manifest",
    "text_role_rows",
)
CATCUP_ROLE_ORDER_KEYS = (
    "catcup_text_role_order_top_to_bottom",
    "catcup_text_track_role_order_top_to_bottom",
    "text_role_order_top_to_bottom",
)
CATCUP_SOURCE_SPEECH_PRESENT_KEYS = (
    "verified_source_speech_present",
    "source_speech_required",
    "original_dialogue_present",
    "source_dialogue_present",
)
CATCUP_CREATIVE_ADDITIONS_KEYS = (
    "creative_additions_use_tts_or_situation_only",
    "added_lines_tts_or_situation_only",
    "no_invented_source_quotes_for_added_lines",
)
CATCUP_WORD_REWRITE_STATUS_KEYS = (
    "source_word_synonym_rewrite_status",
    "word_rewrite_status",
    "urakkai_word_rewrite_status",
)
CATCUP_DRAFT_CONTENT_KEYS = (
    "capcut_draft_content_path",
    "draft_content_path",
    "actual_draft_content_path",
)
CATCUP_REQUIRED_ROLE_ORDER = (
    "top_title_1",       # T1 = 소제목1
    "top_title_2",       # T2 = 소제목2
    "tts",               # T3 = TTS / 나레이션 자막
    "source_speech_1",   # T4 = 검증된 화자발언1
    "source_speech_2",   # T5 = 검증된 화자발언2
    "situation_emotion", # T6 = (현장상황/행동/감정설명)
)
CATCUP_REQUIRED_ACTIVE_ROLES = {
    "top_title_1",
    "top_title_2",
    "tts",
    "situation_emotion",
}
CATCUP_ROLE_ALIASES = {
    "t1": "top_title_1",
    "T1": "top_title_1",
    "title_1": "top_title_1",
    "title_line_1": "top_title_1",
    "top_line_1": "top_title_1",
    "subtitle_1": "top_title_1",
    "소제목1": "top_title_1",
    "t2": "top_title_2",
    "T2": "top_title_2",
    "title_2": "top_title_2",
    "title_line_2": "top_title_2",
    "top_line_2": "top_title_2",
    "subtitle_2": "top_title_2",
    "소제목2": "top_title_2",
    "t3": "tts",
    "T3": "tts",
    "tts_caption": "tts",
    "tts_narration": "tts",
    "plain_tts": "tts",
    "나레이션자막": "tts",
    "t4": "source_speech_1",
    "T4": "source_speech_1",
    "speaker_quote": "source_speech_1",
    "source_speech": "source_speech_1",
    "source_quote": "source_speech_1",
    "화자발언": "source_speech_1",
    "speaker_quote_1": "source_speech_1",
    "source_speech_1": "source_speech_1",
    "화자발언1": "source_speech_1",
    "verified_speaker_1": "source_speech_1",
    "t5": "source_speech_2",
    "T5": "source_speech_2",
    "speaker_quote_2": "source_speech_2",
    "source_speech_2": "source_speech_2",
    "화자발언2": "source_speech_2",
    "verified_speaker_2": "source_speech_2",
    "t6": "situation_emotion",
    "T6": "situation_emotion",
    "emotion_caption": "situation_emotion",
    "situation_caption": "situation_emotion",
    "reaction_caption": "situation_emotion",
    "감정설명": "situation_emotion",
    "상황설명": "situation_emotion",
    "현장상황": "situation_emotion",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GateFail(f"missing file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise GateFail(f"invalid json: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GateFail(f"json root must be an object: {path}")
    return data


def as_path(root: Path, raw_path: str) -> Path:
    if not raw_path:
        raise GateFail("path is empty")
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return path


def require_file(root: Path, rel_path: str, label: str) -> Path:
    path = as_path(root, rel_path)
    if not path.exists():
        raise GateFail(f"{label} file missing: {path}")
    return path


def status_value(data: dict[str, Any]) -> str:
    for key in ("status", "overall_status", "result", "gate_status", "validation_status"):
        value = data.get(key)
        if isinstance(value, str):
            return value.strip().upper()
    summary = data.get("summary")
    if isinstance(summary, dict):
        value = summary.get("status")
        if isinstance(value, str):
            return value.strip().upper()
    return ""


def require_json_status_pass(root: Path, rel_path: str, label: str) -> dict[str, Any]:
    path = require_file(root, rel_path, label)
    data = load_json(path)
    if status_value(data) != "PASS":
        raise GateFail(f"{label} status must be PASS: {path}")
    return data


def upload_ready_state(contract: dict[str, Any] | None) -> dict[str, Any]:
    user_approved = bool(contract) and contract.get("user_upload_approval") is True
    rights_acknowledged = bool(contract) and contract.get("rights_risk_acknowledged") is True
    allowed = user_approved and rights_acknowledged
    if allowed:
        return {
            "upload_ready_allowed": True,
            "upload_ready": True,
            "upload_ready_reason": "USER_APPROVAL_AND_RIGHTS_CHECK_PRESENT",
        }
    return {
        "upload_ready_allowed": False,
        "upload_ready": False,
        "upload_ready_reason": "WAITING_FOR_USER_APPROVAL_AND_RIGHTS_CHECK",
    }


def require_order(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise GateFail(f"{label} must be a non-empty list")
    for item in value:
        if not isinstance(item, (int, str)):
            raise GateFail(f"{label} items must be int or string values: {value}")
    return value


def first_list(data: dict[str, Any], keys: tuple[str, ...]) -> list[Any] | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list) and value:
            return value
    return None


def first_list_any(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> list[Any] | None:
    for source in sources:
        value = first_list(source, keys)
        if value is not None:
            return value
    return None


def first_value_any(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> Any:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value not in (None, "", [], {}):
                return value
    return None


def normalize_seconds(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if abs(number) > 10000:
        return number / 1_000_000.0
    return number


def range_start_seconds(item: dict[str, Any], prefix: str = "target") -> float | None:
    for key in (f"{prefix}_start_sec", f"{prefix}_start", "start_sec", "start"):
        value = normalize_seconds(item.get(key))
        if value is not None:
            return value
    raw_range = item.get(f"{prefix}_range")
    if isinstance(raw_range, dict):
        for key in ("start_sec", "start"):
            value = normalize_seconds(raw_range.get(key))
            if value is not None:
                return value
    elif isinstance(raw_range, list) and raw_range:
        return normalize_seconds(raw_range[0])
    elif isinstance(raw_range, str) and raw_range.strip():
        text = raw_range.strip().replace("~", "-")
        return normalize_seconds(text.split("-", 1)[0].strip())
    return None


def range_end_seconds(item: dict[str, Any], prefix: str = "target") -> float | None:
    for key in (f"{prefix}_end_sec", f"{prefix}_end", "end_sec", "end"):
        value = normalize_seconds(item.get(key))
        if value is not None:
            return value
    raw_range = item.get(f"{prefix}_range")
    if isinstance(raw_range, dict):
        for key in ("end_sec", "end"):
            value = normalize_seconds(raw_range.get(key))
            if value is not None:
                return value
        start = normalize_seconds(raw_range.get("start_sec") or raw_range.get("start"))
        duration = normalize_seconds(raw_range.get("duration_sec") or raw_range.get("duration"))
        if start is not None and duration is not None:
            return start + duration
    elif isinstance(raw_range, list) and len(raw_range) >= 2:
        return normalize_seconds(raw_range[1])
    elif isinstance(raw_range, str) and raw_range.strip():
        parts = raw_range.strip().replace("~", "-").split("-", 1)
        if len(parts) == 2:
            return normalize_seconds(parts[1].strip())
    return None


def range_bounds_seconds(item: dict[str, Any], prefix: str = "target") -> tuple[float, float] | None:
    start = range_start_seconds(item, prefix)
    end = range_end_seconds(item, prefix)
    if start is None or end is None:
        return None
    if end < start:
        raise GateFail(f"{prefix}_range end must be after start")
    return start, end


def ranges_cover_target(
    required_range: tuple[float, float],
    segments: list[Any],
    label: str,
    tolerance: float = 0.05,
) -> bool:
    start, end = required_range
    ranges: list[tuple[float, float]] = []
    for idx, raw_segment in enumerate(segments):
        if not isinstance(raw_segment, dict):
            raise GateFail(f"{label}[{idx}] must be an object")
        bounds = range_bounds_seconds(raw_segment, "target")
        if bounds is None:
            raise GateFail(f"{label}[{idx}] must include target_range")
        if not first_item_value(
            raw_segment,
            ("video_segment_id", "visual_segment_id", "source_video_segment_id", "clip_segment_id", "asset_type"),
        ):
            raise GateFail(f"{label}[{idx}] must reference a visual/video segment")
        ranges.append(bounds)
    if not ranges:
        return False
    ranges.sort(key=lambda item: item[0])
    cursor = start
    for seg_start, seg_end in ranges:
        if seg_end <= cursor + tolerance:
            continue
        if seg_start > cursor + tolerance:
            return False
        cursor = max(cursor, seg_end)
        if cursor >= end - tolerance:
            return True
    return cursor >= end - tolerance


def require_audio_stream(path: Path, label: str) -> None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "json",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError as exc:
        raise GateFail(f"ffprobe is required to verify {label} audio stream") from exc
    if proc.returncode != 0:
        raise GateFail(f"ffprobe failed while checking {label}: {proc.stderr.strip()}")
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise GateFail(f"ffprobe returned invalid json for {label}") from exc
    streams = data.get("streams")
    if not isinstance(streams, list) or not streams:
        raise GateFail(f"{label} must include an audio stream")


def item_id(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def item_role(item: dict[str, Any]) -> str:
    for key in ("beat_role", "role", "type"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def item_text(item: dict[str, Any]) -> str:
    for key in (
        "middle_text",
        "caption",
        "text",
        "script",
        "line",
        "tts_line",
        "narration",
        "visible_text",
    ):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def middle_text_type(item: dict[str, Any]) -> str:
    for key in ("middle_text_type", "caption_type", "text_type", "line_type"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def is_parenthesized_text(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("(") and stripped.endswith(")")


def is_quoted_text(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith('"') and stripped.endswith('"')


def middle_text_color(item: dict[str, Any]) -> str:
    for key in ("text_color_role", "text_color", "font_color", "color", "caption_color"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def is_white_color(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {
        "white",
        "흰색",
        "하얀색",
        "#fff",
        "#ffffff",
        "rgb(255,255,255)",
        "rgb(255, 255, 255)",
        "tts_white",
    }


def validate_middle_caption_type(item: dict[str, Any], label: str) -> None:
    caption_type = middle_text_type(item)
    if not caption_type:
        return
    text = item_text(item)
    color = middle_text_color(item)
    if not color:
        raise GateFail(f"{label} must include text_color_role/text_color")
    if caption_type in VISUAL_ONLY_MIDDLE_TYPES:
        if text and not is_parenthesized_text(text):
            raise GateFail(
                f"{label} visual-only middle text must be parenthesized, e.g. (퍽)"
            )
        if is_white_color(color):
            raise GateFail(f"{label} visual-only middle text must not be white")
        if item.get("include_in_tts") is True and not item.get("tts_exception_reason"):
            raise GateFail(
                f"{label} visual-only middle text cannot be included in TTS "
                "without tts_exception_reason"
            )
        return
    if caption_type in TTS_MIDDLE_TYPES:
        if caption_type in {"verified_speech", "source_speech"} and text and not is_quoted_text(text):
            raise GateFail(f"{label} verified/source speech should use quoted text")
        if is_quoted_text(text) or caption_type in {"verified_speech", "source_speech"}:
            if is_white_color(color):
                raise GateFail(f"{label} quoted speaker utterance must not be white")
        elif not is_white_color(color):
            raise GateFail(f"{label} plain TTS/narration middle text must be white")
        return
    raise GateFail(f"{label} unsupported middle_text_type: {caption_type}")


def has_time_range(item: dict[str, Any], prefix: str) -> bool:
    if item.get(f"{prefix}_range"):
        return True
    start = item.get(f"{prefix}_start")
    end = item.get(f"{prefix}_end")
    if start not in (None, "") and end not in (None, ""):
        return True
    if prefix == "target" and item.get("start") not in (None, "") and item.get("end") not in (None, ""):
        return True
    return False


def get_list_or_fail(
    primary: dict[str, Any],
    secondary: dict[str, Any] | None,
    keys: tuple[str, ...],
    label: str,
) -> list[Any]:
    value = first_list(primary, keys)
    if value is None and secondary is not None:
        value = first_list(secondary, keys)
    if not isinstance(value, list) or not value:
        raise GateFail(f"{label} must be a non-empty list")
    return value


def get_list_optional(
    primary: dict[str, Any],
    secondary: dict[str, Any] | None,
    keys: tuple[str, ...],
) -> list[Any]:
    value = first_list(primary, keys)
    if value is None and secondary is not None:
        value = first_list(secondary, keys)
    if value is None:
        return []
    if not isinstance(value, list):
        raise GateFail(f"{keys[0]} must be a list")
    return value


def scenario_beat_id(item: dict[str, Any]) -> Any:
    return item_id(
        item,
        ("scenario_beat_id", "target_beat_id", "beat_id", "id"),
    )


def assignment_uses_source(item: dict[str, Any]) -> bool:
    if has_time_range(item, "source"):
        return True
    return item_id(
        item,
        ("source_beat_id", "source_beat", "source_id", "source_segment_id"),
    ) not in (None, "")


def assignment_asset_type(item: dict[str, Any]) -> str:
    for key in ("asset_type", "visual_type"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def script_beat_id(item: dict[str, Any]) -> Any:
    return item_id(
        item,
        (
            "script_beat_id",
            "scenario_beat_id",
            "target_beat_id",
            "beat_id",
            "id",
        ),
    )


def first_item_value(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def parse_order_items(value: Any, label: str) -> list[str]:
    if isinstance(value, str):
        raw_items = [
            part.strip()
            for part in value.replace(">", ",").replace("|", ",").split(",")
            if part.strip()
        ]
    elif isinstance(value, list):
        raw_items = [str(item).strip() for item in value if str(item).strip()]
    else:
        raise GateFail(f"{label} must be a list or a delimited string")
    if not raw_items:
        raise GateFail(f"{label} must not be empty")
    return raw_items


def parse_track_order(value: Any, label: str) -> list[str]:
    raw_items = parse_order_items(value, label)
    normalized: list[str] = []
    for raw_item in raw_items:
        key = raw_item.strip().lower().replace(" ", "_").replace("-", "_")
        role = TRACK_ROLE_ALIASES.get(key)
        if role is None:
            raise GateFail(f"{label} has unsupported role: {raw_item}")
        normalized.append(role)
    return normalized


def normalize_catcup_role(raw_role: Any) -> str:
    role = str(raw_role or "").strip()
    if not role:
        return ""
    return CATCUP_ROLE_ALIASES.get(role, role)


def parse_catcup_role_order(
    value: Any,
    label: str,
    allowed_roles: tuple[str, ...] = CATCUP_REQUIRED_ROLE_ORDER,
) -> list[str]:
    allowed = set(allowed_roles)
    normalized: list[str] = []
    for raw_item in parse_order_items(value, label):
        role = normalize_catcup_role(raw_item)
        if role not in allowed:
            raise GateFail(f"{label} has unsupported CatCup role: {raw_item}")
        normalized.append(role)
    return normalized


def catcup_row_active(row: dict[str, Any]) -> bool:
    if row.get("active") is False:
        return False
    status = str(row.get("status") or row.get("row_status") or "").strip().upper()
    return status not in {"N/A", "NA", "INACTIVE", "OFF", "DISABLED"}


def catcup_source_speech_present(sources: list[dict[str, Any]]) -> bool:
    raw = first_value_any(sources, CATCUP_SOURCE_SPEECH_PRESENT_KEYS)
    return truthy(raw)


def validate_catcup_script_rewrite_policy(sources: list[dict[str, Any]]) -> dict[str, Any]:
    creative_raw = first_value_any(sources, CATCUP_CREATIVE_ADDITIONS_KEYS)
    if not truthy(creative_raw):
        raise GateFail(
            "timeline manifest creative additions must use TTS/plain narration or situation_emotion captions only; do not invent source quotes"
        )
    word_status = str(first_value_any(sources, CATCUP_WORD_REWRITE_STATUS_KEYS) or "").strip().upper()
    if word_status != "PASS":
        raise GateFail(
            "timeline manifest source_word_synonym_rewrite_status must be PASS; rewrite source words with different synonyms except verified quotes, names, numbers, or unavoidable nouns"
        )
    return {
        "creative_additions_use_tts_or_situation_only": True,
        "source_word_synonym_rewrite_status": "PASS",
    }


def load_draft_content_for_catcup(
    root: Path,
    timeline_manifest: dict[str, Any],
    contract: dict[str, Any] | None,
    draft_path: str,
) -> dict[str, Any]:
    sources = [timeline_manifest]
    if contract is not None:
        sources.append(contract)
    raw_path = first_value_any(sources, CATCUP_DRAFT_CONTENT_KEYS)
    candidates: list[Path] = []
    if raw_path:
        candidates.append(as_path(root, str(raw_path)))
    candidates.append(root / "capcut" / "draft_content.json")
    if draft_path:
        candidates.append(as_path(root, draft_path) / "draft_content.json")

    for candidate in candidates:
        if candidate.exists():
            return load_json(candidate)
    raise GateFail("catcup reference layout requires actual draft_content.json for post-CapCut validation")


def material_text_map(draft: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    materials = draft.get("materials") or {}
    for raw_text in materials.get("texts", []) or []:
        if not isinstance(raw_text, dict):
            continue
        text_id = raw_text.get("id") or raw_text.get("material_id") or raw_text.get("uid")
        if not text_id:
            continue
        content = raw_text.get("content") or raw_text.get("text") or raw_text.get("text_content") or ""
        if isinstance(content, str) and content.strip().startswith("{"):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    content = parsed.get("text") or parsed.get("content") or content
            except json.JSONDecodeError:
                pass
        result[str(text_id)] = str(content)
    return result


def validate_korean_text_fast_gate(draft: dict[str, Any]) -> dict[str, Any]:
    hits: list[str] = []
    for text_id, text in material_text_map(draft).items():
        if any(pattern in text for pattern in MOJIBAKE_PATTERNS):
            hits.append(str(text_id))

    if hits:
        sample = ", ".join(hits[:5])
        raise GateFail(
            "KOREAN_TEXT_FAST_GATE failed: draft_content.json text scan found "
            f"mojibake in text material(s): {sample}"
        )
    return {
        "korean_text_fast_gate": "PASS",
        "mojibake_pattern_fail": "PASS",
    }


def draft_track_info(draft: dict[str, Any], track_id: str) -> tuple[int, dict[str, Any]]:
    for idx, track in enumerate(draft.get("tracks", []) or []):
        if not isinstance(track, dict):
            continue
        if str(track.get("id") or track.get("name") or "") == track_id:
            return idx, track
    raise GateFail(f"catcup text role track_id not found in actual draft: {track_id}")


def draft_track_texts(draft: dict[str, Any], track_id: str) -> list[str]:
    text_map = material_text_map(draft)
    _, track = draft_track_info(draft, track_id)
    track_type = str(track.get("type") or track.get("track_type") or "").lower()
    if track_type and track_type != "text":
        raise GateFail(f"CapCut T-track {track_id} must be type=text, got {track_type}")
    texts: list[str] = []
    for segment in track.get("segments", []) or []:
        if not isinstance(segment, dict):
            continue
        material_id = segment.get("material_id") or segment.get("materialId")
        if material_id in text_map:
            texts.append(text_map[material_id])
        else:
            raise GateFail(f"CapCut T-track {track_id} contains non-text or unknown material segment")
    return texts


def all_visible_text_values(draft: dict[str, Any]) -> list[str]:
    text_map = material_text_map(draft)
    values: list[str] = []
    for track in draft.get("tracks", []) or []:
        if not isinstance(track, dict):
            continue
        track_type = str(track.get("type") or track.get("track_type") or "").lower()
        if track_type != "text":
            continue
        for segment in track.get("segments", []) or []:
            if not isinstance(segment, dict):
                continue
            material_id = segment.get("material_id") or segment.get("materialId")
            if material_id in text_map:
                values.append(text_map[material_id])
    return values


def draft_folder_for_template_check(
    root: Path,
    sources: list[dict[str, Any]],
    draft_path: str,
) -> Path:
    candidates: list[Path] = []
    if draft_path:
        raw = as_path(root, draft_path)
        candidates.append(raw if raw.is_dir() else raw.parent)
    raw_content_path = first_value_any(sources, CATCUP_DRAFT_CONTENT_KEYS)
    if raw_content_path:
        raw = as_path(root, str(raw_content_path))
        candidates.append(raw.parent if raw.name == "draft_content.json" else raw)

    for candidate in candidates:
        if (candidate / "draft_content.json").exists():
            return candidate
    raise GateFail("Instagram template master check requires the actual registered CapCut draft folder")


def material_path_values(draft: dict[str, Any]) -> list[str]:
    materials = draft.get("materials") or {}
    values: list[str] = []
    for collection_name in ("videos", "audios", "images", "stickers"):
        for material in materials.get(collection_name, []) or []:
            if not isinstance(material, dict):
                continue
            path = material.get("path")
            if isinstance(path, str) and path:
                values.append(path)
    return values


def normalize_capcut_percent_value(raw: Any) -> float | None:
    if not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    if 1.0 < value <= 100.0:
        return value / 100.0
    return value


def material_path_or_name(material: dict[str, Any]) -> str:
    return str(
        material.get("path")
        or material.get("material_name")
        or material.get("name")
        or ""
    )


def is_source_video_material(material: dict[str, Any]) -> bool:
    material_type = str(material.get("type") or "").lower()
    if material_type == "photo":
        return False
    path = material_path_or_name(material).lower().replace("\\", "/")
    return material_type == "video" or Path(path).suffix.lower() in VIDEO_SOURCE_EXTENSIONS


def video_material_has_quality_hd(material: dict[str, Any]) -> bool:
    algorithm = material.get("video_algorithm") or {}
    quality = algorithm.get("quality_enhance")
    if not isinstance(quality, dict):
        return False
    level = quality.get("level")
    if isinstance(level, str):
        if level.strip().upper() != "HD":
            return False
    elif level not in (0, 0.0):
        return False
    algorithms = algorithm.get("algorithms") or []
    return any(
        isinstance(item, dict)
        and str(item.get("type") or "").lower() == "qualityenhance"
        for item in algorithms
    )


def enabled_loudness_normalize_present(materials: dict[str, Any]) -> bool:
    for item in materials.get("loudnesses") or []:
        if not isinstance(item, dict) or item.get("enable") is not True:
            continue
        target = item.get("target_loudness")
        if isinstance(target, (int, float)) and abs(float(target) - MANDATORY_LOUDNESS_TARGET) <= 0.2:
            return True
    return False


def draft_has_active_audio(draft: dict[str, Any], video_materials: dict[str, dict[str, Any]]) -> bool:
    for track in draft.get("tracks") or []:
        track_type = str(track.get("type") or track.get("track_type") or "").lower()
        if track_type == "audio" and track.get("segments"):
            return True
        if track_type != "video":
            continue
        for segment in track.get("segments") or []:
            material = video_materials.get(segment.get("material_id")) or {}
            if material.get("has_audio") is True and float(segment.get("volume", 1.0) or 0.0) > 0.01:
                return True
    return False


def segment_effect_values(
    segment: dict[str, Any],
    effect_materials: dict[str, dict[str, Any]],
) -> dict[str, float]:
    values: dict[str, float] = {}
    for ref in segment.get("extra_material_refs") or []:
        effect = effect_materials.get(ref)
        if not effect:
            continue
        effect_type = str(effect.get("type") or effect.get("name") or "").strip().lower()
        if effect_type not in MANDATORY_EFFECT_RANGES:
            continue
        value = normalize_capcut_percent_value(effect.get("value"))
        if value is not None:
            values[effect_type] = value
    return values


def mandatory_effect_value_in_range(effect_type: str, value: float) -> bool:
    minimum, maximum = MANDATORY_EFFECT_RANGES[effect_type]
    if minimum <= value <= maximum:
        return True
    if effect_type == "particle":
        encoded_minimum, encoded_maximum = PARTICLE_CAPCUT_ENCODED_RANGE
        return encoded_minimum <= value <= encoded_maximum
    return False


def validate_mandatory_capcut_media_settings(draft: dict[str, Any]) -> dict[str, Any]:
    materials = draft.get("materials") or {}
    video_materials = {
        item.get("id"): item
        for item in materials.get("videos", []) or []
        if isinstance(item, dict) and item.get("id")
    }
    effect_materials = {
        item.get("id"): item
        for item in materials.get("effects", []) or []
        if isinstance(item, dict) and item.get("id")
    }

    source_segments: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for track in draft.get("tracks") or []:
        if str(track.get("type") or track.get("track_type") or "").lower() != "video":
            continue
        for segment in track.get("segments") or []:
            if not isinstance(segment, dict):
                continue
            material = video_materials.get(segment.get("material_id"))
            if material and is_source_video_material(material):
                source_segments.append((segment, material))

    if not source_segments:
        raise GateFail("mandatory CapCut media settings require at least one source video segment")

    if draft_has_active_audio(draft, video_materials) and not enabled_loudness_normalize_present(materials):
        raise GateFail("CapCut audio loudness normalize must be ON at -14 LUFS")

    per_segment_values: list[dict[str, float]] = []
    for index, (segment, material) in enumerate(source_segments):
        if not video_material_has_quality_hd(material):
            raise GateFail(f"source video segment {index} must use QualityEnhance HD")
        values = segment_effect_values(segment, effect_materials)
        if segment.get("enable_smart_color_adjust") is not True:
            raise GateFail(f"source video segment {index} must enable smart_color_adjust")
        for effect_type, (minimum, maximum) in MANDATORY_EFFECT_RANGES.items():
            if effect_type not in values:
                raise GateFail(f"source video segment {index} missing mandatory {effect_type} effect")
            value = values[effect_type]
            if not mandatory_effect_value_in_range(effect_type, value):
                raise GateFail(
                    f"source video segment {index} {effect_type} must be "
                    f"{minimum * 100:.0f}-{maximum * 100:.0f}, got {value * 100:.1f}"
                )
        per_segment_values.append(values)

    if len(per_segment_values) > 1:
        for index in range(1, len(per_segment_values)):
            previous = per_segment_values[index - 1]
            current = per_segment_values[index]
            for effect_type in MANDATORY_ADJACENT_DIFF_EFFECTS:
                if abs(current[effect_type] - previous[effect_type]) < MANDATORY_ADJACENT_VALUE_DIFF:
                    raise GateFail(
                        f"{effect_type} values for adjacent source video segments must differ by at least 5"
                    )

    return {
        "mandatory_capcut_media_settings_status": "PASS",
        "mandatory_capcut_source_video_segment_count": len(source_segments),
        "mandatory_capcut_quality_enhance": "HD",
        "mandatory_capcut_loudness_normalize": "ON_-14_LUFS",
        "mandatory_capcut_effect_ranges": {
            key: [int(minimum * 100), int(maximum * 100)]
            for key, (minimum, maximum) in MANDATORY_EFFECT_RANGES.items()
        },
        "mandatory_capcut_particle_encoded_range": [
            round(PARTICLE_CAPCUT_ENCODED_RANGE[0], 4),
            round(PARTICLE_CAPCUT_ENCODED_RANGE[1], 4),
        ],
    }


def validate_catcup_template_master_actual(
    root: Path,
    sources: list[dict[str, Any]],
    draft: dict[str, Any],
    draft_path: str,
    template: dict[str, Any],
) -> dict[str, Any]:
    draft_dir = draft_folder_for_template_check(root, sources, draft_path)
    if draft_dir.name.endswith("-fixed") or "-fixed" in draft_dir.name:
        raise GateFail("CapCut template basis must not be a -fixed draft")

    for filename in ("draft_content.json", "draft_meta_info.json", "draft_virtual_store.json"):
        load_json(draft_dir / filename)

    resources_combination = draft_dir / "Resources" / "combination"
    if not (draft_dir / "subdraft").exists():
        raise GateFail("CapCut template master draft must preserve subdraft")
    if not resources_combination.exists() or not any(resources_combination.iterdir()):
        raise GateFail("CapCut template master draft must preserve Resources/combination")

    tracks = draft.get("tracks", []) or []
    text_track_count = sum(
        1
        for track in tracks
        if isinstance(track, dict)
        and str(track.get("type") or track.get("track_type") or "").lower() == "text"
    )
    if len(tracks) != template["track_count"]:
        raise GateFail(
            f"CapCut template master draft must keep the {template['track_count']}-track structure"
        )
    if text_track_count != template["text_track_count"]:
        raise GateFail(
            f"CapCut template master draft must keep {template['text_track_count']} editable text tracks"
        )

    materials = draft.get("materials") or {}
    if not materials.get("drafts"):
        raise GateFail("CapCut template master draft must preserve materials.drafts")

    placeholder_texts = {"Default", "T1", "T2"}
    visible_placeholders = [
        text for text in all_visible_text_values(draft)
        if text.strip() in placeholder_texts
    ]
    if visible_placeholders:
        raise GateFail(
            "CapCut template draft contains visible placeholder text: "
            + ", ".join(sorted(set(visible_placeholders)))
        )

    video_materials = [
        material for material in materials.get("videos", []) or []
        if isinstance(material, dict)
    ]
    has_template_frame = any(
        any(
            keyword in str(
                material.get("path") or material.get("material_name") or material.get("name") or ""
            ).lower()
            for keyword in template["frame_keywords"]
        )
        or "frame" in str(material.get("path") or material.get("material_name") or material.get("name") or "").lower()
        or str(material.get("type") or "").lower() == "photo"
        for material in video_materials
    )
    if not has_template_frame:
        raise GateFail("CapCut template draft must keep the template frame media")

    has_source_mp4 = False
    has_placeholder_source = False
    for material in video_materials:
        path = str(material.get("path") or "")
        name = str(material.get("material_name") or material.get("name") or "")
        normalized_path = path.lower().replace("\\", "/")
        normalized_name = name.lower()
        if normalized_path.endswith("source.mp4") or normalized_name == "source.mp4":
            if path and not path.startswith("##_draftpath_placeholder"):
                if not Path(path).exists():
                    raise GateFail(f"CapCut source.mp4 material path is missing: {path}")
            has_source_mp4 = True
        if normalized_path.endswith("test.mp4") or normalized_name == "test.mp4":
            if path and not path.startswith("##_draftpath_placeholder"):
                if not Path(path).exists():
                    raise GateFail(f"CapCut template placeholder test.mp4 path is missing: {path}")
            has_placeholder_source = True
    if not (has_source_mp4 or has_placeholder_source):
        raise GateFail("CapCut template draft must keep source.mp4 or test.mp4 source placeholder media")

    placeholder_paths = [
        path for path in material_path_values(draft)
        if path.startswith("##_draftpath_placeholder")
    ]
    portable_flag = first_value_any(sources, ("portable_bundle", "capcut_portable_bundle", "cross_machine_portable"))
    if placeholder_paths and truthy(portable_flag):
        raise GateFail("CapCut draft cannot claim portable_bundle=true while placeholder media paths remain")

    return {
        "catcup_template_master_status": "PASS",
        "catcup_template_master_draft_name": template["reference_project"],
        "catcup_template_master_actual_draft_dir": str(draft_dir),
        "catcup_template_track_count": len(tracks),
        "catcup_template_text_track_count": text_track_count,
        "catcup_template_material_drafts_count": len(materials.get("drafts") or []),
        "catcup_template_subdraft": True,
        "catcup_template_resources_combination": True,
        "catcup_template_frame": True,
        "catcup_source_mp4_material_present": has_source_mp4,
        "catcup_placeholder_source_material_present": has_placeholder_source,
        "catcup_source_or_placeholder_material_present": has_source_mp4 or has_placeholder_source,
        "portable_bundle": not bool(placeholder_paths),
        "placeholder_media_path_count": len(placeholder_paths),
    }


def is_situation_emotion_text(text: str) -> bool:
    value = text.strip()
    compact = "".join(value.split())
    if not value:
        return True
    if is_parenthesized_text(value):
        return True
    if any(token in value for token in ("ㅋ", "ㅎ", "ㅠ", "?", "!", "…")):
        return True
    if len(compact) <= 24 and ("." in value or "," in value):
        return True
    return False


def validate_catcup_role_texts(role: str, texts: list[str]) -> None:
    if role in {"top_title_1", "top_title_2"}:
        if len([t for t in texts if t.strip()]) != 1:
            raise GateFail(f"{role} must be one full-duration title text segment")
    if role == "tts":
        bad = [t for t in texts if is_quoted_text(t.strip()) or is_parenthesized_text(t.strip())]
        if bad:
            raise GateFail("tts row must contain plain narration/TTS text, not quotes or parenthesized captions")
    if role.startswith("source_speech"):
        bad = [t for t in texts if t.strip() and not is_quoted_text(t.strip())]
        if bad:
            raise GateFail("source_speech rows must contain verified quoted speech text only")
    if role == "situation_emotion":
        bad = [
            t for t in texts
            if t.strip()
            and not is_situation_emotion_text(t)
        ]
        if bad:
            raise GateFail("situation_emotion row must contain parenthesized or short reaction/emotion captions")


def validate_catcup_reference_layout_actual(
    root: Path,
    timeline_manifest: dict[str, Any],
    contract: dict[str, Any] | None,
    draft_path: str,
) -> dict[str, Any]:
    sources = [timeline_manifest]
    if contract is not None:
        sources.append(contract)
    script_rewrite_result = validate_catcup_script_rewrite_policy(sources)

    profile = str(first_value_any(sources, CATCUP_LAYOUT_PROFILE_KEYS) or "").strip()
    template = CATCUP_TEMPLATE_MASTERS.get(profile)
    if template is None:
        raise GateFail(
            "timeline manifest catcup_reference_layout_profile must be one of "
            f"{sorted(CATCUP_TEMPLATE_MASTERS)}"
        )

    reference_project = str(first_value_any(sources, CATCUP_REFERENCE_PROJECT_KEYS) or "").strip()
    if reference_project in template["rejected_reference_projects"]:
        raise GateFail("timeline manifest catcup_reference_project must not use a rejected template draft")
    if reference_project not in template["accepted_reference_projects"]:
        raise GateFail(
            "timeline manifest catcup_reference_project must be "
            f"{template['reference_project']}"
        )
    required_role_order = tuple(template.get("required_role_order", CATCUP_REQUIRED_ROLE_ORDER))
    required_active_roles = set(template.get("required_active_roles", CATCUP_REQUIRED_ACTIVE_ROLES))

    rows = first_list_any(sources, CATCUP_TEXT_ROLE_ROWS_KEYS)
    if not rows:
        raise GateFail("timeline manifest must include catcup_text_role_rows")

    order_raw = first_value_any(sources, CATCUP_ROLE_ORDER_KEYS)
    if order_raw not in (None, ""):
        declared_order = parse_catcup_role_order(
            order_raw,
            "catcup_text_role_order_top_to_bottom",
            required_role_order,
        )
    else:
        declared_order = []

    draft = load_draft_content_for_catcup(root, timeline_manifest, contract, draft_path)
    korean_text_result = validate_korean_text_fast_gate(draft)
    active_roles: list[str] = []
    active_track_ids: dict[str, str] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise GateFail(f"timeline catcup_text_role_rows[{idx}] must be an object")
        role = normalize_catcup_role(
            row.get("role")
            or row.get("text_role")
            or row.get("track_role")
            or row.get("caption_role")
        )
        if role not in required_role_order:
            raise GateFail(f"timeline catcup_text_role_rows[{idx}] has invalid role: {role or '<empty>'}")
        if not catcup_row_active(row):
            continue
        track_id = str(row.get("track_id") or row.get("actual_track_id") or row.get("capcut_track_id") or "").strip()
        if not track_id:
            raise GateFail(f"active catcup role {role} must include actual track_id")
        if track_id in active_track_ids.values():
            raise GateFail("active catcup roles must not share the same CapCut text track")
        texts = draft_track_texts(draft, track_id)
        if not texts:
            raise GateFail(f"active catcup role {role} has no text segments in actual draft")
        validate_catcup_role_texts(role, texts)
        active_roles.append(role)
        active_track_ids[role] = track_id

    missing = required_active_roles - set(active_roles)
    if missing:
        raise GateFail(f"actual draft missing active catcup required roles: {sorted(missing)}")
    if catcup_source_speech_present(sources) and "source_speech_1" not in active_roles:
        raise GateFail("verified source/original dialogue exists, so actual source_speech_1 row must be active")
    if "source_speech_2" in active_roles and "source_speech_1" not in active_roles:
        raise GateFail("source_speech_2 cannot be active without source_speech_1")

    ordered_active = [role for role in (declared_order or active_roles) if role in active_roles]
    canonical_positions = {role: idx for idx, role in enumerate(required_role_order)}
    if ordered_active != sorted(ordered_active, key=lambda role: canonical_positions[role]):
        raise GateFail(
            "actual catcup text rows must follow CapCut profile row order: "
            + " > ".join(required_role_order)
        )

    # Re-check actual draft_content.json track order after audio insertion.
    draft_text_track_positions = []
    for role in ordered_active:
        track_id = active_track_ids.get(role)
        if not track_id:
            continue
        track_index, track = draft_track_info(draft, track_id)
        track_type = str(track.get("type") or track.get("track_type") or "").lower()
        if track_type and track_type != "text":
            raise GateFail(f"actual CapCut role {role} must stay on a text/T-track, got {track_type}")
        draft_text_track_positions.append((role, track_index))
    track_indices = [idx for _, idx in draft_text_track_positions]
    expected_track_indices = sorted(
        track_indices,
        reverse=template.get("draft_text_track_index_order") == "descending",
    )
    if track_indices != expected_track_indices:
        raise GateFail("actual draft_content.json T-track order changed after audio insertion")

    template_master_result = validate_catcup_template_master_actual(
        root,
        sources,
        draft,
        draft_path,
        template,
    )

    return {
        "catcup_reference_layout_status": "PASS",
        "catcup_reference_layout_profile": profile,
        "catcup_reference_project": template["reference_project"],
        "catcup_active_text_role_count": len(active_roles),
        "catcup_active_text_roles": active_roles,
        "catcup_active_track_ids": active_track_ids,
        **template_master_result,
        **script_rewrite_result,
        **korean_text_result,
    }


def require_track_order(
    sources: list[dict[str, Any]],
    keys: tuple[str, ...],
    required: tuple[str, ...],
    label: str,
) -> list[str]:
    raw_value = first_value_any(sources, keys)
    if raw_value in (None, "", [], {}):
        raise GateFail(f"{label} is required")
    order = parse_track_order(raw_value, label)
    if order != list(required):
        raise GateFail(f"{label} must be {list(required)}, got {order}")
    return order


def truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "complete", "completed"}
    return False


def truthy_item(item: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return truthy(first_item_value(item, keys))


def text_layer_role(item: dict[str, Any]) -> str:
    value = first_item_value(item, TEXT_LAYER_ROLE_KEYS)
    if isinstance(value, str):
        return value.strip()
    return ""


def text_layer_index(item: dict[str, Any]) -> int | None:
    value = first_item_value(item, TEXT_LAYER_INDEX_KEYS)
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise GateFail("text layer index must be an integer") from exc


def validate_text_layer_assignment(
    raw_item: dict[str, Any],
    label: str,
    text: str,
    caption_type: str,
    quoted: bool,
    parenthesized: bool,
    plain_voice: bool,
) -> None:
    lines = first_list(raw_item, DISPLAY_TEXT_LINES_KEYS)
    if lines is not None:
        seen: set[int] = set()
        for idx, line_item in enumerate(lines):
            if not isinstance(line_item, dict):
                raise GateFail(f"{label}.display_text_lines[{idx}] must be an object")
            raw_index = first_item_value(
                line_item,
                ("line_index", "row", "line", "index", *TEXT_LAYER_INDEX_KEYS),
            )
            try:
                line_index = int(raw_index)
            except (TypeError, ValueError) as exc:
                raise GateFail(f"{label}.display_text_lines[{idx}] must include line_index 1..3") from exc
            if line_index not in {1, 2, 3}:
                raise GateFail(f"{label}.display_text_lines[{idx}] line_index must be 1, 2, or 3")
            if line_index in seen:
                raise GateFail(f"{label}.display_text_lines duplicate line_index: {line_index}")
            seen.add(line_index)
        return
    role = text_layer_role(raw_item)
    index = text_layer_index(raw_item)
    normalized_role = role.strip().lower()
    if not normalized_role and index is None:
        raise GateFail(f"{label} must include display line info: text_layer_role/text_layer_index or display_text_lines")
    if normalized_role:
        actual_index = TEXT_LAYER_ROLE_TO_INDEX.get(normalized_role)
        if actual_index not in {1, 2, 3}:
            raise GateFail(f"{label} text_layer_role must map to display line 1, 2, or 3")
    if index is not None and index not in {1, 2, 3}:
        raise GateFail(f"{label} text_layer_index must be 1, 2, or 3")


def validate_manifest_three_line_text_layout(timeline_manifest: dict[str, Any]) -> dict[str, Any]:
    status = str(first_value_any([timeline_manifest], THREE_LINE_TEXT_LAYOUT_STATUS_KEYS) or "").strip().upper()
    if status != "PASS":
        raise GateFail("timeline manifest three_line_text_layout_status must be PASS")
    text_track_order = require_track_order(
        [timeline_manifest],
        TEXT_TRACK_ORDER_KEYS,
        REQUIRED_TEXT_TRACK_ORDER,
        "middle_text_track_order_top_to_bottom",
    )
    return {
        "three_line_text_layout_status": "PASS",
        "text_layer_rows": {
            "1": "hook_or_dialogue_line",
            "2": "emotion_or_situation_line",
            "3": "tts_caption_line",
        },
        "middle_text_track_order_top_to_bottom": text_track_order,
    }


def validate_tts_visual_fill(raw_item: dict[str, Any], label: str) -> None:
    status = str(first_item_value(raw_item, TTS_VISUAL_FILL_STATUS_KEYS) or "").strip().upper()
    covers_flag = raw_item.get("visual_covers_tts_audio") is True or raw_item.get("visual_covers_voice_audio") is True
    coverage_segments = first_list(raw_item, TTS_VISUAL_COVERAGE_KEYS)
    required_range = range_bounds_seconds(raw_item, "target")
    if required_range is None:
        raise GateFail(f"{label} TTS visual fill requires target_range")
    if coverage_segments is not None:
        if not ranges_cover_target(required_range, coverage_segments, f"{label}.visual_coverage_segments"):
            raise GateFail(f"{label} visual_coverage_segments do not cover the full TTS target range")
        return
    if status != "PASS":
        raise GateFail(f"{label} must set tts_visual_fill_status=PASS")
    if not covers_flag:
        raise GateFail(f"{label} must set visual_covers_tts_audio=true")


def validate_manifest_zero_timeline_start(
    timeline_manifest: dict[str, Any],
    scenario_beats: list[dict[str, Any]],
    clip_assignments: list[dict[str, Any]],
) -> dict[str, Any]:
    explicit = normalize_seconds(first_value_any([timeline_manifest], TIMELINE_CONTENT_START_KEYS))
    if explicit is None:
        starts = [
            start
            for item in [*scenario_beats, *clip_assignments]
            if isinstance(item, dict)
            for start in [range_start_seconds(item, "target")]
            if start is not None
        ]
        explicit = min(starts) if starts else None
    if explicit is None:
        raise GateFail("timeline manifest must include timeline_content_start_sec or target starts")
    if abs(explicit) > 0.05:
        raise GateFail("CapCut timeline content must start at 0.0 sec; do not offset/stage it later")
    return {"timeline_content_start_sec": 0.0}


def validate_manifest_audio_normalization(
    timeline_manifest: dict[str, Any],
    pre_gate_result: dict[str, Any],
) -> dict[str, Any]:
    status = str(first_value_any([timeline_manifest], AUDIO_NORMALIZATION_STATUS_KEYS) or "").strip().upper()
    if status != "PASS":
        raise GateFail("timeline manifest audio_normalization_status must be PASS")
    assets = first_list_any([timeline_manifest], NORMALIZED_AUDIO_ASSET_KEYS)
    if not assets:
        raise GateFail("timeline manifest normalized_audio_assets must list active audio segments")
    pre_count = int(pre_gate_result.get("normalized_audio_asset_count") or 0)
    if pre_count and len(assets) < pre_count:
        raise GateFail("timeline manifest normalized_audio_assets lost assets from pre-gate")
    return {
        "audio_normalization_status": "PASS",
        "normalized_audio_asset_count": len(assets),
    }


def validate_manifest_script_alignment(
    timeline_manifest: dict[str, Any],
    pre_gate_result: dict[str, Any],
    scenario_beats: list[dict[str, Any]],
) -> dict[str, Any]:
    mapping = first_list(timeline_manifest, SCRIPT_ALIGNED_TIMELINE_KEYS)
    if not mapping:
        raise GateFail("timeline manifest must include script_aligned_timeline_structure")

    required_ids = {script_beat_id(item) for item in scenario_beats if isinstance(item, dict)}
    required_ids.discard(None)
    pre_mapping = first_list(pre_gate_result, SCRIPT_ALIGNED_TIMELINE_KEYS) or []
    pre_ids = {script_beat_id(item) for item in pre_mapping if isinstance(item, dict)}
    pre_ids.discard(None)
    required_ids |= pre_ids

    mapped_ids: set[Any] = set()
    source_speech_count = 0
    user_voice_count = 0
    for idx, raw_item in enumerate(mapping):
        if not isinstance(raw_item, dict):
            raise GateFail(f"timeline script_aligned_timeline_structure[{idx}] must be an object")
        beat_id = script_beat_id(raw_item)
        if beat_id in (None, ""):
            raise GateFail(f"timeline script_aligned_timeline_structure[{idx}] must include script_beat_id")
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"timeline script_aligned_timeline_structure[{idx}] must include target_range")
        if not first_item_value(
            raw_item,
            ("video_segment_id", "visual_segment_id", "source_video_segment_id", "clip_segment_id", "asset_type"),
        ):
            raise GateFail(
                f"timeline script_aligned_timeline_structure[{idx}] must reference a visual/video segment"
            )

        text = item_text(raw_item)
        caption_type = middle_text_type(raw_item)
        quoted = is_quoted_text(text) or caption_type in {"verified_speech", "source_speech"}
        parenthesized = is_parenthesized_text(text) or caption_type in VISUAL_ONLY_MIDDLE_TYPES
        plain_voice = (
            not quoted
            and not parenthesized
            and (
                caption_type in TTS_MIDDLE_TYPES
                or truthy_item(raw_item, ("include_in_tts", "has_voice_audio", "user_tts_audio_required"))
            )
        )
        validate_text_layer_assignment(
            raw_item,
            f"timeline script_aligned_timeline_structure[{idx}]",
            text,
            caption_type,
            quoted,
            parenthesized,
            plain_voice,
        )
        if quoted:
            source_speech_count += 1
            if not first_item_value(
                raw_item,
                ("source_speech_audio_segment_id", "source_audio_segment_id", "source_audio_material_id"),
            ):
                raise GateFail(
                    f"timeline script_aligned_timeline_structure[{idx}] quoted/source speech beat "
                    "must reference source speech audio segment"
                )
        if plain_voice:
            user_voice_count += 1
            if not first_item_value(
                raw_item,
                ("voice_audio_segment_id", "caption_voice_audio_segment_id", "user_audio_segment_id"),
            ):
                raise GateFail(
                    f"timeline script_aligned_timeline_structure[{idx}] plain TTS beat "
                    "must reference user caption voice audio segment"
                )
            validate_tts_visual_fill(raw_item, f"timeline script_aligned_timeline_structure[{idx}]")
        if raw_item.get("audio_video_aligned") is not True:
            raise GateFail(
                f"timeline script_aligned_timeline_structure[{idx}] must set audio_video_aligned=true"
            )
        mapped_ids.add(beat_id)

    missing = required_ids - mapped_ids
    if missing:
        raise GateFail(f"timeline script_aligned_timeline_structure missing beats: {sorted(missing, key=str)}")
    return {
        "script_aligned_timeline_status": "PASS",
        "script_aligned_beat_count": len(mapping),
        "script_aligned_source_speech_count": source_speech_count,
        "script_aligned_user_voice_count": user_voice_count,
    }


def validate_manifest_original_source_media(
    root: Path,
    timeline_manifest: dict[str, Any],
    pre_gate_result: dict[str, Any],
) -> dict[str, Any]:
    raw_media = timeline_manifest.get("original_source_media")
    if raw_media is None:
        raise GateFail("timeline manifest must include original_source_media")
    if not isinstance(raw_media, dict):
        raise GateFail("timeline manifest original_source_media must be an object")
    raw_path = raw_media.get("path") or raw_media.get("source_path") or raw_media.get("file")
    if not raw_path:
        raise GateFail("timeline manifest original_source_media must include path")
    if raw_media.get("imported_to_capcut_media") is not True:
        raise GateFail(
            "timeline manifest original_source_media must set imported_to_capcut_media=true"
        )
    media_path = require_file(root, str(raw_path), "timeline original_source_media")
    if media_path.name.lower() != "source.mp4":
        raise GateFail("timeline original_source_media must point to the full source.mp4")
    require_audio_stream(media_path, "timeline original_source_media")

    pre_media = pre_gate_result.get("original_source_media")
    if isinstance(pre_media, dict) and pre_media.get("path"):
        manifest_path = str(raw_path)
        if Path(manifest_path).name != Path(str(pre_media["path"])).name:
            raise GateFail(
                "timeline manifest original_source_media does not match pre-gate source media"
            )
    result = dict(raw_media)
    result["path"] = str(media_path)
    result["has_audio_stream"] = True
    return result


def validate_manifest_video_track_contract(timeline_manifest: dict[str, Any]) -> dict[str, Any]:
    value = timeline_manifest.get("video_track_contract")
    if value != SEMANTIC_VIDEO_TRACK_CONTRACT:
        raise GateFail(
            "timeline manifest video_track_contract must be "
            f"{SEMANTIC_VIDEO_TRACK_CONTRACT}"
        )
    video_track_order = require_track_order(
        [timeline_manifest],
        VIDEO_TRACK_ORDER_KEYS,
        REQUIRED_VIDEO_TRACK_ORDER,
        "video_track_order_top_to_bottom",
    )

    manifest = timeline_manifest.get("video_track_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise GateFail("timeline manifest video_track_manifest must be a non-empty list")
    for idx, item in enumerate(manifest):
        if not isinstance(item, dict):
            raise GateFail(f"timeline manifest video_track_manifest[{idx}] must be an object")
        visual_track = str(item.get("visual_track") or "").strip()
        if visual_track not in ALLOWED_SEMANTIC_VIDEO_TRACKS:
            raise GateFail(
                f"timeline manifest video_track_manifest[{idx}].visual_track must be one of "
                f"{sorted(ALLOWED_SEMANTIC_VIDEO_TRACKS)}"
            )
        if item.get("target_start") is None or item.get("target_end") is None:
            raise GateFail(
                f"timeline manifest video_track_manifest[{idx}] must include target_start and target_end"
            )
        if not str(item.get("source_audio_policy") or "").strip():
            raise GateFail(
                f"timeline manifest video_track_manifest[{idx}] must include source_audio_policy"
            )

    return {
        "video_track_contract": SEMANTIC_VIDEO_TRACK_CONTRACT,
        "video_track_order_top_to_bottom": video_track_order,
        "video_track_manifest_count": len(manifest),
    }


def validate_manifest_unused_split_clips(
    timeline_manifest: dict[str, Any],
    pre_gate_result: dict[str, Any],
) -> list[Any]:
    pre_unused = pre_gate_result.get("unused_split_clips") or []
    manifest_unused = get_list_optional(timeline_manifest, pre_gate_result, UNUSED_SPLIT_KEYS)
    if pre_unused and not manifest_unused:
        raise GateFail(
            "timeline manifest must keep unused_split_clips for manual editing"
        )
    return manifest_unused


def validate_manifest_framing_adjustments(
    timeline_manifest: dict[str, Any],
    pre_gate_result: dict[str, Any],
    clip_assignments: list[Any],
) -> list[Any]:
    adjustments = get_list_optional(
        timeline_manifest,
        pre_gate_result,
        FRAMING_ADJUSTMENT_KEYS,
    )
    has_inline = False
    for item in clip_assignments:
        if not isinstance(item, dict):
            continue
        for key in ("framing", "framing_adjustment", "crop", "scale", "pan", "zoom", "keyframes", "reframe"):
            if key in item and item.get(key) not in (None, "", []):
                has_inline = True
                break
        if has_inline:
            break
    if not adjustments and not has_inline:
        raise GateFail(
            "timeline manifest must include framing_adjustments or inline crop/scale/pan/zoom data"
        )
    return adjustments


def sfx_file_path(item: dict[str, Any]) -> str:
    for key in ("path", "file_path", "sfx_path", "source_path"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def sfx_id(item: dict[str, Any]) -> str:
    for key in ("sfx_id", "id", "file_name", "name"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raw_path = sfx_file_path(item)
    if raw_path:
        return Path(raw_path).name
    return ""


def validate_manifest_sfx_media_bin(
    timeline_manifest: dict[str, Any],
    pre_gate_result: dict[str, Any],
) -> tuple[list[Any], list[Any]]:
    pre_sfx = pre_gate_result.get("sfx_timeline") or []
    manifest_sfx = get_list_optional(timeline_manifest, pre_gate_result, SFX_TIMELINE_KEYS)
    manifest_media = get_list_optional(timeline_manifest, pre_gate_result, SFX_MEDIA_BIN_KEYS)

    if pre_sfx and not manifest_sfx:
        raise GateFail("timeline manifest must keep sfx_timeline from pre-gate")
    if manifest_sfx and not manifest_media:
        schema_limit = (
            timeline_manifest.get("sfx_media_bin_status")
            or pre_gate_result.get("sfx_media_bin_status")
            or ""
        )
        if schema_limit != "TRACK_ONLY_SCHEMA_LIMIT":
            raise GateFail(
                "timeline manifest has SFX timeline cues, so sfx_media_bin is required "
                "unless sfx_media_bin_status=TRACK_ONLY_SCHEMA_LIMIT"
            )

    media_ids = {
        sfx_id(item)
        for item in manifest_media
        if isinstance(item, dict)
    }
    for idx, raw_item in enumerate(manifest_media):
        if not isinstance(raw_item, dict):
            raise GateFail(f"timeline sfx_media_bin[{idx}] must be an object")
        if not sfx_file_path(raw_item):
            raise GateFail(f"timeline sfx_media_bin[{idx}] must include path/file_path")
        imported = raw_item.get("imported_to_capcut_media")
        registered = raw_item.get("registered_in_project_media")
        if imported is not True and registered is not True:
            raise GateFail(
                f"timeline sfx_media_bin[{idx}] must set imported_to_capcut_media=true "
                "or registered_in_project_media=true"
            )

    for idx, raw_item in enumerate(manifest_sfx):
        if not isinstance(raw_item, dict):
            raise GateFail(f"timeline sfx_timeline[{idx}] must be an object")
        cue_id = sfx_id(raw_item)
        cue_path = sfx_file_path(raw_item)
        if not cue_id and not cue_path:
            raise GateFail(f"timeline sfx_timeline[{idx}] must include sfx path or id")
        if manifest_media and cue_id not in media_ids and Path(cue_path).name not in media_ids:
            raise GateFail(
                f"timeline sfx_timeline[{idx}] is not registered in sfx_media_bin: {cue_id or cue_path}"
            )
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"timeline sfx_timeline[{idx}] must include target_range")
    return manifest_sfx, manifest_media


def extract_order_from_segments(items: list[Any]) -> list[Any]:
    order: list[Any] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        beat = None
        for key in (
            "beat_id",
            "source_beat",
            "source_beat_id",
            "original_beat",
            "original_beat_id",
            "remix_beat_id",
            "order_beat",
            "beat",
        ):
            if key in item:
                beat = item[key]
                break
        if beat is None and isinstance(item.get("source"), dict):
            source = item["source"]
            for key in ("beat_id", "source_beat", "original_beat_id"):
                if key in source:
                    beat = source[key]
                    break
        if beat is not None and (not order or order[-1] != beat):
            order.append(beat)
    return order


def extract_actual_order(manifest: dict[str, Any]) -> list[Any]:
    explicit = manifest.get("actual_render_order")
    if isinstance(explicit, list) and explicit:
        return require_order(explicit, "timeline_manifest.actual_render_order")

    for key in ("segments", "render_segments", "timeline", "video_segments", "cuts"):
        value = manifest.get(key)
        if isinstance(value, list):
            order = extract_order_from_segments(value)
            if order:
                return require_order(order, f"timeline_manifest.{key} derived order")

    raise GateFail(
        "timeline manifest must contain actual_render_order or segments with beat ids"
    )


def validate_scenario_post_gate(
    root: Path,
    pre_gate_result: dict[str, Any],
    timeline_manifest: dict[str, Any],
    contract: dict[str, Any] | None,
    draft_name: str,
    draft_path: str,
) -> dict[str, Any]:
    scenario_beats = get_list_or_fail(
        timeline_manifest,
        pre_gate_result,
        SCENARIO_LIST_KEYS,
        "timeline manifest scenario_timeline",
    )
    clip_assignments = get_list_or_fail(
        timeline_manifest,
        pre_gate_result,
        CLIP_ASSIGNMENT_KEYS,
        "timeline manifest clip_assignments",
    )

    scenario_ids: set[Any] = set()
    for idx, raw_item in enumerate(scenario_beats):
        if not isinstance(raw_item, dict):
            raise GateFail(f"timeline scenario_timeline[{idx}] must be an object")
        beat_id = scenario_beat_id(raw_item)
        if beat_id in (None, ""):
            raise GateFail(f"timeline scenario_timeline[{idx}] must include scenario_beat_id")
        if beat_id in scenario_ids:
            raise GateFail(f"timeline duplicate scenario_beat_id: {beat_id}")
        if not item_role(raw_item):
            raise GateFail(f"timeline scenario_timeline[{idx}] must include beat_role")
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"timeline scenario_timeline[{idx}] must include target_range")
        validate_middle_caption_type(raw_item, f"timeline scenario_timeline[{idx}]")
        scenario_ids.add(beat_id)

    assigned_scenario_ids: set[Any] = set()
    source_assignment_count = 0
    for idx, raw_item in enumerate(clip_assignments):
        if not isinstance(raw_item, dict):
            raise GateFail(f"timeline clip_assignments[{idx}] must be an object")
        beat_id = scenario_beat_id(raw_item)
        if beat_id in (None, ""):
            raise GateFail(f"timeline clip_assignments[{idx}] must include scenario_beat_id")
        if beat_id not in scenario_ids:
            raise GateFail(f"timeline clip_assignments[{idx}] points to unknown scenario beat: {beat_id}")
        if not item_role(raw_item):
            raise GateFail(f"timeline clip_assignments[{idx}] must include beat_role")
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"timeline clip_assignments[{idx}] must include target_range")
        validate_middle_caption_type(raw_item, f"timeline clip_assignments[{idx}]")

        if assignment_uses_source(raw_item):
            source_assignment_count += 1
        elif assignment_asset_type(raw_item) not in ALLOWED_NON_SOURCE_ASSETS:
            raise GateFail(
                f"timeline clip_assignments[{idx}] must include source_range/source_beat_id "
                f"or asset_type in {sorted(ALLOWED_NON_SOURCE_ASSETS)}"
            )
        assigned_scenario_ids.add(beat_id)

    missing = scenario_ids - assigned_scenario_ids
    if missing:
        raise GateFail(f"timeline clip_assignments missing scenario beats: {sorted(missing, key=str)}")
    if source_assignment_count < 1:
        raise GateFail("timeline clip_assignments must include at least one source video assignment")

    zero_start_result = validate_manifest_zero_timeline_start(
        timeline_manifest,
        scenario_beats,
        clip_assignments,
    )
    audio_normalization_result = validate_manifest_audio_normalization(
        timeline_manifest,
        pre_gate_result,
    )
    text_layout_result = validate_manifest_three_line_text_layout(timeline_manifest)
    catcup_layout_result = validate_catcup_reference_layout_actual(
        root,
        timeline_manifest,
        contract,
        draft_path,
    )
    draft = load_draft_content_for_catcup(root, timeline_manifest, contract, draft_path)
    script_alignment_result = validate_manifest_script_alignment(
        timeline_manifest,
        pre_gate_result,
        scenario_beats,
    )
    original_source_media = validate_manifest_original_source_media(
        root,
        timeline_manifest,
        pre_gate_result,
    )
    video_track_contract_result = validate_manifest_video_track_contract(timeline_manifest)
    unused_split_clips = validate_manifest_unused_split_clips(
        timeline_manifest,
        pre_gate_result,
    )
    framing_adjustments = validate_manifest_framing_adjustments(
        timeline_manifest,
        pre_gate_result,
        clip_assignments,
    )
    mandatory_media_settings_result = validate_mandatory_capcut_media_settings(draft)
    sfx_timeline, sfx_media_bin = validate_manifest_sfx_media_bin(
        timeline_manifest,
        pre_gate_result,
    )

    if contract is not None:
        require_json_status_pass(
            root,
            contract.get("harness_report_capcut", ""),
            "harness_report_capcut",
        )
        require_json_status_pass(
            root,
            contract.get("harness_report_all", ""),
            "harness_report_all",
        )

    return {
        "gate": "POST_CAPCUT_TIMELINE_GATE",
        "status": "PASS",
        "edit_assembly_mode": "scenario_first_montage",
        "scenario_beat_count": len(scenario_beats),
        "clip_assignment_count": len(clip_assignments),
        "source_assignment_count": source_assignment_count,
        "unused_split_clip_count": len(unused_split_clips),
        "framing_adjustment_count": len(framing_adjustments),
        "sfx_timeline_count": len(sfx_timeline),
        "sfx_media_bin_count": len(sfx_media_bin),
        "original_source_media": original_source_media,
        **mandatory_media_settings_result,
        **video_track_contract_result,
        **zero_start_result,
        **audio_normalization_result,
        **text_layout_result,
        **catcup_layout_result,
        **script_alignment_result,
        "draft_name": draft_name,
        "draft_path": draft_path or "",
        **upload_ready_state(contract),
    }


def validate_post_gate(
    root: Path,
    pre_gate_result: dict[str, Any],
    timeline_manifest: dict[str, Any],
    contract: dict[str, Any] | None,
) -> dict[str, Any]:
    if pre_gate_result.get("status") != "PASS":
        raise GateFail("pre production gate status must be PASS")
    if pre_gate_result.get("production_allowed") is not True:
        raise GateFail("pre production gate production_allowed must be true")
    if pre_gate_result.get("report1_handoff_gate_status") != "PASS":
        raise GateFail(
            "WAIT_REPORT1_HANDOFF_GATE: pre production gate must include report1_handoff_gate_status PASS"
        )

    draft_name = timeline_manifest.get("draft_name") or timeline_manifest.get("capcut_draft_name")
    draft_path = timeline_manifest.get("draft_path") or timeline_manifest.get("capcut_draft_path")
    if not draft_name:
        raise GateFail("timeline manifest must include draft_name")
    if draft_path:
        require_file(root, str(draft_path), "capcut_draft_path")

    mode = (
        pre_gate_result.get("edit_assembly_mode")
        or timeline_manifest.get("edit_assembly_mode")
        or (contract or {}).get("edit_assembly_mode")
        or "order_remix"
    )
    if isinstance(mode, str) and mode.strip() in SCENARIO_FIRST_MODES:
        return validate_scenario_post_gate(
            root,
            pre_gate_result,
            timeline_manifest,
            contract,
            str(draft_name),
            str(draft_path or ""),
        )

    selected = require_order(pre_gate_result.get("selected_remix_order"), "selected_remix_order")
    actual = extract_actual_order(timeline_manifest)
    if selected != actual:
        raise GateFail(
            f"CapCut timeline order mismatch. selected={selected}, actual={actual}"
        )

    if contract is not None:
        require_json_status_pass(
            root,
            contract.get("harness_report_capcut", ""),
            "harness_report_capcut",
        )
        require_json_status_pass(
            root,
            contract.get("harness_report_all", ""),
            "harness_report_all",
        )

    return {
        "gate": "POST_CAPCUT_TIMELINE_GATE",
        "status": "PASS",
        "edit_assembly_mode": "order_remix",
        "selected_remix_order": selected,
        "actual_render_order": actual,
        "draft_name": draft_name,
        "draft_path": draft_path or "",
        **upload_ready_state(contract),
    }


def fail_result(reason: str) -> dict[str, Any]:
    return {
        "gate": "POST_CAPCUT_TIMELINE_GATE",
        "status": "FAIL",
        "reason": reason,
        "upload_ready_allowed": False,
        "upload_ready": "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_dir")
    parser.add_argument("production_gate_result_json")
    parser.add_argument("timeline_manifest_json")
    parser.add_argument("--contract-json")
    parser.add_argument("--out")
    args = parser.parse_args()

    root = Path(args.job_dir)
    gate_path = as_path(root, args.production_gate_result_json)
    manifest_path = as_path(root, args.timeline_manifest_json)
    contract_path = as_path(root, args.contract_json) if args.contract_json else None

    try:
        pre_gate_result = load_json(gate_path)
        timeline_manifest = load_json(manifest_path)
        contract = load_json(contract_path) if contract_path else None
        result = validate_post_gate(root, pre_gate_result, timeline_manifest, contract)
        exit_code = 0
    except GateFail as exc:
        result = fail_result(str(exc))
        exit_code = 1

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    print(output)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
