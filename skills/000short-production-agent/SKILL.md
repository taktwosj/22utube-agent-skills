---
name: 000short-production-agent
description: Use only when the user explicitly asks to create, validate, or repair production assets, subtitles, layout JSON, CapCut drafts, render packages, export packages, upload packages, or production packages. Do not use for script creation, urakkai decisions, hook/channel planning, or draft-only polishing.
---

# 000short Production — Thin Gate Router

This lane owns general-Shorts production after the canonical Tikitaka handoff. It must not rewrite the locked hook, urakkai order, caption role, or production profile; creative repair returns to Tikitaka G20.

## Ownership and prohibitions

```text
Owned gates: G30, G40, G50, G60, G60.USER, G70, G80, G90
Does not own: G00, G10, G20
Forbidden: script/original hook/urakkai creation, automatic external LLM calls, automatic CapCut GUI operations, automatic upload, automatic retry.
CapCut root: shrt white
```

## Gate router

Read `workflow.yaml` first. Resolve the active gate and load only its matching reference:

| Gate | Current-gate reference | Validator |
|---|---|---|
| G30 | `references/gates/G30_AUDIO.md` | `scripts/validate_stage_gate.py` |
| G40 | `references/gates/G40_CAPTION_SRT.md` | `scripts/validate_stage_gate.py` |
| G50 | `references/gates/G50_TRACK_PLAN.md` | `scripts/validate_stage_gate.py` |
| G60 / G60.USER | `references/gates/G60_CAPCUT_ASSEMBLY.md` | `scripts/validate_stage_gate.py` |
| G70 | `references/gates/G70_UPLOAD_PACKAGE.md` | `scripts/validate_stage_gate.py` |
| G80 | `references/gates/G80_RENDER.md` | `scripts/validate_stage_gate.py` |
| G90 | `references/gates/G90_FINAL_QC.md` | `scripts/validate_stage_gate.py` |

Load exactly one current-gate reference after the active gate is known. Do not load future-gate references. Do not reload previous-gate instructions. Do not cross-load another lane's references. Do not inject a full SRT by default. Detailed procedures, schemas, artifacts, and validator rules stay in the matching gate reference and `workflow.yaml`.

`references/legacy_contracts.md` preserves P01–P09 detail for compatibility review only; never load it as default gate context.

## Authority and hard stops

`PASS` is deterministic-validator only. Static G60 success waits for `WAIT_USER_VISUAL_GATE`; G70 keeps `release_allowed=false`; upload remains `WAIT_UPLOAD_APPROVAL` until user approval.

Hard-stop on: `WAIT_TIKITAKA_DESIGN_REPAIR`, `WAIT_USER_VISUAL_GATE`, `WAIT_UPLOAD_APPROVAL`, `PENDING_EVIDENCE`, `STOP_SOURCE_OF_TRUTH_CONFLICT`, unknown cost, or unapproved paid action.

## Status format

```text
{gate}: {NOT_STARTED|READY|RUNNING|WAIT_USER_VISUAL_GATE|WAIT_UPLOAD_APPROVAL|PASS|FAIL|REWORK_REQUIRED|INVALIDATED|NOT_REQUIRED}
```
