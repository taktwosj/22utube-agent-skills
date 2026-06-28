# Gemini Normalization

Gemini/AI Studio output is raw observation. Normalize it before production.

## Save Artifacts

Save the submitted prompt and answer:

```text
gemini_request.md
aistudio_clipboard.txt
analysis_raw_gemini.json
```

`gemini_request.md` must be built from:

```text
references/gemini-capcut-remake-system-prompt.md
```

Append the concrete source URL at the end:

```text
[입력]
video_url: {url}
```

If using a master cross-check:

```text
gemini_master_request.md
aistudio_master_clipboard.md
analysis_master_gemini.md or analysis_master_gemini.json
analysis_crosscheck.md
```

## Common Gemini Failures

Fix these before harness:

- Wrong `video_url` from a stale AI Studio URL context.
- Malformed JSON, especially unescaped quotes inside Korean dialogue.
- Time ranges that do not cover the full video continuously.
- Segment gaps or overlaps.
- `caption_ko_final` longer than two lines or 14 chars per line.
- `title_candidates` longer than 6 Korean chars.
- `top_title_text` too plain or too long.
- `opening_voice_line` missing `라는데` or `다는데`.
- OCR coordinates given as pixels instead of normalized 0..1 ratios.
- `capcut_y` copied from screen y instead of calculated as `(0.5-y)*2`.
- Purple OCR text placed in top or bottom reserved bands.
- Missing script-writer retention fields.
- Upload title written as a topic label instead of a spoken hook. Example failure: `기름빵 한 입에 끝나는 맛`. Better: `자 1000칼로리 들어갑니다`.
- Missing hook-forward decision. Every remake must either pull the strongest visual beat to the first 0.5-2.0 seconds or record why the source already opens strongly.
- Missing `analysis_status`, `all_detected_texts`, `text_removal_assessment`, `automation_judgment`, or exactly 3 `predicted_comments` in the raw Gemini output.

## Cross-Check Checklist

Before `assets`, confirm:

```text
[ ] duration and final timestamp match source.mp4
[ ] no segment gap, overlap, or overrun
[ ] core point matches actual source video
[ ] visible action order matches the source
[ ] OCR/onscreen text candidates are not missed
[ ] speech/sfx are not invented
[ ] reframe/focus keeps the key object visible
[ ] title/captions are standard Korean and within limits
[ ] upload title is a viewer-facing hook, not a summary label
[ ] strongest visual beat is identified and pulled to the front when needed
[ ] safety risks are not sensationalized
[ ] predicted comments are plausible and source-grounded
```

Record the verdict in `analysis_crosscheck.md` as `PASS`, `FIXED`, or `BLOCKED`.

## New Raw Gemini Schema Mapping

The canonical Gemini prompt returns raw fields for analysis, not the final production schema. Normalize them before harness:

```text
video_duration_sec -> duration_seconds
predicted_comments -> best_comments_predicted
segments[].onscreen_text_original -> segments[].onscreen_text_en
segments[].speech_original -> segments[].speech_en
```

Keep these fields in `analysis.json` when useful for review:

```text
analysis_status, analysis_error_reason, all_detected_texts,
timeline_summary_ko, text_removal_assessment, automation_judgment
```

If `automation_judgment.usable_for_remake=false`, or `text_removal_assessment.difficulty` is `reject`, stop before assets/CapCut and report the blocker. If Gemini returns `capcut_y`, recompute it from `y` using `(0.5-y)*2` before writing `onscreen_layout.json`.

## Writer Pass Fields

Every normalized `analysis.json` must include:

```json
{
  "script_writer_mode": "cc_remake_observation_shorts",
  "script_writer_pass_complete": true,
  "writer_mode_applied": true,
  "viewer_to_keep_ko": "",
  "viewer_to_ignore_ko": "",
  "click_emotion_ko": "",
  "memory_anchor_ko": "",
  "big_open_loop_ko": "",
  "first_5_seconds_hook_ko": "",
  "title_strategy_ko": "",
  "bottom_caption_strategy_ko": "",
  "purple_overlay_strategy_ko": "",
  "upload_title_hook_ko": "",
  "hook_forward_plan_ko": "",
  "hook_forward_edit": {
    "applied": true,
    "source_start": "00:00.000",
    "source_end": "00:01.500",
    "target_start": "00:00.000",
    "target_end": "00:01.500",
    "return_to_chronological_at": "00:01.500",
    "reason_ko": ""
  }
}
```

## OCR Coordinate Rule

For each overlay:

```text
x = (overlay_bbox.x1 + overlay_bbox.x2) / 2
y = (overlay_bbox.y1 + overlay_bbox.y2) / 2
width = overlay_bbox.x2 - overlay_bbox.x1
height = overlay_bbox.y2 - overlay_bbox.y1
capcut_x = (x - 0.5) * 2
capcut_y = (0.5 - y) * 2
```

Keep `capcut_y` between -0.68 and 0.68 so the overlay stays out of top/bottom reserved bands.
