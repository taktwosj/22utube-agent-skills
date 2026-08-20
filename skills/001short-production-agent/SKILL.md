---
name: 001short-production-agent
description: Use for original-shorts production, URL/Drive/Desktop intake, CapCut 15-track assembly, or safe 001 handoff resume.
---

# 001short Production

## Load order

1. Read [production-orchestrator.md](references/production-orchestrator.md), `workflow.json`, episode state, and `protocol.json`.
2. Read only the resolved stage document and direct references.
3. `protocol.json` is the machine contract; conflict=`STOP_PROTOCOL_CONFLICT`.

Use [matt-auxiliary-routing.md](references/matt-auxiliary-routing.md) only for pre-lock ambiguity, reproducible defects, or contract changes.

## Environment preflight

`python3 scripts/preflight_env.py --require-fresh` must PASS before Stage 01 ([rules](references/environment-preflight.md)). Never install or hunt for tools mid-episode.

## NORMAL_FAST ownership

`NORMAL_FAST` is default: one task-owner performs Stages 01–04 sequentially and owns canonical writes. No fanout, candidate promotion, or duplicate barriers; run each validator once per artifact revision.

## Authority and divergence

Before skill, runtime, or episode-draft mutation, follow [Source authority and divergence gate](references/production-orchestrator.md#source-authority-and-divergence-gate). Never self-select an exception.

## Types and captions

Audio type and caption kind are independent axes. TTT (captions without matching audio) never narrows the audio axis: types 3–5 keep A10, and source narration never carries into production. Derive type candidates from the 원본표 (no verified 화자발언 → types 1·2 only); lock `execution_strategy` and audio policy at user approval. Decision tree, per-type tracks and policies, artifact chains: [type-assembly-matrix.md](references/type-assembly-matrix.md).

## User-facing phases

Always execute and report `원본표 → 우라까이표 → CapCut 조립`.

1. Build `20_script/original-capcut-grid.md` per [template](templates/original-capcut-grid.md): 원본 5분류 대본 + 15-row table. Exact row order, cell rules, and TTT notation live in the templates and `scripts/validate_capcut_grids.py`.
2. The task owner sends the validated original table to the user's live 투군 GPT tab, saves the returned advice, and builds `20_script/urakkai-capcut-grid.md` per [template](templates/urakkai-capcut-grid.md). Never delegate the live tab or current form state to a subagent.
3. Validate both tables (`validate_capcut_grids.py --emit-report`) and paste 원본표 then 우라까이표. Automatic mode skips approval only.

## Build boundary

For newly requested A9 TTS, read `<factory-root>/00_asset_tools/TYPECAST_TTS_RUNBOOK.md` first; keep user-supplied or approved narration audio unchanged. Audio terms remain `A10_REASSEMBLED_SYNC`, `source_audio[].mode=duck`, `source_audio[].mode=on`, and `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`. `scripts/build_episode_capcut.py` validates both tables before writes, clones `working_project`, injects assets only into the clone, and validates it; never mutate a draft while CapCut is open. After assembly report the CapCut `프로젝트명` first in its own code block, then validator/readback, then `프로젝트 전체 경로` and `미디어 폴더 전체 경로`; missing readback=`NOT RUN`.

## Lane Isolation

- Keep `owner_skill=001short-production-agent`, `lane=general_shorts_production`; never chain another production skill.
- `PAPERCLIP_DISABLED`: Do not request, register, create, validate, wait on, or report Paperclip.
- VMake: the agent submits the source through the official VMake API/SDK at intake, nonblocking ([contract](references/vmake-api-clean-video.md)); DOM automation through Aside is the fallback when the API is unavailable, and URL submission is the last resort and costs resolution ([contract](references/vmake-dom-clean-video-automation.md)).
- Stage 04의 승인 권위는 사용자다. CapCut visual approval, render, and upload are user-manual-only; stop at `WAIT_USER_CAPCUT_CHECK`.

## New Session Handoff Bootstrap

Validate a new-session 001 conversation handoff JSON against `schemas/conversation_handoff.schema.json` with `scripts/validate_conversation_handoff.py --handoff <path>`. Load `$HOME/.hermes/.env` silently; reject secret material as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`.
