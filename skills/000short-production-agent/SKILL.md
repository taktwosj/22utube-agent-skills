---
name: 000short-production-agent
description: Use only when the user explicitly asks to create, validate, or repair production assets, subtitles, layout JSON, CapCut drafts, render packages, export packages, upload packages, or production packages. Do not use for script creation, urakkai decisions, hook/channel planning, or draft-only polishing.
---

# 11short Production Agent

## V2 Shared-Gate Router — Active Authority (2026-07-20)

> Work ID: `SHARED-GATE-SEPARATED-LANES-V2-20260720`
> This lane owns **G30 → G90** of the shared gate model.
> See `workflow.yaml` for the canonical gate router and
> `references/gates/*.md` for per-gate contracts.

### Lane ownership

```text
000short-production-agent  = G30 → G90
                          = TTS/measured audio, final SRT, track plan,
                            CapCut assembly, render/package, QC
                          = production owner (design consumer)
```

The design lane (G00 → G20) is owned by `00-tikitaka`. This lane never
rewrites hook, urakkai order, caption role, or production profile.

### Gate router

| Gate | Reference | Validator |
|---|---|---|
| G30 audio + measured duration lock | `references/gates/G30_AUDIO.md` | `scripts/validate_stage_gate.py` |
| G40 measured-audio-based caption + SRT lock | `references/gates/G40_CAPTION_SRT.md` | `scripts/validate_stage_gate.py` |
| G50 final second-level track plan | `references/gates/G50_TRACK_PLAN.md` | `scripts/validate_stage_gate.py` |
| G60 clean CapCut assembly + static harness | `references/gates/G60_CAPCUT_ASSEMBLY.md` | `scripts/validate_stage_gate.py` |
| G60.USER user CapCut visual gate | `references/gates/G60_CAPCUT_ASSEMBLY.md` | `scripts/validate_stage_gate.py` |
| G70 upload/thumbnail package, release=false | `references/gates/G70_UPLOAD_PACKAGE.md` | `scripts/validate_stage_gate.py` |
| G80 render/export + media integrity | `references/gates/G80_RENDER.md` | `scripts/validate_stage_gate.py` |
| G90 final QC + release gate | `references/gates/G90_FINAL_QC.md` | `scripts/validate_stage_gate.py` |

Runner: `scripts/workflow_runner.py`. The runner enforces cost/ownership
policy and executes only deterministic local operations.

### Entry contract

Reject entry without all of:
```text
owner_transfer_receipt exists and valid
canonical design_handoff SHA matches receipt.canonical_handoff_sha256
source_fingerprint matches
design_blueprint SHA matches
timeline SHA matches
external review receipt valid
```

### Hard prohibitions (this lane)

```text
rewrite hook
rewrite urakkai order
reinterpret caption role
change production profile without returning to G20
automatic CapCut GUI operations
automatic upload
paid TTS without COST_AUTHORIZED ledger event
automatic external LLM calls (auto_external_llm_calls = 0)
automatic retry (max_auto_retries = 0)
```

### Key invariants

```text
G30 measured audio precedes G40 final SRT                    (NORM-002)
NOT_REQUIRED + reason_code=NO_GENERATED_TTS                  (NORM-003)
NOT_REQUIRED_NO_GENERATED_TTS is forbidden                   (NORM-003)
G60 static PASS → WAIT_USER_VISUAL_GATE (static ≠ visual)
G70 release_allowed = false
G80 and G90 are separate gates
G90 release requires FINAL_QC_PASS + UPLOAD_APPROVED         (RW-P03-02)
CapCut root for general Shorts: shrt white
```

### Status-report format

```text
{gate}: {NOT_STARTED|READY|RUNNING|WAIT_USER_INPUT|
         WAIT_USER_VISUAL_GATE|WAIT_PAID_ACTION_APPROVAL|
         WAIT_UPLOAD_APPROVAL|WAIT_TIKITAKA_DESIGN_REPAIR|
         PASS|FAIL|REWORK_REQUIRED|NOT_REQUIRED}
```

`PASS` is emitted only by the deterministic validator.

### Hard-stop conditions

```text
WAIT_USER_INPUT
WAIT_USER_VISUAL_GATE
WAIT_PAID_ACTION_APPROVAL
WAIT_UPLOAD_APPROVAL
WAIT_TIKITAKA_DESIGN_REPAIR
FAIL_TEMPLATE_*              (V2 design section 41)
FAIL_MEDIA_*
FAIL_STALE_TEMPLATE_*
STOP_UNAPPROVED_PAID_ACTION
STOP_SOURCE_OF_TRUTH_CONFLICT
```

---

## Legacy / pre-V2 references (P10 will thin this section)

> 아래 콘텐츠는 V2 라우터 도입 전 원본입니다. P10에서 thin router로
> 축소될 예정입니다. 그 전까지는 V2 라우터 블록이 최상위 권위를 갖습니다.
> 충돌 시 V2 라우터와 `workflow.yaml`이 우선합니다 (NORM-002, NORM-003).

## Ownership Matrix

- `00-tikitaka`: Shorts source analysis, remake script draft, hook, top/timed-middle, and script handoff only.
- `000short-production-agent`: SRT, layout JSON, CapCut, validation, exports, upload packages, and other production assets only.

## Escalation Rule

Do not start this skill from script-adjacent intent alone. Use it only when the
user explicitly asks for subtitles, layout JSON, render plans, CapCut drafts,
exports, upload packages, production packages, production validation, or repair.

Route Tikitaka, 우라까이, hook, 상단, timed 중단, or Gemini source-note scripting
to `00-tikitaka`; keep wording-only revisions in that skill; follow the
workspace `AGENTS.md` and `docs/YOUTUBE_PRODUCTION_WORK_ORDER.md` for policy.

