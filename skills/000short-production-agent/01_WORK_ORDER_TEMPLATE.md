# 01_WORK_ORDER_TEMPLATE

## Purpose

Use this work order for current 11short Shorts remake production.
User-provided Gemini JSON, VLM summaries, GPT drafts, and rough notes are
`analysis_hint` only. They are never source truth.

## Source Of Truth

Priority order:

1. `source/source.mp4`
2. `source/ffprobe_report.json`
3. `evidence/scene_segments.json`
4. `evidence/whisper_segments.json`
5. `evidence/ocr_segments.json`
6. `evidence/audio_vad_segments.json`
7. `evidence/source_evidence.json`
8. `evidence/target_phrase_check.json`
9. `evidence/crosscheck_report.json`
10. `decisions/segment_decision_table.json`
11. `decisions/capcut_layout_plan.json`
12. `capcut/draft_content.json` or `capcut/normalized_draft.json`
13. `input/analysis_hint_raw.txt` or `input/analysis_hint.json`

If `analysis_hint` conflicts with source evidence, source evidence wins.

## Required Outputs

- `input/video_url.txt`
- `input/analysis_hint_raw.txt` when the user provides Gemini/VLM/GPT analysis
- `source/source.mp4`
- `source/ffprobe_report.json`
- `evidence/scene_segments.json`
- `evidence/whisper_segments.json`
- `evidence/ocr_segments.json`
- `evidence/audio_vad_segments.json`
- `evidence/source_evidence.json`
- `evidence/target_phrase_check.json` when a phrase matters or is user-mentioned
- `evidence/crosscheck_report.json`
- `decisions/segment_decision_table.json`
- `decisions/capcut_layout_plan.json`
- `capcut/draft_content.json`
- `capcut/draft_meta_info.json`
- `capcut/draft_virtual_store.json`
- `capcut/normalized_draft.json`
- `reports/validation_report.json`
- `reports/evidence_pack.json`
- `reports/final_report.md`

## Prohibitions

- Do not report source analysis complete from `analysis_hint` alone.
- Do not finalize CapCut layout without STT, OCR, SceneDetect, VAD, and
  `segment_decision_table.json`.
- Do not grant PASS from `final_report.md` wording.
- Do not grant `SCRIPT_LOCK=YES` without `validation_report.json`.
- Do not call a voice "Daniel", "Chunsik", or any other label unless the
  requested voice id is recorded and verified.
- Do not create a bottom caption layer for current 11short production.
