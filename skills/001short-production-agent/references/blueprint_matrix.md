# shrt_white_base_v2 canonical 15-track matrix

| Track | Seed role | Approved-plan role | Contract |
|---:|---|---|---|
| 1 | VIDEO | VIDEO | Source or clean visual only. Embedded audio is muted. |
| 2 | SCREEN_EFFECT | SCREEN_EFFECT | Full-duration fixed screen effect. |
| 3 | SCREEN_WHITE | SCREEN_WHITE | Full-duration white screen/frame. |
| 4 | STATE_FLICKER | STATE | `FLICKER_RAVE` situation seed. |
| 5 | STATE_GLITCH | STATE | `GLITCH_SHAKE` situation seed. |
| 6 | STATE_LASER | STATE | `LASER_CUT` situation seed. |
| 7 | A10_TEXT_WHITE | A10_TEXT | Primary speaker caption only. |
| 8 | A10_TEXT_YELLOW | A10_TEXT | Every other known speaker caption only. |
| 9 | A9_TEXT | A9_TEXT | TTS display text. |
| 10 | T2 | T2 | Approved second title, exact and non-empty. |
| 11 | T1 | T1 | Approved first title, exact and non-empty. |
| 12 | A9 | A9 | TTS audio. |
| 13 | A10 | A10 | Original speaker audio or approved deferred separation input. |
| 14 | A11 | A11 | SFX placements. |
| 15 | A12 | A12 | Full-duration BGM. |

Rules:

- This 15-track table is canonical. A 12-track layout is stale and must not pass Stage 08.
- `T1` and `T2` are separate approved values. Do not merge, split, copy, or leave `T2` empty.
- A speaker utterance uses logical role `A10_TEXT` only. The primary speaker uses `WHITE`; every other known speaker uses `YELLOW`.
- `UNKNOWN` and `UNASSIGNED` speaker IDs are not guessed or placed.
- Situation narration uses logical role `STATE` only and selects exactly one approved STATE seed.
- STATE text is a short phrase with at most 8 meaningful characters after whitespace is removed.
- `A10_TEXT` and `STATE` are never cross-routed.