Do not originate the script, choose the urakkai angle, create hook/channel
planning, or polish a draft inside this skill. Confirm script authority first,
then build or validate the requested production files.

## Default Boundary

Default state is `PRODUCTION_GATE`.

No production pass is allowed from intent alone. Do not claim `PASS`,
`SCRIPT_LOCK`, upload-ready, export-ready, or complete unless the required
evidence files exist and the relevant validator has been run in this turn.

Working drafts, compatibility drafts, and draft-fast packages are intermediate
states. They are not production approval.

## CapCut Edit-Ready Boundary

For Tikitaka remake Shorts, the practical target of this skill is
`CAPCUT_EDIT_READY` / `HUMAN_POLISH_READY`: a local CapCut draft whose edit
order, text lanes, video lane, and audio lanes follow the locked handoff and are
ready for human polish in CapCut.

Shorts factory has two stages:

```text
1st stage = SCRIPT_LOCK_PACKAGE
2nd stage = CAPCUT_OPENABLE_PROJECT
```

`CAPCUT_OPENABLE_PROJECT` must use the 1st-stage package as authority:

```text
SCRIPT_LOCK_PACKAGE is the Source of Truth
No SCRIPT_LOCK_PACKAGE, no CapCut build
```

The 2nd stage means an openable CapCut project whose timeline reflects the 1st
stage script lock. `opening in CapCut is not enough`; the role map/audio map/TTS
body reflected in the actual timeline is required.

```text
role map/audio map/TTS body reflected
```

State meanings:

```text
script only = draft
SCRIPT_LOCK_PACKAGE = build allowed
openable CapCut project + SCRIPT_LOCK_PACKAGE reflected = project candidate
timeline validation PASS = production PASS candidate
```

```text
upload_ready is not the goal
production pass is not the goal
```

Do not report upload-ready, final, 100% complete, or production pass from this
stage. Report `CAPCUT_EDIT_READY_GATE` only after the project opens, the locked
edit order is implemented, and the remaining human work is listed:

```json
{
  "status": "CAPCUT_EDIT_READY",
  "human_polish_required": true,
  "manual_polish_items": []
}
```

Openable-stage validator split:

```text
validate_capcut_openable_project_entry
next_gate: ASSET_PREP_GATE
```

Use `validate_capcut_openable_project_entry` for the second stage. It validates
`REPORT1_HANDOFF_GATE`, `SCRIPT_HANDOFF_GATE`, Tikitaka v3 timeline design
files, role/audio maps, timing gates, and source manifest readiness for local CapCut project
creation. `validate_shared_requirements is FINAL_LOCK only`.
n8n is a FINAL_LOCK blocker only when `n8n_required=true`, not a
CAPCUT_OPENABLE_PROJECT blocker.
When the handoff gate is PASS, do not stop CapCut project creation just because
final report, upload, or optional n8n evidence is not complete.

## Stage 2 Tikitaka v3 Expanded Timeline Source of Truth

When input comes from `00-tikitaka` v3, production must implement the expanded
`20_script/timeline_design.json`. Do not reinterpret the script.

This extends the existing Stage 2 gate. It does not create a new stage.

Existing requirements still apply:

- `20_script/report1_handoff.json`
- `report1_approved=true`
- `voice_audio_route_decided=true`
- default CapCut base `shrt white`

Required Stage 2 inputs:

```text
20_script/report1_handoff.json
20_script/script_handoff_gate.json
20_script/timeline_design.json
20_script/timeline_design_gate.json
20_script/humanize_korean_gate.json
20_script/block_map.json
20_script/block_role_map.json
20_script/block_voice_switch_map.json
20_script/tts_copy_text.txt
20_script/tts_duration_probe.json when narration-audio exists
20_script/tts_timing_reconciliation_gate.json when narration-audio exists
00_source/source_manifest.json or 00_source/source.mp4
20_script/caption_beat_map.json
```

## Caption Assembly Contract

`caption_beat_map.json` is required for every timed middle-caption package.
This file is the visible-text timing authority consumed by the CapCut builder.
If it is missing, stop with `CAPTION_BEAT_MAP_REQUIRED`.

The fixed profiles are:

```text
profile_version=caption_profiles_v2
TTS (T3): y=-900, max_chars_per_line=10, max_lines=1
화자발언 (T4/T5): y=-500, max_chars_per_line=10, max_lines=1
( ) 상황설명 (T6): y=700, max_chars_per_line=10, max_lines=1
원본 영상 V1: video_scale=1.20
```

The 10-character limit includes whitespace. Every timed middle-caption beat is
one line only. Text exceeding the profile is split into sequential,
non-overlapping time beats. Splitting visible text must not trim, shift, or
otherwise alter audio or video duration. Face placement uses the fixed lower
safe-zone profile (`face_avoidance=fixed_lower_safe_zone_v1`); it is not a
manual-only layout decision.

The builder must consume `caption_beat_map.json`, apply the profile to the
actual text segment, and write the applied profile into the assembly manifest.

Primary machine-readable authority:

```text
20_script/timeline_design.json
```

Derived implementation artifacts:

```text
10_analysis/capcut_layout_plan.json
cut_manifest.json
capcut_timeline_manifest.json
50_capcut_project/draft_content_snapshot.json
50_capcut_project/draft_meta_info_snapshot.json
50_capcut_project/media_link_manifest.json
50_capcut_project/source_relink_gate.json
90_reports/report2_handoff.json
```

Protected fields:

```text
edit_id
source_ref
source_order
timeline_order
assembly_role
caption_type
visible_text_role
audio_role
time_start
time_end
track
duration_basis
duration_status
audio_policy
visual_strategy
```

If any protected field must change, stop with:

