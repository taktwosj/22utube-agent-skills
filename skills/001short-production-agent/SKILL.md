---
name: 001short-production-agent
description: Use for original-shorts production, or when a new-session 001 conversation handoff JSON must load env safely and resume the same lane.
---

# 001short Compact Production

## Load order

1. Read [production-orchestrator.md](references/production-orchestrator.md) first.
2. Read `workflow.json`, episode state, and `protocol.json`; select one internal stage from the orchestrator's state/lock table.
3. Load exactly one current stage MD: [original-capcut-grid.md](templates/original-capcut-grid.md), [urakkai-production-grid.md](templates/urakkai-production-grid.md), or [capcut-assembly-grid.md](templates/capcut-assembly-grid.md).
4. Load only the direct supporting references linked by that stage MD. Do not load a second stage MD or replace a stage authority with a legacy document.

## Minimal executable protocol

- `protocol.json` is the machine contract and `workflow.json` owns state transitions. Stop with `STOP_PROTOCOL_CONFLICT` on conflict.
- Start locally from the episode root. Keep one active writer and never mutate an active CapCut draft while CapCut or its background processes are open.
- Validate an approved Stage 05 production plan with `scripts/validate_executable_protocol.py --plan <path>` before a build. Static validation does not establish a user visual approval.
- Treat every `WAIT_*` and `FAIL_*` in the selected stage MD as a hard stop. Do not use conversational memory as evidence.
- This documentation router does not authorize CapCut UI actions, cloud sync, render, upload, Drive writes, VMake, or any external action. Those require a separate explicit request and their own evidence.

## Compatibility

Existing legacy references, templates, schemas, and scripts remain available only through the orchestrator or a current-stage direct link. Do not delete them, copy their prose into this router, or let them compete with the selected stage authority.
