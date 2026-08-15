# 001short NORMAL_FAST Execution Spec

> Task owner: one implementation worker. No parallel implementers may edit this scope.

## Goal

Implement the approved `NORMAL_FAST` execution profile while preserving all existing validator and CapCut root-clone safety guarantees.

## Baseline RED evidence

The current workflow declares `parallel_execution.enabled=true`, Stage 01 with three workers, Stage 03 with four workers, post-design with three workers, and postbuild with four workers. Production traces therefore enter repeated worker waits and coordinator/barrier revalidation. The current grid contract also applies 15 characters to every A9 text instead of a target-only 10-character rule, and legacy external-review files remain installed.

## Files

### Create

- `docs/001SHORT_NORMAL_FAST_WORK_ORDER.md`: approved behavioral authority.
- `docs/001SHORT_NORMAL_FAST_EXECUTION_SPEC.md`: implementation and verification map.
- `skills/001short-production-agent/scripts/validate_original_blueprint.py`: validate every Stage 02 `Bxx` field and emit locked beat IDs.

### Modify

- `skills/001short-production-agent/SKILL.md`: point to NORMAL_FAST, single-owner stages, target-only A9 rule, validators retained, and no external AI review route.
- `skills/001short-production-agent/workflow.json`: declare default `NORMAL_FAST`; replace default fanout/coordinator/barrier execution with sequential single-owner routing.
- `skills/001short-production-agent/protocol.json`: machine-contract execution profile, five-field source-beat contract, Stage 03 writer contract, and target A9 2x10 values.
- `skills/001short-production-agent/tools.json`: remove the obsolete external-review policy flag; preserve every build and track policy.
- `skills/001short-production-agent/schemas/executable_protocol.schema.json`: require the new protocol fields without weakening existing invariants.
- `skills/001short-production-agent/schemas/structure_snapshot.schema.json`: require the v2 working-project snapshot authority.
- `skills/001short-production-agent/references/matt-auxiliary-routing.md`: remove stale external-editorial wording while retaining advisory boundaries.
- `skills/001short-production-agent/references/production-orchestrator.md`: define one-owner execution, validator ownership, and immutable root ZIP -> source-authority -> working clone -> assembled draft flow.
- `skills/001short-production-agent/references/parallel-execution.md`: mark parallel execution non-default and unavailable to `NORMAL_FAST` without a separately approved future profile.
- `skills/001short-production-agent/references/structure-blueprint-reporting.md`: define the five original-beat fields.
- `skills/001short-production-agent/steps/01-input-ocr.md`: single-owner Stage 01 output and five-field beat preparation.
- `skills/001short-production-agent/steps/02-original-blueprint.md`: require all five fields per `Bxx`.
- `skills/001short-production-agent/steps/03-first-recommendation.md`: one independent urakkai author; immutable Stage 02 original grid.
- `skills/001short-production-agent/steps/04-user-approval.md`: user approval only, with no external reviewer handoff.
- `skills/001short-production-agent/steps/05-final-blueprint.md`: replace stale external-review wording with the Stage 04 user/automatic approval authority.
- `skills/001short-production-agent/steps/08-capcut-assembly.md`: retain and make explicit the root-contract extraction and clone-only assembly sequence.
- `skills/001short-production-agent/templates/human-design-blueprint.md`: use canonical `Bxx` rows and five distinct observation columns.
- `skills/001short-production-agent/scripts/validate_stage.py`: validate and SHA-bind both Stage 02 artifacts, recheck their locks at Stage 03/04 entry, and reject v1 snapshots at Stage 08/09.
- `skills/001short-production-agent/scripts/build_episode_capcut.py`: hash and clone immutable source authority before mutating only the working project.
- `skills/001short-production-agent/scripts/capcut_model.py`: emit structure snapshot v2.
- `skills/001short-production-agent/scripts/validate_capcut_project.py`: validate v2 snapshot authority and fail closed on v1 migration.
- `skills/001short-production-agent/scripts/validate_capcut_grids.py`: apply 2 lines x 10 characters only to target-grid `A9_TEXT` values.
- `skills/001short-production-agent/scripts/validate_executable_protocol.py`: self-check NORMAL_FAST, single-owner, validator retention, five-field beats, Stage 03 writer, root-clone safety, and final stop state.
- `skills/001short-production-agent/tests/test_parallel_contract.py`: RED/GREEN assertions for default single-owner and disabled worker fanout.
- `skills/001short-production-agent/tests/test_executable_protocol.py`: RED/GREEN machine-contract assertions.
- `skills/001short-production-agent/tests/test_capcut_grid_harness.py`: RED/GREEN target-only A9 2x10 cases.
- `skills/001short-production-agent/tests/test_original_capcut_grid_contract.py`: RED/GREEN five-field `Bxx` contract cases.
- `skills/001short-production-agent/tests/test_v2_release_contract.py`: root ZIP/source-authority/working-clone and terminal-state regression checks.
- `skills/001short-production-agent/tests/test_validate_stage_router.py`: Stage 02 grid lock, Bxx parity, mutation, and snapshot migration routing tests.