```text
WAIT_TIKITAKA_DESIGN_REPAIR
```

`capcut_layout_plan.json` is derived from `timeline_design.json`. It must not
override, shorten, reorder, merge, split, rename, or reinterpret protected
timeline fields. `source_order` is source provenance. `timeline_order` is
playback/edit order. Do not derive timeline_order from source_order. Semantic
audio lanes may be resolved to real CapCut A-tracks by template profile, but
that resolution must be recorded in the CapCut timeline manifest.

`tts_caption/audio_role=none` is caption-only and must not trigger TTS generation or TTS timing requirements.
`tts_narration/audio_role=audio.narration_tts` is narration audio
and requires `tts_duration_probe.json` plus
`tts_timing_reconciliation_gate.json`.

`capcut_timeline_manifest.json` must prove:

```text
protected_fields_preserved=true
assembly_role_sequence_preserved=true
timeline_order_preserved=true
source_order_preserved=true
duration_basis_preserved=true
duration_status_preserved=true
```

The active production gate must reject old six-field-only `timeline_design.json`
packages. If an active validation path accepts only `edit_id`, `time_start`,
`time_end`, `track`, `caption_type`, and `audio_policy`, treat it as:

```text
FAIL_ACTIVE_GATE_ACCEPTS_OLD_TIMELINE_DESIGN
```

## Default CapCut Mother Template Rule

This rule has higher priority than any episode-local builder script, old report,
or previous CapCut output.

For `production_type=politics_longform_derived`, do not apply the normal
`shrt white` default. Defer to `111-politics-longform` and require:

```text
reference_project_name=SHRTJUNGCHI
20_script/shorts/SHxx/edit_plan_approved.json
20_script/design_lock_manifest.json
```

If the current active writer machine cannot prove the actual `SHRTJUNGCHI`
folder, registry link, and locked plan hashes, stop with
`WAIT_SHRTJUNGCHI_ROOT_REQUIRED`. Do not substitute `shrt white`, a longform
`jungchilong` project, an earlier derived project, or a JSON snapshot.

Unless the user explicitly names another root CapCut template and provides
template-root proof, every normal/current 11short CapCut build or repair must
start by cloning the local CapCut draft named exactly:

```text
shrt white
```

Required default evidence before CapCut build:

```text
template_profile=shrt_white_base_v1
reference_project_name=shrt white
reference_project_path=<actual local CapCut draft path for shrt white>
derived_from_reference_project=true
```

Do not search old episode folders, old `90_reports/build_*.py` scripts, or prior
CapCut outputs for the base before using `shrt white`. A hard-coded
`REFERENCE_NAME` in an old builder is stale evidence, not template authority.

These names are never the default root base:

```text
260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1
260708 short
*_base_v2
*_base_v3
previous episode project folders
```

They may be inspected only as style samples or forensic evidence. If `shrt
white` is missing, inaccessible, or not recorded as the cloned reference, stop
with `WAIT_SHRT_WHITE_BASE_REQUIRED` / `WAIT_SHRT_WHITE_BASE_MISSING` /
`FAIL_SHRT_WHITE_BASE_NOT_CLONED`. If a stale builder points at a derived
project, stop with `FAIL_STALE_DERIVED_REFERENCE_BUILDER`; do not repair that
builder into the next project.

## Report 2 Contract

`보고서2` starts only after `설계도 승인` and a voice/audio route decision.
A CapCut/project request can select stage 2, but it cannot skip 설계도
승인 or TTS/오디오 방식 결정. If either is missing, stop with:

```text
WAIT_REPORT1_APPROVAL_TTS_DECISION
required: report1_approved + voice_audio_route_decided
```

When receiving a Tikitaka 설계도 package, read the legacy-compatible internal
`report1_handoff.json` when
present. It must have `REPORT1_HANDOFF_GATE`, `owner_skill=00-tikitaka`, and
`next_skill=000short-production-agent`. If the handoff is missing, invalid, or
points elsewhere, stop with `WAIT_REPORT1_HANDOFF_GATE`. 보고서2 starts only
after that handoff plus `report1_approved=true` and
`voice_audio_route_decided=true`.

It is the final user-facing report for the two-report Shorts workflow. The
workflow has one 설계도 and one 보고서2; 보고서2 is the final report. It is still not
an upload-ready claim unless the user explicitly approves upload and
rights/risk handling.

Write 보고서2 in 한글 우선 with 예/아니오 단답 rows. The default report template must
exist from the first CapCut project creation, because the same shape is reused
for later repairs.

Required 보고서2 기본 양식:

```text
# 보고서2

보고서2 시작: 예
최종보고서: 예
상태: REPORT2_FINAL
CapCut 프로젝트 생성 후 보고: 예
CapCut 프로젝트명:
CapCut 열어보기 필요: 예
사용자 확인 대기: 예
업로드 준비 완료: 아니오
최종 잠금: 아니오

제목:

내용(출처 태그 포함):

대본 반영: 예/아니오
TTS/오디오 반영: 예/아니오
자막 반영: 예/아니오
원본 영상 반영: 예/아니오
임시파일 정리: 예/아니오

현재 기준:
- 현재 draft_content.json 기준
- 현재 draft_meta_info.json 기준

남은 일:
- 사용자가 CapCut을 열고 문제를 제시하면 수정 후 다시 보고서2
- 사용자가 내보내기로 영상 생성하면 보고서2 종료
```

When the user opens CapCut and reports a problem, repair the local project and
emit 보고서2 again with `status: REPORT2_REVISED`. It is still 보고서2, the final
report shape for that repaired state. Keep the same basic form so each revision
is comparable.

