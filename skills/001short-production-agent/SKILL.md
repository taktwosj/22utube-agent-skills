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

Before Stage 01, `python3 scripts/preflight_env.py --require-fresh` must PASS ([rules](references/environment-preflight.md)). Never install or hunt for tools mid-episode; installs are user-terminal-only.

## NORMAL_FAST ownership

`NORMAL_FAST` is default. One task-owner performs Stages 01–04 sequentially and owns canonical writes. No Stage 01/03 fanout, candidate promotion, coordinator revalidation, or duplicate barriers. Run each validator once per artifact revision and rerun only after a proven relevant change.

## Authority and divergence

Before skill, runtime, or episode-draft mutation, follow [Source authority and divergence gate](references/production-orchestrator.md#source-authority-and-divergence-gate). Never self-select an exception.

## User-facing phases

Always execute and report `원본표 → 우라까이표 → CapCut 조립`.

1. Build `20_script/original-capcut-grid.md`: source `Bxx` columns, copyable five-field `B01 → BN` script, and 15-row table. Fields: situation/literal OCR, source speaker utterance, source narration, generated speaker TTS, generated narration TTS. Multiple speakers use `[A] ... / [B] ...`; A=`A10_TEXT_WHITE`, B=`A10_TEXT_YELLOW`.
2. The task owner sends the validated copyable original table to the user's already-open 투군 GPT tab, reads the returned advice, and saves it to the episode. Do not delegate the live tab or current form state to a subagent. From the returned urakkai script, build `20_script/urakkai-capcut-grid.md` with target `Vxx` columns and source `Bxx` in every header.
3. Validate and emit both complete tables:

```text
python -B scripts/validate_capcut_grids.py \
  --original <episode_root>/20_script/original-capcut-grid.md \
  --urakkai <episode_root>/20_script/urakkai-capcut-grid.md \
  --emit-report
```

Paste 원본표 then 우라까이표. Automatic mode skips approval only.

Exact row order:

```text
T1, T2, A9_TEXT, A10_TEXT_YELLOW, A10_TEXT_WHITE,
STATE_LASER, STATE_GLITCH, STATE_FLICKER, SCREEN_WHITE,
SCREEN_EFFECT, VIDEO, A9, A10, A11, A12_RESERVED_EMPTY
```

Every cell is a real value, `없음`, or `비움`; empty/placeholders/`미확인` fail. A12=`비움`. Original `A9_TEXT` and all `STATE_LASER`: 2×15. Target `A9_TEXT` paired with A9 TTS: 2×10. For approved `CAPTION_ONLY_MUTE_SOURCE`, use STATE_LASER only and leave A9/A9_TEXT/A10/A10_TEXT/A11 empty.

## TTT caption policy

- `TTT` means actual visible, narration-free on-screen text captions. It is not TTS and never means a no-caption edit.
- For TTT, obtain 투군's new wording from the validated original-table facts and locked `Vxx` order. The recommendation is advisory: preserve source facts and source ranges.
- Absolute rule: never copy, re-display, or lightly edit original baked-in caption text as TTT. This includes parenthetical situation labels, exclamations, and original punchlines. Use 투군's meaning-similar but newly written text.
- Keep the user-approved audio policy. In `CAPTION_ONLY_MUTE_SOURCE`, source VIDEO is muted and `A9`, `A10`, and `A11` are empty.
- TTT must be real, readback-verifiable CapCut text segments. `STATE_LASER` TTT cues require matching approved-timeline `STATE`, caption-lock, and caption-timing evidence.

## Build boundary

For newly requested A9 narration TTS, read `<factory-root>/00_asset_tools/TYPECAST_TTS_RUNBOOK.md` before synthesis. Keep user-supplied or approved narration audio unchanged.

`scripts/build_episode_capcut.py` validates both tables before writes, validates the root ZIP, extracts immutable `source_authority`, clones `working_project`, assigns new IDs, injects assets only into the clone, and validates it. Audio terms remain `A10_REASSEMBLED_SYNC`, `source_audio[].mode=duck`, `source_audio[].mode=on`, and `MIXED_A10_PARTIAL_OVERLAP_UNSUPPORTED`. Never mutate a draft while CapCut or its background processes are open.

After assembly, the first item in the result report is the exact CapCut `프로젝트명` in its own copyable code block. Then report validator/readback, followed by separate code blocks for `프로젝트 전체 경로` and `미디어 폴더 전체 경로`; missing readback=`NOT RUN`.

## Lane Isolation

- 하나의 lane만 확정: keep `owner_skill=001short-production-agent`, `lane=general_shorts_production`; do not chain `top5isu-shorts` or another production skill.
- `PAPERCLIP_DISABLED`: Do not request, register, create, validate, wait on, or report Paperclip.
- VMake is agent-first and nonblocking; replace provisional VIDEO after clean-asset verification.
- Stage 04의 승인 권위는 사용자다.
- CapCut visual approval/refinement, render, and upload are user-manual-only. Stop at `WAIT_USER_CAPCUT_CHECK`.

## New Session Handoff Bootstrap

Validate a new-session 001 conversation handoff JSON against `schemas/conversation_handoff.schema.json` with `scripts/validate_conversation_handoff.py --handoff <path>`. Load `$HOME/.hermes/.env` silently; reject secret material as `HANDOFF_SECRET_MATERIAL_FORBIDDEN`.
