# CapCut assembly grid

> Stage 08 authority. Copy this file to `40_capcut/CAPCUT_ASSEMBLY_GRID.md`. Do not fill the installed template with an episode ID, draft UUID, root UUID, actual path, or actual media ID.

## Supporting references

- [Production orchestrator](../references/production-orchestrator.md)
- [Root contract and production plan](../references/root-contract-production-plan.md)
- [CapCut build readiness](../references/capcut-build-readiness.md)
- [Post-open visual QA](../references/capcut-tts-visual-qa-post-open.md)

## Locked inputs and preflight

| Check | Required record | Stop condition |
|---|---|---|
| Root authority | Immutable `shrt_white_base_v2` archive, reviewed root contract, archive/layout fingerprint | `FAIL_V2_ROOT_CONTRACT_MISSING` or `FAIL_V2_ROOT_ARCHIVE_MUTATED` |
| v1 exclusion | Never open, parse, or use a v1 ZIP, v1 role map, or v1 draft | `FAIL_V1_ROOT_FORBIDDEN` |
| Stage 05 lock | Approved timeline, production plan, titles, speaker routing, effects, and SFX are locked | `WAIT_STAGE05_APPROVAL_LOCK` |
| Writer / CapCut lock | One active writer; CapCut and background processes are closed before draft mutation | `WAIT_CAPCUT_WRITER_LOCK` |
| Path guard | Portable draft-path prefix derives from regenerated root UUID; no unresolved placeholder remains | `FAIL_DRAFT_PREFIX_UNRESOLVED` |

## Media preparation and user-relink boundary

| Action | Evidence | Boundary |
|---|---|---|
| Prepare `Resources/media` | `<asset manifest / copied-media receipt>` | Prepare files and manifest only. |
| CapCut relink | `<user manual-relink receipt>` | Default is user manual relink. Do not automate editor UI relinking or claim it occurred. |
| Media readiness stop | `<WAIT_USER_CAPCUT_MANUAL_RELINK or PASS>` | Static project creation and editor readiness are distinct claims. |

## Deterministic staging build

| Build step | Required record | Stop condition |
|---|---|---|
| Unique staging | `<unique staging path / regenerated draft and timeline identifiers>` | `FAIL_STAGING_TARGET_EXISTS` |
| Apply 15 roles | `<contract-anchor placement receipt>` | Require VIDEO, SCREEN_EFFECT, SCREEN_WHITE, 3 STATE effect lanes, 2 speaker-caption lanes, A9_TEXT, T1, T2, A9, A10, A11_SFX, and A12 by role, never track index. |
| Mute / volume policy | `<VIDEO/A9/A10 muted-seed receipt; A11/A12 normal-volume receipt>` | `FAIL_AUDIO_ROLE_POLICY` |
| Static validation | `<root/timeline parity, media refs, layout, IDs, duration, style preservation>` | `FAIL_STATIC_PROJECT_VALIDATION` |
| Atomic promotion | `<staging-to-final promotion receipt>` | On failure remove staging only; preserve root and leave final target absent. |

## Output and separated visual check

| Output | Status rule |
|---|---|
| Project creation | `<editable project path / static validation receipt>`; report only after atomic promotion. |
| UI visual check | Separate user/editor check for display, effects, audio, and relink. Static PASS is not visual PASS. |
| Final stop condition | `WAIT_USER_CAPCUT_MANUAL_RELINK` or `WAIT_USER_STAGE09_VISUAL_CHECK` until applicable user evidence exists; never report visual completion from JSON or static validation alone. |