Manual CapCut editing is expected. 수동 편집 길이 변화 is expected after the
operator opens CapCut. A duration difference between an earlier
automatic snapshot and the current local project is `MANUAL_EDIT_EXPECTED`, not
a failure by itself. 길이 차이만으로 FAIL 금지. Re-read the current local
`draft_content.json` and `draft_meta_info.json`; treat those as the latest
technical state after user edits.

When the user says they exported the video through CapCut, mark:

```text
status: REPORT2_CLOSED_BY_USER_EXPORT
보고서2 종료: 예
```

Even after export, keep `업로드 준비 완료: 아니오` unless the user explicitly
approves upload and rights/risk handling. 명시 승인 전 아니오.

## Stage Scope Gate

For `URL + Gemini/source analysis` intake, do not treat the URL, Gemini text,
or a generic `진행/해줘` as stage-2 permission by itself. Before source download,
TTS, SRT/layout, CapCut, render, or upload work, the coordinator must identify
one of these scopes:

```text
stage_1_script = 00-tikitaka only; produce 상단 + timed 중단 + 중단 TTS 글자만 복사 + 설계도; then WAIT
stage_2_full = source verification + TTS/user audio + SRT/layout + CapCut project + 보고서2
```

If the user says `대본까지`, `대본만`, `초벌`, `티키타카`, `초안만`, `검토용`,
or `스크립트만`, stop before stage 2 with `WAIT_USER_STAGE_DECISION`.

Stage 2 intent is selected only with one of:

- `user_stage_decision=stage_2_full`
- explicit stage-2 wording such as `끝까지`, `자동으로 다`, `최종`, `다음단계`,
  `업로드까지`, `슈퍼톤`, `슈퍼톤으로`, `supertone`, `TTS 만들어`,
  `tts 만들`, `TTS 생성`, `tts 생성`, `TTS mp3`, `tts mp3`,
  `캣컵프로젝트파일까지`, `캣컵 프로젝트 파일까지`,
  `캐컷프로젝트파일까지`, or `capcut project`
- user-provided or explicitly authorized TTS/SRT/audio path

`자동모드` is explicit stage-2 wording: user says 자동모드 = stage_2_full.

`AUTO_FULL_CAPCUT_PROJECT selects the target`; it does not waive report1 approval
or the voice/audio route decision. It is a destination/mode choice, not a gate
bypass.

Stage 2 work and 보고서2 still require both:

```text
report1_approved=true
voice_audio_route_decided=true
```

If the user already asked for stage 2 before seeing the script, treat that as
future intent only. After 설계도, ask for design OK and TTS/오디오 route before
CapCut creation.

Mandatory report/checklist gates:

```text
G0 INTAKE = ask "어디까지 만들까?" unless stage_1_script or stage_2_full is already explicit
G1 STAGE 1 = 1차설계서 + timeline_design.json + caption_beat_map.json + timeline_design_gate.json + humanize_korean_gate.json + block_map.json + block_role_map.json + block_voice_switch_map.json + tts_copy_text.txt + script_handoff_gate.json + report1_handoff.json
G2 STAGE 1 STOP = 설계도 and WAIT_REPORT1_APPROVAL_TTS_DECISION until report1_approved + voice_audio_route_decided
G3 STAGE 2 ENTRY = stage_2_full intent + report1_approved + voice_audio_route_decided
G4 FINAL = [FINAL_LOCK 최종 보고] only after production, visual, media-settings, cleanup, and harness gates pass
```

The Tikitaka harness must emit `stage_gate_todo.md` and
`stage_scope_report.md`. Production must not treat a missing checklist/report as
permission to skip reporting.

RE-ENTRY:

```text
REWORK_IN_NEW_CHAT_ANALYZE_FIRST
MIDDLE_PACKAGE_REWORK_REVIEW_GATE
REPORT_BEFORE_ACTION
```

When the user brings an existing package or asks in a new chat to rework a
CapCut project/package, analyze the files and report the resume point before
editing: `draft_content.json` plus `script_handoff_gate.json` PASS plus
`block_map.json` means CapCut rework, `draft_content.json` alone means
`WAIT_SCRIPT_HANDOFF_GATE` and `stage_1_repair`, `script_handoff_gate.json`
FAIL or invalid means `WAIT_SCRIPT_HANDOFF_GATE_REPAIR` and `stage_1_repair`,
`script_handoff_gate.json` PASS means stage-2 resume after user decision, and
neither means restart at G0.

The validator enforces this through `project_file_request_mode()`. Do not work
around it by writing `project_file_request_mode=AUTO_FULL_CAPCUT_PROJECT` into a
contract unless the user-stage evidence, 설계도 approval, and voice/audio route
decision above exist.

## Production Mode Selection

When the user provides a Shorts URL plus Gemini/source analysis and explicitly
opens stage 2, route as:

```text
URL_PLUS_GEMINI_PLUS_PROJECT_FILE
PROJECT_FILE_REQUEST_MODE=AUTO_FULL_CAPCUT_PROJECT
```

In `AUTO_FULL_CAPCUT_PROJECT`, build toward the best possible complete local
CapCut project file / perfect local CapCut project file and run the source, script, SRT/layout, CapCut,
visual/template, media-settings, cleanup, and report gates.
Do not default URL+Gemini intake to AUTO_FULL or DRAFT_FAST without the Stage
Scope Gate evidence above.

Use `INTERACTIVE_SCRIPT_APPROVAL` when the user asks to choose or approve the
urakkai/script/template direction before production. In that mode, stop at the
named script checkpoints and ask before continuing.

