# 001short production orchestrator

Read this reference before every internal stage MD. It selects the one stage authority, preserves the locks between stages, and defines the shared boundaries. It does not itself create a project, operate a UI, sync cloud data, render, or upload.

## State and lock selection

Use the actual `workflow.json`, episode state, and listed evidence. Never infer a later stage from a filename, a message, or a prior episode.

| Current evidence / lock | Internal stage | Load exactly this MD | Stop if missing |
|---|---|---|---|
| Canonical OneDrive intake receipt, source identity, readback metadata, or measured duration is absent or changing | 1. Original | [original-capcut-grid.md](../templates/original-capcut-grid.md) | `WAIT_ORIGINAL_INTAKE_EVIDENCE` |
| Original grid is complete and final order, copy, speaker policy, caption timing, STATE/SFX, or user approval is unresolved | 2. Urakkai | [urakkai-production-grid.md](../templates/urakkai-production-grid.md) | the selected table's `WAIT_*` / `URAKKAI_STRUCTURE_UNCHANGED` |
| Approved timeline and production plan are locked, or static CapCut creation / Stage 09 visual handoff is current | 3. CapCut assembly | [capcut-assembly-grid.md](../templates/capcut-assembly-grid.md) | the selected table's `WAIT_*` / `FAIL_*` |

If no row uniquely applies, stop `WAIT_STAGE_SELECTION`. Do not load two stage tables to resolve ambiguity.

## 1 -> 2 -> 3 handoff

| From | Required locked output | To | Acceptance |
|---|---|---|---|
| 1. Original | `20_script/original-capcut-grid.md`: canonical OneDrive intake receipt, source identity, metadata, measured duration, and evidence rows | 2. Urakkai | Original grid handoff table is complete. |
| 2. Urakkai | `20_script/URAKKAI_PRODUCTION_GRID.md`, approved timeline, and production plan | 3. CapCut assembly | User approval is explicit; every 15-role placement and all effect/SFX choices are recorded. |
| 3. CapCut assembly | Static project receipt and separate visual-handoff status | Stage 09 user review | Static PASS is not visual PASS; retain `WAIT_USER_STAGE09_VISUAL_CHECK` until user evidence exists. |

## User approval gates

| Gate | Required evidence | Prohibited shortcut |
|---|---|---|
| Urakkai approval | Explicit user approval of the completed Stage 2 grid / review companion before Stage 05 compilation | Reviewer output, draft JSON, or assistant inference is not approval. |
| Manual media relink | User manual-relink receipt after `Resources/media` preparation when relink is required | Builder or static JSON must not claim editor relink. |
| Stage 09 visual check | User/editor evidence for display, effects, audio, and relink | Root/timeline parity or a static validator is not a visual check. |

## Shared non-negotiable rules

- `shrt_white_base_v2` is the immutable root authority. Never open, parse, or use a v1 ZIP, v1 role map, or v1 draft for this flow.
- The approved timeline is the only placement authority. Use the 15 logical roles listed in the Stage 2 table; resolve by contract anchor, never track index.
- VIDEO, A9, and A10 use muted seeds where required. A11 SFX and A12 BGM retain normal volume. T1, T2, SCREEN_WHITE, and SCREEN_EFFECT span the final duration.
- Keep primary speaker captions white and every other resolved speaker yellow. Keep uncertain speakers `UNASSIGNED`; never guess.
- Use slash-free A9 captions. Split a caption into sequential placements instead of inserting literal `/`.
- Use exactly one STATE effect lane per cue: `FLICKER_RAVE`, `GLITCH_SHAKE`, or `LASER_CUT`. Record each SFX choice in the approved timeline before build.
- Prepare `Resources/media` plus a manifest, then default to user manual relink. Do not automate editor relink.
- Build only in unique staging. Regenerate the draft path prefix from the root UUID, reject unresolved placeholders, validate first, then atomically promote. On failure remove staging only.
- The canonical final working, assembly, and validation root is `C:\Users\arajun\OneDrive\22utube\22factory_20260628\0000shrt\<YYMMDD_short-title_source-id>`. Intake may originate from a Google Drive folder/file, a YouTube Shorts URL, or a user-designated Desktop local folder; normalize every accepted origin into that root before Stage 01.
- Require an immutable `90_workflow/onedrive_intake_receipt.json` before Stage 01 handoff. It records the origin type and locator, source URL/ID when applicable, `00_input/source.mp4` relative path, SHA-256, measured duration, and storage policy. A changed source requires a new receipt and revalidation.
- Google Drive is an optional read-only intake origin, never a mandatory Stage 01 gate. Do not modify, share, upload, or create Drive content under this workflow.

## Compatibility references

Legacy detail remains authoritative only when a current stage MD links to it: [source acquisition](youtube-source-acquisition.md), [urakkai structural contract](urakkai-structural-reorder-capcut.md), [root contract and plan](root-contract-production-plan.md), [build readiness](capcut-build-readiness.md), and [post-open visual QA](capcut-tts-visual-qa-post-open.md). They do not override the selected table's input, output, or stop condition.
