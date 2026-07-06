# DRAFT_FAST / FINAL_LOCK Report Contract

This document preserves the 11short factory reporting and fast-mode contract that used to live in the large `SKILL.md`. Keep `SKILL.md` as the short router, but do not drop these tokens or rules when splitting the skill.

## Template Default Contract

Current official template defaults are only `black` / `블랙기본` and `insta white` / `인스타템플릿`; there is no separate official third/basic template base unless the operator adds it to `manifests/capcut-template-set.json`.

## DRAFT_FAST_REFERENCE_SIMILARITY_REQUIRED

When the selected template is `black` / `블랙기본` or `insta white` / `인스타템플릿`, `DRAFT_FAST` must create or locate a reference fingerprint before reporting a CapCut draft as DRAFT.

Required fast gates:

- `template_profile_match`: selected template name, reference draft path, text-track roles, background/frame material, and source-video slot match the reference profile.
- `middle_caption_format_match`: timed `중단` text uses the planned caption role and layer. `T3` is TTS/narration, `T4/T5` are verified quote layers, and `T6` is situation/emotion/card text. Do not collapse all middle text into one arbitrary caption style when the handoff names role-separated layers.
- `reference_visual_preview_match`: cover/contact sheet or screenshot shows the selected `black` or `insta white` structure, not only media readability.
- `active_draft_cleanup_gate`: the active local draft folder has no `*.bak`, `.before_*`, `before_*`, `*_backup_*`, `*.tmp`, `template-*.tmp`, or temporary helper leftovers before `DRAFT_FAST` can pass.

Failure tokens:

```text
FAIL_TEMPLATE_PROFILE_MISMATCH
FAIL_MIDDLE_CAPTION_FORMAT_MISMATCH
FAIL_PROJECT_CLEANUP
```

`SIMILARITY_LOOP_PASS is not DRAFT_FAST_PASS`: the similarity loop may only clear similarity dimensions. `DRAFT_FAST` still needs the fast gates above plus media, openability, Korean text, and visual checks.

## Production Mode Gate

`PROJECT_FILE_REQUEST_DEFAULT` is `AUTO_FULL_CAPCUT_PROJECT`, not `DRAFT_FAST`.

Use `URL_PLUS_GEMINI_PLUS_PROJECT_FILE` when the user provides a Shorts URL,
Gemini/source analysis, and asks to `진행`, `해`, `끝까지`, `골기능`,
`캣컵프로젝트파일까지`, `CapCut project`, or equivalent project-file completion.
That means: produce the best possible local CapCut project file through the
normal script, production, visual/template, and cleanup gates. The target is a
perfect local CapCut project file, not a deliberately shallow technical draft.

Use `INTERACTIVE_SCRIPT_APPROVAL` when the user asks to choose, review, or
decide during the urakkai/script/template phase. In that mode, stop at the
named checkpoints and ask before production continues.

Use `DRAFT_FAST_EXPLICIT_ONLY` for fast technical drafts. DRAFT_FAST is allowed
only when the user explicitly says `DRAFT_FAST`, `빠른 초안`, `기술 초안`,
`초안만`, `검토용 draft만`, or a clear equivalent. Do not default ordinary
project-file requests to DRAFT_FAST.

## DRAFT_FAST State Split

Never use one generic `DRAFT_FAST PASS` label. Split draft evidence into
separate states:

```text
TECHNICAL_DRAFT_CHECK: PASS / FAIL
LOCAL_JSON_CHECK_PASS: PASS / FAIL
MEDIA_LINK_CHECK_PASS: PASS / FAIL
VISUAL_TEMPLATE_CHECK: PASS / FAIL / NOT_RUN
USER_CAPCUT_REVIEW: PASS / WAIT
USER_CAPCUT_REVIEW_WAIT
FINAL_LOCK: PASS / WAIT
FINAL_LOCK_WAIT
```

Use these as hard language rules:

```text
JSON PASS != 영상 PASS
runtime HASH_MATCH != CapCut quality PASS
DRAFT_FAST != FINAL_LOCK
```

`TECHNICAL_DRAFT_CHECK` covers parseability, media links, SRT/openability, hash
sync, and mojibake checks only. It does not approve visual template quality.
`VISUAL_TEMPLATE_CHECK` requires screenshot/frame evidence and template/profile
comparison. `USER_CAPCUT_REVIEW_WAIT` remains the state until the operator has
actually reviewed the CapCut screen or preview evidence.

