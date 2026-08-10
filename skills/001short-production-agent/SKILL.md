---
name: 001short-production-agent
description: Use for original-shorts production, source intake from Google Drive, URL, or Desktop, CapCut 15-track assembly, or safe resume from a 001 conversation handoff.
---

# 001short Production

## Load order

1. Read [production-orchestrator.md](references/production-orchestrator.md), `workflow.json`, episode state, and `protocol.json`.
2. Select one internal stage and read only its stage document plus directly linked references.
3. Use `protocol.json` as the machine contract. Stop with `STOP_PROTOCOL_CONFLICT` on conflict.

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

Paste the emitted 원본표 first and 우라까이표 second into the 대화창. Automatic mode skips user approval only; it never skips either full table.

Both tables must use this exact 15-row report order:

```text
T1, T2, A9_TEXT, A10_TEXT_YELLOW, A10_TEXT_WHITE,
STATE_LASER, STATE_GLITCH, STATE_FLICKER, SCREEN_WHITE,
SCREEN_EFFECT, VIDEO, A9, A10, A11, A12_RESERVED_EMPTY
```

Every intersection cell must contain a real value, `없음`, or `비움`. Empty strings, whitespace, dashes, and placeholders fail with `TABLE_EMPTY_CELL_FORBIDDEN`. `미확인` fails with `TABLE_UNVERIFIED_CELL`. Every A12 cell must be `비움`. `A9_TEXT` and `STATE_LASER` allow at most 15 characters per line and 2 lines.

## Build boundary

- `scripts/build_episode_capcut.py` validates both tables before creating or mutating a work root or local draft.
- It binds normalized text, cue/layer/color/effect, and state path/SHA locks for timeline, manifest, design, audio, and captions.
- Keep the `shrt_white_base_v2_15` physical 15-track contract. Route STATE only to `STATE_LASER`; keep `STATE_GLITCH`, `STATE_FLICKER`, and A12 empty.
- A9/A9_TEXT require actual narration audio. STATE_LASER is a no-audio situation description; do not request a TTS engine for STATE-only screens.
- Prepare A10 and run Demucs only when the approved table contains A10.
- Use `A9_TTS_PLUS_A10_RETAINED` when approved narration and retained source speech coexist. Use `source_audio[].mode=duck` under A9 and `source_audio[].mode=on` outside it; reject partial overlap as `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`.
- Keep VIDEO embedded audio muted and preserve the selected audio policy.
- Do not mutate a draft while CapCut or its background processes are open.

After assembly, report the actual validator/readback summary. Then show `프로젝트 파일명` in its own code block and `프로젝트 전체 경로` in a second code block. If readback did not run, report `NOT RUN`, never `PASS`.

## Lane and finalization

- Keep `owner_skill=001short-production-agent`, `lane=general_shorts_production`; do not mix another production skill.
- `PAPERCLIP_DISABLED`: Do not request, register, create, validate, wait on, or report Paperclip.
- VMake acquisition remains agent-first and nonblocking: a provisional source build may continue, followed by VIDEO-only replacement after a verified clean asset.
- CapCut visual approval/refinement, render, and upload are user-manual-only. Stop automation at `WAIT_USER_CAPCUT_CHECK`.
- 외부 AI 검토를 호출하지 않는다.

## New Session Handoff Bootstrap

For a new-session 001 conversation handoff JSON, validate `templates/conversation-handoff.json` against `schemas/conversation_handoff.schema.json` with `scripts/validate_conversation_handoff.py --handoff <path>`. Load `$HOME/.hermes/.env` once without output. Reject tokens, cookies, keys, passwords, OAuth values, and session identifiers as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`.
