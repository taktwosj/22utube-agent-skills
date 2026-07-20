# P08 Runner, Cost, Context, and Effects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce one fail-closed execution policy for deterministic runner actions, episode cost authorization, model-call context evidence, and reproducible lane-local effect selection.

**Architecture:** Add shared `runner_policy.py` and `effect_policy.py`, extend the existing shared cost/context modules, regenerate the three byte-identical shared cores, and keep each lane runner as a thin adapter with its own deterministic action allowlist. Effect assets stay lane-local and are selected only from an explicitly named versioned pool.

**Tech Stack:** Python 3 standard library, JSON, `unittest`.

## Global Constraints

- Base commit is `d492197c0f742ce10b0e72dbe12498f1b35f58fd`.
- Automatic external model calls, paid actions, CapCut GUI operations, retries, upload, and release remain forbidden.
- Unknown cost and budget overrun return STOP.
- A paid action requires a matching `COST_AUTHORIZED` event for the exact episode and action limit.
- Every model-call preparation writes a context manifest containing loaded and excluded files.
- `unrelated_lane_reads` must be zero.
- Effect selection seed is `episode_id + segment_id + preset_pool_version`.
- Politics defaults to `EXPLICIT_ONLY` or a conservative approved pool.
- Do not deploy runtimes, push, merge, edit CapCut, or call external/paid services.

---

### Task 1: RED tests

**Files:**
- Create: `tests/test_shared_gate_runner_cost_guard.py`
- Create: `tests/test_shared_gate_context_token_policy.py`

- [ ] Test deterministic-only runner decisions, zero retry, unknown cost, authorization scope, and budget overrun.
- [ ] Test manifest write-before-call, negative context, unrelated lane rejection, and seeded effect selection.
- [ ] Run both modules and confirm failures are caused by missing P08 APIs/assets.

### Task 2: Shared policy core

**Files:**
- Modify: `shared/workflow-harness/core/cost_guard.py`
- Modify: `shared/workflow-harness/core/context_manifest.py`
- Create: `shared/workflow-harness/core/runner_policy.py`
- Create: `shared/workflow-harness/core/effect_policy.py`
- Modify: `scripts/sync_shared_workflow_harness.py`

- [ ] Implement exact episode/action authorization and USD/character/token limits.
- [ ] Implement atomic context-manifest writing with fail-closed lane-read checks.
- [ ] Implement runner decisions with deterministic allowlists and manual waits.
- [ ] Implement versioned seeded effect selection and `EXPLICIT_ONLY`.
- [ ] Regenerate all three shared cores.

### Task 3: Lane assets and adapters

**Files:**
- Create: `skills/000short-production-agent/assets/effect_pools/shorts_comedy.json`
- Create: `skills/000short-production-agent/assets/effect_pools/shorts_emotion.json`
- Create: `skills/000short-production-agent/assets/effect_pools/shorts_tension.json`
- Create: `skills/111-politics-longform/assets/effect_pools/politics_neutral.json`
- Create: `skills/111-politics-longform/assets/effect_pools/politics_emphasis.json`
- Modify: `skills/00-tikitaka/scripts/workflow_runner.py`
- Modify: `skills/000short-production-agent/scripts/workflow_runner.py`
- Modify: `skills/111-politics-longform/scripts/workflow_runner.py`

- [ ] Add conservative, versioned, lane-local preset pools.
- [ ] Route all three runners through shared `decide_runner_action`.
- [ ] Preserve existing public runner functions and wait-state behavior.

### Task 4: Verification and commit

- [ ] Run both P08 test modules.
- [ ] Run runner, shared-core, Tikitaka, Shorts, and politics tests.
- [ ] Run the full repository suite and shared-core hash verifier.
- [ ] Run `git diff --check` and confirm zero managed bytecode.
- [ ] Commit P08 scope with `feat: add safe runner cost guard and context policy` while disabling the runtime auto-sync hook.