## Final CapCut Project Type/Template Gate

For every `final_capcut_project_file` or final local draft claim, verify the
project by shorts type and template, not by JSON existence alone.

Required matrix:

```text
shorts_type_template_matrix
story_type
production_type
template_profile
```

Required visual/template checks:

- `caption_layer_role_match`: the actual CapCut text layers follow the planned
  role map for the selected `story_type`, `production_type`, and
  `template_profile`.
- `caption_position_match`: top/middle/card captions use the reference
  position, scale, line count, safe area, and effect for that template.
- `reference_frame_similarity`: sampled frames or screenshots visually match
  the reference profile for the selected type/template.
- `visual_screenshot_required`: a screenshot, cover/contact sheet, or frame
  sample is required before `VISUAL_TEMPLATE_CHECK` can be `PASS`.
- `source_caption_overlap_check`: source burned-in captions, faces, key action,
  and our generated captions do not awkwardly overlap.
- `capcut_processing_idle_check`: CapCut must not be left in an internal
  processing state such as "features applying" before review is called ready.
- `mandatory_capcut_media_settings_status`: the mandatory media-settings
  validator evidence must be present when the project is presented as ready.

If screenshot/frame evidence is missing, stop with:

```text
WAIT_VISUAL_SCREENSHOT_REQUIRED
```

If the operator still needs to inspect the CapCut preview, stop with:

```text
WAIT_USER_CAPCUT_REVIEW
```

## Pre-CapCut Script Package Contract

For legacy external handoff or user-supplied SRT/audio package workflows, produce `pre_capcut_script_package.md` for the user before CapCut creation. Do not call that file `reports/final_report.md`; the final report is reserved for post-CapCut validation.

The modern validator may record this as `pre_capcut_script_package_status`, but the filename token `pre_capcut_script_package.md` remains part of the contract for compatibility and reporting tests.

## DRAFT_FAST / FINAL_LOCK Mode Gate

`DRAFT_FAST` is an explicit fast-review mode only. The user must explicitly say
`FINAL_LOCK`, `최종 업로드용`, `업로드 준비`, or equivalent to switch to
`FINAL_LOCK`.

- `DRAFT_FAST` creates a reviewable CapCut draft and runs only the fast draft checks: template-copy basis, `template_profile_match`, placeholder media removal, real source video link, T1-T6 role order, `middle_caption_format_match`, bottom-layer ban, mandatory CapCut media settings, Korean text gate, media path/openability, `reference_visual_preview_match`, visual preview sanity, and `active_draft_cleanup_gate`.
- `AUTO_FULL_CAPCUT_PROJECT` creates a complete local project-file candidate and runs the same script authority, source, SRT/layout, CapCut, visual/template, media-settings, cleanup, and report gates needed for a user-reviewable project file.
- `INTERACTIVE_SCRIPT_APPROVAL` pauses before production at the urakkai/script/template checkpoints selected by the user.
- `FINAL_LOCK` runs full writer/persona gates, policy/safety, `SCRIPT_LOCK`, production gate, post-CapCut gate, harness `all`, upload copy, and upload readiness.
- Any older gate that requires `SCRIPT_LOCK`, 5-persona approval, `production_gate_result.json`, `post_capcut_timeline_gate_result.json`, `--stage all`, or upload text is `FINAL_LOCK only` unless this document says it is part of the DRAFT_FAST fast-check list.

## DRAFT_FAST_COST_BUDGET

`DRAFT_FAST` is a fast draft-production mode, not a full upload-production mode. Expected effort split:

```text
skill_rule_check=5-10%
input_srt_tts=15-25%
capcut_create_rebuild=35-45%
korean_repair=0-5%
final_verify_report=10-15%
```

If skill/rule checking exceeds 10% or Korean repair exceeds 5%, stop and report the exact blocker instead of continuing to browse rules or manually repair mojibake.

## KOREAN_TEXT_FAST_GATE

Korean text corruption is a preflight failure, not a normal work stage.

