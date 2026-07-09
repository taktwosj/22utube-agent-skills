# 02_PIPELINE_RULES

## Current Pipeline

If Tikitaka v3 handoff exists, use the Tikitaka v3 Handoff-First Pipeline below
before the source-first sequence. Do not reinterpret the locked script.

1. Confirm `input/video_url.txt`.
2. Save user Gemini/VLM/GPT content as `input/analysis_hint_raw.txt`.
3. Download or locate `source/source.mp4`; for YouTube sources, prefer
   FHD/1080-first source media when available (`1920x1080` landscape or
   `1080x1920` vertical Shorts) using a `width<=1920 AND height<=1920`
   yt-dlp cap.
4. Create `source/ffprobe_report.json`.
5. Extract frames and contact sheet.
6. Run PySceneDetect and write `evidence/scene_segments.json`.
7. Run Whisper or faster-whisper and write `evidence/whisper_segments.json`.
8. Run PaddleOCR first. If it fails, run EasyOCR fallback and record the fallback
   in `evidence/ocr_segments.json`.
9. Run audio VAD and write `evidence/audio_vad_segments.json`.
10. Create `evidence/source_evidence.json`.
11. Compare `analysis_hint` with source evidence and write
    `evidence/crosscheck_report.json`.
12. If user or story mentions specific speech, write
    `evidence/target_phrase_check.json`.
13. Create `decisions/segment_decision_table.json`.
14. If the script came from `00-tikitaka`, import or create
    `decisions/tikitaka_segment_audio_plan.json` from `구간 오디오 정책표`.
15. If the script came from `00-tikitaka`, require `SCRIPT_HANDOFF_GATE` before
    SRT/TTS/layout/asset prep or CapCut creation:
    `20_script/script_handoff_gate.json`, `20_script/block_map.json`, and
    `20_script/block_voice_switch_map.json` must pass with every edit block
    covered by explicit `source_audio` and `tts` decisions.
16. If an explicit production request and script authority already exist, and
    Tikitaka, Shorts Academy, 마라하기, 우라까이, 일치율 0%, ranking/TOP-N, or
    benchmark-remake strategy applies, create
    `decisions/shorts_academy_gate.json`.
17. Create `decisions/capcut_layout_plan.json`.
18. Create CapCut draft files.
19. Normalize the draft to `capcut/normalized_draft.json`.
20. Run harness validation.
21. Create `reports/evidence_pack.json`.
22. Create `reports/final_report.md`.

## Tikitaka v3 Handoff-First Pipeline

If Tikitaka v3 handoff exists, start from the locked handoff package.

1. Read `20_script/report1_handoff.json`.
2. Confirm `owner_skill=00-tikitaka`.
3. Confirm `next_skill=000short-production-agent`.
4. Confirm `report1_approved=true`.
5. Confirm `voice_audio_route_decided=true`.
6. Read `20_script/script_handoff_gate.json`.
7. Confirm `SCRIPT_HANDOFF_GATE` PASS and `capcut_allowed=true`.
8. Read `20_script/timeline_design.json`.
9. Validate expanded segment fields:

```text
source_ref
source_order
timeline_order
assembly_role
visible_text_role
audio_role
duration_basis
duration_status
visual_strategy
```

10. Confirm `20_script/timeline_design_gate.json` PASS.
11. Confirm `20_script/humanize_korean_gate.json` PASS.
12. Read `20_script/block_map.json`.
13. Read `20_script/block_role_map.json`.
14. Read `20_script/block_voice_switch_map.json`.
15. If narration-audio exists, read `20_script/tts_copy_text.txt`,
    `20_script/tts_duration_probe.json`, and
    `20_script/tts_timing_reconciliation_gate.json`.
16. If only `tts_caption/audio_role=none` exists, do not require TTS timing
    files and do not generate narration audio.
17. Confirm `00_source/source_manifest.json` or `00_source/source.mp4`.
18. Resolve template. Default is `shrt white`.
19. Resolve semantic audio tracks:

```text
audio.narration_tts  -> A9
audio.speaker_source -> A10
audio.sfx            -> A11
audio.bgm            -> A12
```

20. Generate `10_analysis/capcut_layout_plan.json` from `timeline_design.json`
    while preserving source_order/timeline_order/assembly_role/duration fields.
21. Generate `cut_manifest.json`.
22. Clone `shrt white`.
23. Implement `timeline_design.json` into `draft_content.json`.
24. Generate `capcut_timeline_manifest.json` proving protected field
    preservation.
