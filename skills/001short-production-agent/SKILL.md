---
name: 001short-production-agent
description: Use for original-shorts production, source intake from Google Drive, URL, or Desktop, CapCut 15-track assembly, or safe resume from a 001 conversation handoff.
---

# 001short Production

## Load order

1. Read [production-orchestrator.md](references/production-orchestrator.md), `workflow.json`, episode state, and `protocol.json`.
2. Select one internal stage and read only its stage document plus directly linked references.
3. Use `protocol.json` as the machine contract. Stop with `STOP_PROTOCOL_CONFLICT` on conflict.

For pre-lock ambiguity, reproducible code/tool defects, or contract changes, read
[matt-auxiliary-routing.md](references/matt-auxiliary-routing.md). Normal/AUTO episodes stay on the owner workflow.

## Authority and divergence

Before any skill, runtime, or episode-draft mutation, read and follow the single detailed contract in [Source authority and divergence gate](references/production-orchestrator.md#source-authority-and-divergence-gate). Never infer or self-select an exception.

## User-facing three phases

Always execute and report `원본표 → 우라까이표 → CapCut 조립`.

1. Build `20_script/original-capcut-grid.md` on source `Bxx` time columns.
2. Build `20_script/urakkai-capcut-grid.md` on target `Vxx` time columns, including the source `Bxx` in every header.
3. Validate and emit both complete tables with:

```text
python -B scripts/validate_capcut_grids.py \
  --original <episode_root>/20_script/original-capcut-grid.md \
  --urakkai <episode_root>/20_script/urakkai-capcut-grid.md \
  --emit-report
```

Paste 원본표 then 우라까이표. Automatic mode skips approval only.

Both tables must use this exact 15-row report order:

```text
T1, T2, A9_TEXT, A10_TEXT_YELLOW, A10_TEXT_WHITE,
STATE_LASER, STATE_GLITCH, STATE_FLICKER, SCREEN_WHITE,
SCREEN_EFFECT, VIDEO, A9, A10, A11, A12_RESERVED_EMPTY
```

Every cell: real value, `없음`, or `비움`; empty/placeholders/`미확인` fail. A12=`비움`. `A9_TEXT`/`STATE_LASER`: 15 characters per line, 2 lines.

## Build boundary

- `scripts/build_episode_capcut.py` validates both tables before work-root or draft writes. All build, overlay, track, and audio detail lives in the orchestrator.
- Mixed-audio contract vocabulary remains `A10_REASSEMBLED_SYNC`, `source_audio[].mode=duck`, `source_audio[].mode=on`, and `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`.
- Do not mutate a draft while CapCut or its background processes are open.

After assembly, report validator/readback, then separate code blocks for `프로젝트 파일명` and `프로젝트 전체 경로`. Missing readback=`NOT RUN`.

## Lane and finalization

- Keep `owner_skill=001short-production-agent`, `lane=general_shorts_production`; do not mix another production skill.
- `PAPERCLIP_DISABLED`: Do not request, register, create, validate, wait on, or report Paperclip.
- VMake is agent-first and nonblocking: continue provisional builds, then replace VIDEO after clean-asset verification.
- CapCut visual approval/refinement, render, and upload are user-manual-only. Stop automation at `WAIT_USER_CAPCUT_CHECK`.
- 외부 AI 검토를 호출하지 않는다.

## New Session Handoff Bootstrap

Validate a new-session 001 conversation handoff JSON against `schemas/conversation_handoff.schema.json` with `scripts/validate_conversation_handoff.py --handoff <path>`. Load `$HOME/.hermes/.env` silently; reject secret material as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`.
