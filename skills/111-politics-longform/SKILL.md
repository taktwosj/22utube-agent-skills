---
name: 111-politics-longform
description: Use when the user says 111정치롱폼, 정치롱폼, 정치미드폼, 민주진영 유튜브, 매불쇼 롱폼, 유시민 롱폼, or asks to design, review, assemble, validate, or package a Korean political longform video, lower two-line commentary, 1-3 derived political Shorts, 45-70 second source candidates, jungchilong CapCut project, upload copy, API upload, or thumbnail hooks.
---

# 111 Politics Longform — Thin Gate Router

This lane owns politics-longform and its derived Shorts end-to-end. Derived Shorts remain in this lane and use `SHRTJUNGCHI`; cross-lane handoff is forbidden.

For `politics_longform_derived`, require `20_script/shorts/SHxx/edit_plan_approved.json` and `20_script/design_lock_manifest.json`; otherwise stop with `WAIT_SHRTJUNGCHI_ROOT_REQUIRED`.

## Ownership and prohibitions

```text
Owned gates: G00, G10, G20, G30, G40, G50, G60, G60.USER, G70, G80, G90
Profiles: politics_longform, politics_derived_short
Forbidden: cross-lane handoff, automatic external LLM calls, automatic CapCut GUI operations, automatic upload, automatic retry.
```

## Gate router

Read `workflow.yaml` first. Resolve the active gate and load only its matching reference:

| Gate | Current-gate reference | Validator |
|---|---|---|
| G00 | `references/gates/G00_INTAKE.md` | `scripts/validate_stage_gate.py` |
| G10 | `references/gates/G10_DESIGN.md` | `scripts/validate_stage_gate.py` |
| G20 | `references/gates/G20_MANUAL_DIALOGUE_TWO_PASS.md` | `scripts/validate_stage_gate.py` |
| G30 | `references/gates/G30_AUDIO.md` | `scripts/validate_stage_gate.py` |
| G40 | `references/gates/G40_CAPTION_SRT.md` | `scripts/validate_stage_gate.py` |
| G50 | `references/gates/G50_TRACK_PLAN.md` | `scripts/validate_stage_gate.py` |
| G60 / G60.USER | `references/gates/G60_CLEAN_ASSEMBLY.md` | `scripts/validate_stage_gate.py` |
| G70 | `references/gates/G70_UPLOAD_PACKAGE.md` | `scripts/validate_stage_gate.py` |
| G80 | `references/gates/G80_RENDER.md` | `scripts/validate_stage_gate.py` |
| G90 | `references/gates/G90_FINAL_QC.md` | `scripts/validate_stage_gate.py` |

Load exactly one current-gate reference after the active gate is known. Do not load future-gate references. Do not reload previous-gate instructions. Do not cross-load another lane's references. Do not inject a full SRT by default. Detailed procedures, schemas, artifacts, and validator rules stay in the matching gate reference and `workflow.yaml`.

`references/legacy_contracts.md` preserves P01–P09 detail for compatibility review only; never load it as default gate context.

## Authority and hard stops

External review transport is USER manual only and recommendation-only. `PASS` is deterministic-validator only. Static G60 success waits for `WAIT_USER_VISUAL_GATE`; G70 keeps release false; upload remains `WAIT_UPLOAD_APPROVAL` until user approval.

Hard-stop on: `WAIT_USER_INPUT`, `WAIT_EXTERNAL_RETURN`, `WAIT_USER_EDITORIAL_CONFIRMATION`, `PENDING_EVIDENCE`, `WAIT_SHRTJUNGCHI_ROOT_REQUIRED`, `WAIT_USER_VISUAL_GATE`, `WAIT_UPLOAD_APPROVAL`, unknown cost, or unapproved paid action.

## Status format

```text
{gate}: {NOT_STARTED|READY|RUNNING|WAIT_USER_INPUT|WAIT_EXTERNAL_RETURN|WAIT_USER_EDITORIAL_CONFIRMATION|WAIT_USER_VISUAL_GATE|WAIT_UPLOAD_APPROVAL|PASS|FAIL|REWORK_REQUIRED|INVALIDATED|NOT_REQUIRED}
```
