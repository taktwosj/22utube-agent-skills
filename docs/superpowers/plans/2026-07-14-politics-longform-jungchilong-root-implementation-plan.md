# Politics Longform Jungchilong Root Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore `jungchilong` as the single fail-closed Stage 2 CapCut root and synchronize the verified skill to Codex and Claude.

**Architecture:** Keep the existing monolithic operating contract but replace YP007/YP005 base selection and YP007-specific track assumptions with a role-based `jungchilong` contract. Restore only the deterministic clean-base scanner and validator needed to enforce that contract. Lock the behavior with focused Python tests.

**Tech Stack:** Markdown skill contract, Python 3 standard library, `unittest`, PowerShell runtime installer/verifier, Git/GitHub.

## Global Constraints

- `jungchilong` is the only default/root Stage 2 CapCut project.
- Never modify the root project in place; copy it to a new episode draft.
- Never automatically fall back to YP007, YP005, YM007, YSM, or generated derivatives.
- Preserve Stage 1/Stage 2 boundaries and T1-T5 text roles.
- Git is the source of truth; Codex and Claude are copy-installed runtimes.
- Do not stage or alter unrelated Shorts changes in the primary checkout.
- Do not use subagents for this execution.

---

### Task 1: Lock the base contract with failing tests

**Files:**
- Create: `tests/test_politics_longform_jungchilong_base_contract.py`
- Test: `tests/test_politics_longform_jungchilong_base_contract.py`

**Interfaces:**
- Consumes: `skills/111-politics-longform/SKILL.md` and the future `scripts/validate_clean_base.py`.
- Produces: Assertions for the single-base contract, forbidden fallback wording, stop codes, and clean-base behavior.

- [ ] Write tests requiring `jungchilong`, rejecting YP007/YP005 automatic fallback, and exercising missing/dirty/clean fixtures.
- [ ] Run `python -m unittest tests.test_politics_longform_jungchilong_base_contract -v`.
- [ ] Confirm RED because the current skill names YP007 as default and the validator script is absent.

### Task 2: Implement the minimal skill and validator change

**Files:**
- Modify: `skills/111-politics-longform/SKILL.md`
- Create: `skills/111-politics-longform/scripts/scan_forbidden_capcut_refs.py`
- Create: `skills/111-politics-longform/scripts/validate_clean_base.py`
- Test: `tests/test_politics_longform_jungchilong_base_contract.py`

**Interfaces:**
- Consumes: the failing assertions from Task 1.
- Produces: `validate_base(base: pathlib.Path) -> dict`, `scan_tree(root: pathlib.Path) -> dict`, and the `jungchilong` Stage 2 contract.

- [ ] Replace base priority and YP007-only layout assumptions with `jungchilong` single-root and role detection.
- [ ] Restore the two standard-library validation scripts.
- [ ] Run the focused test and confirm GREEN.
- [ ] Run `tests.test_politics_longform_embedded_contract` and confirm its six existing tests remain green.

### Task 3: Validate, synchronize, and publish

**Files:**
- Verify: `skills/111-politics-longform/**`
- Verify: `manifests/skill-set.json`
- Install targets: `$HOME\.codex\skills\111-politics-longform`, `$HOME\.claude\skills\111-politics-longform`

**Interfaces:**
- Consumes: the tested Git skill folder.
- Produces: matching Git/Codex/Claude file trees and a published Git branch.

- [ ] Run the focused tests and repository verification.
- [ ] Scan for unresolved YP007/YP005 default/fallback wording and placeholders.
- [ ] Commit only the skill, focused test, design, and plan files.
- [ ] Install only `111-politics-longform` into Codex and Claude using repository scripts.
- [ ] Run Codex and Claude verification and compare SHA-256 for all managed skill files.
- [ ] Push `agent/politics-jungchilong-root` and open a Draft PR.

## Self-Review

- Spec coverage: single root, no fallback, copy-only, stop codes, validation, runtime synchronization, and publication are mapped to Tasks 1-3.
- Placeholder scan: no TBD/TODO/implementation-later markers are present.
- Type consistency: tests and scripts use `validate_base(Path) -> dict` and `scan_tree(Path) -> dict` consistently.
- Scope: Stage boundaries and T1-T5 remain unchanged; unrelated historical utilities are excluded.

## Execution Choice

Use Inline Execution in this isolated worktree. Subagents are prohibited by the active developer instruction.
