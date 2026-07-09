# 01_WORK_ORDER_TEMPLATE

## Purpose

Use this work order for current 11short Shorts remake production.
User-provided Gemini JSON, VLM summaries, GPT drafts, and rough notes are
`analysis_hint` only. They are never source truth.

## Source Of Truth

Priority order for current `22factory_20260628` episodes:

1. `00_source/source_manifest.json` plus local source path evidence
2. `00_source/ffprobe_report.json`
3. `10_analysis/scene_segments.json`
4. `10_analysis/whisper_segments.json`
5. `10_analysis/ocr_segments.json`
6. `10_analysis/audio_vad_segments.json`
7. `10_analysis/source_evidence.json`
8. `10_analysis/target_phrase_check.json`
9. `10_analysis/crosscheck_report.json`
10. `10_analysis/segment_decision_table.json`
11. `10_analysis/capcut_layout_plan.json`
12. `50_capcut_project/draft_content_snapshot.json` or `50_capcut_project/normalized_draft_snapshot.json`
13. `10_analysis/analysis_hint_raw.txt` or `10_analysis/analysis_hint.json`

Legacy flat paths such as `source/`, `evidence/`, `decisions/`, `capcut/`, and
`reports/` are compatibility aliases only. New work should write the numbered
factory paths above.

If `analysis_hint` conflicts with source evidence, source evidence wins.

## Tikitaka v2 Handoff Source Of Truth

When the job comes from `00-tikitaka` v2, the Stage 2 source of truth is:

1. `20_script/report1_handoff.json`
2. `20_script/script_handoff_gate.json`
3. `20_script/timeline_design.json`
4. `20_script/timeline_design_gate.json`
5. `20_script/humanize_korean_gate.json`
6. `20_script/block_map.json`
7. `20_script/block_role_map.json`
8. `20_script/block_voice_switch_map.json`
9. `20_script/tts_copy_text.txt`
10. `00_source/source_manifest.json` or `00_source/source.mp4`

`10_analysis/capcut_layout_plan.json` is derived from `timeline_design.json`.
It is not higher authority than the locked Tikitaka design.

## Required Outputs

- `00_source/video_url.txt`
- `10_analysis/analysis_hint_raw.txt` when the user provides Gemini/VLM/GPT analysis
- `00_source/source_manifest.json` with the active local source path and hash/probe evidence
- `00_source/ffprobe_report.json`
- `10_analysis/scene_segments.json`
- `10_analysis/whisper_segments.json`
- `10_analysis/ocr_segments.json`
- `10_analysis/audio_vad_segments.json`
- `10_analysis/source_evidence.json`
- `10_analysis/target_phrase_check.json` when a phrase matters or is user-mentioned
- `10_analysis/crosscheck_report.json`
- `10_analysis/segment_decision_table.json`
- `10_analysis/capcut_layout_plan.json`
- `20_script/report1_handoff.json`
- `20_script/timeline_design.json`
- `20_script/timeline_design_gate.json`
- `20_script/humanize_korean_gate.json`
- `20_script/script_handoff_gate.json`
- `20_script/block_map.json`
- `20_script/block_role_map.json`
- `20_script/block_voice_switch_map.json`
- `20_script/tts_copy_text.txt`
- `50_capcut_project/capcut_project_name.txt`
- `50_capcut_project/local_capcut_path.txt`
- `50_capcut_project/capcut_draft_manifest.json`
- `50_capcut_project/draft_content_snapshot.json`
- `50_capcut_project/draft_meta_info_snapshot.json`
- `50_capcut_project/media_link_manifest.json`
- `50_capcut_project/source_relink_gate.json`
- `50_capcut_project/restore_notes.md`
- `cut_manifest.json`
- `proof/contact_sheet.jpg`
- `proof/clip_durations.csv`
- `proof/timeline_order.txt`
- `proof/capcut_assembly_report.json`
- `90_reports/validation_report.json`
- `90_reports/evidence_pack.json`
- `90_reports/report2_handoff.json`
- `90_reports/final_report.md`

## Prohibitions

- Do not report source analysis complete from `analysis_hint` alone.
- Do not finalize CapCut layout without STT, OCR, SceneDetect, VAD, and
  `segment_decision_table.json`.
- Do not grant PASS from `final_report.md` wording.
- Do not grant `SCRIPT_LOCK=YES` without `validation_report.json`.
- Do not call a voice "Daniel", "Chunsik", or any other label unless the
  requested voice id is recorded and verified.
- Do not create a bottom caption layer for current 11short production.