Use `DRAFT_FAST_EXPLICIT_ONLY` only when the user explicitly says `DRAFT_FAST`,
`빠른 초안`, `기술 초안`, `검토용 draft만`, or `검토용 드래프트만`.
Plain `초안만` belongs to `stage_1_script`; it is not fast
CapCut permission unless the user also says draft/CapCut. DRAFT_FAST is allowed
only when the user explicitly says a fast draft is the goal. DRAFT_FAST does not
waive `report1_approved + voice_audio_route_decided`; it is still a CapCut
draft stage and must wait behind `WAIT_REPORT1_APPROVAL_TTS_DECISION`.

## Template Base Rule

`TEMPLATE_REFERENCE_RESOLUTION_GATE` is mandatory before any template-backed
CapCut draft/project build or repair.

For the current 11short default lane, `TEMPLATE_REFERENCE_RESOLUTION_GATE` starts
from the Default CapCut Mother Template Rule above: no explicit non-default
template from the user means `shrt white`, not an old derived project.

Required evidence fields:

```text
reference_project_name
reference_project_path
template_profile
```

A user-visible CapCut reference project beats generic defaults, but a prior
episode/project is not automatically the root template. Before building, resolve
the actual root/mother CapCut template for that style. Do not chain derivatives
as `1 -> 2 -> 3 -> 4`.

For character-comments / game-character-comments work,
`260707-Fk5D_FboO6M-game-character-comments-CAPCUT_v1` is a prior derived
project / style sample only. It must not be reported or enforced as the root
template authority unless the user explicitly proves that it is the original
mother template. If the root template cannot be identified, stop with
`FAIL_TEMPLATE_ROOT_NOT_RESOLVED` before cloning or building.

`template_profile is not satisfied by `neutral_base_template` text alone`.
`neutral_base_template` is only a fallback label after no user-visible reference
project exists or after the user explicitly waives the visible reference. Do not
create a helper-only fresh draft, do not generate a synthetic
`source + audio + text` CapCut draft, and do not use a helper script output as
the style basis until `reference_project_name` and `reference_project_path` have
been resolved.

Failure states:

```text
FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED
FAIL_TEMPLATE_REFERENCE_MISMATCH
```

Use `FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED` when the reference project name/path
is missing, inaccessible, or not opened/located before build. Use
`FAIL_TEMPLATE_ROOT_NOT_RESOLVED` when a named reference is only a prior derived
project and the true root/mother template is unknown. Use
`FAIL_TEMPLATE_REFERENCE_MISMATCH` when the produced draft was not cloned or
derived from the resolved root/reference. In every CapCut report, manifest, and
validation result, report both the root template and any style/sample project
used.

If a current builder temporarily copies an episode-specific project such as china-driver,
treat that project as a structure seed only, not story/content authority. The
`SCRIPT_LOCK_PACKAGE remains the Source of Truth` for text, edit order, caption
roles, audio policy, and source ranges.

Do not let a template project's old title, script, BGM decision, source-audio
decision, or failed episode status leak into a new draft. Report any
episode-specific seed as temporary and replace with a neutral base template only
when no user-visible reference project exists or the user explicitly approves
that fallback.

## Active Root

For new 22utube Shorts production, read:

```text
${env:WORKSPACE_ROOT}\22factory_20260628\AGENTS.md
```

Treat `${env:WORKSPACE_ROOT}` as a portable placeholder. Resolve the active
factory root from the opened workspace or OneDrive location and verify both
`AGENTS.md` and `docs/YOUTUBE_PRODUCTION_WORK_ORDER.md` exist before production.
If the root cannot be resolved, stop with `WAIT_FACTORY_ROOT_NOT_RESOLVED`.

Create new Shorts episode outputs under:

```text
22factory_20260628\01_shorts_factory\episodes\SH_YYYYMMDD_slug
```

Store CapCut metadata, manifests, snapshots, reports, and upload/final packages
in OneDrive. The editable CapCut draft itself stays in the local CapCut project
directory on the machine that builds it.

Legacy `11utube/11short/000short-production-agent/episodes` folders are
reference or explicit repair targets unless the user asks for legacy work.

## Production Inputs

Before generating or repairing production assets, identify the current authority:

- `source.mp4` or equivalent source file
- source provenance and usable-file check
- source-evidence/watch/direct-frame findings when the video content matters
- `10_analysis/source_identity_lock.json` with `status=PASS`, canonical URL,
  video id, actual local source path, SHA256, and duration. Missing or mismatched
  lock is `WAIT_SOURCE_IDENTITY_LOCK`.
- `10_analysis/source_evidence.json` and
  `10_analysis/crosscheck_report.json` with `status=PASS`, the same video id,
  and the same source SHA256. Missing or mismatched evidence is
  `WAIT_SOURCE_EVIDENCE_REQUIRED`.
- `10_analysis/tikitaka_source_request.json` written by `00-tikitaka` from its
  Shorts intake URL. Its URL/video id must match the source identity lock or
  stop at `WAIT_SOURCE_REQUEST_BINDING`.
- Do an actual ffprobe of the local media in Stage 2 validation; copied
  `ffprobe_status=PASS` text is not evidence. Invalid/non-video media is
  `WAIT_SOURCE_MEDIA_FFPROBE`.
- script authority, usually `final_script_ko.txt` or the current Tikitaka draft
- Tikitaka `SCRIPT_LOCK_PACKAGE` when the script came from `00-tikitaka`; this
  package is the Source of Truth for `CAPCUT_OPENABLE_PROJECT`.
- Current Tikitaka v3 `timeline_design.json` when the script came from `00-tikitaka`;
  this is the machine-readable Stage 2 source of truth and `capcut_layout_plan`
  must be derived from it.
- Tikitaka `timeline_design_gate.json` and `humanize_korean_gate.json`; both
  must be PASS before SRT/layout/CapCut work.
- Tikitaka segment audio plan when the script came from `00-tikitaka`
  (`tikitaka_segment_audio_plan` or equivalent `구간 오디오 정책표`)
