---
name: 001short-production-agent
description: Use for original-shorts production, a source intake from Google Drive, URL, or Desktop, or when a new-session 001 conversation handoff JSON must safely resume the same lane.
---

# 001short Compact Production

## Load order

1. Read [production-orchestrator.md](references/production-orchestrator.md) first.
2. Read `workflow.json`, episode state, and `protocol.json`; select one internal stage from the orchestrator's state/lock table.
3. Load exactly one current stage MD: [original-capcut-grid.md](templates/original-capcut-grid.md), [final-blueprint.md](steps/05-final-blueprint.md), or [capcut-assembly.md](steps/08-capcut-assembly.md).
4. Load only the direct supporting references linked by that stage MD. Do not load a second stage MD or replace a stage authority with a legacy document.

## Minimal executable protocol

- `protocol.json` is the machine contract and `workflow.json` owns state transitions. Stop with `STOP_PROTOCOL_CONFLICT` on conflict.
- Start locally from the `0000shrt` episode root. Keep one active writer and never mutate an active CapCut draft while CapCut or its background processes are open.
- Validate a source intake receipt with `scripts/validate_source_intake.py --receipt <path>` before Stage 01. Static validation does not authorize Drive, browser, CapCut, cloud, render, or upload actions.
- Validate an approved Stage 05 production plan with `scripts/validate_executable_protocol.py --plan <path>` before a build. Static validation does not establish a user visual approval.
- For approved generated narration plus retained source speech, use `A9_TTS_PLUS_A10_RETAINED`; A10 rows must be boundary-aligned with A9, and partial overlap fails with `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`.
- Treat every `WAIT_*` and `FAIL_*` in the selected stage MD as a hard stop. Do not use conversational memory as evidence.

## New Session Handoff Bootstrap

Validate `templates/conversation-handoff.json` against `schemas/conversation_handoff.schema.json` with `scripts/validate_conversation_handoff.py --handoff <path>` before work. Load `$HOME/.hermes/.env` once without output. Resume an old episode only when `resume_requested=true`, its episode ID, and current artifact readback all agree. Tokens, cookies, API keys, passwords, OAuth values, and session/conversation IDs are `HANDOFF_SECRET_MATERIAL_FORBIDDEN`.

## Compatibility

Existing legacy references, templates, schemas, and scripts remain available only through the orchestrator or a current-stage direct link. Do not delete them, copy their prose into this router, or let them compete with the selected stage authority.
