# P07 Politics G00-G90 Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route `111-politics-longform` through its own deterministic G00-G90 lane without importing or transferring authority to either general Shorts skill.

**Architecture:** Add a lane-local workflow contract, gate references, JSON schemas, validator, and runner. Reuse only the generated shared workflow core; preserve the existing politics two-pass and corrected-SRT validators as authoritative evidence providers.

**Tech Stack:** Python 3 standard library, JSON Schema documents, YAML configuration, `unittest`.

## Global Constraints

- Work only in `C:/Users/arajun/worktrees/agent-skills-shared-gates-v2`.
- Preserve approved HEAD `f98f7cc098a55dc945d6601117647af8f4e804dc`.
- Do not deploy runtimes, push, merge, edit CapCut, or call external/paid services.
- `content_profile` is locked at G00 to `politics_longform` or `politics_derived_short`.
- `production_mode` is locked at G00 to `source_led` or `narrated`.
- Main longform uses `jungchilong_base_v3_intro15`; derived Shorts use `SHRTJUNGCHI`.
- Static G60 PASS transitions to `WAIT_USER_VISUAL_GATE`; it never grants visual PASS.
- Runner automation is deterministic-only, with zero automatic retries.

---

### Task 1: Behavioral contract tests

**Files:**
- Create: `tests/test_politics_shared_gate_router.py`

**Interfaces:**
- Consumes: existing generated core and existing politics review/SRT validators.
- Produces: executable P07 acceptance tests for ownership, locks, audio modes, corrected-SRT authority, roots, release policy, and runner safety.

- [ ] Write file-presence, routing, and validator behavior tests.
- [ ] Run `python -B -m unittest -v tests.test_politics_shared_gate_router`.
- [ ] Confirm RED is caused by missing P07 files and functions.

### Task 2: Lane contract and schemas

**Files:**
- Create: `skills/111-politics-longform/workflow.yaml`
- Create: `skills/111-politics-longform/references/gates/G00_INTAKE.md`
- Create: `skills/111-politics-longform/references/gates/G10_DESIGN.md`
- Create: `skills/111-politics-longform/references/gates/G20_MANUAL_DIALOGUE_TWO_PASS.md`
- Create: `skills/111-politics-longform/references/gates/G30_AUDIO.md`
- Create: `skills/111-politics-longform/references/gates/G40_CAPTION_SRT.md`
- Create: `skills/111-politics-longform/references/gates/G50_TRACK_PLAN.md`
- Create: `skills/111-politics-longform/references/gates/G60_CLEAN_ASSEMBLY.md`
- Create: `skills/111-politics-longform/references/gates/G70_UPLOAD_PACKAGE.md`
- Create: `skills/111-politics-longform/references/gates/G80_RENDER.md`
- Create: `skills/111-politics-longform/references/gates/G90_FINAL_QC.md`
- Create: `skills/111-politics-longform/schemas/politics_editorial_lock.schema.json`
- Create: `skills/111-politics-longform/schemas/politics_audio_lock.schema.json`
- Create: `skills/111-politics-longform/schemas/politics_caption_lock.schema.json`
- Create: `skills/111-politics-longform/schemas/politics_track_plan.schema.json`
- Create: `skills/111-politics-longform/schemas/politics_assembly_contract.schema.json`

**Interfaces:**
- Produces: exact gate ownership/configuration and lane-local artifact contracts consumed by the validator.

- [ ] Add the minimal workflow and gate contracts required by the approved design.
- [ ] Add strict lane-local schemas with required lock fields and `additionalProperties`.
- [ ] Run the P07 tests and keep remaining failures limited to missing validator/runner behavior.

### Task 3: Deterministic validator and runner

**Files:**
- Create: `skills/111-politics-longform/scripts/validate_stage_gate.py`
- Create: `skills/111-politics-longform/scripts/workflow_runner.py`

**Interfaces:**
- Validator produces `gate-result-v1` through `_generated/workflow_harness_core.py`.
- Runner consumes a validator result and emits a deterministic action decision without executing the next gate.

- [ ] Implement G00/G10 locks and G20 manual two-pass evidence validation.
- [ ] Implement production-mode-aware G30 and corrected-SRT-aware G40.
- [ ] Implement G50 root/role locks, G60 clean assembly and user visual separation.
- [ ] Implement G70 release false, G80 render evidence, and ordered G90 manual release events.
- [ ] Implement CLI JSON input and fail-closed parsing.
- [ ] Implement runner rejection of LLM, paid, upload, GUI, retry, and non-deterministic actions.
- [ ] Run the P07 tests until GREEN.

### Task 4: Router integration and verification

**Files:**
- Modify: `skills/111-politics-longform/SKILL.md`

**Interfaces:**
- Produces: a discoverable route from the skill entrypoint to the new workflow and current-gate references.

- [ ] Add a compact P07 routing section without deleting legacy contracts.
- [ ] Run all politics tests and cross-lane router tests.
- [ ] Run the full repository suite.
- [ ] Run shared-core verification, `git diff --check`, and managed bytecode checks.
- [ ] Commit only P07 scope with `feat: route politics through separated G00-G90 lane`.

