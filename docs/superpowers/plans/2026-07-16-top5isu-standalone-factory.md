# top5isu Standalone Factory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `top5isu-shorts` the single self-contained user-facing and runtime skill for TOP5 and 군림보 work, from intake and script design through assets, audio, CapCut project validation, and reporting, without routing to `00-tikitaka` or `000short-production-agent`.

**Architecture:** Keep one installed skill and split responsibilities into focused references and scripts. `SKILL.md` is the only entry router; `top5` and `gunlimbo` remain internal profiles. A new episode scaffold script creates the fixed production folder contract, and standalone validators enforce blueprint, track, package, draft, and final-gate requirements.

**Tech Stack:** Markdown skill contracts, Python 3 standard library, unittest, existing repository installer.

---

### Task 1: Lock the standalone contract with failing tests

**Files:**
- Modify: `tests/test_top5isu_shorts_contract.py`
- Create: `tests/test_top5isu_standalone_factory.py`

- [ ] Add assertions that `SKILL.md` contains `standalone_factory=true`, owns `INTAKE`, `SCRIPT_DESIGN`, `AUDIO_ASSETS`, `CAPCUT_PROJECT`, and `FINAL_REPORT`, and does not route to either external skill.
- [ ] Add assertions for required internal references and scripts.
- [ ] Add executable tests for profile routing and fixed episode directories.
- [ ] Run `python3 tests/test_top5isu_shorts_contract.py -v` and `python3 tests/test_top5isu_standalone_factory.py -v`; verify failure because the standalone files and tokens do not exist.

### Task 2: Implement the single-entry skill contract

**Files:**
- Rewrite: `skills/top5isu-shorts/SKILL.md`
- Modify: `skills/top5isu-shorts/agents/openai.yaml`
- Create: `skills/top5isu-shorts/references/script-contract.md`
- Create: `skills/top5isu-shorts/references/production-contract.md`
- Create: `skills/top5isu-shorts/references/report-contract.md`

- [ ] Define only two internal profiles: `top5` and `gunlimbo`.
- [ ] Define one user command: `$top5isu-shorts <TOP5|군림보> <request>`.
- [ ] Forbid external skill routing and generic `shrt white` fallback.
- [ ] Lock the lifecycle `INTAKE -> SCRIPT_DESIGN -> AUDIO_ASSETS -> CAPCUT_PROJECT -> FINAL_REPORT`.
- [ ] Preserve approval, audio, visual playback, export, and upload safety gates.

### Task 3: Add the standalone episode scaffold and validators

**Files:**
- Create: `skills/top5isu-shorts/scripts/create_top5isu_episode.py`
- Create: `skills/top5isu-shorts/scripts/validate_top5isu_blueprint.py`
- Create: `skills/top5isu-shorts/scripts/validate_top5isu_track_mapping.py`
- Create: `skills/top5isu-shorts/schemas/top5isu-episode-state.schema.json`

- [ ] Implement `route_profile()` for explicit TOP5/ranking and 군림보/story requests; reject ambiguous requests.
- [ ] Implement `create_episode()` creating `00_source`, `10_analysis`, `20_script`, `30_audio`, `40_assets`, `50_capcut_project`, and `90_reports` plus `top5isu_episode_state.json`.
- [ ] Implement blueprint validation for required sections and selected profile.
- [ ] Move/copy the top5isu track-mapping validator into this skill so runtime validation has no external skill path.
- [ ] Run the new standalone test and verify PASS.

### Task 4: Update old contracts and run regression tests

**Files:**
- Modify: `skills/top5isu-shorts/references/handoff-contract.md`
- Modify: `tests/test_000short_top5isu_track_mapping.py`
- Modify: `tests/test_top5isu_shorts_contract.py`

- [ ] Replace cross-skill ownership language with internal-stage ownership.
- [ ] Point track mapping tests to `skills/top5isu-shorts/scripts/validate_top5isu_track_mapping.py`.
- [ ] Run the three original focused test files and the new standalone test.
- [ ] Run `python3 -m unittest discover -s tests -p 'test_*top5isu*.py' -v`.

### Task 5: Install only the standalone skill and verify three runtimes

**Files:**
- Runtime targets only; no source edits.

- [ ] Run `bash scripts/install.sh --target all --only top5isu-shorts`.
- [ ] Confirm `SKILL.md` exists in Codex, Claude, and Hermes paths.
- [ ] Confirm Codex prompt input exposes `top5isu-shorts`.
- [ ] Confirm Claude `/top5isu-shorts` resolves.
- [ ] Confirm Hermes `skills_list(category='22utube')` exposes `top5isu-shorts`.
- [ ] Report that the original dirty `~/agent-skills` repository was not modified.