- Tikitaka `SCRIPT_HANDOFF_GATE` when the script came from `00-tikitaka`:
  `20_script/script_handoff_gate.json` must exist, be generated by the handoff
  validator, and have `status=PASS`.
- canonical `20_script/block_map.json` with `edit_block_sequence`,
  `block_voice_switch_map`, `original_order`, `urakkai_order`,
  `source_block_id`, and `edit_id`.
- canonical `20_script/block_role_map.json` and
  `20_script/block_voice_switch_map.json`.
- `20_script/tts_copy_text.txt` when any `caption_type=tts_narration` exists.
- `20_script/caption_beat_map.json` for every timed middle-caption row.
- humanized final Korean text when visible text is final
- `story_type`, `production_type`, and `template_profile` when the project is
  template-backed or when the user asks for a final CapCut project file
- target template/layout
- requested voice/audio policy, if any
- requested BGM/SFX asset, if any. BGM is optional unless the user explicitly
  chooses or requires it.

Missing `source.mp4` is a hard stop for source-derived production. Do not proceed
to source evidence, verified analysis, SRT/layout, CapCut, export, upload, or
final validation without source acquisition and provenance.

Stage 2 validators must parse `block_map.json`, `block_role_map.json`, and
`block_voice_switch_map.json` and require exact `edit_id` coverage against
`timeline_design.json`; mismatch is `WAIT_HANDOFF_MAP_COHERENCE`. Approval and
voice-route booleans must exist in `report1_handoff.json` itself; an external
contract/status file cannot supply missing approval.

`report1_handoff.json`, `script_handoff_gate.json`, and
`timeline_design.json` must all carry the exact source media SHA256 as
`source_fingerprint_sha256`. Any omission or mismatch is
`WAIT_SOURCE_HANDOFF_FINGERPRINT`.

Before `CAPCUT_OPENABLE_PROJECT`, run the active media-link validator and prove
that the real source path is present in active draft materials. Empty or
source-unlinked materials are `WAIT_CAPCUT_SOURCE_MEDIA_LINK`. Before production
PASS, the actual source media must be included in declared SHA256 inputs;
otherwise stop with `SOURCE_MEDIA_HASH_REQUIRED`.

If the script came from Tikitaka and timed `중단` blocks exist, missing segment
audio policy is a hard stop:

```text
WAIT_TIKITAKA_SEGMENT_AUDIO_PLAN
```

If the script came from Tikitaka and the handoff gate or canonical block map is
missing or failed, stop before SRT, TTS, layout, asset prep, or CapCut work:

```text
WAIT_SCRIPT_HANDOFF_GATE
required:
- script_handoff_gate.json
- timeline_design.json
- timeline_design_gate.json
- humanize_korean_gate.json
- block_map.json
- block_role_map.json
- edit_block_sequence
- block_voice_switch_map
- tts_copy_text.txt when tts_narration exists
```

Do not infer quote/TTS/source-audio policy inside production. Use the Tikitaka
plan as the authority:

- `caption_type=speaker_quote` or visible `"..."` => source audio must be audible
- `caption_type=tts_narration` => source audio must be muted unless
  `caption_type=tts_plus_source` explicitly allows ducking
- `caption_type=situation_caption` => source audio muted by default
- `caption_type=ranking_item` => source audio muted by default, except verified
  quote/reaction beats
- `source_order` and `timeline_order` must be preserved when the script remixes
  source order
- `bgm_policy=optional` or `optional_duck` never requires a BGM track. Treat BGM
  as mandatory only when the plan says `bgm_policy=on` or `duck`, or when the
  user named a specific BGM/SFX asset.

## Audio Assembly Contract

Narration is never trimmed to fit a shorter visual slot. When a TTS narration
file is longer than the scripted or SRT slot, preserve the full audio duration
and extend the visual beat, shift later source-audio/body segments, add usable
source duration, or use an approved hold/freeze/repeat strategy. Do not solve a
duration mismatch by cutting the narration.

For Tikitaka remixes such as `source 1-2-3-4-5 -> timeline 4-3-1-5-2`, build
audio as separate lanes, not as one mixed source clip:

```text
shrt white canonical audio mapping:
audio.narration_tts  -> A9
audio.speaker_source -> A10
audio.sfx            -> A11
audio.bgm            -> A12
source video track: video visible, source-video audio muted by default
```

The source video's embedded audio may remain present in the file, but it must
not be the active uncontrolled audio carrier. Extract or reference source audio
as its own CapCut audio material, then enable, mute, or duck only the segments
authorized by `tikitaka_segment_audio_plan`.

Tikitaka `block_voice_switch_map` is the lane authority. Build and validate
these lanes by `edit_block_sequence`, not by original source order:

```text
V1 source video      = source video visual only; embedded source audio muted
A9 narration/TTS    = generated narration; full duration preserved
A10 speaker/source  = extracted original/source speech; quote ranges only
A11 SFX             = optional; must not cover speech
A12 BGM             = optional; duck under speech and TTS
```

Required switch mapping:

```text
speaker_quote:
- audio.speaker_source ON -> A10
- audio.narration_tts OFF -> A9 off

tts_narration:
- audio.narration_tts ON -> A9
- audio.speaker_source OFF -> A10 off

situation_caption:
- A9 OFF
- A10 OFF
- unless explicit exception_reason exists

tts_plus_source:
- A9 ON
- A10 duck/on according to locked audio_policy

source_audio=on/off/duck
tts=on/off
edit_order implemented
```

If `situation_caption` needs source ambience or TTS, the block must carry an
explicit exception reason from the handoff. Otherwise keep both speech lanes
off for that caption role.

For every audio-backed report, include:

