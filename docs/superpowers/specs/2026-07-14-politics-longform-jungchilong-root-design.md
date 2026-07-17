# Politics Longform Jungchilong Root Design

## Decision

`jungchilong` is the only default/root CapCut project for `111-politics-longform` Stage 2. Stage 1 remains research/source handoff only. Stage 2 validates the Stage 1 package or a user-approved politics-only locked-clips override, validates `jungchilong`, copies the whole base to a new episode draft, and patches only the copy.

## Base Contract

- Default base folder: `%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft\jungchilong`.
- Never modify `jungchilong` in place.
- Never automatically fall back to YP007, YP005, YM007, YSM, or a generated derivative.
- Missing base: `WAIT_JUNGCHILONG_BASE_MISSING`.
- Dirty base: `FAIL_JUNGCHILONG_DIRTY_BASE`.
- Preserve `jungchilong` geometry, text roles, banners, graphics, transitions, effects, and render order by role. Do not impose YP007 track indexes or fabricate YP007-only overlays/effects.

## Runtime Contract

Git remains the source of truth. After tests pass and the change is committed, install the changed skill into both `$HOME\.codex\skills` and `$HOME\.claude\skills`, then verify file parity.

## Validation

- A regression test must fail against the current YP007/YP005 contract.
- A bundled `validate_clean_base.py` must reject missing and contaminated roots and accept a placeholder-only `jungchilong` fixture.
- Existing embedded political-longform contract tests must remain green.
- Repo verification and Codex/Claude runtime hash checks must pass before publishing.

## Out of Scope

- Changing Stage 1/Stage 2 boundaries.
- Changing T1-T5 text roles.
- Building or modifying a live CapCut episode draft.
- Restoring unrelated historical hooks or validators.
- Touching existing Shorts worktree changes.