25. Normalize draft.
26. Run media link gate.
27. Run T1/T2 full-duration gate.
28. Run visible text clean gate.
29. Run timeline implementation gate.
30. Create `90_reports/report2_handoff.json` and report.
27. Create `90_reports/report2_handoff.json` and 보고서2.

`capcut_layout_plan.json` is a derived implementation plan. It is not allowed to
override `timeline_design.json`.

Do not derive timeline_order from source_order.
Do not treat source_order as playback order.
Do not collapse tts_caption into tts_narration.
Do not generate narration audio when audio_role=none.
Do not modify assembly_role sequence.
Do not modify duration_basis/duration_status without WAIT_TIKITAKA_DESIGN_REPAIR.

## Input URL Rule

If `input/video_url.txt` is missing or empty, stop with:

```json
{
  "status": "BLOCKED",
  "reason": "video_url_missing",
  "SCRIPT_LOCK": "NO",
  "upload_ready": "NO"
}
```

## Analysis Hint Rule

Gemini JSON, VLM analysis, and user-provided rough analysis can be used only for:

- expected story structure
- expected timeline
- expected preserved speech
- expected on-screen text
- expected emotion peak
- expected remake point

They cannot be used as evidence for:

- STT complete
- OCR complete
- source analysis complete
- CapCut PASS
- SCRIPT_LOCK
- upload_ready

## Shorts Academy Production Gate

Run this gate only after an explicit production request and script authority
exist. Broad Shorts Academy wording alone does not start production. It only
validates handed-off script decisions before SRT/layout, CapCut, harness, or
final-report work.

The gate can apply when the production job came from `00-tikitaka`,
`00script-writer`, or a user-approved script package that contains terms such
as 쇼츠학개론, 마라하기 공식, 한계선, 돈통/에셋, 결, 가단야, 우라까이,
일치율 0%, 벤치영상, 채널기획, ranking/TOP-N, benchmark remake, or
channel-family labels such as 한짜/국뽕/해짜/드짜/영짜/랭킹/유머/군림보.

Read `references/shorts-academy.md` before segment decisions, render plan,
SRT/layout, CapCut draft creation, harness, or final report.

Required output:

```json
{
  "shorts_academy_reference_applied": true,
  "shorts_academy_gate": "PASS|WAIT|REWRITE_REQUIRED|N/A",
  "shorts_academy_gate_reason": "...",
  "channel_ceiling_checked": true,
  "ceiling_status": "checked|not_applicable",
  "asset_bank_basis": "...",
  "channel_texture_basis": "...",
  "benchmark_message": "...",
  "source_region": "domestic_korea|overseas|mixed_global|unknown",
  "emotion_intent": "감동|정보|웃음|충격|분노|국뽕|공감|사이다|호기심|스포츠감탄|실용|미담|unknown",
  "channel_family": "...",
  "content_mode": "...",
  "source_surface": "cctv|sports_game|broadcast_variety|drama_movie|game_screen|animation_3d|recipe_process|lifehack_process|photo_tts_explainer|interview_speech|speech_award|pet_moment|rescue_incident|other",
  "composite_label": "...",
  "layer_mix_decision_required": true,
  "caption_layer_mix": {
    "alias": "source_layer_mix",
    "tts_density": "none|sparse|balanced|heavy",
    "quoted_speech_density": "none|low|medium|high",
    "situation_caption_density": "low|medium|high",
    "source_audio_priority": "keep|duck|replace|unknown",
    "tts_role": "...",
    "quoted_speech_role": "...",
    "situation_caption_role": "...",
    "layer_mix_basis": "source_script_analysis|direct_source_evidence|user_sample_script",
    "do_not_invent_quotes": true
  },
  "verified_source_speech_present": false,
  "original_dialogue_reuse_policy": "maximize_verified_original_dialogue",
  "creative_additions_use_tts_or_situation_only": true,
  "source_word_synonym_rewrite_status": "PASS",
  "source_word_synonym_rewrite_policy": "rewrite source/benchmark wording with different Korean synonyms and sentence rhythm except verified quotes, names, numbers, or unavoidable nouns",
  "urakkai_required": true,
  "same_flow_allowed": false,
  "flow_urakkai_plan": {
    "original_flow": "...",
    "new_flow": "...",
    "changed_hook_entry": "...",
    "changed_tension_point": "...",
    "changed_payoff_recovery": "..."
  },
  "gadanya_check": {
    "guideline": "...",
    "word_rewrite": "...",
    "yaburi_comment_pressure": "..."
  },
  "similarity_break_plan": {
    "keyword": "...",
    "audio_timing": "...",
    "pixel_frame": "..."
  },
  "catcup_reference_layout_required": true,
  "catcup_reference_layout_profile": "black_template_master_v1 or insta_white_template_master_v1",
  "catcup_reference_project": "black or insta white",
  "catcup_text_role_order_top_to_bottom": [
    "top_title_1",
    "top_title_2",
    "tts",
    "source_speech_1",
    "source_speech_2",
    "situation_emotion"
  ],
  "capcut_t_track_contract": {
    "T1": "소제목1",
    "T2": "소제목2",
    "T3": "TTS / 나레이션 자막",
    "T4": "화자발언1",
    "T5": "화자발언2",
    "T6": "현장상황 / 행동 / 감정설명",
    "A9": "narration / TTS audio",
    "A10": "speaker source audio / original speech",
    "A11": "SFX",
    "A12": "BGM"
  },
  "catcup_text_role_rows": [
    {"role": "top_title_1", "active": true, "planned_track_id": "T1"},
    {"role": "top_title_2", "active": true, "planned_track_id": "T2"},
    {"role": "tts", "active": true, "planned_track_id": "T3"},
    {"role": "source_speech_1", "active": false, "planned_track_id": "T4"},
    {"role": "source_speech_2", "active": false, "planned_track_id": "T5"},
    {"role": "situation_emotion", "active": true, "planned_track_id": "T6"}
  ],
  "ranking_order_gate": {
    "required_for_ranking_top_n": true,
    "structure_remix_required": true,
    "source_order_allowed": false,
    "implemented_order": ["..."],
    "ranking_middle_preset_required": true,
    "ranking_middle_preset_name": "랭킹중간",
    "ranking_middle_preset_insertions": ["between_rank_items"],
    "ranking_transition_precision_required": true,
    "ranking_transition_probe_step_sec": "0.2-0.4",
    "ranking_transition_boundaries_file": "source_scene_transitions_precision.json"
  }
}
```

