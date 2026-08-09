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

## Lane Isolation

This is the independent `owner_skill=001short-production-agent`, `lane=general_shorts_production` lane. 요청을 시작할 때 하나의 lane만 확정한다. Do not load or combine `top5isu-shorts` or another production skill while it is active.

## Minimal executable protocol

- `protocol.json` is the machine contract and `workflow.json` owns state transitions. Stop with `STOP_PROTOCOL_CONFLICT` on conflict.
- Start locally from the `0000shrt` episode root. Keep one active writer and never mutate an active CapCut draft while CapCut or its background processes are open.
- Validate a source intake receipt with `scripts/validate_source_intake.py --receipt <path>` before Stage 01. Static validation does not authorize Drive, browser, CapCut, cloud, render, or upload actions.
- Validate an approved Stage 05 production plan with `scripts/validate_executable_protocol.py --plan <path>` before a build. Static validation does not establish a user visual approval.
- `PAPERCLIP_DISABLED`: Do not request, register, create, validate, wait on, or report Paperclip artifacts or states in this lane. Episode intake and progress use only the local episode root, `workflow.json`, and validated episode artifacts.
- For approved generated narration plus retained source speech, use `A9_TTS_PLUS_A10_RETAINED`; overlapping A10 rows use `source_audio[].mode=duck`, non-overlapping rows use `source_audio[].mode=on`, rows must be boundary-aligned with A9, and partial overlap fails with `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`.
- Treat every `WAIT_*` and `FAIL_*` in the selected stage MD as a hard stop. Do not use conversational memory as evidence.

## Urakkai Review Loop Contract

001 `URAKKAI` Stage 04의 검토 개선 loop는 정확히 1회 실행한다. 현재 승인 후보를 현재 로컬 runtime의 Claude CLI Claude Opus 5 `--effort low`로 검토하고 Hermes가 개선한다. Claude CLI가 실패했을 때만 동일 입력의 Codex CLI `gpt-5.6-sol` `--effort low` 검토 1회로 대체하며, 증거가 없으면 `WAIT_EXTERNAL_REVIEW`에서 중단한다.

## New Session Handoff Bootstrap

Validate `templates/conversation-handoff.json` against `schemas/conversation_handoff.schema.json` with `scripts/validate_conversation_handoff.py --handoff <path>` before work. Load `$HOME/.hermes/.env` once without output. Resume an old episode only when `resume_requested=true`, its episode ID, and current artifact readback all agree. Tokens, cookies, API keys, passwords, OAuth values, and session/conversation IDs are `HANDOFF_SECRET_MATERIAL_FORBIDDEN`.

## Compatibility

Existing legacy references, templates, schemas, and scripts remain available only through the orchestrator or a current-stage direct link. Do not delete them, copy their prose into this router, or let them compete with the selected stage authority.
