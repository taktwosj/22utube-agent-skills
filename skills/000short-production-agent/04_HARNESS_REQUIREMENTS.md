# 04_HARNESS_REQUIREMENTS

## Required Inputs

- `source/source.mp4`
- `source/ffprobe_report.json`
- `evidence/scene_segments.json`
- `evidence/whisper_segments.json`
- `evidence/ocr_segments.json`
- `evidence/audio_vad_segments.json`
- `evidence/source_evidence.json`
- `evidence/crosscheck_report.json`
- `decisions/segment_decision_table.json`
- `decisions/shorts_academy_gate.json` when Tikitaka, Shorts Academy, ranking/TOP-N,
  or benchmark-remake strategy applies
- `decisions/capcut_layout_plan.json`
- `capcut/draft_content.json`
- `capcut/draft_meta_info.json`
- `capcut/draft_virtual_store.json`
- `capcut/normalized_draft.json`
- `capcut_timeline_manifest.json`
- `cut_manifest.json`
- `proof/contact_sheet.jpg`
- `proof/clip_durations.csv`
- `proof/timeline_order.txt`
- `proof/capcut_assembly_report.json`
- `reports/validation_report.json`
- `reports/evidence_pack.json`

## Hard Fail

Any one of these fails or blocks the job:

- missing `input/video_url.txt`
- missing `source/source.mp4`
- invalid ffprobe
- SceneDetect `NOT_RUN` or `FAILED`
- STT `NOT_RUN` or `FAILED`
- OCR `NOT_RUN` or `FAILED`
- missing OCR engine record
- missing `segment_decision_table.json`
- Tikitaka/Shorts Academy/ranking/TOP-N/benchmark-remake job is missing
  `decisions/shorts_academy_gate.json`
- applicable `shorts_academy_gate` is not `PASS` or `N/A` with a concrete reason
- applicable `shorts_academy_reference_applied` is not true
- applicable `source_region`, `emotion_intent`, `source_surface`, or
  `composite_label` is missing
- applicable `layer_mix_decision_required` is not true
- applicable `caption_layer_mix` is missing TTS density, verified quote density,
  situation-caption density, source-audio priority, layer basis, or
  `do_not_invent_quotes=true`
- verified source/original dialogue exists but `source_speech_1` is not active
  in `catcup_text_role_rows`
- `creative_additions_use_tts_or_situation_only` is missing or not true
- `source_word_synonym_rewrite_status` is missing or not `PASS`
- humanizer or wording-polish pass changed verified source speech, speaker
  meaning, source timing, facts, names, numbers, policy-sensitive wording, or
  the separation between quoted speech, parenthesized situation captions, and
  plain TTS/narration
- applicable `urakkai_required` is not true
- applicable `same_flow_allowed` is not false
- applicable `flow_urakkai_plan` is missing original flow, new flow,
  changed hook entry, changed tension point, or changed payoff recovery
- applicable `gadanya_check` is missing guideline, word rewrite, or
  야부리/comment pressure coverage
- applicable `similarity_break_plan` is missing keyword, audio/timing when
  audio is used, or pixel/frame/order coverage. SFX, BGM, transition effects,
  and decorative text effects are optional and do not fail by absence.
- ranking/TOP-N job has `source_order_allowed` not false, missing
  `structure_remix_required=true`, or no implemented order different from the
  source/benchmark order
- ranking/TOP-N job is missing `ranking_middle_preset_required=true`,
  `ranking_middle_preset_name=랭킹중간`, or visible/manifested `랭킹중간`
  separator insertions between rank/item sections
- ranking/TOP-N job is missing `ranking_transition_precision_required=true`,
  `ranking_transition_probe_step_sec=0.2-0.4`, or recorded refined rank/item
  boundaries in `source_scene_transitions_precision.json`
- CapCut draft was created from generic wording without a recorded
  user-selected template or template-selection gate result
- normal/general Shorts target is not routed to one of the official manifest
  defaults, `black` or `insta white`
- Instagram/Reels target is not cloned or derived from `인스타템플릿` /
  `인스타 템플릿`, unless the user explicitly requested the legacy route and the
  report says so