If channel/category planning is outside the job, use
`shorts_academy_gate=N/A` only with a concrete reason. For ranking/TOP-N,
`N/A` is not allowed for the structure remix fields. Ranking/TOP-N also requires
the `랭킹중간` CapCut preset/template between rank/item sections and a
transition-boundary precision pass around each rank/item change. If the source
scan starts at 1-second buckets, each bucket containing a rank transition must
be rescanned at `0.2` to `0.4` second intervals or by frame difference and
recorded in `source_scene_transitions_precision.json`.

All applicable remake jobs require `urakkai_required=true` and
`same_flow_allowed=false`. Ranking/TOP-N must change the literal order. Other
content modes may preserve unavoidable factual/source chronology only when the
functional viewing flow is changed through hook entry, tension placement,
reaction timing, caption interpretation, cut emphasis, or payoff recovery.

For current CatCup/11short template-backed projects, the default base is the
local draft named `shrt white`. Use `black` or `insta white` only when the user
explicitly selects that variant.

```text
$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\shrt white
$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\black
$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft\260625-ig-contortion-top3-urakkai-instagram-tts
```

The third folder displays in CapCut as `insta white`. Variant sample projects
use test media internally; generated drafts must replace that media with the job
source while preserving the selected project structure.

The hard check is the role-separated placement in `catcup_text_role_rows`, not
the presence of SFX, BGM, transition effects, or decorative animation. Effects
are optional unless the user explicitly requests them. The post-CapCut gate must
read the actual registered draft `draft_content.json` through
`capcut_draft_content_path` or the draft path and verify the active rows.

Original dialogue and creative additions:

- If verified source/original dialogue exists, set
  `verified_source_speech_present=true` and keep the corresponding
  `source_speech_1` row active.
- Use original dialogue as much as possible, but mark it as verified source
  speech. Do not invent new quoted speech.
- Added creative lines must be plain TTS/narration or `(상황설명)/(감정설명)` only.
- Source/benchmark wording outside verified quotes must pass
  `source_word_synonym_rewrite_status=PASS`: use different Korean words,
  synonyms, reordered sentence rhythm, and different caption phrasing except for
  names, numbers, and unavoidable nouns.

