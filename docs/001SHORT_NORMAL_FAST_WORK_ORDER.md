# 001short NORMAL_FAST Work Order

## Authority

- Base: `origin/main` at `088daf29d0cfda9078ef7f3dc86cd9e8504905e9`.
- Worktree: `worktrees/001short-normal-fast-20260815`.
- Existing uncommitted work from `001short-three-stage-grid-contract-20260810` is `SEPARATE_UNFINISHED_WORK` and is not an input to this change.
- Preserved patch: `worktrees/_preserved_uncommitted/001short-20260815-separate-unfinished-work.patch`.
- This work order changes execution ownership and editorial contracts. It does not weaken CapCut build or validation safety.

## Goal

Make `NORMAL_FAST` the default 001short execution profile. One task-owner carries Stage 01 through Stage 04 without worker fanout, evidence-only promotion, coordinator revalidation, or barrier duplication. Existing stage validators, root-template checks, build safety, postbuild inspection, and manual CapCut finalization remain mandatory.

## Required behavior

1. `NORMAL_FAST` is the default execution profile.
2. One `task-owner` performs Stage 01, Stage 02, Stage 03, and Stage 04 sequentially.
3. The default profile does not spawn Stage 01, Stage 03, post-design, or postbuild parallel workers.
4. The default profile does not create evidence-only worker candidates, promote them through a coordinator, or repeat the same evidence at a barrier.
5. Every existing stage validator remains required at its owning stage. A validator runs once per current artifact revision and reruns only after a proven relevant change.
6. Stage 08 verifies the canonical CapCut root ZIP and root contract, extracts the ZIP into a source-authority directory, clones it into a separate working project, assigns new project/draft/timeline IDs, injects episode assets into the clone, and validates the assembled clone. The root ZIP and extracted source are immutable.
7. External AI editorial review is absent from the normal and automatic production route. Remove legacy external-review stage files, routing entries, and stale wording.
8. Every original `Bxx` beat records five separate fields: `situation_action`, `lead_speaker`, `delivery_mode`, `narrative_function`, and `split_basis`. These fields are observations of the source and are not replaced by an urakkai interpretation.
9. Stage 03 uses one independent urakkai author: the same task-owner writes one complete recommendation from locked Stage 02 inputs. Hook, caption, audio/SFX, and screen-composition subworkers are not used. Stage 03 cannot rewrite the original grid.
10. The 2-line by 10-character contract applies only to newly authored target `A9_TEXT` in the urakkai grid. Original-source `A9_TEXT` and `STATE_LASER` retain their existing contracts.
11. Automation stops at `WAIT_USER_CAPCUT_CHECK`. Visual approval/refinement, render, and upload remain user-only.

## Validation invariants

- `validate_source_intake.py` continues to bind source path, SHA-256, identity, and receipt.
- `validate_capcut_grids.py` continues to validate both complete 15-row grids before build writes.
- Design, audio, caption, source-time, path, SHA-256, and revision bindings remain enforced.
- `build_episode_capcut.py` keeps all root/working separation, CapCut-process, material registration, caption, audio, Timeline mirror, and ID mirror safeguards.
- Postbuild validation continues to inspect the actual assembled draft rather than accepting worker status text.
- Missing validation is `NOT RUN`, never `PASS`, `FINAL`, or an assembly-success substitute.

## Forbidden changes

- No validator-skip route.
- No `ASSEMBLED_NOT_VALIDATED` state.
- No SHA, path, audio material, caption, project-ID mirror, or Timeline mirror bypass.
- No default unvalidated assembly profile.
- No deletion or weakening of `build_episode_capcut.py` safety checks.
- No direct mutation of the canonical CapCut root ZIP or extracted source-authority tree.
- No merge, copy, or adoption of the preserved five-file unfinished patch.
- No external AI reviewer in Stage 03 or Stage 04.

## Completion criteria

- Machine contracts declare `NORMAL_FAST` as default and single-owner.
- Default worker fanout and duplicate coordinator/barrier validation are disabled.
- Validators and CapCut root/clone safety remain present and covered by tests.
- The five-field `Bxx` contract, single-writer Stage 03 contract, and target-only A9 2x10 rule are enforced.
- Legacy external-review files and every live reference to them are removed.
- Protocol self-check and directly related tests pass.
- Runtime publish/activation is not performed until source commit is separately approved.