```text
narration_not_trimmed
source_audio_separated
source_video_muted
audio_loudness_normalize target -14 LUFS
```

## Supertone TTS / Voice Generation

When the user explicitly asks for TTS, voice generation, narration audio, or
voice files for a YouTube/Shorts production, use the local Supertone route
before considering any other provider.

Default local command on Windows:

```powershell
py -3.14 "${env:WORKSPACE_ROOT}\22factory_20260628\00_asset_tools\tools\make_supertone_tts.py" "<대본 텍스트>" "<출력파일.wav>"
```

Required behavior:

- Read configuration only from environment variables:
  `SUPERTONE_API_KEY`, `SUPERTONE_VOICE_ID`, `SUPERTONE_PITCH`,
  `SUPERTONE_SPEED`, `SUPERTONE_MODEL`.
- Never paste, print, write, serialize, or report the API key. Do not put it in
  Git, OneDrive production files, CapCut JSON, manifests, logs, reports, or
  chat.
- On `home_windows`, User-scope Supertone variables may be registered even when
  the current Codex process environment is stale. The shared script reads the
  Windows User environment as a fallback.
- If a stale process `SUPERTONE_API_KEY` is present and invalid, it overrides the
  Windows User fallback. For that command, clear/unset the process variable so
  the script can read the valid HKCU User value. Never print the key while
  diagnosing this.
- Use `py -3.14` because the installed Supertone SDK is on that interpreter; do
  not rely on bare `python` unless you have verified `import supertone` there.
- The default voice/model are controlled by env vars. Current home_windows
  setup uses Chunsik through `SUPERTONE_VOICE_ID` and `sona_speech_1`.
- If env variables or SDK are missing, stop with
  `WAIT_SUPERTONE_ENV_OR_SDK_MISSING`; do not switch to Edge TTS, ElevenLabs,
  browser TTS, Kokoro, or any fallback provider without explicit user approval.
- Record generated audio path, duration, voice id label, model, pitch, and
  speed in the production manifest, but never record the API key.

For TTS-capable story, narration, 사연, 미담, photo-explainer, 군림보-style, or
썰풀이 Shorts, script authority must show the TTS storytelling gate was handled.
Before SRT/layout/CapCut work, confirm which truth mode the script owner chose:

- `fact_first`: information, knowledge, news, politics, medical, legal, safety,
  accident, crime, finance, or source-sensitive factual explainers. Require
  source-supported claims and do not accept unverifiable hook premises as fact.
- `hook_first_writer_premise`: 감동형 narration, TTS-only, BGM-heavy, family,
  reunion, cute/moment, photo-explainer, or ordinary emotional story Shorts.
  If the user says `후킹 쎄게`, `작가모드`, `우라까이`, or directly tells the agent
  to make the hook stronger, production must accept a strong writer premise
  from the script authority even when it is not source-verifiable. Do not block
  it just because it is not evidence-backed; block only high-risk or materially
  harmful invented claims.

For `fact_first`, confirm the script has source-supported fields. For
`hook_first_writer_premise`, confirm the script has a strong emotional hook or
equivalent fields such as:

- `tts_story_mode_required`
- `truth_mode`
- `source_supported_emotional_condition`
- `writer_premise_for_hook`
- `writer_premise_status`
- `emotional_entry_line`
- `changed_scene_entry_order`
- `changed_korean_expression_strategy`
- `viewer_emotion_target`
- `payoff_recovery_line`

If this is missing or the draft opens as a flat event summary, stop at
`WAIT_SCRIPT_REWRITE_REQUIRED` and route back to `00-tikitaka`. Do not rewrite
the story inside production. Do not reject an
ordinary emotional/TTS script solely because the hook premise is plausible,
fictionalized, or not source-verifiable.

## Owned Outputs

This skill may create, validate, or repair:

- SRT/subtitle files
- caption/layout JSON
- render plans
- explicitly requested voice/audio files for production use
- CapCut draft folders and draft JSON
- production manifests
- export packages
- upload packages
- reports and validation logs

This skill does not originate Tikitaka creative structure when no script authority
exists. Ask for or route to the script owner first.

## Standard Sequence

1. Confirm active root and episode folder.
2. Select production mode: `AUTO_FULL_CAPCUT_PROJECT`,
   `INTERACTIVE_SCRIPT_APPROVAL`, `DRAFT_FAST_EXPLICIT_ONLY`, or `FINAL_LOCK`.
3. Confirm source file and provenance.
4. Confirm script authority and visible-text cleanup status.
5. Confirm `tikitaka_segment_audio_plan` / `구간 오디오 정책표` when the script came from Tikitaka.
6. Validate `SCRIPT_HANDOFF_GATE` and canonical `block_map.json` first when the
   script came from Tikitaka; stop at `WAIT_SCRIPT_HANDOFF_GATE` if the gate is
   missing or failed.
7. For template-backed CapCut work, resolve `TEMPLATE_REFERENCE_RESOLUTION_GATE`
   before any draft generation. Stop with `FAIL_TEMPLATE_REFERENCE_NOT_RESOLVED`
   when `reference_project_name` or `reference_project_path` is missing, and
   stop with `FAIL_TEMPLATE_REFERENCE_MISMATCH` if the new draft is not derived
   from the resolved reference.
8. Build or repair SRT/layout/render-plan assets from that segment audio plan.
9. Build or repair the local CapCut draft/project by `edit_block_sequence`.
10. If reference sameness is requested or required, run the bounded similarity
   loop from `08_SIMILARITY_LOOP_CONTRACT.md`; patch only failed dimensions.