Use `NO_INLINE_KOREAN_IN_SHELL`: do not embed Korean final captions, SRT, or CapCut text directly inside PowerShell one-liners, shell heredocs, or inline Python strings. Write Korean through UTF-8 files such as `final_script_ko.txt`, `onscreen_ko.srt`, `scenario.json`, `tts_lines.txt`, or `guide_ko.srt` and read those files from builders.

## MOJIBAKE_PATTERN_FAIL

Before draft creation and after draft creation, scan all Korean text artifacts and the actual registered `draft_content.json` text scan. The `draft_content.json text scan` must look at the text material values actually registered in the CapCut draft, not only generated SRT or manifest files.

Scan for `????`, `���`, replacement character `�`, broken common Korean labels, or mojibake patterns. Any hit is DRAFT_FAST `FAIL_KOREAN_TEXT_GATE`; fix the input file or builder encoding, then regenerate. Do not spend a late 20-30% "Korean repair" stage manually editing generated JSON.

## DRAFT_FAST_WORKING_DRAFT_CREATED

A successful `DRAFT_FAST` outcome is a reviewable CapCut draft state, not final production completion.

Use:

```text
DRAFT_FAST_WORKING_DRAFT_CREATED
WORKING_DRAFT_CREATED
technical_ready=true
```

Do not use:

```text
FINAL
production PASS
upload_ready=YES
```

for `DRAFT_FAST`. `upload_ready=YES` is allowed only in `FINAL_LOCK` or explicit upload-readiness work.

## 11short Factory Report Contract

Every 11short response after a draft attempt must use one of these two report shapes. Do not invent a third shape.

### DRAFT_FAST report shape

```text
[DRAFT_FAST 쇼츠공장 보고]
상태: DRAFT / FAIL / WAIT
모드: DRAFT_FAST
템플릿:
CapCut draft:
draft path:
source:

쇼츠 유형:
- story_type:
- production_type:
- template_profile:
- shorts_type_template_matrix:

분리 판정:
- TECHNICAL_DRAFT_CHECK:
- LOCAL_JSON_CHECK_PASS:
- MEDIA_LINK_CHECK_PASS:
- VISUAL_TEMPLATE_CHECK:
- USER_CAPCUT_REVIEW:
- FINAL_LOCK:

빠른 검증:
- template_copy:
- template_profile_match:
- source_replaced:
- T1_T6_role_order:
- middle_caption_format_match:
- caption_layer_role_match:
- caption_position_match:
- bottom_layer_forbidden:
- mandatory_capcut_media_settings:
- mandatory_capcut_media_settings_status:
- KOREAN_TEXT_FAST_GATE:
- media_link_gate:
- openability_gate:
- reference_visual_preview_match:
- reference_frame_similarity:
- visual_screenshot_required:
- source_caption_overlap_check:
- capcut_processing_idle_check:
- visual_preview:
- active_draft_cleanup_gate:

시간/작업비율:
- skill_rule_check:
- input_srt_tts:
- capcut_create_rebuild:
- korean_repair:
- final_verify_report:

BLOCKERS:
- ...

NEXT:
- ...
```

Rules:

- DRAFT_FAST report must not say `SCRIPT_LOCK`, `production PASS`, `upload_ready`, or `FINAL` unless FINAL_LOCK was explicitly requested.
- If the draft exists, end with `CAPCUT_COPY_BLOCK_LAST`.
- If no draft exists, report the planned draft name and the blocker.

### FINAL_LOCK final report shape

```text
[FINAL_LOCK 최종 보고]
상태: PASS / FAIL / WAIT
모드: FINAL_LOCK
source evidence:
script lock:
writer/humanize:
policy/safety:
production gate:
CapCut post gate:
harness:
visual QA:
upload_ready:

COPY_READY_OUTPUT_BLOCK
제목
내용
출처:{url}
태그
상단
중단
중단 TTS 글자만 복사

CAPCUT_COPY_BLOCK_LAST
캣컵복사하기
{draft_name}
```

Rules:

- `COPY_READY_OUTPUT_BLOCK` is required only for completed FINAL_LOCK or when the user explicitly asks for upload/copy text.
- `CAPCUT_COPY_BLOCK_LAST` means the final visible block in the reply is the CapCut project name only. Do not place evidence, paths, warnings, or extra upload copy after it.
- Final report wording is never validation authority. Validation authority is the actual gate files, actual `draft_content.json`, and harness output.
