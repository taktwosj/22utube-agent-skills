# DRAFT_FAST / FINAL_LOCK Report Contract

This document preserves the 11short factory reporting and fast-mode contract that used to live in the large `SKILL.md`. Keep `SKILL.md` as the short router, but do not drop these tokens or rules when splitting the skill.

## Template Default Contract

Current official template defaults are only `black` / `블랙기본` and `insta white` / `인스타템플릿`; there is no separate official third/basic template base unless the operator adds it to `manifests/capcut-template-set.json`.

## Pre-CapCut Script Package Contract

For legacy external handoff or user-supplied SRT/audio package workflows, produce `pre_capcut_script_package.md` for the user before CapCut creation. Do not call that file `reports/final_report.md`; the final report is reserved for post-CapCut validation.

The modern validator may record this as `pre_capcut_script_package_status`, but the filename token `pre_capcut_script_package.md` remains part of the contract for compatibility and reporting tests.

## DRAFT_FAST / FINAL_LOCK Mode Gate

Every ordinary 11short factory run is `DRAFT_FAST` by default. The user must explicitly say `FINAL_LOCK`, `최종 업로드용`, `업로드 준비`, or equivalent to switch to `FINAL_LOCK`.

- `DRAFT_FAST` creates a reviewable CapCut draft and runs only the fast draft checks: template-copy basis, placeholder media removal, real source video link, T1-T6 role order, bottom-layer ban, mandatory CapCut media settings, Korean text gate, media path/openability, and visual preview sanity.
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

빠른 검증:
- template_copy:
- source_replaced:
- T1_T6_role_order:
- bottom_layer_forbidden:
- mandatory_capcut_media_settings:
- KOREAN_TEXT_FAST_GATE:
- media_link_gate:
- openability_gate:
- visual_preview:

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