- Instagram/Reels target silently used legacy `인스타기본` as the production base without
  an explicit user request; current default route is `인스타템플릿` or an explicit blocker
- Instagram/Reels target does not record
  `catcup_reference_layout_profile=insta_white_template_master_v1`
  and `catcup_reference_project=insta white`
- Black-template target does not record
  `catcup_reference_layout_profile=black_template_master_v1`
  and `catcup_reference_project=black`
- Instagram/Reels target uses
  `260625-ig-contortion-top3-urakkai-instagram-tts-fixed` or any draft name
  containing `-fixed` as the basis
- Instagram/Reels target was built as a fake lookalike from only
  `source.mp4 + PNG frame + text` instead of copying the template master draft
  folder and preserving `subdraft`, `Resources/combination`, preset audio
  placeholder relationships, sticker/effect rows, and track/z-order structure
- Template-backed actual draft is missing 10 total tracks, 4 editable text
  tracks, `materials.drafts`, `subdraft`, template-frame media, or
  `Resources/combination`, unless a new template version was explicitly approved
- Instagram/Reels actual draft contains visible `Default`, `T1`, or `T2`
  placeholder text
- Instagram/Reels actual draft leaves `##_draftpath_placeholder_##` media paths
  while claiming `portable_bundle=true`, cross-machine portability, or
  Mac/Windows/Claude/Hermes install portability
- selected template was recreated manually instead of cloned/derived from the
  actual local CapCut preset/reference draft
- active text role font, color, size, transform, position, alignment,
  animation/effect reference, or full-duration top-title style differs from the
  selected template/reference without explicit user approval
- caption text overflows the safe frame, runs outside the visible area, overlaps
  incoherently with another required text row, or is unreadable at the selected
  font size
- stale placeholder source video/audio/nested draft metadata remains on the
  active timeline or can break draft opening; required template-master
  `subdraft`, `Resources/combination`, `materials.drafts`, and preset audio
  placeholder relationships are preserved instead of deleted
- segment missing `segment_type`
- segment missing `audio_action`
- segment missing `evidence_refs`
- missing `capcut_layout_plan.json`
- missing `cut_manifest.json`
- `cut_manifest.source_segments` is missing or empty
- `cut_manifest.timeline_order` is missing, contains unknown segment ids, or
  omits a source segment id
- any cut segment is exact split-only instead of handle-included media
- any cut segment is missing `visible_start_ms`, `visible_end_ms`,
  `media_start_ms`, `media_end_ms`, `handle_before_ms`, `handle_after_ms`,
  `timeline_visible_trim_start_ms`, `timeline_visible_trim_end_ms`, or
  `export_file`
- any cut segment violates visible/media/trim bounds or source duration bounds
- any referenced `clips/S*_handle_*.mp4` export file is missing
- missing `proof/contact_sheet.jpg`, `proof/clip_durations.csv`,
  `proof/timeline_order.txt`, or `proof/capcut_assembly_report.json`
- `proof/clip_durations.csv` does not report PASS rows within media duration
  ±100ms
- `proof/capcut_assembly_report.json` is missing
  `timeline_order_verified=true`, `visible_trim_verified=true`,
  `handle_extendable=true`, `independent_clips_verified=true`, or
  `proof_files_verified=true`
- missing `draft_content.json`
- missing `normalized_draft.json`
- missing `capcut_timeline_manifest.json`
- registered CapCut draft folder is missing from the active local draft root
- reported `draft_name` does not match the actual registered CapCut draft folder
- `draft_content.json`, `draft_meta_info.json`, or `draft_virtual_store.json`
  cannot be parsed as JSON
- `capcut_timeline_manifest.video_track_contract` is missing or not
  `caption_video_plus_situation_speaker_video`
- `capcut_timeline_manifest.video_track_order_top_to_bottom` is missing or not
  `["caption_video","situation_speaker_video"]`
- `capcut_timeline_manifest.middle_text_track_order_top_to_bottom` is missing or not
  `["tts","source_speech","situation_emotion"]`
- actual `draft_content.json` T-track order changed after audio insertion, or audio/video/material segments were written into T1~T6 text tracks
- applicable `catcup_reference_layout_profile` is missing or not one of
  `insta_white_template_master_v1` or `black_template_master_v1`
