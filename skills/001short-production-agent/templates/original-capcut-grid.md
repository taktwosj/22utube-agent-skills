# Original grid

> Stage 02 authority. Copy this file to `20_script/original-capcut-grid.md`. Do not fill the installed template with an episode ID, actual URL, actual person, or actual time.

## Supporting references

- [Production orchestrator](../references/production-orchestrator.md)
- [Source acquisition](../references/youtube-source-acquisition.md)
- [Structure blueprint reporting](../references/structure-blueprint-reporting.md)

## Inputs and next stage

| Item | Record | Rule |
|---|---|---|
| Source identity | `<source URL / local path / content fingerprint>` | Bind the original and local file 1:1. |
| Metadata readback | `<title / channel / published value / retrieval time>` | Record only visible source metadata. |
| Measured duration | `<ffprobe duration>` | Use a local measurement, never an estimate. |
| Drive-grid receipt | `<read-only URL / visible scope / checked time / row count / result>` | Verify Drive in read-only mode. Do not modify, share, or upload. |
| Next-stage input | `20_script/original-capcut-grid.md` | This is the sole original-source input to the Stage 03 urakkai grid. |

## Observable source grid

> Split time columns at observed changes in picture, text, speech, or sound. Mark uncertainty as `UNVERIFIED` with its evidence. This record does not decide final TTS or CapCut assembly.

| Role / source range | `<source range 1>` | `<source range 2>` |
|---|---|---|
| VIDEO | `<visible action / framing / transition>` | `<visible action / framing / transition>` |
| T1 | `<observed title or title-evidence status>` | `<observed title or title-evidence status>` |
| T2 | `<observed subtitle or title-evidence status>` | `<observed subtitle or title-evidence status>` |
| A9 narration evidence | `<spoken narration or explicit absence with evidence>` | `<spoken narration or explicit absence with evidence>` |
| A10 speaker / dialogue | `<source range + literal or verified summary + speaker status>` | `<source range + literal or verified summary + speaker status>` |
| STATE observation | `<visible present action / emotion / relationship>` | `<visible present action / emotion / relationship>` |
| A11 / A12 observation | `<heard SFX or BGM, or explicit absence with evidence>` | `<heard SFX or BGM, or explicit absence with evidence>` |
| SCREEN | `<baked-in text / watermark / position / style evidence>` | `<baked-in text / watermark / position / style evidence>` |

## Stage 03 handoff

| Required before handoff | Value |
|---|---|
| Source identity, metadata, and measured duration recorded | `<PASS / missing item>` |
| Drive-grid read-only receipt recorded | `<PASS / missing item>` |
| Every source range has a VIDEO row and applicable evidence rows | `<PASS / missing ranges>` |
| Uncertain identity or audio marked without guessing | `<PASS / missing evidence>` |
| Stop condition | `WAIT_ORIGINAL_GRID_EVIDENCE` until every required row and receipt is complete. |
