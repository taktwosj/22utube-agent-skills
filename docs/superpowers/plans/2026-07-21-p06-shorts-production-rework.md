# P06 Shorts Production Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the P06 G30-G90 Shorts production router fail closed against real files, canonical hashes, template locks, user ledger events, and validator-runner integration.

**Architecture:** Keep `validate_stage_gate.py` as the lane adapter and use the generated shared core only for canonical gate-result construction, ledger-chain validation, and state projection. Validate every P06 input at the adapter boundary, recompute hashes from files, run `ffprobe` for media duration/streams, and compare creative/template locks structurally instead of trusting booleans.

**Tech Stack:** Python 3 standard library, `unittest`, `ffprobe`, JSON/JSONL, generated shared workflow core.

## Global Constraints

- Work only in `C:/Users/arajun/worktrees/agent-skills-shared-gates-v2`.
- Do not start P07.
- Do not deploy Codex, Claude, or Hermes runtimes.
- Do not push or merge.
- Do not mutate local CapCut drafts.
- Every production-code change follows RED, GREEN, then full regression verification.

---

### Task 1: Generated-core schema isolation

**Files:**
- Modify: `shared/workflow-harness/core/gate_validation.py`
- Modify: `shared/workflow-harness/core/context_manifest.py`
- Regenerate: `skills/00-tikitaka/scripts/_generated/workflow_harness_core.py`
- Regenerate: `skills/000short-production-agent/scripts/_generated/workflow_harness_core.py`
- Regenerate: `skills/111-politics-longform/scripts/_generated/workflow_harness_core.py`
- Test: `tests/test_generated_core_compile_and_entrypoints.py`
- Test: `tests/test_short_production_shared_gate_router.py`

**Interfaces:**
- Consumes: `validate_gate(...) -> dict`
- Produces: validator results with exact `schema_version="gate-result-v1"` after bundle generation.

- [ ] Add a failing integration test that calls P06 validator output through `workflow_runner.apply_validator_result`.
- [ ] Run `python -B -m unittest -v tests.test_short_production_shared_gate_router` and confirm `INVALID_VALIDATOR_RESULT_SHAPE`.
- [ ] Rename module globals to `GATE_RESULT_SCHEMA_VERSION` and `CONTEXT_MANIFEST_SCHEMA_VERSION`.
- [ ] Run `python -B scripts/sync_shared_workflow_harness.py`.
- [ ] Re-run the focused test and confirm the runner accepts the gate-result shape.

### Task 2: G30-G50 artifact and creative locks

**Files:**
- Modify: `skills/000short-production-agent/scripts/validate_stage_gate.py`
- Modify: `skills/000short-production-agent/schemas/shorts_audio_lock.schema.json`
- Modify: `skills/000short-production-agent/schemas/shorts_caption_lock.schema.json`
- Modify: `skills/000short-production-agent/schemas/shorts_track_plan.schema.json`
- Test: `tests/test_short_production_shared_gate_router.py`

**Interfaces:**
- Consumes: owner-transfer receipt path, design-handoff path, G30 audio-lock path, G40 caption-lock path, media/SRT files.
- Produces: `validate_g30`, `validate_g40`, and `validate_g50` results that contain `gate-result-v1` and fail closed on missing or mismatched authority.

- [ ] Add failing tests for missing receipt, missing canonical SHA, wrong file SHA, no-TTS without measured source duration, fabricated evidence, empty G40 lock, failed G40 input, wrong upstream lock SHA, and changed creative fields.
- [ ] Run the focused test and confirm each new case fails for the expected old behavior.
- [ ] Add strict JSON-object contract validation, file resolution, SHA-256 recomputation, `ffprobe` duration probing, SRT/cue verification, and exact upstream-lock hash checks.
- [ ] Compare G50 `segments` against canonical design-handoff timeline rows for hook, urakkai/timeline order, caption role, production profile, and editorial fields.
- [ ] Re-run focused tests until all G30-G50 cases pass.

### Task 3: G60-G90 template, visual, render, and release gates

**Files:**
- Modify: `skills/000short-production-agent/scripts/validate_stage_gate.py`
- Modify: `skills/000short-production-agent/scripts/workflow_runner.py`
- Modify: `skills/000short-production-agent/schemas/shorts_production_gate.schema.json`
- Test: `tests/test_short_production_shared_gate_router.py`

**Interfaces:**
- Consumes: G50 track-plan path, pinned `shrt_white_base_v1` contract, assembly slots, append-only ledger events, upload package, rendered media, and G90 events.
- Produces: implemented `G60.USER`, enforced `USER_VISUAL_PASS`, actual G80 media integrity, and G90 release only from ordered canonical ledger events.

- [ ] Add failing tests for empty G60 assembly, missing/wrong root, every protected template-lock drift, missing G50 hash binding, G60.USER missing user event, G70 without visual approval, fake G80 media, G80 without G70, G90 booleans without events, wrong actors/gates/order, and valid ordered release.
- [ ] Run the focused test and confirm expected RED failures.
- [ ] Require `capcut_root="shrt white"`, exact template-contract SHA, complete slot coverage, protected-field equality, internal white asset, and zero `Cache/onlineMaterial` references.
- [ ] Implement `validate_g60_user` and require a valid USER-owned `USER_VISUAL_PASS` ledger event before G70.
- [ ] Verify G70 artifacts while keeping `release_allowed=false`.
- [ ] Run `ffprobe` against the actual G80 render, verify size/hash/video/audio streams/duration tolerance, and keep G80 separate from release.
- [ ] Rebuild G90 state from a valid ledger chain and require VALIDATOR `FINAL_QC_PASS` followed by USER `UPLOAD_APPROVED` on G90.
- [ ] Re-run focused tests until all G60-G90 cases pass.

### Task 4: Full verification and re-review handoff

**Files:**
- Create: `C:/Users/arajun/Desktop/2026-07-21_codex_p06_rework_review_result_v1.json`

**Interfaces:**
- Consumes: final Git diff, focused test results, full repository suite, generated-core hash, and worktree status.
- Produces: a separate P06 re-review artifact with one of the authorized decisions.

- [ ] Run `python -B -m unittest -v tests.test_short_production_shared_gate_router`.
- [ ] Run `python -B -m unittest -v tests.test_shared_core_rework tests.test_generated_core_compile_and_entrypoints`.
- [ ] Run `python -B -m unittest discover -s tests -p "test_*.py"`.
- [ ] Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1 -Target repo`.
- [ ] Run `python -B scripts/verify_shared_workflow_harness.py`.
- [ ] Run `python -B scripts/sync_shared_workflow_harness.py --check-only`.
- [ ] Run `git diff --check b455c976a82c4ab9bb59cd672eec09e3cca36937..HEAD`.
- [ ] Confirm runtime deployments, pushes, merges, P07 changes, and CapCut mutations remain zero.
- [ ] Write and parse the re-review JSON, compute its SHA-256, and report the exact decision.
