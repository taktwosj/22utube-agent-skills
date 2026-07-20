---
name: 00-tikitaka
description: Use only when the user explicitly asks for Tikitaka Korean Shorts source analysis, remake scripting, 티키타카 하자, 우라까이, hook candidates, 상단/timed 중단 draft creation, Gemini raw intake for Shorts URLs, or Gemini Shorts source notes. Do not use for SRT, CapCut, production packages, or polishing-only existing scripts.
---

# 00 Tikitaka — Thin Gate Router

This lane owns source analysis, urakkai, hook, timeline design, and manual external-review adjudication.

## Ownership and prohibitions

```text
Owned gates: G00, G10, G20
Does not own: G30–G90 (000short-production-agent)
Forbidden outputs: TTS audio generation, final SRT, CapCut assembly, render, upload package, browser automation, automatic external LLM calls, auto retry.
```

## Gate router

Read `workflow.yaml` first. Resolve the active gate there, then load its single matching reference:

| Gate | Current-gate reference | Validator |
|---|---|---|
| G00 | `references/gates/G00_INTAKE.md` | `scripts/validate_stage_gate.py` |
| G10 | `references/gates/G10_DESIGN.md` | `scripts/validate_stage_gate.py` |
| G20 | `references/gates/G20_MANUAL_EXTERNAL_REVIEW.md` | `scripts/validate_stage_gate.py` |

Load exactly one current-gate reference after the active gate is known. Do not load future-gate references. Do not reload previous-gate instructions. Do not cross-load another lane's references. Do not inject a full SRT by default. Detailed procedures, schemas, artifacts, and validator rules stay in the matching gate reference and `workflow.yaml`.

`references/legacy_contracts.md` preserves P01–P09 detail for compatibility review only; never load it as default gate context.

## Authority and hard stops

External review transport is USER manual only; external output is recommendation only. `PASS` is emitted only by the deterministic validator.

Hard-stop on: `WAIT_USER_INPUT`, `WAIT_EXTERNAL_RETURN`, `WAIT_USER_EDITORIAL_CONFIRMATION`, `EXTERNAL_ANALYSIS_MISMATCH`, `EXTERNAL_AUTHORITY_OVERREACH`, `SAME_CONVERSATION_REQUIRED`, `PENDING_EVIDENCE`, `HUMAN_MD_CANONICAL_JSON_MISMATCH`, or `STOP_SOURCE_OF_TRUTH_CONFLICT`.

## Status format

```text
{gate}: {NOT_STARTED|READY|RUNNING|WAIT_USER_INPUT|WAIT_EXTERNAL_RETURN|WAIT_USER_EDITORIAL_CONFIRMATION|PASS|FAIL|REWORK_REQUIRED|INVALIDATED|NOT_REQUIRED}
```
