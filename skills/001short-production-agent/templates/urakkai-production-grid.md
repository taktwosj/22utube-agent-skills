# Urakkai production grid

> Stage 03--05 authority. Copy this file to `20_script/URAKKAI_PRODUCTION_GRID.md`. Consume the original grid, define approved order and placements, then let Stage 05 mechanically compile the approved timeline and production plan. Do not fill the installed template with an episode ID, actual speaker ID, or actual media ID.

## Supporting references

- [Production orchestrator](../references/production-orchestrator.md)
- [Urakkai structural contract](../references/urakkai-structural-reorder-capcut.md)
- [Stage 04 review contract](../references/stage04-external-review-contract.md)
- [Root contract and production plan](../references/root-contract-production-plan.md)

## Inputs and approval status

| Item | Value |
|---|---|
| Required input | `20_script/original-capcut-grid.md` |
| Original order signature | `<source structure order>` |
| Final order signature | `<approved final structure order>` |
| Audio policy | `<TTS_ONLY_MUTE_SOURCE / A10_RETAINED_SYNC>` |
| Primary speaker ID | `<approved primary speaker ID>` |
| Approval status | `<DRAFT / WAIT_USER_URAKKAI_APPROVAL / APPROVED>` |

## Original-to-final order

| Final order | Original structure | Source range | Target range | Delivery | Change reason |
|---:|---|---|---|---|---|
| `<1>` | `<source structure>` | `<source range>` | `<target range>` | `<speaker / A9 / STATE / SFX>` | `<narrative reason>` |

> Stop with `URAKKAI_STRUCTURE_UNCHANGED` when the original and final order signatures match. Record source and target ranges 1:1 for every VIDEO and retained A10 placement.

## 15-role placement contract

| Logical role | Placement / asset decision | Target range | Required rule |
|---|---|---|---|
| VIDEO | `<source media placement>` | `<full episode or approved cuts>` | Use picture only; volume is `0`. |
| SCREEN_EFFECT | `<seed retained>` | `<0 to final end>` | Keep through final duration. |
| SCREEN_WHITE | `<seed retained>` | `<0 to final end>` | Keep through final duration. |
| STATE_EFFECT_1 | `<FLICKER_RAVE cue or unused>` | `<range>` | Use exactly one effect lane per STATE cue. |
| STATE_EFFECT_2 | `<GLITCH_SHAKE cue or unused>` | `<range>` | Use exactly one effect lane per STATE cue. |
| STATE_EFFECT_3 | `<LASER_CUT cue or unused>` | `<range>` | Use exactly one effect lane per STATE cue. |
| A10_TEXT_WHITE | `<primary speaker caption or unused>` | `<range>` | White is primary speaker only. |
| A10_TEXT_YELLOW | `<other resolved speaker caption or unused>` | `<range>` | Yellow is every other resolved speaker. |
| A9_TEXT | `<approved TTS caption or muted seed>` | `<range>` | Never use literal `/`; split into sequential placements if needed. |
| T2 | `<approved title>` | `<0 to final end>` | Keep through final duration. |
| T1 | `<approved title>` | `<0 to final end>` | Keep through final duration. |
| A9 | `<TTS asset or muted seed>` | `<range>` | TTS role only. |
| A10 | `<retained source voice or muted seed>` | `<range>` | Original speaker-audio role only. |
| A11_SFX | `<transition / reversal / wow SFX>` | `<range>` | Use at transition, reversal, or wow point at normal volume. |
| A12 | `<approved BGM>` | `<0 to final end>` | Keep through final duration at normal volume. |

## Cue detail and compiler output

| Cue type | Text / media | Start--end | Routing / effect / SFX | Evidence |
|---|---|---|---|---|
| A9 caption | `<caption text without slash>` | `<target range>` | `A9_TEXT + A9` | `<approved copy>` |
| Speaker line | `<literal or approved caption>` | `<target range>` | `<WHITE / YELLOW / UNASSIGNED>` | `<speaker evidence>` |
| STATE | `<present-action explanation>` | `<target range>` | `<exactly one effect lane + optional A11 SFX>` | `<placement rationale>` |

| Stage 05 output | Required result |
|---|---|
| Approved timeline | `<path to approved timeline>` with every role placement and effect/SFX choice explicit. |
| Production plan | `<path to production plan>` compiled mechanically from this approved table. |
| Stop condition | `WAIT_USER_URAKKAI_APPROVAL` before approval; `WAIT_PRIMARY_SPEAKER_ASSIGNMENT` when a required primary is unknown; `WAIT_URAKKAI_GRID_COMPLETE` for a missing range, role, caption timing, effect, or SFX decision. Keep uncertain non-primary speakers `UNASSIGNED`; never guess. |
