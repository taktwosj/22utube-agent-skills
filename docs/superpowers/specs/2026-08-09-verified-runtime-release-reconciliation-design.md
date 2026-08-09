# Verified Runtime Release Reconciliation

## Goal

Apply one committed `main` manifest to Codex, Claude, and Hermes on the same computer without converting verified runtime junctions into mutable copied folders.

## Approved design

`scripts/skill_release.py` becomes the official release path on `main`. `publish` snapshots only enabled manifest skills into an immutable release. `activate --target all` links every enabled skill for all three local targets and reconciles only stale managed junctions that point to the prior active local release. A stale managed link is backed up before removal; unmanaged folders are preserved. The activation transaction restores changed links if a later step fails. `verify --target all --self-check` proves every selected target points to the immutable local release.

## Boundaries

- Source changes remain local until commit, push, PR review, and merge.
- `update.ps1`, direct copies, and save-watch hooks are not used for verified release activation.
- The current expected manifest has six shared skills. Removed 110, 111, and 112 links are reconciled; their Git source folders remain untouched.
- No cross-computer scheduling is introduced by this patch.