- applicable `catcup_text_role_rows` is missing active role-separated rows for
  `top_title_1`/T1, `top_title_2`/T2, `tts`/T3, and
  `situation_emotion`/T6
- active `catcup_text_role_rows` share the same CapCut text track
- post-CapCut gate cannot read actual `draft_content.json` for the registered
  draft
- actual `draft_content.json` does not contain separate active text tracks for
  the CatCup reference roles
- actual draft has video/audio/media material accidentally placed into a text
  track or a text role placed into the wrong media track type
- actual `tts` row contains quoted speech or parenthesized situation/emotion
  captions
- actual `source_speech_*` rows contain non-quoted text
- actual or planned `source_speech_*` rows contain invented/creative additions
  instead of verified source dialogue
- actual `situation_emotion` row contains plain narration instead of
  parenthesized/reaction/emotion captions
- missing or empty `video_track_manifest`
- missing semantic video track `자막영상`
- missing semantic video track `상황·화자음성영상`
- missing `original_source_media.path=source.mp4`
- `original_source_media.imported_to_capcut_media` is not true
- `original_source_media.has_audio_stream` is not true
- CapCut draft media/material references do not retain `source.mp4`
- any referenced active video/audio/sticker/image/source media path is missing
  on disk
- CatCup top title rows `top_title_1` and `top_title_2` are missing or not full
  duration
- bottom text count is greater than 0
- TTS requested but split audio missing
- `spoken_scene` source audio covered by TTS
- source-video material missing `QualityEnhance` `HD`
- active audio exists but CapCut loudness normalize is not enabled at `-14 LUFS`
- source-video segment missing mandatory `smart_color_adjust`, `clear`,
  `sharpen`, or `particle`
- source-video segment `smart_color_adjust`, `clear`, or `sharpen` is outside
  `30-50`
- source-video segment `particle` is outside visible-slider `5-30`
- adjacent source-video segments do not differ by at least `5` points for
  `smart_color_adjust`, `clear`, and `sharpen`
- final report exists but draft validation does not
- final report after CapCut creation is missing the required CapCut 검수 summary
  with draft path, selected template, openability gate, media-link gate,
  style-preservation gate, role-track gate, frame/layout QA, and harness states
- Compound, gstack, Superpowers, humanizer, Honcho, Paperclip, or another
  optional tool result is cited as final authority instead of file-based source
  evidence, actual draft JSON, harness output, or explicit user approval
- Compound failure-review output is saved as a durable rule without operator
  review or without being reflected in a skill/harness/memory path that the
  current workflow actually loads

## Soft Warnings

These remain warnings only when they are decorative or non-user-visible polish.
Font, position, safe-zone, caption-fit, openability, media links, template
style preservation, and report completeness are hard failures above.

- text density that is readable and inside safe-zone but could be prettier
- missing or stale non-layout CatCup style metadata that cannot affect opening,
  visible text, media links, or user editing
- missing `situation_emotion` / `reaction_laugh` wobble-shake effect preset id
  before a captured CapCut preset id is available. The row role itself remains
  hard-required; only the exact preset id is a warning.
- missing SFX, BGM, transition effects, or decorative text animation when the
  user did not explicitly request them

## Validation Report

`reports/validation_report.json` is the PASS/FAIL authority.

Required top-level sections:

- `source_acquisition`
- `evidence_extraction`
- `crosscheck`
- `segment_decision`
- `shorts_academy_gate` when applicable
- `capcut_layout`
- `final_gate`

## SCRIPT_LOCK

`SCRIPT_LOCK=YES` requires:

- source exists
- source evidence exists
- crosscheck exists
- segment decision table exists
- if applicable, shorts academy gate is PASS or N/A with a concrete reason
- capcut layout plan exists
- normalized draft exists
- validation report overall status is PASS
- evidence pack exists
- no hard failures

## upload_ready

Validation PASS is not enough for upload readiness.

Before user approval and rights/remake risk confirmation:

```json
{
  "SCRIPT_LOCK": "YES",
  "upload_ready": "NO",
  "upload_ready_reason": "WAITING_FOR_USER_APPROVAL_AND_RIGHTS_CHECK"
}
```