### Delete

- `skills/001short-production-agent/steps/04-external-review.md`.
- `skills/001short-production-agent/references/stage04-external-review-contract.md`.

## Implementation order

### 1. RED: execution profile and legacy routing

- Add tests asserting `NORMAL_FAST` is default, owner count is one, Stage 01-04 are sequential, fanout is disabled, and no normal route references external review.
- Run only the named tests and confirm failure against `088daf2`.

### 2. GREEN: machine contract and workflow

- Add the required protocol/schema fields.
- Replace the workflow's default parallel coordinator/fanout block with the NORMAL_FAST single-owner contract.
- Keep stage validators and `update_state_after_pass_only=true`.
- Run the same tests and confirm PASS.

### 3. RED/GREEN: source beat and Stage 03 author

- Add assertions for the five required `Bxx` fields and one Stage 03 writer.
- Update source-structure references and Stage 01-03 documents.
- Confirm Stage 02 original artifacts are read-only inputs to Stage 03.

### 4. RED/GREEN: target-only A9 text

- Add one passing urakkai case with two lines of at most 10 characters.
- Add one failing urakkai case with an 11-character line.
- Add an original-grid case proving the target-only limit is not applied to source A9 text.
- Update the grid validator and protocol values; run only grid tests.

### 5. Root-template and build-safety regression

- Assert the canonical v2 root contract, immutable extracted source, separate working copy, new IDs, material/audio/caption/mirror checks, and `WAIT_USER_CAPCUT_CHECK` terminal state.
- Do not modify the root template or weaken builder safeguards.

### 6. Remove external-review legacy

- Remove the two legacy files.
- Remove all live references to external-review stages or external AI review loops.
- Preserve user approval at Stage 04.

### 7. Verification

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
python -B -m unittest skills.001short-production-agent.tests.test_parallel_contract
python -B -m unittest skills.001short-production-agent.tests.test_executable_protocol
python -B -m unittest skills.001short-production-agent.tests.test_capcut_grid_harness
python -B -m unittest skills.001short-production-agent.tests.test_original_capcut_grid_contract
python -B -m unittest skills.001short-production-agent.tests.test_v2_release_contract
python -B skills/001short-production-agent/scripts/validate_executable_protocol.py --self-check
```

If module-name discovery is incompatible with the hyphenated folder, run the same five files through `python -B -m unittest discover -s skills/001short-production-agent/tests -p "test_*.py"` and report that broader test count separately.

### 8. Independent read-only review

Review the final diff against this Work Order. The reviewer must not edit. Any finding returns to the same task-owner for a minimal fix and targeted re-test.

## Stop conditions

- Stop at the first same-file overlap with the preserved unfinished patch.
- Stop on a required builder/validator weakening.
- Stop after two failed fixes for the same root cause.
- Stop before commit, push, publish, activation, runtime relink, render, or upload unless separately approved.

## Required final report

```text
result:
changed files:
commands run:
validation:
expected result:
actual result:
failed checks:
remaining risks:
rollback point:
next action:
```
