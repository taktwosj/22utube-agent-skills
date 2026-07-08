#!/usr/bin/env python3
"""Fail-closed pre-production gate for 11short remake jobs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


class GateFail(Exception):
    pass


ALLOWED_SCRIPT_LOCK_SOURCES = {
    "tikitaka_harness_runner",
}
ALLOWED_SCRIPT_HANDOFF_GATE_GENERATORS = {
    "tikitaka_harness_runner",
    "validate_tikitaka_handoff",
    "validate_tikitaka_handoff.py",
}
SCRIPT_HANDOFF_GATE_PATH_KEYS = (
    "script_handoff_gate_path",
    "script_handoff_gate_json",
    "script_handoff_gate",
)
REPORT1_HANDOFF_GATE_PATH_KEYS = (
    "report1_handoff_path",
    "report1_handoff_json",
    "report1_handoff_gate_path",
    "report1_handoff_gate_json",
    "report1_handoff_gate",
)
BLOCK_MAP_PATH_KEYS = (
    "block_map_path",
    "canonical_block_map_path",
    "tikitaka_block_map_path",
)
BLOCK_VOICE_SWITCH_MAP_PATH_KEYS = (
    "block_voice_switch_map_path",
    "voice_switch_map_path",
    "tikitaka_voice_switch_map_path",
)
CAPCUT_DRAFT_CONTENT_PATH_KEYS = (
    "draft_content_path",
    "draft_content_json",
    "capcut_draft_content_path",
    "capcut_draft_content_json",
)
TEMPLATE_REFERENCE_NAME_KEYS = (
    "reference_project_name",
    "template_reference_project_name",
    "reference_capcut_project",
    "catcup_reference_project",
)
TEMPLATE_REFERENCE_PATH_KEYS = (
    "reference_project_path",
    "template_reference_project_path",
    "reference_capcut_project_path",
    "catcup_reference_project_path",
)
TEMPLATE_REFERENCE_REQUIRED_KEYS = (
    "template_reference_required",
    "reference_project_required",
    "template_backed_capcut_project",
)
TEMPLATE_REFERENCE_DERIVED_KEYS = (
    "derived_from_reference_project",
    "template_reference_derived",
    "reference_project_cloned",
    "template_copy_from_reference",
)
TEMPLATE_PROFILE_KEYS = (
    "template_profile",
    "catcup_text_template_profile",
    "selected_template_profile",
)
USER_EXPLICIT_TEMPLATE_OVERRIDE_KEYS = (
    "user_explicit_template_override",
    "explicit_template_override",
    "user_selected_non_default_template",
    "non_default_template_user_approved",
)
STALE_BUILDER_REFERENCE_NAME_KEYS = (
    "builder_reference_name",
    "hardcoded_reference_name",
    "reference_name_from_builder",
    "REFERENCE_NAME",
)
DEFAULT_CAPCUT_BASE_PROJECT = "shrt white"
DEFAULT_CAPCUT_BASE_PROFILE = "shrt_white_base_v1"
DEFAULT_CAPCUT_BASE_ALIASES = {"shrt white", "short white"}
DEFAULT_CAPCUT_BASE_PROFILE_ALIASES = {
    "shrt_white_base_v1",
    "shrt white",
    "short white",
}
CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT = "260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1"
FORBIDDEN_DERIVED_REFERENCE_PROJECTS = {
    CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT,
    "260708 short",
}
FORBIDDEN_DERIVED_REFERENCE_MARKERS = (
    "_base_v2",
    "_base_v3",
)
PRODUCTION_PROOF_PATHS = (
    (("cut_manifest_path", "cut_manifest_json"), "cut_manifest.json", "cut_manifest"),
    (
        ("capcut_assembly_report_path", "capcut_assembly_report_json"),
        "proof/capcut_assembly_report.json",
        "capcut_assembly_report",
    ),
    (("contact_sheet_path", "contact_sheet_jpg"), "proof/contact_sheet.jpg", "contact_sheet"),
    (("clip_durations_path", "clip_durations_csv"), "proof/clip_durations.csv", "clip_durations"),
    (("timeline_order_path", "timeline_order_txt"), "proof/timeline_order.txt", "timeline_order"),
)
CAPCUT_ASSEMBLY_PROOF_FLAGS = (
    "timeline_order_verified",
    "visible_trim_verified",
    "handle_extendable",
    "independent_clips_verified",
    "proof_files_verified",
)
DRAFT_FAST_REQUEST_TOKENS = (
    "DRAFT_FAST",
    "검토용 draft만",
    "검토용 드래프트만",
    "빠른 초안",
    "기술 초안",
)
STAGE1_REQUEST_TOKENS = (
    "대본만",
    "대본까지",
    "대본까지만",
    "초벌",
    "초벌대본",
    "티키타카",
    "초안만",
    "검토용",
    "스크립트만",
)
STAGE2_REQUEST_TOKENS = (
    "끝까지",
    "자동으로 다",
    "자동모드",
    "최종",
    "다음단계",
    "다음 단계",
    "업로드까지",
    "슈퍼톤",
    "SUPERTONE",
    "TTS 만들",
    "TTS 생성",
    "TTS mp3",
    "캣컵프로젝트파일까지",
    "캣컵 프로젝트 파일까지",
    "캐컷프로젝트파일까지",
    "캡컷프로젝트파일까지",
    "CAPCUT PROJECT",
)
STAGE2_DECISION_VALUES = {
    "STAGE_2_FULL",
    "STAGE2_FULL",
    "STAGE_2",
    "AUTO_FULL",
    "AUTO_FULL_CAPCUT_PROJECT",
    "FINAL_LOCK",
    "FULL",
    "PRODUCTION",
    "자동모드",
    "자동으로 다",
    "끝까지",
    "최종",
}
STAGE1_DECISION_VALUES = {
    "STAGE_1_SCRIPT",
    "STAGE1_SCRIPT",
    "STAGE_1_ONLY",
    "SCRIPT_ONLY",
    "DRAFT_SCRIPT",
    "TIKITAKA_ONLY",
    "대본까지",
    "대본만",
}
STAGE_SCOPE_DECISION_KEYS = {
    "user_stage_decision",
    "stage_scope",
    "requested_stage",
}
TRUSTED_STAGE_SCOPE_GENERATORS = {
    "tikitaka_harness_runner",
}
USER_TTS_OR_SRT_PATH_KEYS = (
    "user_tts_audio_path",
    "user_tts_path",
    "tts_audio_path",
    "user_audio_path",
    "user_mp3_path",
    "provided_tts_audio_path",
    "provided_mp3_path",
    "user_srt_path",
    "user_srt_audio_package_path",
)
REPORT1_APPROVAL_KEYS = (
    "report1_approved",
    "report_1_approved",
    "script_approved_by_user",
    "user_script_ok",
    "user_ok_after_report1",
    "report1_user_ok",
)
VOICE_AUDIO_ROUTE_DECISION_KEYS = (
    "voice_audio_route_decided",
    "tts_route_decided",
    "audio_route_decided",
    "tts_user_decision_done",
    "no_tts_source_bgm_route_approved",
)
VOICE_AUDIO_ROUTE_VALUE_KEYS = (
    "voice_audio_route",
    "tts_route",
    "audio_route",
    "source_audio_route",
    "selected_voice_audio_route",
)

SCENARIO_FIRST_MODES = {
    "scenario_first_montage",
    "scenario_montage",
    "scenario_first",
}

LEGACY_ORDER_MODES = {
    "order_remix",
    "simple_order_remix",
    "legacy_order_remix",
}

SCENARIO_LIST_KEYS = ("scenario_timeline", "scenario_beats")
CLIP_ASSIGNMENT_KEYS = ("clip_assignments", "visual_assignments", "assignments")
SOURCE_LIBRARY_KEYS = ("source_beat_library", "source_beats", "source_segments")
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
SEMANTIC_VIDEO_TRACK_CONTRACT = "caption_video_plus_situation_speaker_video"
ALLOWED_SEMANTIC_VIDEO_TRACKS = {
    "caption_video",
    "situation_speaker_video",
}
VISUAL_ONLY_ROLES = {
    "hook_visual",
    "context_video",
    "dialogue_video",
    "reaction_video",
    "payoff_video",
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
YOUTUBE_RESTRICTION_POLICY_CONTAINERS = (
    "youtube_restriction_guideline",
    "youtube_restriction_gate",
    "youtube_guideline_gate",
    "youtube_policy_gate",
    "policy_gate",
)
YOUTUBE_RESTRICTION_COMPLETE_KEYS = (
    "youtube_restriction_guideline_gate_complete",
    "youtube_guideline_gate_complete",
    "restriction_guideline_gate_complete",
)
YOUTUBE_RESTRICTION_RISK_KEYS = (
    "youtube_restriction_policy_risk_tier",
    "youtube_restriction_risk_tier",
    "policy_risk_tier",
)
YOUTUBE_RESTRICTION_VERDICT_KEYS = (
    "youtube_restriction_platform_verdict",
    "youtube_restriction_verdict",
    "platform_safety_verdict",
)
YOUTUBE_RESTRICTION_FLAG_KEYS = (
    "youtube_restriction_flagged_categories",
    "flagged_categories",
)
YOUTUBE_RESTRICTION_HARD_BLOCK_KEYS = (
    "youtube_restriction_hard_blocks",
    "youtube_restriction_block_flags",
    "hard_blocks",
)
YOUTUBE_RESTRICTION_REWRITE_KEYS = (
    "youtube_restriction_rewrite_required",
    "youtube_restriction_required_rewrites",
    "rewrite_required",
    "required_rewrites",
)
SOURCE_DIALOGUE_POLICY_CONTAINERS = (
    "source_dialogue_analysis",
    "elevenlabs_dialogue_analysis",
    "dialogue_analysis",
)
ELEVENLABS_DIALOGUE_STATUS_KEYS = (
    "elevenlabs_dialogue_analysis_status",
    "source_dialogue_analysis_status",
    "source_dialogue_status",
)
ELEVENLABS_DIALOGUE_PROVIDER_KEYS = (
    "source_dialogue_analysis_provider",
    "elevenlabs_dialogue_provider",
    "dialogue_analysis_provider",
    "stt_provider",
)
ELEVENLABS_DIALOGUE_PATH_KEYS = (
    "source_dialogue_analysis_path",
    "source_dialogue_report_path",
    "elevenlabs_dialogue_report_path",
    "elevenlabs_scribe_json",
    "scribe_json_path",
)
FINAL_REPORT_STATUS_KEYS = (
    "pre_capcut_script_package_status",
    "script_package_status",
    "final_report_status",
    "script_report_status",
    "report_before_capcut_status",
)
USER_SRT_AUDIO_STATUS_KEYS = (
    "user_srt_audio_gate_status",
    "user_srt_audio_package_status",
    "voice_package_status",
    "user_voice_package_status",
)
USER_SRT_AUDIO_REQUIRED_KEYS = (
    "requires_user_srt_audio_before_capcut",
    "user_srt_audio_required",
    "voice_package_required_before_capcut",
)
USER_SRT_PATH_KEYS = (
    "user_srt_path",
    "voice_srt_path",
    "voiceover_srt_path",
    "voice_body_split_srt_path",
    "voice_body_split_srt",
)
USER_AUDIO_PATH_KEYS = (
    "user_audio_path",
    "user_voice_audio_path",
    "voiceover_audio_path",
    "voiceover_body_mp3_path",
    "voiceover_body_mp3",
    "voice_audio_path",
)
USER_SRT_AUDIO_PACKAGE_PATH_KEYS = (
    "user_srt_audio_package_path",
    "user_voice_zip_path",
    "voice_package_zip_path",
    "voice_zip_path",
)
USER_SRT_AUDIO_EXCEPTION_STATUSES = {
    "N/A_USER_CONFIRMED_NO_VOICE",
    "N/A_NO_VOICE_USER_CONFIRMED",
    "SOURCE_AUDIO_ONLY_USER_CONFIRMED",
}
SCRIPT_ALIGNED_TIMELINE_KEYS = (
    "script_aligned_timeline_structure",
    "script_aligned_timeline",
    "beat_audio_video_map",
    "beat_timeline_map",
)
SCRIPT_ALIGNED_REQUIRED_KEYS = (
    "script_aligned_timeline_required",
    "script_beat_mapping_required",
    "beat_audio_video_mapping_required",
)
SCRIPT_ALIGNED_STATUS_KEYS = (
    "script_aligned_timeline_status",
    "script_beat_mapping_status",
    "beat_audio_video_mapping_status",
)
AUDIO_NORMALIZATION_CONTAINERS = (
    "audio_normalization",
    "audio_normalization_gate",
    "audio_loudness_gate",
)
AUDIO_NORMALIZATION_REQUIRED_KEYS = (
    "audio_normalization_required",
    "audio_normalize_required",
    "loudness_normalization_required",
)
AUDIO_NORMALIZATION_STATUS_KEYS = (
    "audio_normalization_status",
    "audio_normalize_status",
    "loudness_normalization_status",
)
AUDIO_NORMALIZATION_METHOD_KEYS = (
    "audio_normalization_method",
    "audio_normalize_method",
    "loudness_normalization_method",
)
NORMALIZED_AUDIO_ASSET_KEYS = (
    "normalized_audio_assets",
    "audio_normalized_assets",
    "loudness_normalized_assets",
    "active_normalized_audio_segments",
)
AUDIO_NORMALIZATION_REPORT_KEYS = (
    "audio_normalization_report_path",
    "audio_loudness_report_path",
    "loudness_report_path",
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
THREE_LINE_TEXT_LAYOUT_REQUIRED_KEYS = (
    "three_line_text_layout_required",
    "three_text_layer_layout_required",
    "text_role_rows_required",
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
    "insta_white_template_master_v1": {
        "reference_project": "insta white",
        "accepted_reference_projects": {
            "insta white",
            "260625-ig-contortion-top3-urakkai-instagram-tts",
        },
    },
    "insta_white_audio_split_v1": {
        "reference_project": "insta white",
        "accepted_reference_projects": {
            "insta white",
            "260625-ig-contortion-top3-urakkai-instagram-tts",
        },
    },
    "black_template_master_v1": {
        "reference_project": "black",
        "accepted_reference_projects": {"black"},
    },
}
CATCUP_LAYOUT_REQUIRED_KEYS = (
    "catcup_reference_layout_required",
    "catcup_broadcast_reference_layout_required",
    "broadcast_accident_reference_layout_required",
)
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


def require(value: Any, message: str) -> None:
    if not value:
        raise GateFail(message)


def require_file(root: Path, rel_path: str, label: str) -> Path:
    require(rel_path, f"{label} path is empty")
    path = as_path(root, rel_path)
    if not path.exists():
        raise GateFail(f"{label} file missing: {path}")
    return path


def require_declared_file(
    root: Path,
    rel_path: str,
    label: str,
    base_dir: Path | None = None,
) -> Path:
    require(rel_path, f"{label} path is empty")
    path = as_path(root, rel_path)
    if not path.exists() and base_dir is not None and not Path(rel_path).is_absolute():
        path = base_dir / rel_path
    if not path.exists():
        raise GateFail(f"{label} file missing: {path}")
    return path


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def truthy(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "pass",
            "passed",
            "yes",
            "y",
            "ok",
            "okay",
            "complete",
            "completed",
            "예",
            "승인",
            "완료",
        }
    return False


def nonempty_policy_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [item for item in value if item not in (None, "", [], {})]
    if isinstance(value, str):
        text = value.strip()
        if text and text.lower() not in {"none", "n/a", "na", "[]", "없음"}:
            return [text]
    return []


def collect_policy_sources(contract: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = [contract]
    for key in ("status_json_path", "status_path", "status_file"):
        raw_path = contract.get(key)
        if isinstance(raw_path, str) and raw_path.strip():
            path = as_path(root, raw_path)
            if path.exists():
                sources.append(load_json(path))

    expanded: list[dict[str, Any]] = []
    for source in sources:
        expanded.append(source)
        for key in YOUTUBE_RESTRICTION_POLICY_CONTAINERS:
            nested = source.get(key)
            if isinstance(nested, dict):
                expanded.append(nested)
    return expanded


def first_policy_value(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> Any:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
    return None


def policy_items(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> list[Any]:
    items: list[Any] = []
    for source in sources:
        for key in keys:
            items.extend(nonempty_policy_items(source.get(key)))
    return items


def collect_status_sources(
    contract: dict[str, Any],
    root: Path,
    containers: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = [contract]
    for key in ("status_json_path", "status_path", "status_file"):
        raw_path = contract.get(key)
        if isinstance(raw_path, str) and raw_path.strip():
            path = as_path(root, raw_path)
            if path.exists():
                sources.append(load_json(path))

    expanded: list[dict[str, Any]] = []
    for source in sources:
        expanded.append(source)
        for key in containers:
            nested = source.get(key)
            if isinstance(nested, dict):
                expanded.append(nested)
    return expanded


def first_status_value(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> Any:
    return first_policy_value(sources, keys)


def first_existing_file_from_keys(
    sources: list[dict[str, Any]],
    root: Path,
    keys: tuple[str, ...],
    label: str,
) -> Path | None:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        path = as_path(root, item)
                        if path.exists():
                            return path
            elif isinstance(value, str) and value.strip():
                path = as_path(root, value)
                if path.exists():
                    return path
    return None


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


def default_or_declared_path(
    sources: list[dict[str, Any]],
    keys: tuple[str, ...],
    default_path: str,
) -> str:
    value = first_status_value(sources, keys)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default_path


def normalized_stage_decision(value: Any) -> str:
    return str(value or "").strip().upper()


def is_stage2_decision(value: Any) -> bool:
    return normalized_stage_decision(value) in STAGE2_DECISION_VALUES


def status_block_passes(value: Any) -> bool:
    return isinstance(value, dict) and status_value(value) == "PASS"


def has_trusted_stage_scope_generator(source: dict[str, Any]) -> bool:
    stage_scope_gate = source.get("stage_scope_gate")
    script_lock = source.get("script_lock")
    candidates: list[Any] = [
        source.get("source"),
        source.get("generated_by"),
    ]
    if isinstance(stage_scope_gate, dict):
        candidates.extend((stage_scope_gate.get("source"), stage_scope_gate.get("generated_by")))
    if isinstance(script_lock, dict):
        candidates.extend((script_lock.get("source"), script_lock.get("generated_by")))
    return any(str(item or "").strip() in TRUSTED_STAGE_SCOPE_GENERATORS for item in candidates)


def trusted_stage_scope_source_allows(source: dict[str, Any], decision: Any) -> bool:
    if not is_stage2_decision(decision):
        return True

    stage_scope_gate = source.get("stage_scope_gate")
    if not isinstance(stage_scope_gate, dict):
        return False
    gate_status = normalized_stage_decision(stage_scope_gate.get("status"))
    gate_decision = normalized_stage_decision(stage_scope_gate.get("decision"))
    if gate_status != "PASS" or gate_decision not in STAGE2_DECISION_VALUES:
        return False
    if not has_trusted_stage_scope_generator(source):
        return False
    return all(
        status_block_passes(source.get(key))
        for key in ("validation", "evidence_pack", "harness_trace")
    )


def has_report1_approval(contract: dict[str, Any]) -> bool:
    return any(truthy(contract.get(key)) for key in REPORT1_APPROVAL_KEYS)


def has_voice_audio_route_decision(contract: dict[str, Any]) -> bool:
    return any(truthy(contract.get(key)) for key in VOICE_AUDIO_ROUTE_DECISION_KEYS)


def require_report1_approval_and_voice_route(contract: dict[str, Any]) -> None:
    if has_report1_approval(contract) and has_voice_audio_route_decision(contract):
        return
    raise GateFail(
        "WAIT_REPORT1_APPROVAL_TTS_DECISION: report1_approved and voice_audio_route_decided are required before 보고서2/CapCut stage"
    )


def project_file_request_mode(contract: dict[str, Any]) -> str:
    explicit = str(
        contract.get("project_file_request_mode")
        or contract.get("requested_mode")
        or contract.get("production_mode")
        or ""
    ).strip().upper()

    request_text = " ".join(
        str(contract.get(key) or "")
        for key in (
            "user_request",
            "request_text",
            "prompt",
            "expected_output",
            "requested_output",
            "work_order",
        )
    )
    request_text_upper = request_text.upper()
    user_stage_decision = str(contract.get("user_stage_decision") or "").strip().upper()
    has_draft_fast_token = any(
        token.upper() in request_text_upper for token in DRAFT_FAST_REQUEST_TOKENS
    )

    if explicit in {"DRAFT_FAST", "DRAFT_FAST_EXPLICIT_ONLY"} and has_draft_fast_token:
        require_report1_approval_and_voice_route(contract)
        return "DRAFT_FAST"
    if explicit in {"DRAFT_FAST", "DRAFT_FAST_EXPLICIT_ONLY"} and not has_draft_fast_token:
        raise GateFail(
            "WAIT_DRAFT_FAST_EXPLICIT_TOKEN: DRAFT_FAST requires a literal fast-draft request token"
        )

    has_stage2_asset = any(
        isinstance(contract.get(key), str) and str(contract.get(key)).strip()
        for key in USER_TTS_OR_SRT_PATH_KEYS
    )
    has_stage2_request = any(token.upper() in request_text_upper for token in STAGE2_REQUEST_TOKENS)
    has_strong_stage2_request = any(
        token.upper() in request_text_upper
        for token in STAGE2_REQUEST_TOKENS
        if token not in {"진행", "해줘", "쭉"}
    )
    has_stage1_request = user_stage_decision in STAGE1_DECISION_VALUES or any(
        token.upper() in request_text_upper for token in STAGE1_REQUEST_TOKENS
    )
    verified_stage2_decision = (
        user_stage_decision in STAGE2_DECISION_VALUES
        and contract.get("_stage_scope_gate_verified") is True
    )

    if has_stage1_request and not has_stage2_asset and not has_strong_stage2_request:
        raise GateFail(
            "WAIT_USER_STAGE_DECISION: stage 1 request detected; ask user '어디까지 만들까?' before stage 2"
        )

    if (
        user_stage_decision in STAGE2_DECISION_VALUES
        and not verified_stage2_decision
        and not has_stage2_asset
        and not has_strong_stage2_request
    ):
        raise GateFail(
            "WAIT_USER_STAGE_DECISION: stage 2 decision requires verified Stage Scope Gate PASS"
        )

    if verified_stage2_decision or has_stage2_asset or has_strong_stage2_request:
        require_report1_approval_and_voice_route(contract)
        if explicit == "FINAL_LOCK":
            return "FINAL_LOCK"
        if explicit == "DRAFT_FAST" and has_draft_fast_token:
            return "DRAFT_FAST"
        return "AUTO_FULL_CAPCUT_PROJECT"

    if has_stage1_request:
        raise GateFail(
            "WAIT_USER_STAGE_DECISION: stage 1 request detected; ask user '어디까지 만들까?' before stage 2"
        )

    raise GateFail(
        "WAIT_USER_STAGE_DECISION: URL+Gemini intake requires user_stage_decision, stage 2 request text, or user TTS/SRT path before stage 2"
    )


def status_source_allows_stage2_decision(source: dict[str, Any], decision: Any) -> bool:
    return trusted_stage_scope_source_allows(source, decision)


def status_source_allows_report1_voice_decision(source: dict[str, Any]) -> bool:
    decision = (
        source.get("user_stage_decision")
        or source.get("stage_scope")
        or source.get("requested_stage")
    )
    stage_scope_gate = source.get("stage_scope_gate")
    if not decision and isinstance(stage_scope_gate, dict):
        decision = stage_scope_gate.get("decision")
    if not is_stage2_decision(decision):
        return False
    return trusted_stage_scope_source_allows(source, decision)


def merged_request_scope_contract(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    merged = dict(contract)
    merged.pop("_stage_scope_gate_verified", None)
    verified_stage2_decision = False
    for key in STAGE_SCOPE_DECISION_KEYS:
        if key in merged and is_stage2_decision(merged.get(key)):
            if status_source_allows_stage2_decision(contract, merged.get(key)):
                verified_stage2_decision = True
            else:
                merged.pop(key, None)

    scope_keys = (
        "user_stage_decision",
        "stage_scope",
        "requested_stage",
        "user_request",
        "request_text",
        "prompt",
        "expected_output",
        "requested_output",
        "work_order",
        *USER_TTS_OR_SRT_PATH_KEYS,
    )
    for index, source in enumerate(collect_status_sources(contract, root)):
        for key in scope_keys:
            if key not in merged and source.get(key):
                if key in STAGE_SCOPE_DECISION_KEYS and is_stage2_decision(source.get(key)):
                    if not status_source_allows_stage2_decision(source, source.get(key)):
                        continue
                    verified_stage2_decision = True
                merged[key] = source[key]
        if index > 0 and status_source_allows_report1_voice_decision(source):
            for key in (*REPORT1_APPROVAL_KEYS, *VOICE_AUDIO_ROUTE_DECISION_KEYS):
                if key not in merged and source.get(key):
                    merged[key] = source[key]
        stage_scope_gate = source.get("stage_scope_gate")
        if isinstance(stage_scope_gate, dict) and "user_stage_decision" not in merged:
            decision = stage_scope_gate.get("decision")
            if decision and is_stage2_decision(decision):
                if not status_source_allows_stage2_decision(source, decision):
                    continue
                verified_stage2_decision = True
                merged["user_stage_decision"] = decision
            elif decision:
                merged["user_stage_decision"] = decision
    if verified_stage2_decision:
        merged["_stage_scope_gate_verified"] = True
    return merged


def upload_ready_state(contract: dict[str, Any], *, stage: str) -> dict[str, Any]:
    user_approved = contract.get("user_upload_approval") is True
    rights_acknowledged = contract.get("rights_risk_acknowledged") is True
    allowed = stage == "production" and user_approved and rights_acknowledged
    if allowed:
        return {
            "upload_ready_allowed": True,
            "upload_ready": True,
            "upload_ready_reason": "USER_APPROVAL_AND_RIGHTS_CHECK_PRESENT",
        }
    reason = (
        "CAPCUT_OPENABLE_PROJECT_IS_NOT_UPLOAD_READY"
        if stage != "production"
        else "WAITING_FOR_USER_APPROVAL_AND_RIGHTS_CHECK"
    )
    return {
        "upload_ready_allowed": False,
        "upload_ready": False,
        "upload_ready_reason": reason,
    }


def validate_declared_input_hashes(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    declared = contract.get("input_files") or contract.get("declared_input_files") or []
    if not declared:
        raise GateFail("input_files must include at least one hashed input file")
    if not isinstance(declared, list):
        raise GateFail("input_files must be a list")

    verified = 0
    for index, item in enumerate(declared):
        if isinstance(item, str):
            raise GateFail(f"input_files[{index}] sha256 required; use object form")
        if not isinstance(item, dict):
            raise GateFail(f"input_files[{index}] must be a path string or object")
        raw_path = item.get("path") or item.get("file") or item.get("rel_path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise GateFail(f"input_files[{index}] path missing")
        path = require_file(root, raw_path, f"input_files[{index}]")
        expected_hash = item.get("sha256") or item.get("sha_256")
        if not isinstance(expected_hash, str) or not expected_hash.strip():
            raise GateFail(f"input_files[{index}] sha256 missing")
        actual_hash = sha256_file(path)
        if actual_hash.lower() != expected_hash.strip().lower():
            raise GateFail(
                f"input_files[{index}] sha256 mismatch: {raw_path}"
            )
        verified += 1
    return {"input_file_hashes_verified": True, "input_file_count": verified}


def source_segment_ids(source_segments: list[Any]) -> list[str]:
    ids: list[str] = []
    for index, item in enumerate(source_segments):
        if isinstance(item, str):
            ids.append(item)
            continue
        if not isinstance(item, dict):
            raise GateFail(f"cut_manifest.source_segments[{index}] must be object or string")
        segment_id = (
            item.get("id")
            or item.get("segment_id")
            or item.get("source_segment_id")
            or item.get("clip")
            or item.get("clip_id")
        )
        if segment_id in (None, ""):
            raise GateFail(f"cut_manifest.source_segments[{index}] id missing")
        ids.append(str(segment_id))
    return ids


def validate_contact_sheet_file(path: Path) -> None:
    data = path.read_bytes()
    is_jpeg = len(data) >= 4 and data.startswith(b"\xff\xd8") and data.endswith(b"\xff\xd9")
    is_png = len(data) >= 8 and data.startswith(b"\x89PNG\r\n\x1a\n")
    if not is_jpeg and not is_png:
        raise GateFail("contact_sheet must be a readable JPEG or PNG proof image")


def validate_clip_durations_csv(path: Path, required_ids: list[str]) -> None:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    if not rows:
        raise GateFail("clip_durations.csv must contain PASS rows")
    seen: set[str] = set()
    for row in rows:
        clip_id = (
            row.get("clip")
            or row.get("id")
            or row.get("segment_id")
            or row.get("source_segment_id")
        )
        if not clip_id:
            continue
        status = str(row.get("status") or row.get("result") or "").strip().upper()
        if str(clip_id) in required_ids:
            if status != "PASS":
                raise GateFail(f"clip_durations.csv row is not PASS: {clip_id}")
            seen.add(str(clip_id))
    missing = [segment_id for segment_id in required_ids if segment_id not in seen]
    if missing:
        raise GateFail("clip_durations.csv missing PASS rows: " + ", ".join(missing))


def validate_timeline_order_text(path: Path, expected_order: list[str]) -> None:
    actual_order = [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    if actual_order != expected_order:
        raise GateFail(
            f"timeline_order.txt mismatch: expected={expected_order}, actual={actual_order}"
        )


def validate_production_proof_files(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    sources = collect_status_sources(contract, root)
    paths: dict[str, str] = {}
    for keys, default_path, label in PRODUCTION_PROOF_PATHS:
        rel_path = default_or_declared_path(sources, keys, default_path)
        path = require_file(root, rel_path, label)
        paths[f"{label}_path"] = str(path)

    cut_manifest = load_json(Path(paths["cut_manifest_path"]))
    source_segments = cut_manifest.get("source_segments")
    timeline_order = cut_manifest.get("timeline_order")
    if not isinstance(source_segments, list) or not source_segments:
        raise GateFail("cut_manifest.source_segments must be a non-empty list")
    if not isinstance(timeline_order, list) or not timeline_order:
        raise GateFail("cut_manifest.timeline_order must be a non-empty list")
    required_segment_ids = source_segment_ids(source_segments)
    timeline_order_ids = [str(item) for item in timeline_order]
    unknown = sorted(set(timeline_order_ids) - set(required_segment_ids))
    missing = [segment_id for segment_id in required_segment_ids if segment_id not in timeline_order_ids]
    if unknown:
        raise GateFail("cut_manifest.timeline_order contains unknown segment ids: " + ", ".join(unknown))
    if missing:
        raise GateFail("cut_manifest.timeline_order missing segment ids: " + ", ".join(missing))
    validate_contact_sheet_file(Path(paths["contact_sheet_path"]))
    validate_clip_durations_csv(Path(paths["clip_durations_path"]), required_segment_ids)
    validate_timeline_order_text(Path(paths["timeline_order_path"]), timeline_order_ids)

    assembly_report = load_json(Path(paths["capcut_assembly_report_path"]))
    assembly_status = status_value(assembly_report)
    if assembly_status and assembly_status != "PASS":
        raise GateFail("capcut_assembly_report status must be PASS")
    missing_flags = [
        key for key in CAPCUT_ASSEMBLY_PROOF_FLAGS
        if assembly_report.get(key) is not True
    ]
    if missing_flags:
        raise GateFail(
            "capcut_assembly_report missing true flags: " + ", ".join(missing_flags)
        )

    return {
        "hard_fail_proof_status": "PASS",
        **paths,
    }


def normalize_voice_switch_map(raw_value: Any) -> list[dict[str, Any]]:
    if isinstance(raw_value, dict):
        raw_value = raw_value.get("switches") or raw_value.get("block_voice_switch_map")
    if not isinstance(raw_value, list):
        return []
    return [item for item in raw_value if isinstance(item, dict)]


def validate_handoff_block_map(block_map: dict[str, Any], label: str = "block_map.json") -> None:
    sequence = block_map.get("edit_block_sequence")
    blocks = block_map.get("blocks") or block_map.get("edit_blocks")
    voice_switch_map = normalize_voice_switch_map(
        block_map.get("block_voice_switch_map") or block_map.get("voice_switches")
    )

    if not isinstance(sequence, list) or not sequence:
        raise GateFail(f"WAIT_SCRIPT_HANDOFF_GATE: {label} edit_block_sequence missing")
    if not isinstance(blocks, list) or not blocks:
        raise GateFail(f"WAIT_SCRIPT_HANDOFF_GATE: {label} blocks missing")
    if not voice_switch_map:
        raise GateFail(f"WAIT_SCRIPT_HANDOFF_GATE: {label} block_voice_switch_map missing")

    required = {"edit_id", "source_block_id", "original_order", "urakkai_order"}
    block_ids: list[str] = []
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise GateFail(f"WAIT_SCRIPT_HANDOFF_GATE: {label} blocks[{index}] must be object")
        missing = sorted(key for key in required if block.get(key) in (None, ""))
        if missing:
            raise GateFail(
                f"WAIT_SCRIPT_HANDOFF_GATE: {label} blocks[{index}] missing {', '.join(missing)}"
            )
        block_ids.append(str(block["edit_id"]))

    sequence_ids = [str(item) for item in sequence]
    if sequence_ids != block_ids:
        raise GateFail(
            f"WAIT_SCRIPT_HANDOFF_GATE: {label} edit_block_sequence must match blocks edit_id order"
        )

    switch_ids: list[str] = []
    for index, switch in enumerate(voice_switch_map):
        edit_id = switch.get("edit_id")
        if edit_id in (None, ""):
            raise GateFail(f"WAIT_SCRIPT_HANDOFF_GATE: {label} voice switch missing edit_id")
        if switch.get("source_audio") in (None, "") or switch.get("tts") in (None, ""):
            raise GateFail(
                f"WAIT_SCRIPT_HANDOFF_GATE: {label} voice switch {edit_id} missing source_audio or tts"
            )
        switch_ids.append(str(edit_id))

    if sorted(switch_ids) != sorted(block_ids) or len(set(switch_ids)) != len(switch_ids):
        raise GateFail(
            f"WAIT_SCRIPT_HANDOFF_GATE: {label} voice switch coverage must match every edit block"
        )


def validate_script_handoff_gate(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    sources = collect_status_sources(contract, root)
    gate_rel_path = default_or_declared_path(
        sources,
        SCRIPT_HANDOFF_GATE_PATH_KEYS,
        "20_script/script_handoff_gate.json",
    )
    gate_path = as_path(root, gate_rel_path)
    if not gate_path.exists():
        raise GateFail(f"WAIT_SCRIPT_HANDOFF_GATE: script_handoff_gate.json file missing: {gate_path}")
    gate = load_json(gate_path)

    if gate.get("gate_name") != "SCRIPT_HANDOFF_GATE":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: gate_name must be SCRIPT_HANDOFF_GATE")
    if str(gate.get("status") or "").upper() != "PASS":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: script_handoff_gate status must be PASS")
    if gate.get("script_status") != "SCRIPT_LOCK_PACKAGE":
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: script_status must be SCRIPT_LOCK_PACKAGE")
    if gate.get("capcut_allowed") is not True:
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: capcut_allowed must be true")
    generator = str(gate.get("generated_by") or "").strip()
    if generator not in ALLOWED_SCRIPT_HANDOFF_GATE_GENERATORS:
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: script_handoff_gate must be validator generated")

    block_map_rel_path = (
        first_status_value(sources, BLOCK_MAP_PATH_KEYS)
        or gate.get("block_map_path")
        or "20_script/block_map.json"
    )
    if not isinstance(block_map_rel_path, str) or not block_map_rel_path.strip():
        raise GateFail("WAIT_SCRIPT_HANDOFF_GATE: block_map.json path missing")
    block_map_path = require_declared_file(root, block_map_rel_path, "block_map", gate_path.parent)
    block_map = load_json(block_map_path)
    voice_map_rel_path = (
        first_status_value(sources, BLOCK_VOICE_SWITCH_MAP_PATH_KEYS)
        or gate.get("block_voice_switch_map_path")
        or gate.get("voice_switch_map_path")
    )
    if not voice_map_rel_path:
        for input_file in gate.get("input_files") or []:
            if isinstance(input_file, str) and "voice_switch" in input_file:
                voice_map_rel_path = input_file
                break
    if isinstance(voice_map_rel_path, str) and voice_map_rel_path.strip():
        voice_map_path = require_declared_file(
            root,
            voice_map_rel_path,
            "block_voice_switch_map",
            gate_path.parent,
        )
        block_map["block_voice_switch_map"] = normalize_voice_switch_map(load_json(voice_map_path))
    validate_handoff_block_map(block_map)

    for input_file in gate.get("input_files") or []:
        if isinstance(input_file, str) and input_file.strip():
            require_declared_file(root, input_file, "gate input file", gate_path.parent)

    return {
        "script_handoff_gate_status": "PASS",
        "script_handoff_gate_path": str(gate_path),
        "script_status": "SCRIPT_LOCK_PACKAGE",
        "block_map_path": str(block_map_path),
        "capcut_permission": "CAPCUT_OPENABLE_PROJECT_ALLOWED",
    }


def report1_handoff_gate_path(sources: list[dict[str, Any]], root: Path) -> Path:
    declared = first_status_value(sources, REPORT1_HANDOFF_GATE_PATH_KEYS)
    if isinstance(declared, str) and declared.strip():
        return as_path(root, declared)
    for rel_path in ("20_script/report1_handoff.json", "report1_handoff.json"):
        candidate = as_path(root, rel_path)
        if candidate.exists():
            return candidate
    return as_path(root, "20_script/report1_handoff.json")


def validate_report1_handoff_gate(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    sources = collect_status_sources(contract, root)
    gate_path = report1_handoff_gate_path(sources, root)
    if not gate_path.exists():
        raise GateFail(f"WAIT_REPORT1_HANDOFF_GATE: report1_handoff.json file missing: {gate_path}")
    gate = load_json(gate_path)

    if gate.get("gate_name") != "REPORT1_HANDOFF_GATE":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: gate_name must be REPORT1_HANDOFF_GATE")
    if str(gate.get("status") or "").upper() != "PASS":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: report1_handoff status must be PASS")
    if gate.get("owner_skill") != "00-tikitaka":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: owner_skill must be 00-tikitaka")
    if gate.get("next_skill") != "000short-production-agent":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: next_skill must be 000short-production-agent")
    if gate.get("next_gate") != "CAPCUT_OPENABLE_PROJECT":
        raise GateFail("WAIT_REPORT1_HANDOFF_GATE: next_gate must be CAPCUT_OPENABLE_PROJECT")

    return {
        "report1_handoff_gate_status": "PASS",
        "report1_handoff_gate_path": str(gate_path),
        "report1_handoff_owner_skill": gate["owner_skill"],
        "report1_handoff_next_skill": gate["next_skill"],
        "report1_handoff_next_gate": gate["next_gate"],
    }


def report_scalar(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, list):
        return " ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def first_report_field(
    sources: list[dict[str, Any]],
    source_manifest: dict[str, Any],
    keys: tuple[str, ...],
) -> str:
    value = first_status_value(sources, keys)
    text = report_scalar(value)
    if text:
        return text
    for key in keys:
        text = report_scalar(source_manifest.get(key))
        if text:
            return text
    return ""


def report_yes_no(value: Any, default: str = "아니오") -> str:
    if value in (None, ""):
        return default
    return "예" if truthy(value) else "아니오"


def normalized_reference_text(value: Any) -> str:
    return " ".join(report_scalar(value).lower().split())


def is_default_capcut_base_name(value: Any) -> bool:
    return normalized_reference_text(value) in DEFAULT_CAPCUT_BASE_ALIASES


def is_default_capcut_base_profile(value: Any) -> bool:
    return normalized_reference_text(value) in DEFAULT_CAPCUT_BASE_PROFILE_ALIASES


def is_forbidden_derived_reference_name(value: Any) -> bool:
    text = report_scalar(value)
    normalized = normalized_reference_text(text)
    if normalized in {item.lower() for item in FORBIDDEN_DERIVED_REFERENCE_PROJECTS}:
        return True
    text_lc = text.lower()
    return any(marker in text_lc for marker in FORBIDDEN_DERIVED_REFERENCE_MARKERS)


def stale_derived_builder_reference_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel_dir in ("90_reports", "50_capcut_project", "scripts"):
        base = root / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("build*.py"):
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="ignore")
            if "REFERENCE_NAME" not in text:
                continue
            if any(name in text for name in FORBIDDEN_DERIVED_REFERENCE_PROJECTS):
                files.append(path)
                continue
            text_lc = text.lower()
            if any(marker in text_lc for marker in FORBIDDEN_DERIVED_REFERENCE_MARKERS):
                files.append(path)
    return files


def user_explicit_template_override(sources: list[dict[str, Any]]) -> bool:
    return truthy(first_status_value(sources, USER_EXPLICIT_TEMPLATE_OVERRIDE_KEYS))


def validate_default_capcut_base_policy(
    sources: list[dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    stale_reference_name = first_status_value(sources, STALE_BUILDER_REFERENCE_NAME_KEYS)
    if is_forbidden_derived_reference_name(stale_reference_name):
        raise GateFail(
            "FAIL_STALE_DERIVED_REFERENCE_BUILDER: stale builder REFERENCE_NAME points to "
            f"{report_scalar(stale_reference_name)}; default CapCut base must be shrt white"
        )

    stale_files = stale_derived_builder_reference_files(root)
    if stale_files:
        stale_list = ", ".join(str(path) for path in stale_files)
        raise GateFail(
            "FAIL_STALE_DERIVED_REFERENCE_BUILDER: stale build script uses a prior derived "
            f"reference project; remove/ignore it before CapCut build: {stale_list}"
        )

    reference_name = report_scalar(first_status_value(sources, TEMPLATE_REFERENCE_NAME_KEYS))
    profile = report_scalar(first_status_value(sources, TEMPLATE_PROFILE_KEYS))
    override = user_explicit_template_override(sources)
    if override:
        if not reference_name or not profile:
            raise GateFail(
                "FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED: explicit template override requires "
                "reference_project_name and template_profile"
            )
        return {
            "default_capcut_base_gate": "USER_OVERRIDE",
            "default_capcut_base_project": "USER_EXPLICIT_OVERRIDE",
            "default_capcut_base_profile": profile,
        }

    if not reference_name:
        raise GateFail(
            "WAIT_SHRT_WHITE_BASE_REQUIRED: default CapCut base must be shrt white; "
            "do not fall back to prior episode builders or derived projects"
        )
    if not is_default_capcut_base_name(reference_name):
        raise GateFail(
            "FAIL_DEFAULT_SHRT_WHITE_BASE_REQUIRED: default CapCut base must be shrt white; "
            f"got {reference_name}"
        )
    if not profile:
        raise GateFail(
            "WAIT_SHRT_WHITE_BASE_REQUIRED: template_profile must be shrt_white_base_v1 "
            "for the default shrt white base"
        )
    if not is_default_capcut_base_profile(profile):
        raise GateFail(
            "FAIL_DEFAULT_SHRT_WHITE_BASE_REQUIRED: template_profile must be "
            f"shrt_white_base_v1 for shrt white; got {profile}"
        )

    reference_path_raw = report_scalar(first_status_value(sources, TEMPLATE_REFERENCE_PATH_KEYS))
    if not reference_path_raw:
        raise GateFail(
            "WAIT_SHRT_WHITE_BASE_REQUIRED: reference_project_path for shrt white is missing"
        )
    reference_path = Path(reference_path_raw)
    if not reference_path.is_absolute():
        reference_path = root / reference_path
    if not reference_path.exists():
        raise GateFail(
            f"WAIT_SHRT_WHITE_BASE_MISSING: shrt white reference_project_path not found: {reference_path}"
        )
    if not truthy(first_status_value(sources, TEMPLATE_REFERENCE_DERIVED_KEYS)):
        raise GateFail(
            "FAIL_SHRT_WHITE_BASE_NOT_CLONED: CapCut draft must be cloned/derived from shrt white"
        )

    return {
        "default_capcut_base_gate": "PASS",
        "default_capcut_base_project": DEFAULT_CAPCUT_BASE_PROJECT,
        "default_capcut_base_profile": DEFAULT_CAPCUT_BASE_PROFILE,
        "default_capcut_base_path": str(reference_path),
    }


def template_reference_required(sources: list[dict[str, Any]]) -> bool:
    required_raw = first_status_value(sources, TEMPLATE_REFERENCE_REQUIRED_KEYS)
    if required_raw not in (None, ""):
        return truthy(required_raw)

    if report_scalar(first_status_value(sources, TEMPLATE_PROFILE_KEYS)):
        return True
    if report_scalar(first_status_value(sources, TEMPLATE_REFERENCE_NAME_KEYS)):
        return True
    if report_scalar(first_status_value(sources, TEMPLATE_REFERENCE_PATH_KEYS)):
        return True

    request_text = " ".join(
        report_scalar(first_status_value(sources, (key,)))
        for key in ("user_request", "operator_request", "production_request")
    ).lower()
    return any(
        token in request_text
        for token in (
            "reference project",
            "template project",
            "capcut reference",
            "character-comments",
            "game-character-comments",
            "기준",
            "템플릿",
        )
    )


def validate_template_reference_resolution(
    sources: list[dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    if not template_reference_required(sources):
        return {
            "template_reference_resolution_gate": "NOT_REQUIRED",
            "reference_project_name": "",
            "reference_project_path": "",
        }

    reference_name = report_scalar(first_status_value(sources, TEMPLATE_REFERENCE_NAME_KEYS))
    if not reference_name:
        raise GateFail("FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED: reference_project_name missing")
    if is_forbidden_derived_reference_name(reference_name):
        raise GateFail(
            "FAIL_TEMPLATE_ROOT_NOT_RESOLVED: "
            f"{reference_name} is a prior derived project, not a root CapCut template authority"
        )

    reference_path_raw = report_scalar(first_status_value(sources, TEMPLATE_REFERENCE_PATH_KEYS))
    if not reference_path_raw:
        raise GateFail("FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED: reference_project_path missing")

    reference_path = Path(reference_path_raw)
    if not reference_path.is_absolute():
        reference_path = root / reference_path
    if not reference_path.exists():
        raise GateFail(f"FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED: reference_project_path not found: {reference_path}")

    profile = report_scalar(first_status_value(sources, TEMPLATE_PROFILE_KEYS))
    profile_text = f"{profile} {reference_name}".lower()
    if "character" in profile_text and "comment" in profile_text:
        if reference_name == CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT:
            raise GateFail(
                "FAIL_TEMPLATE_ROOT_NOT_RESOLVED: "
                f"{CHARACTER_COMMENTS_DERIVED_REFERENCE_PROJECT} is a prior derived project, "
                "not the root character-comments template authority"
            )

    if not truthy(first_status_value(sources, TEMPLATE_REFERENCE_DERIVED_KEYS)):
        raise GateFail(
            "FAIL_TEMPLATE_REFERENCE_MISMATCH: derived_from_reference_project must be true"
        )

    return {
        "template_reference_resolution_gate": "PASS",
        "reference_project_name": reference_name,
        "reference_project_path": str(reference_path),
        "template_profile": profile,
        "derived_from_reference_project": True,
    }


def build_report2_openable_report(result: dict[str, Any]) -> str:
    project_name = result.get("capcut_project_name") or "N/A"
    local_path = result.get("local_capcut_path") or "N/A"
    reference_project_name = result.get("reference_project_name") or "N/A"
    reference_project_path = result.get("reference_project_path") or "N/A"
    upload_title = result.get("upload_title") or "N/A"
    upload_description = result.get("upload_description") or "N/A"
    source_tag = result.get("source_tag") or result.get("source_url") or "N/A"
    upload_tags = result.get("upload_tags") or "N/A"
    script_reflected = result.get("script_reflected") or "아니오"
    tts_audio_reflected = result.get("tts_audio_reflected") or "아니오"
    subtitle_reflected = result.get("subtitle_reflected") or "아니오"
    source_video_reflected = result.get("source_video_reflected") or "아니오"
    temp_files_cleaned = result.get("temp_files_cleaned") or "아니오"
    return "\n".join(
        [
            "# 보고서2",
            "",
            "보고서2 시작: 예",
            "최종보고서: 예",
            "상태: REPORT2_FINAL",
            "CapCut 프로젝트 생성 후 보고: 예",
            f"CapCut 프로젝트명: {project_name}",
            f"local_capcut_path: {local_path}",
            f"reference_project_name: {reference_project_name}",
            f"reference_project_path: {reference_project_path}",
            "CapCut 열어보기 필요: 예",
            "사용자 확인 대기: 예",
            "업로드 준비 완료: 아니오",
            "최종 잠금: 아니오",
            "",
            f"제목: {upload_title}",
            "",
            "내용(출처 태그 포함):",
            str(upload_description).rstrip(),
            f"출처: {source_tag}",
            f"태그: {upload_tags}",
            "",
            f"대본 반영: {script_reflected}",
            f"TTS/오디오 반영: {tts_audio_reflected}",
            f"자막 반영: {subtitle_reflected}",
            f"원본 영상 반영: {source_video_reflected}",
            f"임시파일 정리: {temp_files_cleaned}",
            "",
            "현재 기준:",
            f"- project_file_request_mode: {result.get('project_file_request_mode', 'N/A')}",
            f"- script_handoff_gate_status: {result.get('script_handoff_gate_status', 'N/A')}",
            f"- source_manifest_path: {result.get('source_manifest_path', 'N/A')}",
            f"- draft_content_path: {result.get('draft_content_path', 'N/A')}",
            f"- draft_meta_info_path: {result.get('draft_meta_info_path', 'N/A')}",
            f"- template_reference_resolution_gate: {result.get('template_reference_resolution_gate', 'N/A')}",
            f"- reference_project_name: {reference_project_name}",
            f"- reference_project_path: {reference_project_path}",
            f"- upload_ready_reason: {result.get('upload_ready_reason', 'N/A')}",
            "",
            "남은 일:",
            "- 사용자가 CapCut에서 문제를 제시하면 수정 후 다시 보고서2",
            "- 사용자가 직접 내보내기로 영상을 만들면 REPORT2_CLOSED_BY_USER_EXPORT",
            "",
        ]
    )


def validate_capcut_openable_project_entry(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    """Validate only the second-stage CapCut-openable entry contract.

    This gate intentionally does not require FINAL_LOCK writer/persona, n8n, or
    upload-readiness fields. Those remain owned by validate_shared_requirements.
    """

    request_mode = project_file_request_mode(merged_request_scope_contract(contract, root))
    report1_handoff_result = validate_report1_handoff_gate(contract, root)
    script_handoff_result = validate_script_handoff_gate(contract, root)
    sources = collect_status_sources(contract, root)
    default_capcut_base_result = validate_default_capcut_base_policy(sources, root)
    template_reference_result = validate_template_reference_resolution(sources, root)
    source_manifest_rel_path = (
        first_status_value(
            sources,
            (
                "source_manifest_path",
                "source_manifest_json",
                "source_manifest",
            ),
        )
        or "00_source/source_manifest.json"
    )
    if not isinstance(source_manifest_rel_path, str) or not source_manifest_rel_path.strip():
        raise GateFail("source_manifest_path missing before CAPCUT_OPENABLE_PROJECT")
    source_manifest_path = require_file(root, source_manifest_rel_path, "source_manifest")
    source_manifest = load_json(source_manifest_path)
    if status_value(source_manifest) != "PASS":
        raise GateFail(f"source_manifest status must be PASS: {source_manifest_path}")
    draft_content_rel_path = default_or_declared_path(
        sources,
        CAPCUT_DRAFT_CONTENT_PATH_KEYS,
        "50_capcut_project/draft_content.json",
    )
    draft_content_path = require_file(root, draft_content_rel_path, "draft_content")
    load_json(draft_content_path)
    capcut_project_name = first_status_value(sources, ("capcut_project_name", "project_name"))
    local_capcut_path = first_status_value(sources, ("local_capcut_path", "capcut_local_path"))
    upload_title = first_report_field(
        sources,
        source_manifest,
        ("upload_title", "youtube_title", "shorts_title", "video_title", "title"),
    )
    upload_description = first_report_field(
        sources,
        source_manifest,
        ("upload_description", "youtube_description", "description", "content", "body"),
    )
    source_tag = first_report_field(
        sources,
        source_manifest,
        ("source_tag", "source_credit", "source_url", "url", "original_url"),
    )
    upload_tags = first_report_field(
        sources,
        source_manifest,
        ("upload_tags", "hashtags", "tags"),
    )
    draft_meta_info_path = first_report_field(
        sources,
        source_manifest,
        ("draft_meta_info_path", "draft_meta_path", "draft_meta_info"),
    )
    script_reflected = "예" if script_handoff_result.get("script_handoff_gate_status") == "PASS" else "아니오"
    tts_audio_reflected = report_yes_no(
        first_status_value(sources, ("tts_audio_reflected", "tts_reflected", "audio_reflected", "tts_audio_applied"))
    )
    subtitle_reflected = report_yes_no(
        first_status_value(sources, ("subtitle_reflected", "srt_reflected", "caption_reflected", "subtitles_applied"))
    )
    source_video_reflected = report_yes_no(
        first_status_value(sources, ("source_video_reflected", "original_video_reflected", "source_media_applied"))
    )
    temp_files_cleaned = report_yes_no(
        first_status_value(sources, ("temp_files_cleaned", "cleanup_done", "project_cleanup_passed"))
    )

    result = {
        "status": "CAPCUT_OPENABLE_PROJECT_ALLOWED",
        "mode": "CAPCUT_OPENABLE_PROJECT",
        "project_file_request_mode": request_mode,
        "script_handoff_gate_status": script_handoff_result["script_handoff_gate_status"],
        "report1_handoff_gate_status": report1_handoff_result["report1_handoff_gate_status"],
        "report1_handoff_gate_path": report1_handoff_result["report1_handoff_gate_path"],
        "script_status": script_handoff_result["script_status"],
        "capcut_permission": script_handoff_result["capcut_permission"],
        "block_map_path": script_handoff_result["block_map_path"],
        "source_manifest_path": str(source_manifest_path),
        "draft_content_path": str(draft_content_path),
        "draft_meta_info_path": draft_meta_info_path,
        "capcut_project_name": capcut_project_name or "",
        "local_capcut_path": local_capcut_path or "",
        "upload_title": upload_title,
        "upload_description": upload_description,
        "source_tag": source_tag,
        "upload_tags": upload_tags,
        "script_reflected": script_reflected,
        "tts_audio_reflected": tts_audio_reflected,
        "subtitle_reflected": subtitle_reflected,
        "source_video_reflected": source_video_reflected,
        "temp_files_cleaned": temp_files_cleaned,
        **default_capcut_base_result,
        **template_reference_result,
        "next_gate": "ASSET_PREP_GATE",
        "final_lock_required": False,
        **upload_ready_state(contract, stage="capcut-openable"),
    }
    result["report2"] = build_report2_openable_report(result)
    return result


def require_scalar_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise GateFail(f"{label} must be a non-empty list")
    for item in value:
        if not isinstance(item, (int, str)):
            raise GateFail(f"{label} items must be int or string values: {value}")
    return value


def require_unique_order(value: Any, label: str) -> list[Any]:
    order = require_scalar_list(value, label)
    if len(order) != len(set(order)):
        raise GateFail(f"{label} must not contain duplicate beats: {order}")
    return order


def first_list(data: dict[str, Any], keys: tuple[str, ...]) -> list[Any] | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, list) and value:
            return value
    return None


def first_list_from_sources(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> list[Any] | None:
    for source in sources:
        value = first_list(source, keys)
        if value is not None:
            return value
    return None


def source_list_value(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> list[Any]:
    value = first_list_from_sources(sources, keys)
    if value is None:
        return []
    return value


def first_number_value(sources: list[dict[str, Any]], keys: tuple[str, ...]) -> float | None:
    raw_value = first_status_value(sources, keys)
    if raw_value in (None, ""):
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError) as exc:
        raise GateFail(f"{keys[0]} must be a number") from exc


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


def parse_catcup_role_order(value: Any, label: str) -> list[str]:
    normalized: list[str] = []
    for raw_item in parse_order_items(value, label):
        role = normalize_catcup_role(raw_item)
        if role not in CATCUP_REQUIRED_ROLE_ORDER:
            raise GateFail(f"{label} has unsupported CatCup role: {raw_item}")
        normalized.append(role)
    return normalized


def catcup_row_active(row: dict[str, Any]) -> bool:
    if row.get("active") is False:
        return False
    status = str(row.get("status") or row.get("row_status") or "").strip().upper()
    if status in {"N/A", "NA", "INACTIVE", "OFF", "DISABLED"}:
        return False
    return True


def catcup_source_speech_present(sources: list[dict[str, Any]]) -> bool:
    raw = first_status_value(sources, CATCUP_SOURCE_SPEECH_PRESENT_KEYS)
    return truthy(raw)


def validate_catcup_script_rewrite_policy(sources: list[dict[str, Any]]) -> dict[str, Any]:
    creative_raw = first_status_value(sources, CATCUP_CREATIVE_ADDITIONS_KEYS)
    if not truthy(creative_raw):
        raise GateFail(
            "creative additions must use TTS/plain narration or situation_emotion captions only; do not invent source quotes"
        )
    word_status = str(first_status_value(sources, CATCUP_WORD_REWRITE_STATUS_KEYS) or "").strip().upper()
    if word_status != "PASS":
        raise GateFail(
            "source_word_synonym_rewrite_status must be PASS; rewrite source words with different synonyms except verified quotes, names, numbers, or unavoidable nouns"
        )
    return {
        "creative_additions_use_tts_or_situation_only": True,
        "source_word_synonym_rewrite_status": "PASS",
    }


def validate_catcup_reference_layout_gate(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
) -> dict[str, Any]:
    sources = [contract, render_plan]
    script_rewrite_result = validate_catcup_script_rewrite_policy(sources)
    required_raw = first_status_value(sources, CATCUP_LAYOUT_REQUIRED_KEYS)
    required = True if required_raw is None else truthy(required_raw)
    if not required:
        raise GateFail("catcup_reference_layout_required must be true")

    profile = str(first_status_value(sources, CATCUP_LAYOUT_PROFILE_KEYS) or "").strip()
    template = CATCUP_TEMPLATE_MASTERS.get(profile)
    if template is None:
        raise GateFail(
            "catcup_reference_layout_profile must be one of "
            f"{sorted(CATCUP_TEMPLATE_MASTERS)}"
        )

    reference_project = str(first_status_value(sources, CATCUP_REFERENCE_PROJECT_KEYS) or "").strip()
    if reference_project not in template["accepted_reference_projects"]:
        raise GateFail(
            "catcup_reference_project must be "
            f"{template['reference_project']}"
        )

    rows = source_list_value(sources, CATCUP_TEXT_ROLE_ROWS_KEYS)
    if not rows:
        raise GateFail("catcup_text_role_rows must describe role-separated CapCut text rows")

    order_raw = first_status_value(sources, CATCUP_ROLE_ORDER_KEYS)
    if order_raw not in (None, ""):
        declared_order = parse_catcup_role_order(order_raw, "catcup_text_role_order_top_to_bottom")
    else:
        declared_order = []

    seen_roles: set[str] = set()
    active_roles: list[str] = []
    role_indexes: dict[str, int] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise GateFail(f"catcup_text_role_rows[{idx}] must be an object")
        role = normalize_catcup_role(
            row.get("role")
            or row.get("text_role")
            or row.get("track_role")
            or row.get("caption_role")
        )
        if role not in CATCUP_REQUIRED_ROLE_ORDER:
            raise GateFail(f"catcup_text_role_rows[{idx}] has invalid role: {role or '<empty>'}")
        if role in seen_roles:
            raise GateFail(f"catcup_text_role_rows duplicate role: {role}")
        seen_roles.add(role)
        if catcup_row_active(row):
            active_roles.append(role)
            role_indexes[role] = idx
            if not (row.get("track_id") or row.get("planned_track_id") or row.get("track_name") or row.get("row_index")):
                raise GateFail(f"active catcup role {role} must include track_id/planned_track_id/row_index")

    missing = CATCUP_REQUIRED_ACTIVE_ROLES - set(active_roles)
    if missing:
        raise GateFail(f"catcup_text_role_rows missing active required roles: {sorted(missing)}")

    if catcup_source_speech_present(sources) and "source_speech_1" not in active_roles:
        raise GateFail("verified source/original dialogue exists, so source_speech_1 must be active")

    if "source_speech_2" in active_roles and "source_speech_1" not in active_roles:
        raise GateFail("source_speech_2 cannot be active without source_speech_1")

    if declared_order:
        missing_order = set(active_roles) - set(declared_order)
        if missing_order:
            raise GateFail(f"catcup_text_role_order_top_to_bottom missing active roles: {sorted(missing_order)}")
        ordered_active = [role for role in declared_order if role in active_roles]
    else:
        ordered_active = active_roles

    canonical_positions = {role: idx for idx, role in enumerate(CATCUP_REQUIRED_ROLE_ORDER)}
    if ordered_active != sorted(ordered_active, key=lambda role: canonical_positions[role]):
        raise GateFail(
            "catcup text rows must follow the CapCut T1~T6 track order: "
            + " > ".join(CATCUP_REQUIRED_ROLE_ORDER)
        )

    return {
        "catcup_reference_layout_required": True,
        "catcup_reference_layout_profile": profile,
        "catcup_reference_project": template["reference_project"],
        "catcup_text_role_order_top_to_bottom": ordered_active,
        "catcup_active_text_role_count": len(active_roles),
        "catcup_text_role_rows": rows,
        **script_rewrite_result,
    }


def require_track_order(
    sources: list[dict[str, Any]],
    keys: tuple[str, ...],
    required: tuple[str, ...],
    label: str,
) -> list[str]:
    raw_value = first_status_value(sources, keys)
    if raw_value in (None, "", [], {}):
        raise GateFail(f"{label} is required")
    order = parse_track_order(raw_value, label)
    if order != list(required):
        raise GateFail(f"{label} must be {list(required)}, got {order}")
    return order


def truthy_item(item: dict[str, Any], keys: tuple[str, ...]) -> bool:
    value = first_item_value(item, keys)
    return truthy(value)


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
        first = text.split("-", 1)[0].strip()
        return normalize_seconds(first)
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
        text = raw_range.strip().replace("~", "-")
        parts = text.split("-", 1)
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
    if not visual_role(raw_item):
        raise GateFail(f"{label} must include visual_role/video_role for TTS visual fill")


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


def validate_three_line_text_layout_gate(contract: dict[str, Any], render_plan: dict[str, Any]) -> dict[str, Any]:
    sources = [contract, render_plan]
    required_raw = first_status_value(sources, THREE_LINE_TEXT_LAYOUT_REQUIRED_KEYS)
    required = True if required_raw is None else truthy(required_raw)
    if not required:
        raise GateFail("three_line_text_layout_required must be true")
    status = str(first_status_value(sources, THREE_LINE_TEXT_LAYOUT_STATUS_KEYS) or "").strip().upper()
    if status != "PASS":
        raise GateFail("three_line_text_layout_status must be PASS")
    text_track_order = require_track_order(
        sources,
        TEXT_TRACK_ORDER_KEYS,
        REQUIRED_TEXT_TRACK_ORDER,
        "middle_text_track_order_top_to_bottom",
    )
    return {
        "three_line_text_layout_required": True,
        "three_line_text_layout_status": "PASS",
        "text_layer_rows": {
            "1": "hook_or_dialogue_line",
            "2": "emotion_or_situation_line",
            "3": "tts_caption_line",
        },
        "middle_text_track_order_top_to_bottom": text_track_order,
    }


def validate_display_text_lines(raw_item: dict[str, Any], label: str) -> bool:
    lines = first_list(raw_item, DISPLAY_TEXT_LINES_KEYS)
    if lines is None:
        return False
    seen: set[int] = set()
    for idx, line_item in enumerate(lines):
        if not isinstance(line_item, dict):
            raise GateFail(f"{label}.display_text_lines[{idx}] must be an object")
        line_index = text_layer_index(line_item)
        if line_index is None:
            raw_index = first_item_value(line_item, ("line_index", "row", "line", "index"))
            try:
                line_index = int(raw_index)
            except (TypeError, ValueError) as exc:
                raise GateFail(f"{label}.display_text_lines[{idx}] must include line_index 1..3") from exc
        if line_index not in {1, 2, 3}:
            raise GateFail(f"{label}.display_text_lines[{idx}] line_index must be 1, 2, or 3")
        if line_index in seen:
            raise GateFail(f"{label}.display_text_lines duplicate line_index: {line_index}")
        seen.add(line_index)
    return True


def validate_text_layer_assignment(
    raw_item: dict[str, Any],
    label: str,
    text: str,
    caption_type: str,
    quoted: bool,
    parenthesized: bool,
    plain_voice: bool,
) -> None:
    if validate_display_text_lines(raw_item, label):
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


def visual_role(item: dict[str, Any]) -> str:
    for key in ("visual_role", "video_role", "beat_role", "role", "type"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def validate_zero_timeline_start(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    scenario_beats: list[dict[str, Any]],
) -> dict[str, Any]:
    explicit_start = first_number_value([contract, render_plan], TIMELINE_CONTENT_START_KEYS)
    if explicit_start is None:
        starts = [
            start
            for item in scenario_beats
            if isinstance(item, dict)
            for start in [range_start_seconds(item, "target")]
            if start is not None
        ]
        explicit_start = min(starts) if starts else None
    if explicit_start is None:
        raise GateFail("timeline_content_start_sec or first target start is required")
    if abs(explicit_start) > 0.05:
        raise GateFail("timeline content must start at 0.0 sec; do not offset/stage it later")
    return {"timeline_content_start_sec": 0.0}


def validate_audio_normalization_gate(
    contract: dict[str, Any],
    root: Path,
    render_plan: dict[str, Any],
) -> dict[str, Any]:
    sources = collect_status_sources(contract, root, AUDIO_NORMALIZATION_CONTAINERS)
    sources.append(render_plan)
    required_raw = first_status_value(sources, AUDIO_NORMALIZATION_REQUIRED_KEYS)
    required = True if required_raw is None else truthy(required_raw)
    if not required:
        raise GateFail("audio_normalization_required must be true")

    status = str(first_status_value(sources, AUDIO_NORMALIZATION_STATUS_KEYS) or "").strip().upper()
    if status != "PASS":
        raise GateFail("audio_normalization_status must be PASS before CapCut")

    method = str(first_status_value(sources, AUDIO_NORMALIZATION_METHOD_KEYS) or "").strip()
    if not method:
        raise GateFail("audio_normalization_method is required")

    assets = source_list_value(sources, NORMALIZED_AUDIO_ASSET_KEYS)
    if not assets:
        raise GateFail("normalized_audio_assets must list active source/TTS audio; BGM/SFX only when used")
    for idx, asset in enumerate(assets):
        if isinstance(asset, str):
            if asset.strip() and any(token in asset for token in ("\\", "/", ".")):
                require_file(root, asset, f"normalized_audio_assets[{idx}]")
        elif isinstance(asset, dict):
            role = str(asset.get("role") or asset.get("audio_role") or asset.get("type") or "").strip()
            if not role:
                raise GateFail(f"normalized_audio_assets[{idx}] must include role")
            path_raw = str(asset.get("path") or asset.get("file_path") or asset.get("audio_path") or "")
            segment_id = asset.get("segment_id") or asset.get("material_id")
            if path_raw:
                require_file(root, path_raw, f"normalized_audio_assets[{idx}]")
            elif not segment_id:
                raise GateFail(f"normalized_audio_assets[{idx}] must include path or segment_id")
        else:
            raise GateFail(f"normalized_audio_assets[{idx}] must be string or object")

    report_path = first_existing_file_from_keys(
        sources,
        root,
        AUDIO_NORMALIZATION_REPORT_KEYS,
        "audio_normalization_report",
    )
    if any(token in method.lower() for token in ("ffmpeg", "loudnorm", "external")) and report_path is None:
        raise GateFail("audio_normalization_report_path is required for ffmpeg/loudnorm normalization")

    return {
        "audio_normalization_required": True,
        "audio_normalization_status": status,
        "audio_normalization_method": method,
        "normalized_audio_asset_count": len(assets),
        "audio_normalization_report_path": str(report_path) if report_path else "",
    }


def validate_script_aligned_timeline_gate(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    scenario_beats: list[dict[str, Any]],
) -> dict[str, Any]:
    sources = [contract, render_plan]
    required_raw = first_status_value(sources, SCRIPT_ALIGNED_REQUIRED_KEYS)
    required = True if required_raw is None else truthy(required_raw)
    if not required:
        raise GateFail("script_aligned_timeline_required must be true")

    status = str(first_status_value(sources, SCRIPT_ALIGNED_STATUS_KEYS) or "").strip().upper()
    if status != "PASS":
        raise GateFail("script_aligned_timeline_status must be PASS")

    mapping = source_list_value(sources, SCRIPT_ALIGNED_TIMELINE_KEYS)
    if not mapping:
        raise GateFail("script_aligned_timeline_structure must be a non-empty list")

    scenario_ids = {script_beat_id(item) for item in scenario_beats if isinstance(item, dict)}
    scenario_ids.discard(None)
    mapped_ids: set[Any] = set()
    source_speech_count = 0
    user_voice_count = 0
    visual_count = 0
    for idx, raw_item in enumerate(mapping):
        if not isinstance(raw_item, dict):
            raise GateFail(f"script_aligned_timeline_structure[{idx}] must be an object")
        beat_id = script_beat_id(raw_item)
        if beat_id in (None, ""):
            raise GateFail(f"script_aligned_timeline_structure[{idx}] must include script_beat_id")
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"script_aligned_timeline_structure[{idx}] must include target_range")
        role = visual_role(raw_item)
        if not role:
            raise GateFail(f"script_aligned_timeline_structure[{idx}] must include visual_role/video_role")

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
            f"script_aligned_timeline_structure[{idx}]",
            text,
            caption_type,
            quoted,
            parenthesized,
            plain_voice,
        )

        if quoted:
            source_speech_count += 1
            if not (
                truthy_item(raw_item, ("source_speech_audio_required", "has_source_speech_audio"))
                or first_item_value(raw_item, ("source_speech_audio_role", "source_audio_role", "source_audio_segment_id", "source_audio_ref"))
            ):
                raise GateFail(
                    f"script_aligned_timeline_structure[{idx}] quoted/source speech beat "
                    "must require or reference source speech audio"
                )
        if plain_voice:
            user_voice_count += 1
            if not first_item_value(
                raw_item,
                ("voice_audio_role", "user_audio_role", "caption_voice_role", "voice_audio_ref", "voice_audio_segment_id"),
            ):
                raise GateFail(
                    f"script_aligned_timeline_structure[{idx}] plain TTS beat must reference user caption voice audio"
                )
            validate_tts_visual_fill(raw_item, f"script_aligned_timeline_structure[{idx}]")
        if role:
            visual_count += 1
        mapped_ids.add(beat_id)

    missing = scenario_ids - mapped_ids
    if missing:
        raise GateFail(f"script_aligned_timeline_structure missing scenario beats: {sorted(missing, key=str)}")

    return {
        "script_aligned_timeline_required": True,
        "script_aligned_timeline_status": "PASS",
        "script_aligned_beat_count": len(mapping),
        "script_aligned_visual_count": visual_count,
        "script_aligned_source_speech_count": source_speech_count,
        "script_aligned_user_voice_count": user_voice_count,
        "script_aligned_timeline_structure": mapping,
    }


def has_scenario_data(contract: dict[str, Any], render_plan: dict[str, Any]) -> bool:
    return bool(
        first_list(contract, SCENARIO_LIST_KEYS)
        or first_list(render_plan, SCENARIO_LIST_KEYS)
        or first_list(contract, CLIP_ASSIGNMENT_KEYS)
        or first_list(render_plan, CLIP_ASSIGNMENT_KEYS)
    )


def assembly_mode(contract: dict[str, Any], render_plan: dict[str, Any]) -> str:
    raw_mode = (
        contract.get("edit_assembly_mode")
        or contract.get("assembly_mode")
        or render_plan.get("edit_assembly_mode")
        or render_plan.get("assembly_mode")
    )
    if isinstance(raw_mode, str) and raw_mode.strip():
        return raw_mode.strip()
    if has_scenario_data(contract, render_plan):
        return "scenario_first_montage"
    return "order_remix"


def item_id(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


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


def item_summary(item: dict[str, Any]) -> str:
    for key in (
        "summary_ko",
        "visual_summary_ko",
        "action_ko",
        "description_ko",
        "summary",
        "visual_summary",
        "action",
        "description",
    ):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def item_role(item: dict[str, Any]) -> str:
    for key in ("beat_role", "role", "type"):
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


def first_present(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data and data.get(key) not in (None, ""):
            return data.get(key)
    return None


def get_list_or_fail(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    keys: tuple[str, ...],
    label: str,
) -> list[Any]:
    value = first_list(contract, keys) or first_list(render_plan, keys)
    if not isinstance(value, list) or not value:
        raise GateFail(f"{label} must be a non-empty list")
    return value


def get_list_optional(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    keys: tuple[str, ...],
) -> list[Any]:
    value = first_list(contract, keys) or first_list(render_plan, keys)
    if value is None:
        return []
    if not isinstance(value, list):
        raise GateFail(f"{keys[0]} must be a list")
    return value


def target_duration(contract: dict[str, Any], render_plan: dict[str, Any]) -> float:
    value = first_present(
        contract,
        (
            "target_total_duration_sec",
            "target_video_duration_sec",
            "final_duration_sec",
            "draft_duration_sec",
        ),
    )
    if value is None:
        value = first_present(
            render_plan,
            (
                "target_total_duration_sec",
                "target_video_duration_sec",
                "final_duration_sec",
                "draft_duration_sec",
            ),
        )
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def validate_duration_not_source_match(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
) -> None:
    source_duration = float(contract.get("source_duration_sec") or render_plan.get("source_duration_sec") or 0)
    final_duration = target_duration(contract, render_plan)
    if source_duration <= 0 or final_duration <= 0:
        return
    same_duration_exception = (
        contract.get("same_duration_exception_reason")
        or render_plan.get("same_duration_exception_reason")
        or ""
    )
    if abs(source_duration - final_duration) <= 0.25 and not same_duration_exception:
        raise GateFail(
            "target duration must not automatically match source duration; "
            "set same_duration_exception_reason only when exact matching is intentional"
        )


def validate_original_source_media(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    raw_media = contract.get("original_source_media") or render_plan.get("original_source_media")
    if raw_media is None:
        raise GateFail("original_source_media is required for scenario_first_montage")

    media_path_raw = ""
    import_flag = None
    if isinstance(raw_media, str):
        media_path_raw = raw_media
    elif isinstance(raw_media, dict):
        media_path_raw = str(
            raw_media.get("path")
            or raw_media.get("source_path")
            or raw_media.get("source_mp4")
            or raw_media.get("file")
            or ""
        )
        import_flag = (
            raw_media.get("imported_to_capcut_media")
            if "imported_to_capcut_media" in raw_media
            else raw_media.get("import_to_capcut_media")
        )
    else:
        raise GateFail("original_source_media must be a path string or object")

    if not media_path_raw:
        raise GateFail("original_source_media path is required")
    media_path = require_file(root, media_path_raw, "original_source_media")
    if media_path.name.lower() != "source.mp4":
        raise GateFail("original_source_media must point to the full source.mp4, not a derived clip")
    require_audio_stream(media_path, "original_source_media")
    if import_flag is not True:
        raise GateFail("original_source_media must set imported_to_capcut_media/import_to_capcut_media=true")
    return {
        "path": str(media_path),
        "imported_to_capcut_media": True,
        "has_audio_stream": True,
    }


def validate_semantic_video_track_contract(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
) -> dict[str, Any]:
    sources = [contract, render_plan]
    value = contract.get("video_track_contract") or render_plan.get("video_track_contract")
    if value != SEMANTIC_VIDEO_TRACK_CONTRACT:
        raise GateFail(
            "video_track_contract must be "
            f"{SEMANTIC_VIDEO_TRACK_CONTRACT} for 11short urakkai CapCut work"
        )
    video_track_order = require_track_order(
        sources,
        VIDEO_TRACK_ORDER_KEYS,
        REQUIRED_VIDEO_TRACK_ORDER,
        "video_track_order_top_to_bottom",
    )

    manifest = render_plan.get("video_track_manifest") or contract.get("video_track_manifest")
    manifest_count = 0
    if manifest is not None:
        if not isinstance(manifest, list) or not manifest:
            raise GateFail("video_track_manifest must be a non-empty list when provided")
        for idx, item in enumerate(manifest):
            if not isinstance(item, dict):
                raise GateFail(f"video_track_manifest[{idx}] must be an object")
            visual_track = str(item.get("visual_track") or "").strip()
            if visual_track not in ALLOWED_SEMANTIC_VIDEO_TRACKS:
                raise GateFail(
                    f"video_track_manifest[{idx}].visual_track must be one of "
                    f"{sorted(ALLOWED_SEMANTIC_VIDEO_TRACKS)}"
                )
        manifest_count = len(manifest)

    return {
        "video_track_contract": SEMANTIC_VIDEO_TRACK_CONTRACT,
        "video_track_order_top_to_bottom": video_track_order,
        "video_track_manifest_count": manifest_count,
    }


def validate_source_beat_library(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[Any]]:
    raw_library = get_list_or_fail(
        contract,
        render_plan,
        SOURCE_LIBRARY_KEYS,
        "source_beat_library",
    )
    source_duration = float(contract.get("source_duration_sec") or render_plan.get("source_duration_sec") or 0)
    minimum = 3 if 0 < source_duration < 15 else 5
    if len(raw_library) < minimum:
        raise GateFail(
            f"source_beat_library must split the source into at least {minimum} reusable beats"
        )

    library: list[dict[str, Any]] = []
    source_ids: set[Any] = set()
    for idx, raw_item in enumerate(raw_library):
        if not isinstance(raw_item, dict):
            raise GateFail(f"source_beat_library[{idx}] must be an object")
        beat_id = item_id(
            raw_item,
            ("source_beat_id", "beat_id", "id", "source_id"),
        )
        if beat_id in (None, ""):
            raise GateFail(f"source_beat_library[{idx}] must include beat_id")
        if not has_time_range(raw_item, "source"):
            raise GateFail(f"source_beat_library[{idx}] must include source_range")
        if not item_role(raw_item):
            raise GateFail(f"source_beat_library[{idx}] must include beat_role")
        if not item_summary(raw_item):
            raise GateFail(f"source_beat_library[{idx}] must include visual summary")
        source_ids.add(beat_id)
        library.append(raw_item)
    return library, source_ids


def validate_scenario_beats(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[Any], dict[Any, str]]:
    raw_beats = get_list_or_fail(
        contract,
        render_plan,
        SCENARIO_LIST_KEYS,
        "scenario_timeline",
    )
    beats: list[dict[str, Any]] = []
    beat_ids: set[Any] = set()
    subjects: dict[Any, str] = {}
    for idx, raw_item in enumerate(raw_beats):
        if not isinstance(raw_item, dict):
            raise GateFail(f"scenario_timeline[{idx}] must be an object")
        beat_id = item_id(
            raw_item,
            ("scenario_beat_id", "target_beat_id", "beat_id", "id"),
        )
        if beat_id in (None, ""):
            raise GateFail(f"scenario_timeline[{idx}] must include scenario_beat_id")
        if beat_id in beat_ids:
            raise GateFail(f"scenario_timeline duplicate scenario_beat_id: {beat_id}")
        role = item_role(raw_item)
        if not role:
            raise GateFail(f"scenario_timeline[{idx}] must include beat_role")
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"scenario_timeline[{idx}] must include target_range")
        if not item_text(raw_item) and role not in VISUAL_ONLY_ROLES:
            raise GateFail(
                f"scenario_timeline[{idx}] must include middle_text/caption/script text"
            )
        validate_middle_caption_type(raw_item, f"scenario_timeline[{idx}]")
        beat_ids.add(beat_id)
        subject = subject_value(
            raw_item,
            (
                "caption_subject",
                "target_subject",
                "visual_subject",
                "subject",
                "speaker",
            ),
        )
        if subject:
            subjects[beat_id] = subject
        beats.append(raw_item)
    return beats, beat_ids, subjects


def assignment_scenario_id(item: dict[str, Any]) -> Any:
    return item_id(
        item,
        (
            "scenario_beat_id",
            "target_beat_id",
            "beat_id",
            "id",
        ),
    )


def assignment_source_id(item: dict[str, Any]) -> Any:
    return item_id(
        item,
        (
            "source_beat_id",
            "source_beat",
            "source_id",
            "source_segment_id",
        ),
    )


def assignment_asset_type(item: dict[str, Any]) -> str:
    for key in ("asset_type", "visual_type"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def subject_value(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def assignment_uses_source(item: dict[str, Any], source_ids: set[Any]) -> bool:
    source_id = assignment_source_id(item)
    return has_time_range(item, "source") or source_id in source_ids


def validate_clip_assignments(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    scenario_ids: set[Any],
    source_ids: set[Any],
    scenario_subjects: dict[Any, str],
) -> list[dict[str, Any]]:
    raw_assignments = get_list_or_fail(
        contract,
        render_plan,
        CLIP_ASSIGNMENT_KEYS,
        "clip_assignments",
    )
    assignments: list[dict[str, Any]] = []
    assigned_scenario_ids: set[Any] = set()
    source_assignment_count = 0

    for idx, raw_item in enumerate(raw_assignments):
        if not isinstance(raw_item, dict):
            raise GateFail(f"clip_assignments[{idx}] must be an object")
        scenario_id = assignment_scenario_id(raw_item)
        if scenario_id in (None, ""):
            raise GateFail(f"clip_assignments[{idx}] must include scenario_beat_id")
        if scenario_id not in scenario_ids:
            raise GateFail(f"clip_assignments[{idx}] points to unknown scenario beat: {scenario_id}")
        role = item_role(raw_item)
        if not role:
            raise GateFail(f"clip_assignments[{idx}] must include beat_role")
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"clip_assignments[{idx}] must include target_range")

        uses_source = assignment_uses_source(raw_item, source_ids)
        asset_type = assignment_asset_type(raw_item)
        if uses_source:
            source_assignment_count += 1
        elif asset_type not in ALLOWED_NON_SOURCE_ASSETS:
            raise GateFail(
                f"clip_assignments[{idx}] must include source_range/source_beat_id "
                f"or asset_type in {sorted(ALLOWED_NON_SOURCE_ASSETS)}"
            )

        expected_subject = scenario_subjects.get(scenario_id, "")
        visual_subject = subject_value(
            raw_item,
            (
                "visual_subject",
                "caption_subject",
                "target_subject",
                "subject",
                "speaker",
            ),
        )
        if expected_subject and visual_subject and expected_subject != visual_subject:
            raise GateFail(
                f"clip_assignments[{idx}] visual_subject does not match scenario subject. "
                f"expected={expected_subject}, actual={visual_subject}"
            )
        validate_middle_caption_type(raw_item, f"clip_assignments[{idx}]")

        assigned_scenario_ids.add(scenario_id)
        assignments.append(raw_item)

    missing = scenario_ids - assigned_scenario_ids
    if missing:
        raise GateFail(f"clip_assignments missing scenario beats: {sorted(missing, key=str)}")
    if source_assignment_count < 1:
        raise GateFail("clip_assignments must include at least one source video assignment")
    return assignments


def validate_multi_clip_fill(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    scenario_count: int,
    assignments: list[dict[str, Any]],
) -> None:
    if scenario_count < 1:
        return
    by_scenario: dict[Any, int] = {}
    for item in assignments:
        scenario_id = assignment_scenario_id(item)
        by_scenario[scenario_id] = by_scenario.get(scenario_id, 0) + 1

    for scenario_id, count in by_scenario.items():
        if count <= 1:
            continue
        split_reason = ""
        for item in assignments:
            if assignment_scenario_id(item) != scenario_id:
                continue
            split_reason = str(
                item.get("split_reason_ko")
                or item.get("subject_change_reason_ko")
                or item.get("action_change_reason_ko")
                or item.get("split_reason")
                or split_reason
            ).strip()
        if not split_reason:
            raise GateFail(
                f"scenario beat {scenario_id} has multiple clip assignments; "
                "add split_reason_ko, subject_change_reason_ko, or action_change_reason_ko"
            )


def validate_unused_split_clips(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    source_library: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    used_source_ids = {
        assignment_source_id(item)
        for item in assignments
        if assignment_source_id(item) not in (None, "")
    }
    all_source_ids = {
        item_id(item, ("source_beat_id", "beat_id", "id", "source_id"))
        for item in source_library
    }
    all_source_ids.discard(None)
    unused_source_ids = all_source_ids - used_source_ids

    raw_unused = get_list_optional(contract, render_plan, UNUSED_SPLIT_KEYS)
    if unused_source_ids and not raw_unused:
        raise GateFail(
            "unused split clips must be recorded as unused_split_clips for manual editing"
        )

    unused_clips: list[dict[str, Any]] = []
    for idx, raw_item in enumerate(raw_unused):
        if not isinstance(raw_item, dict):
            raise GateFail(f"unused_split_clips[{idx}] must be an object")
        clip_id = item_id(
            raw_item,
            ("source_beat_id", "beat_id", "id", "source_id"),
        )
        if clip_id in (None, ""):
            raise GateFail(f"unused_split_clips[{idx}] must include source_beat_id")
        if not has_time_range(raw_item, "source"):
            raise GateFail(f"unused_split_clips[{idx}] must include source_range")
        placement = raw_item.get("placement") or raw_item.get("storage") or raw_item.get("timeline_position")
        if not placement:
            raise GateFail(
                f"unused_split_clips[{idx}] must include placement/storage "
                "such as timeline_tail, spare_track, or media_bin"
            )
        unused_clips.append(raw_item)

    recorded_unused_ids = {
        item_id(item, ("source_beat_id", "beat_id", "id", "source_id"))
        for item in unused_clips
    }
    missing = unused_source_ids - recorded_unused_ids
    if missing:
        raise GateFail(f"unused_split_clips missing source beats: {sorted(missing, key=str)}")
    return unused_clips


def has_assignment_framing(item: dict[str, Any]) -> bool:
    for key in (
        "framing",
        "framing_adjustment",
        "crop",
        "scale",
        "pan",
        "zoom",
        "keyframes",
        "reframe",
    ):
        if key in item and item.get(key) not in (None, "", []):
            return True
    return False


def validate_framing_adjustments(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    assignments: list[dict[str, Any]],
) -> list[Any]:
    adjustments = get_list_optional(contract, render_plan, FRAMING_ADJUSTMENT_KEYS)
    has_inline_framing = any(has_assignment_framing(item) for item in assignments)
    exception = (
        contract.get("framing_adjustments_exception_reason")
        or render_plan.get("framing_adjustments_exception_reason")
        or ""
    )
    if not adjustments and not has_inline_framing and not exception:
        raise GateFail(
            "framing_adjustments or inline crop/scale/pan/zoom plan is required "
            "to keep the subject centered"
        )

    for idx, raw_item in enumerate(adjustments):
        if not isinstance(raw_item, dict):
            raise GateFail(f"framing_adjustments[{idx}] must be an object")
        if assignment_scenario_id(raw_item) in (None, ""):
            raise GateFail(f"framing_adjustments[{idx}] must include scenario_beat_id")
        description = (
            raw_item.get("adjustment_ko")
            or raw_item.get("framing_ko")
            or raw_item.get("description_ko")
            or raw_item.get("description")
        )
        if not description:
            raise GateFail(f"framing_adjustments[{idx}] must describe crop/scale/pan/zoom")
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


def validate_sfx_media_bin(
    contract: dict[str, Any],
    render_plan: dict[str, Any],
    root: Path,
) -> tuple[list[Any], list[Any]]:
    sfx_timeline = get_list_optional(contract, render_plan, SFX_TIMELINE_KEYS)
    sfx_media_bin = get_list_optional(contract, render_plan, SFX_MEDIA_BIN_KEYS)
    if not sfx_timeline:
        return [], sfx_media_bin

    if not sfx_media_bin:
        schema_limit = (
            contract.get("sfx_media_bin_status")
            or render_plan.get("sfx_media_bin_status")
            or ""
        )
        if schema_limit != "TRACK_ONLY_SCHEMA_LIMIT":
            raise GateFail(
                "sfx_timeline is present, so sfx_media_bin is required "
                "unless sfx_media_bin_status=TRACK_ONLY_SCHEMA_LIMIT"
            )

    media_ids = {
        sfx_id(item)
        for item in sfx_media_bin
        if isinstance(item, dict)
    }
    for idx, raw_item in enumerate(sfx_media_bin):
        if not isinstance(raw_item, dict):
            raise GateFail(f"sfx_media_bin[{idx}] must be an object")
        raw_path = sfx_file_path(raw_item)
        if not raw_path:
            raise GateFail(f"sfx_media_bin[{idx}] must include path/file_path")
        require_file(root, raw_path, "sfx_media_bin")
        imported = raw_item.get("imported_to_capcut_media")
        registered = raw_item.get("registered_in_project_media")
        if imported is not True and registered is not True:
            raise GateFail(
                f"sfx_media_bin[{idx}] must set imported_to_capcut_media=true "
                "or registered_in_project_media=true"
            )

    for idx, raw_item in enumerate(sfx_timeline):
        if not isinstance(raw_item, dict):
            raise GateFail(f"sfx_timeline[{idx}] must be an object")
        raw_path = sfx_file_path(raw_item)
        item_key = sfx_id(raw_item)
        if not raw_path and not item_key:
            raise GateFail(f"sfx_timeline[{idx}] must include sfx path or id")
        if raw_path:
            require_file(root, raw_path, "sfx_timeline")
        if sfx_media_bin and item_key not in media_ids and Path(raw_path).name not in media_ids:
            raise GateFail(
                f"sfx_timeline[{idx}] is not registered in sfx_media_bin: {item_key or raw_path}"
            )
        if not has_time_range(raw_item, "target"):
            raise GateFail(f"sfx_timeline[{idx}] must include target_range")
    return sfx_timeline, sfx_media_bin


def sequence_matches_policy(
    original: list[Any],
    sequence: list[Any],
    label: str,
    allowed_repeated_beats: set[Any],
    declared_removed_beats: set[Any],
) -> None:
    original_set = set(original)
    sequence_set = set(sequence)
    unknown = sequence_set - original_set
    if unknown:
        raise GateFail(f"{label} contains unknown beats: {sorted(unknown, key=str)}")

    counts = Counter(sequence)
    for beat in original:
        count = counts.get(beat, 0)
        if beat in declared_removed_beats:
            if count != 0:
                raise GateFail(f"{label} includes a declared removed beat: {beat}")
            continue
        if count < 1:
            raise GateFail(f"{label} is missing beat: {beat}")
        if count > 1 and beat not in allowed_repeated_beats:
            raise GateFail(f"{label} repeats undeclared beat: {beat}")

    for beat, count in counts.items():
        if count > 1 and beat not in allowed_repeated_beats:
            raise GateFail(f"{label} repeats undeclared beat: {beat}")


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


def extract_actual_order(render_plan: dict[str, Any]) -> list[Any]:
    explicit = render_plan.get("actual_render_order")
    if isinstance(explicit, list) and explicit:
        return require_scalar_list(explicit, "render_plan.actual_render_order")

    for key in ("segments", "render_segments", "timeline", "video_segments", "cuts"):
        value = render_plan.get(key)
        if isinstance(value, list):
            order = extract_order_from_segments(value)
            if order:
                return require_scalar_list(order, f"render_plan.{key} derived order")

    raise GateFail(
        "render_plan_path must contain actual_render_order or segments with beat ids"
    )


def validate_legacy_order_remix(
    contract: dict[str, Any],
    root: Path,
    render_plan_path: Path,
    render_plan: dict[str, Any],
) -> dict[str, Any]:
    original = require_unique_order(contract.get("original_beat_order"), "original_beat_order")
    candidates_raw = contract.get("remix_candidates")
    if not isinstance(candidates_raw, list) or len(candidates_raw) < 3:
        raise GateFail("remix_candidates must be at least 3")

    allowed_repeated_beats = set(contract.get("allowed_repeated_beats") or [])
    declared_removed_beats = set(contract.get("declared_removed_or_compressed_beats") or [])

    candidates: list[list[Any]] = []
    for idx, candidate_raw in enumerate(candidates_raw):
        candidate = require_scalar_list(candidate_raw, f"remix_candidates[{idx}]")
        sequence_matches_policy(
            original,
            candidate,
            f"remix_candidates[{idx}]",
            allowed_repeated_beats,
            declared_removed_beats,
        )
        candidates.append(candidate)

    selected = require_scalar_list(contract.get("selected_remix_order"), "selected_remix_order")
    if selected not in candidates:
        raise GateFail(
            f"selected_remix_order must be one of remix_candidates. "
            f"selected={selected}, candidates={candidates}"
        )
    sequence_matches_policy(
        original,
        selected,
        "selected_remix_order",
        allowed_repeated_beats,
        declared_removed_beats,
    )

    if selected == original:
        reason = contract.get("same_order_exception_reason", "")
        approved = contract.get("user_approved_same_order", False)
        if not reason or approved is not True:
            raise GateFail(
                "selected_remix_order is same as original_beat_order "
                "without approved exception"
            )

    actual = extract_actual_order(render_plan)
    if selected != actual:
        raise GateFail(
            f"selected_remix_order != actual_render_order. "
            f"selected={selected}, actual={actual}"
        )

    if contract.get("similarity_breaker_harness") != "PASS":
        raise GateFail("similarity_breaker_harness is not PASS")

    return {
        "edit_assembly_mode": "order_remix",
        "original_beat_order": original,
        "selected_remix_order": selected,
        "actual_render_order": actual,
        "render_plan_path": str(render_plan_path),
    }


def validate_scenario_first_montage(
    contract: dict[str, Any],
    root: Path,
    render_plan_path: Path,
    render_plan: dict[str, Any],
) -> dict[str, Any]:
    validate_duration_not_source_match(contract, render_plan)
    original_source_media = validate_original_source_media(contract, render_plan, root)
    video_track_contract_result = validate_semantic_video_track_contract(contract, render_plan)
    source_library, source_ids = validate_source_beat_library(contract, render_plan)
    scenario_beats, scenario_ids, scenario_subjects = validate_scenario_beats(contract, render_plan)
    zero_start_result = validate_zero_timeline_start(contract, render_plan, scenario_beats)
    text_layout_result = validate_three_line_text_layout_gate(contract, render_plan)
    catcup_layout_result = validate_catcup_reference_layout_gate(contract, render_plan)
    script_aligned_result = validate_script_aligned_timeline_gate(
        contract,
        render_plan,
        scenario_beats,
    )
    clip_assignments = validate_clip_assignments(
        contract,
        render_plan,
        scenario_ids,
        source_ids,
        scenario_subjects,
    )
    validate_multi_clip_fill(contract, render_plan, len(scenario_beats), clip_assignments)
    unused_split_clips = validate_unused_split_clips(
        contract,
        render_plan,
        source_library,
        clip_assignments,
    )
    framing_adjustments = validate_framing_adjustments(
        contract,
        render_plan,
        clip_assignments,
    )
    sfx_timeline, sfx_media_bin = validate_sfx_media_bin(contract, render_plan, root)
    audio_normalization_result = validate_audio_normalization_gate(contract, root, render_plan)

    if len(source_library) <= len(scenario_beats) // 2:
        raise GateFail(
            "source_beat_library is too coarse for cut editing; split the source into more reusable beats"
        )

    if contract.get("similarity_breaker_harness") not in {"PASS", "N/A_SCENARIO_FIRST_MONTAGE"}:
        raise GateFail(
            "similarity_breaker_harness must be PASS or N/A_SCENARIO_FIRST_MONTAGE"
        )

    return {
        "edit_assembly_mode": "scenario_first_montage",
        "source_beat_count": len(source_library),
        "scenario_beat_count": len(scenario_beats),
        "clip_assignment_count": len(clip_assignments),
        "unused_split_clip_count": len(unused_split_clips),
        "framing_adjustment_count": len(framing_adjustments),
        "sfx_timeline_count": len(sfx_timeline),
        "sfx_media_bin_count": len(sfx_media_bin),
        "original_source_media": original_source_media,
        **video_track_contract_result,
        **zero_start_result,
        **text_layout_result,
        **catcup_layout_result,
        **script_aligned_result,
        **audio_normalization_result,
        "source_beat_library": source_library,
        "scenario_timeline": scenario_beats,
        "clip_assignments": clip_assignments,
        "unused_split_clips": unused_split_clips,
        "framing_adjustments": framing_adjustments,
        "sfx_timeline": sfx_timeline,
        "sfx_media_bin": sfx_media_bin,
        "render_plan_path": str(render_plan_path),
    }


def validate_shared_requirements(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    script_handoff_result = validate_script_handoff_gate(contract, root)
    report1_handoff_result = validate_report1_handoff_gate(contract, root)

    if contract.get("similarity_breaker_harness") != "PASS":
        if contract.get("similarity_breaker_harness") != "N/A_SCENARIO_FIRST_MONTAGE":
            raise GateFail("similarity_breaker_harness is not PASS")

    writer_agent_source = contract.get("writer_agent_source")
    if writer_agent_source in {"INLINE_FALLBACK", "VISIBLE_WRITER_BATTLE"}:
        raise GateFail(f"{writer_agent_source} cannot produce SCRIPT_LOCK")
    if writer_agent_source not in {"REAL_AGENT", "REAL_WRITER_AGENT_MODE"}:
        raise GateFail("writer_agent_source must be REAL_AGENT or REAL_WRITER_AGENT_MODE")

    if contract.get("writer_agent_mode_status") != "REAL_RUN":
        raise GateFail("writer_agent_mode_status must be REAL_RUN")
    if int(contract.get("writer_persona_total", 0)) < 5:
        raise GateFail("writer_persona_total must be at least 5")
    if int(contract.get("writer_persona_pass_count", 0)) < 4:
        raise GateFail("writer_persona_pass_count must be at least 4")

    evidence_files = contract.get("writer_agent_evidence_files")
    if not isinstance(evidence_files, list) or not evidence_files:
        raise GateFail("writer_agent_evidence_files must be a non-empty list")
    for file_path in evidence_files:
        require_file(root, str(file_path), "writer_agent_evidence")

    if contract.get("hard_veto") is True:
        raise GateFail("hard_veto is true")

    script_lock_path = require_file(
        root,
        contract.get("script_lock_evidence_path", ""),
        "script_lock_evidence",
    )
    script_lock = load_json(script_lock_path)
    if script_lock.get("status") != "SCRIPT_LOCK":
        raise GateFail("script_lock_evidence status must be SCRIPT_LOCK")
    lock_source = script_lock.get("source") or script_lock.get("generated_by")
    if lock_source not in ALLOWED_SCRIPT_LOCK_SOURCES:
        raise GateFail("SCRIPT_LOCK must be generated by a validator, not a human report")
    if int(script_lock.get("writer_persona_pass_count", contract.get("writer_persona_pass_count", 0))) < 4:
        raise GateFail("script_lock_evidence writer_persona_pass_count must be at least 4")
    if script_lock.get("hard_veto", contract.get("hard_veto")) is True:
        raise GateFail("script_lock_evidence hard_veto is true")

    if contract.get("watch_direct_frame_status") != "PASS":
        raise GateFail("watch_direct_frame_status must be PASS")
    require_json_status_pass(
        root,
        contract.get("watch_direct_frame_report", ""),
        "watch_direct_frame_report",
    )

    require_file(root, contract.get("final_script_ko_path", ""), "final_script_ko")
    require_file(root, contract.get("analysis_json_path", ""), "analysis_json")
    require_file(root, contract.get("tikitaka_decision_log_path", ""), "tikitaka_decision_log")
    require_json_status_pass(
        root,
        contract.get("harness_report_analysis", ""),
        "harness_report_analysis",
    )
    require_json_status_pass(
        root,
        contract.get("harness_report_assets", ""),
        "harness_report_assets",
    )
    validation_report_path = contract.get("validation_report_path") or "reports/validation_report.json"
    validation_report = require_json_status_pass(
        root,
        validation_report_path,
        "validation_report",
    )

    return {
        **script_handoff_result,
        **report1_handoff_result,
        "validation_report_path": str(as_path(root, validation_report_path)),
        "validation_report_status": status_value(validation_report),
    }


def validate_youtube_restriction_guideline(
    contract: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    sources = collect_policy_sources(contract, root)
    complete = first_policy_value(sources, YOUTUBE_RESTRICTION_COMPLETE_KEYS)
    if not truthy(complete):
        raise GateFail("youtube_restriction_guideline_gate_complete must be true")

    risk_raw = first_policy_value(sources, YOUTUBE_RESTRICTION_RISK_KEYS)
    risk = str(risk_raw or "").strip().upper()
    if risk not in {"LOW", "MEDIUM", "HIGH", "BLOCK"}:
        raise GateFail("youtube_restriction_policy_risk_tier must be LOW, MEDIUM, HIGH, or BLOCK")
    if risk == "BLOCK":
        raise GateFail("youtube_restriction_policy_risk_tier is BLOCK")

    verdict_raw = first_policy_value(sources, YOUTUBE_RESTRICTION_VERDICT_KEYS)
    verdict = str(verdict_raw or "").strip().upper()
    if verdict != "PASS":
        raise GateFail("youtube_restriction_platform_verdict must be PASS")

    hard_blocks = policy_items(sources, YOUTUBE_RESTRICTION_HARD_BLOCK_KEYS)
    if hard_blocks:
        raise GateFail(f"youtube_restriction_hard_blocks must be empty: {hard_blocks}")

    rewrites = policy_items(sources, YOUTUBE_RESTRICTION_REWRITE_KEYS)
    if rewrites:
        raise GateFail(f"youtube_restriction_rewrite_required must be empty: {rewrites}")

    return {
        "youtube_restriction_guideline_gate_complete": True,
        "youtube_restriction_policy_risk_tier": risk,
        "youtube_restriction_platform_verdict": verdict,
        "youtube_restriction_flagged_categories": policy_items(
            sources,
            YOUTUBE_RESTRICTION_FLAG_KEYS,
        ),
    }


def validate_report_first_voice_gate(
    contract: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    sources = collect_status_sources(contract, root, SOURCE_DIALOGUE_POLICY_CONTAINERS)

    # Current v5 factory route: when the user explicitly authorizes generated
    # Supertone/Daniel TTS, do not force the legacy user-supplied SRT/audio
    # handoff or ElevenLabs-only dialogue provider. Source speech still needs a
    # timestamped source-dialogue/STT evidence file, and generated TTS clips
    # still need a manifest.
    generated_tts_authorized = truthy(
        first_status_value(
            sources,
            (
                "generated_tts_authorized",
                "supertone_generation_enabled",
                "daniel_tts_authorized",
            ),
        )
    ) or any(
        token in str(first_status_value(sources, ("voice_generation_mode", "source_audio_mode")) or "").lower()
        for token in ("supertone", "daniel", "generated")
    )
    required_raw = first_status_value(sources, USER_SRT_AUDIO_REQUIRED_KEYS)
    user_srt_audio_required = True if required_raw is None else truthy(required_raw)
    if generated_tts_authorized and not user_srt_audio_required:
        dialogue_status = str(
            first_status_value(sources, ELEVENLABS_DIALOGUE_STATUS_KEYS) or ""
        ).strip().upper()
        if dialogue_status not in {"PASS", "NO_DIALOGUE", "NO_SOURCE_DIALOGUE", "NO_AUDIO"}:
            raise GateFail("source_dialogue_analysis_status must be PASS or NO_DIALOGUE")

        provider = str(
            first_status_value(sources, ELEVENLABS_DIALOGUE_PROVIDER_KEYS) or ""
        ).strip()
        provider_lc = provider.lower()
        if not any(token in provider_lc for token in ("whisper", "faster-whisper", "source", "stt")):
            raise GateFail(
                "source_dialogue_analysis_provider must be Whisper/faster-whisper/source evidence "
                "for generated TTS factory route"
            )

        dialogue_report = first_existing_file_from_keys(
            sources,
            root,
            ELEVENLABS_DIALOGUE_PATH_KEYS,
            "source_dialogue_analysis",
        )
        if dialogue_report is None:
            raise GateFail("source_dialogue_analysis_path file missing")

        tts_manifest_raw = (
            first_status_value(
                sources,
                (
                    "supertone_tts_manifest_path",
                    "supertone_manifest_path",
                    "tts_manifest_path",
                    "tts_segments_file",
                ),
            )
            or "supertone_tts_manifest.json"
        )
        tts_manifest = require_file(root, str(tts_manifest_raw), "generated_tts_manifest")

        return {
            "source_dialogue_analysis_status": dialogue_status,
            "source_dialogue_analysis_provider": provider,
            "source_dialogue_analysis_path": str(dialogue_report),
            "generated_tts_authorized": True,
            "generated_tts_manifest_path": str(tts_manifest),
            "user_srt_audio_gate_status": "N/A_GENERATED_TTS_AUTHORIZED",
            "requires_user_srt_audio_before_capcut": False,
        }

    dialogue_required = truthy(
        first_status_value(
            sources,
            ("elevenlabs_dialogue_analysis_required", "source_dialogue_analysis_required"),
        )
    )
    if not dialogue_required:
        raise GateFail("elevenlabs_dialogue_analysis_required must be true before CapCut")

    dialogue_status = str(
        first_status_value(sources, ELEVENLABS_DIALOGUE_STATUS_KEYS) or ""
    ).strip().upper()
    if dialogue_status not in {"PASS", "NO_DIALOGUE", "NO_SOURCE_DIALOGUE", "NO_AUDIO"}:
        raise GateFail("elevenlabs_dialogue_analysis_status must be PASS or NO_DIALOGUE")

    provider = str(
        first_status_value(sources, ELEVENLABS_DIALOGUE_PROVIDER_KEYS) or ""
    ).strip()
    if "eleven" not in provider.lower():
        raise GateFail("source_dialogue_analysis_provider must be ElevenLabs/Scribe")

    dialogue_report = first_existing_file_from_keys(
        sources,
        root,
        ELEVENLABS_DIALOGUE_PATH_KEYS,
        "source_dialogue_analysis",
    )
    if dialogue_report is None:
        raise GateFail("source_dialogue_analysis_path file missing")

    pre_capcut_script_package_status = str(
        first_status_value(sources, FINAL_REPORT_STATUS_KEYS) or ""
    ).strip().upper()
    if pre_capcut_script_package_status not in {"PASS", "DELIVERED", "USER_REVIEWED_OR_DELIVERED"}:
        raise GateFail("pre_capcut_script_package_status must be DELIVERED/PASS before CapCut")

    required_raw = first_status_value(sources, USER_SRT_AUDIO_REQUIRED_KEYS)
    user_srt_audio_required = True if required_raw is None else truthy(required_raw)
    package_status = str(
        first_status_value(sources, USER_SRT_AUDIO_STATUS_KEYS) or ""
    ).strip().upper()
    if not user_srt_audio_required:
        if package_status not in USER_SRT_AUDIO_EXCEPTION_STATUSES:
            raise GateFail(
                "user_srt_audio_gate_status must record a no-voice user-confirmed exception"
            )
        return {
            "elevenlabs_dialogue_analysis_status": dialogue_status,
            "source_dialogue_analysis_provider": provider,
            "source_dialogue_analysis_path": str(dialogue_report),
            "pre_capcut_script_package_status": pre_capcut_script_package_status,
            "user_srt_audio_gate_status": package_status,
            "requires_user_srt_audio_before_capcut": False,
        }

    if package_status not in {"PASS", "RECEIVED", "USER_SUPPLIED", "USER_SRT_AUDIO_RECEIVED"}:
        raise GateFail("user_srt_audio_gate_status must be RECEIVED/PASS before CapCut")

    package_path = first_existing_file_from_keys(
        sources,
        root,
        USER_SRT_AUDIO_PACKAGE_PATH_KEYS,
        "user_srt_audio_package",
    )
    srt_path = first_existing_file_from_keys(sources, root, USER_SRT_PATH_KEYS, "user_srt")
    audio_path = first_existing_file_from_keys(sources, root, USER_AUDIO_PATH_KEYS, "user_audio")
    if package_path is None and (srt_path is None or audio_path is None):
        raise GateFail("user SRT/audio package missing: provide ZIP or matching SRT plus audio")

    return {
        "elevenlabs_dialogue_analysis_status": dialogue_status,
        "source_dialogue_analysis_provider": provider,
        "source_dialogue_analysis_path": str(dialogue_report),
        "pre_capcut_script_package_status": pre_capcut_script_package_status,
        "user_srt_audio_gate_status": package_status,
        "requires_user_srt_audio_before_capcut": True,
        "user_srt_audio_package_path": str(package_path) if package_path else "",
        "user_srt_path": str(srt_path) if srt_path else "",
        "user_audio_path": str(audio_path) if audio_path else "",
    }


def validate_gate(contract: dict[str, Any], root: Path) -> dict[str, Any]:
    source_pointer = (
        contract.get("source_url")
        or contract.get("source_path")
        or contract.get("source_mp4")
        or contract.get("source_file")
    )
    require(source_pointer, "source_url or source_path is required")
    request_mode = project_file_request_mode(merged_request_scope_contract(contract, root))

    render_plan_path = require_file(root, contract.get("render_plan_path", ""), "render_plan")
    render_plan = load_json(render_plan_path)
    proof_result = validate_production_proof_files(contract, root)
    input_hash_result = validate_declared_input_hashes(contract, root)
    mode = assembly_mode(contract, render_plan)

    if mode in SCENARIO_FIRST_MODES:
        assembly_result = validate_scenario_first_montage(
            contract,
            root,
            render_plan_path,
            render_plan,
        )
    elif mode in LEGACY_ORDER_MODES:
        assembly_result = validate_legacy_order_remix(
            contract,
            root,
            render_plan_path,
            render_plan,
        )
    else:
        raise GateFail(f"unsupported edit_assembly_mode: {mode}")

    policy_result = validate_youtube_restriction_guideline(contract, root)
    report_voice_result = validate_report_first_voice_gate(contract, root)
    shared_result = validate_shared_requirements(contract, root)

    result = {
        "gate": "PRODUCTION_GATE",
        "status": "PASS",
        "gate_stage": "pre_capcut",
        "source_pointer": source_pointer,
        "project_file_request_mode": request_mode,
        "script_lock_status": "SCRIPT_LOCK",
        "production_allowed": True,
        "ignored_contract_production_allowed": contract.get("production_allowed", "not_provided"),
    }
    result.update(policy_result)
    result.update(report_voice_result)
    result.update(shared_result)
    result.update(assembly_result)
    result.update(proof_result)
    result.update(input_hash_result)
    result.update(upload_ready_state(contract, stage="production"))
    return result


def fail_result(reason: str) -> dict[str, Any]:
    return {
        "gate": "PRODUCTION_GATE",
        "status": "FAIL",
        "gate_stage": "pre_capcut",
        "reason": reason,
        "production_allowed": False,
        "capcut_creation": "BLOCKED",
        "script_lock_status": "NOT_LOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_dir")
    parser.add_argument("contract_json")
    parser.add_argument("--stage", choices=("capcut-openable", "production"), default="production")
    parser.add_argument("--out")
    args = parser.parse_args()

    root = Path(args.job_dir)
    contract_path = Path(args.contract_json)
    if not contract_path.is_absolute():
        contract_path = root / contract_path

    try:
        contract = load_json(contract_path)
        if args.stage == "capcut-openable":
            result = validate_capcut_openable_project_entry(contract, root)
        else:
            result = validate_gate(contract, root)
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