11. For template-backed drafts/projects, apply
   `DRAFT_FAST_REFERENCE_SIMILARITY_REQUIRED` from
   `07_DRAFT_FAST_REPORT_CONTRACT.md`: `template_profile_match`,
   `middle_caption_format_match`, `caption_layer_role_match`,
   `caption_position_match`, `reference_visual_preview_match`,
   `reference_frame_similarity`, `source_caption_overlap_check`,
   `capcut_processing_idle_check`, and `active_draft_cleanup_gate` must pass
   before reporting visual/template readiness.
   `SIMILARITY_LOOP_PASS is not DRAFT_FAST_PASS`.
12. For a `final_capcut_project_file`, verify the
   `shorts_type_template_matrix` (`story_type`, `production_type`,
   `template_profile`) before any visual/template claim.
13. Snapshot CapCut draft JSON into the episode metadata folder.
14. Run the required harness or validator for the current stage, including
    `CAPCUT_EDIT_READY_GATE` when the target is a CapCut edit-ready draft.
15. Report `PASS/FAIL/WAIT` with evidence paths and one concrete next blocker.

## Mandatory CapCut Media Settings — HARNESS LOCK

This is a **HARNESS_LOCK** production gate. It is not an optional style checklist and not something to remember verbally. The coordinator must require the harness/validator result before claiming any CapCut draft/project/profile is production-ready.

Every source video segment must carry the Git manifest media settings from `manifests/capcut-template-set.json` and pass `scripts/validate_capcut_timeline_order.py`:

- 품질보정 / QualityEnhance: `HD`
- 사운드 노멀라이즈: enabled, target loudness `-14 LUFS`
- 자동조정 / smart_color_adjust: `30~50`
- 선명하게 / clear: `30~50`
- 선명도 / sharpen: `30~50`
- 입자 / particle: `5~30`
- 인접 source segment는 자동조정/선명하게/선명도 값이 최소 `5` 이상 차이 나야 함

Required validator evidence:

```text
mandatory_capcut_media_settings_status: PASS
```

If any of these are missing, out of range, or not checked by the validator, the state is:

```text
FINAL: BLOCKED
reason: MANDATORY_CAPCUT_MEDIA_SETTINGS_NOT_HARNESS_VERIFIED
```

Coordinator rule: whenever the operator asks about CapCut video/sound settings, CapCut readiness, draft quality, or finalization, answer with this harness-locked media gate first. Do not answer only with export settings such as 9:16/1080p/30fps.

## CapCut Rules

For any CapCut draft/project/profile creation, modification, repair, patch, or
validation response, the final answer must end with a `캣컵복사하기` Markdown
block containing only the CapCut project name. Put paths and reports in the main
body, never inside that block.

## Validation Rules

Use validators and harness scripts that already exist in this skill before
claiming a stage is complete.

If a validator fails, stop at that stage, report the failing item, fix it if the
request allows, and re-run validation. Do not continue downstream on a failed
stage.

Do not confuse:

- working draft created
- harness pass
- production gate pass
- upload ready
- `TECHNICAL_DRAFT_CHECK` with `VISUAL_TEMPLATE_CHECK`
- `LOCAL_JSON_CHECK_PASS` or `MEDIA_LINK_CHECK_PASS` with CapCut quality
- runtime sync or hash match with visual correctness
- `DRAFT_FAST` with `FINAL_LOCK`

Each state needs its own evidence.

## Reference Routing

- For CapCut text effect presets, read
  `references/capcut_text_effect_presets.md`.
- For Shorts craft constraints after an explicit production request and script
  authority, read `references/shorts-academy.md`.
- For the old Tikitaka production-script contract, read
  `references/tikitaka-script-v17.md` only for legacy repair. It is not current
  Tikitaka script authority.
- For work-order, pipeline, layout, harness, cut-assembly, DRAFT_FAST /
  FINAL_LOCK report-contract, and reference-similarity loop details, read the
  numbered root docs in this skill folder, including
  `07_DRAFT_FAST_REPORT_CONTRACT.md` and
  `08_SIMILARITY_LOOP_CONTRACT.md`.
- For old full-contract details or legacy repair only, read
  `references/archived-full-skill-20260629.md`.

Keep this `SKILL.md` as the active production router. Do not re-add broad
Tikitaka, 우라까이, channel-family, hook, or analysis triggers to the description.

## Integrated Blueprint and Upload Contract

Do not create a separate human-facing assembly report. Read and preserve
`20_script/design_blueprint.md`, then append `## 조립도` after the Stage 1
design sections. The assembly section must include `프로젝트 실체`,
`설계도 반영 결과` table, `실제 CapCut 트랙 구성` table, `TTS 실제 길이 대조`
table, `검증 결과`, and `남은 사람 작업`.

The Stage 1 design portion must also contain `## 자막 레이아웃 기준` with
`caption_beat_map.json` and the fixed TTS/speaker/situation profile values.
The `## 조립도` section must begin with these fixed 보고서2 fields:

```text
보고서2 시작: 예
최종보고서: 예
상태: CAPCUT_EDIT_READY|REPORT2_REVISED|REPORT2_CLOSED_BY_USER_EXPORT
CapCut 프로젝트명: <name>
CapCut 열어보기 필요: 예
사용자 확인 대기: 예
업로드 준비 완료: 아니오
최종 잠금: 아니오
```

After assembly, append `## 업로드 패키지` as the final H2 section. It must
contain non-empty `제목`, `상세설명`, `출처`, `해시태그`, and
`추천 업로드채널` fields. Missing sections or a different final section are
hard failures: `FAIL_DESIGN_BLUEPRINT`, `FAIL_ASSEMBLY_BLUEPRINT`, or
`FAIL_UPLOAD_PACKAGE`. Run `scripts/validate_integrated_blueprint.py` in
`production` phase before reporting `CAPCUT_EDIT_READY`.