Layer mix is not optional. Decide whether the script is mostly TTS, mostly
verified source speech, or mostly `(상황설명)` from the source surface. For
example, `군림보` means `photo_tts_explainer` with heavy continuous TTS over
photos/images; sports games may use commentator/player quotes; CCTV usually
uses high situation captions and restrained TTS with no invented speech.

Missing or weak gate evidence blocks CapCut/final PASS with:

```json
{
  "status": "REWRITE_REQUIRED",
  "reason": "shorts_academy_gate_missing_or_incomplete"
}
```

## STT Status Values

Use exactly one:

```json
{
  "stt_status": "RAN_WITH_RESULT|RAN_EMPTY|AUDIO_ABSENT|FAILED|NOT_RUN"
}
```

`FAILED` and `NOT_RUN` fail. `RAN_EMPTY` and `AUDIO_ABSENT` can pass only when
execution evidence and reason are recorded.

## OCR Status Values

Use exactly one:

```json
{
  "ocr_status": "RAN_WITH_RESULT|RAN_EMPTY|NO_ONSCREEN_TEXT|FAILED|NOT_RUN"
}
```

`FAILED` and `NOT_RUN` fail. `RAN_EMPTY` and `NO_ONSCREEN_TEXT` can pass only
when execution evidence and reason are recorded.

## OCR Engine Rule

PaddleOCR is primary. EasyOCR is fallback.

If EasyOCR is used, record:

```json
{
  "ocr_engine_primary": "PaddleOCR",
  "ocr_engine_used": "EasyOCR",
  "engine_fallback": true,
  "fallback_reason": "..."
}
```

Never claim PaddleOCR ran when it did not.

## Target Phrase Check

When the user mentions a phrase such as `테슬라야`, `존중해`, `뭐 이런`, or a
script depends on a source phrase, create `evidence/target_phrase_check.json`.

Timestamp-free phrases are not verified source speech.

Required fields per detected phrase:

- `phrase`
- `found`
- `start`
- `end`
- `matched_text`
- `speaker`
- `source`
- `confidence`
- `is_verified_source_speech`

## Segment Decision Table

`decisions/segment_decision_table.json` is required before CapCut.

When Tikitaka is the script authority, `decisions/tikitaka_segment_audio_plan.json`
is also required before CapCut. It must be copied from the Tikitaka
`구간 오디오 정책표` / `tikitaka_segment_audio_plan`, not guessed in production.

Required fields per Tikitaka segment:

```json
{
  "segment_id": "seg_001",
  "source_order": 4,
  "timeline_order": 1,
  "edit_range": "00:00-00:03",
  "caption_type": "speaker_quote|tts_narration|situation_caption|tts_plus_source|ranking_item",
  "source_audio_policy": "on|off|duck",
  "tts_policy": "on|off",
  "bgm_policy": "optional|optional_duck|on|off|duck",
  "visible_text_role": "speaker_quote|tts|situation|ranking"
}
```

Tikitaka handoff rows may use `edit_range` as the human-readable timing label.
The normalized `segment_decision_table.json` must still expand that into numeric
`start` and `end` fields for validators and CapCut workers.

Validation rules:

- `caption_type=speaker_quote` or visible `"..."` requires `source_audio_policy=on`
- `caption_type=tts_narration` requires `source_audio_policy=off`
- `caption_type=tts_plus_source` requires `source_audio_policy=duck` or `on`
  with a recorded reason
- `caption_type=situation_caption` defaults to `source_audio_policy=off`
- ranking items default to `source_audio_policy=off`, except verified quote or
  reaction beats
- `bgm_policy=optional` or `optional_duck` means no BGM is required yet. Do not
  fail production for missing BGM unless the user selected a BGM/SFX asset or the
  locked plan says `bgm_policy=on` or `duck`.
- `source_order` and `timeline_order` are both required when the script remixes
  source order

If this plan is missing or conflicts with the script, stop with:

```json
{
  "status": "WAIT",
  "reason": "WAIT_TIKITAKA_SEGMENT_AUDIO_PLAN"
}
```

Each segment must include:

- `segment_id`
- `start`
- `end`
- `scene_ids`
- `visual_summary_ko`
- `whisper_text`
- `voice_present`
- `ocr_texts`
- `audio_type`
- `segment_type`
- `story_function`
- `audio_action`
- `source_audio_policy`
- `tts_policy`
- `bgm_policy`
- `text_action`
- `capcut_text_layer`
- `capcut_audio_layer`
- `decision_reason`
- `evidence_refs`
- `uncertainty`
