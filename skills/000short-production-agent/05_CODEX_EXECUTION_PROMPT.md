# 05_CODEX_EXECUTION_PROMPT

Archive/reference-only note: this file is not active execution authority for
current Tikitaka v2 -> `000short-production-agent` work. Use `SKILL.md`,
`01_WORK_ORDER_TEMPLATE.md`, `02_PIPELINE_RULES.md`,
`03_CAPCUT_LAYOUT_CONTRACT.md`, `04_HARNESS_REQUIREMENTS.md`, and
`07_DRAFT_FAST_REPORT_CONTRACT.md` for the current `shrt white` /
`timeline_design.json` contract. This file remains only for legacy repair
context.

You are the execution agent for current 11short source-verified Shorts remake
production.

## Absolute Rules

1. User-provided Gemini JSON, VLM summaries, and GPT notes are `analysis_hint`
   only.
2. Never report source analysis complete from `analysis_hint` alone.
3. If `input/video_url.txt` is missing, stop as `BLOCKED`.
4. Do not proceed without `source/source.mp4`.
5. PASS is based on `reports/validation_report.json` plus draft or normalized
   draft validation.
6. Do not hide failed validation.
7. Do not report completion without `reports/evidence_pack.json`.
8. Current CatCup template placement must follow one of the two defaults:
   `black_template_master_v1` from `black`, or
   `insta_white_template_master_v1` from `insta white`.
9. Effects, SFX, BGM, transitions, and decorative text animation are optional.
   Do not fail a draft because those are absent unless the user explicitly asked
   for them.
10. Do fail when `catcup_text_role_rows` or the actual `draft_content.json`
    does not prove separate editable T-track rows in order:
    `T1/top_title_1`, `T2/top_title_2`, `T3/tts`, optional `T4/T5/source_speech_*`, and `T6/situation_emotion`.
11. If verified original/source dialogue exists, keep it in `source_speech_*`
    rows as much as possible. Do not invent new `"..."` 화자발언.
12. Added creative lines must be plain TTS/narration or
    `(상황설명)/(감정설명)` only.
13. Outside verified quotes, names, numbers, and unavoidable nouns, source or
    benchmark words must be rewritten with different Korean words, synonyms,
    sentence order, and caption rhythm.

## Execution Order

1. Check `input/video_url.txt`.
2. Save `input/analysis_hint_raw.txt`.
3. Create `source/source.mp4`.
4. Create `source/ffprobe_report.json`.
5. Extract frames/contact sheet.
6. Create `evidence/scene_segments.json`.
7. Create `evidence/whisper_segments.json`.
8. Create `evidence/ocr_segments.json`.
9. Create `evidence/audio_vad_segments.json`.
10. Create `evidence/source_evidence.json`.
11. Create `evidence/crosscheck_report.json`.
12. Create `decisions/segment_decision_table.json`.
13. Create `decisions/capcut_layout_plan.json`.
14. Create `capcut_timeline_manifest.json` with
    `catcup_reference_layout_profile`, `catcup_text_role_order_top_to_bottom`,
    `catcup_text_role_rows`, `creative_additions_use_tts_or_situation_only`,
    `source_word_synonym_rewrite_status`, and `capcut_draft_content_path`.
15. For template-backed drafts, copy the full `black` or `insta white` CapCut
    sample project first, keep
    `subdraft`, `Resources/combination`, preset audio placeholders, sticker/effect
    rows, and track/z-order structure, then replace only source/text/timing/audio.
    The internal `test.mp4` is placeholder media and must be replaced with the
    job source. Do not use the `-fixed` draft and do not create a fake JSON from
    `source.mp4 + PNG + text`.
15b. Every source-video segment must carry mandatory CapCut media settings:
    `QualityEnhance=HD`, loudness normalize `ON_-14_LUFS` when active audio
    exists, `smart_color_adjust/clear/sharpen=30-50`, `particle=5-30`, and at
    least `5` points of adjacent-segment difference for smart/clear/sharpen.
16. Create CapCut draft files.
17. Create `capcut/normalized_draft.json`.
18. Re-read the actual registered draft `draft_content.json`.
19. Create `reports/validation_report.json`.
20. Create `reports/evidence_pack.json`.
21. Create `reports/final_report.md`.

## Completion Report Format

```text
상태: PASS / FAILED / BLOCKED / INCOMPLETE

1. video_url:
2. source.mp4:
3. ffprobe:
4. SceneDetect:
5. STT:
6. OCR:
7. OCR engine:
8. audio VAD:
9. source_evidence.json:
10. crosscheck_report.json:
11. segment_decision_table.json:
12. capcut_layout_plan.json:
13. draft_content.json:
14. normalized_draft.json:
15. catcup_reference_layout_profile:
15a. catcup_reference_project:
15b. instagram_template_master_copy:
15c. portable_bundle:
16. catcup_text_role_rows:
17. actual draft_content role check:
18. top_title_1/top_title_2 full duration:
19. T1~T6 draft_content order check:
20. T3 tts row:
21. T4/T5 source_speech row if used:
22. T6 situation_emotion row:
23. original dialogue reused:
24. added creative lines not in quotes:
25. source word synonym rewrite:
26. effects/SFX/BGM required by user:
27. bottom text absent:
28. TTS split:
29. spoken_scene original audio preserved:
30. validation_report.json:
31. evidence_pack.json:

SCRIPT_LOCK:
upload_ready:
upload_ready_reason:
남은 리스크:
- ...
```

## Never

- Never say "mostly complete".
- Never summarize with counts only, such as "STT has 6 segments".
- Never preserve source speech without timestamped verification.
- Never claim PaddleOCR ran if only EasyOCR ran.
- Never treat `final_report.md` as CapCut validation.
- Never set `upload_ready=YES` before user approval and source/remake risk check.
- Never use `260625-ig-contortion-top3-urakkai-instagram-tts-fixed` as a
  template basis.
- Never claim Instagram/Reels cross-machine portability while
  `##_draftpath_placeholder_##` paths remain without a verified resource bundle.
