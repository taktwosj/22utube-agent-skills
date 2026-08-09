# Verified Runtime Release Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore immutable local release deployment on `main` and reconcile only stale prior-release junctions when a committed manifest removes a shared skill.

**Architecture:** Add the reviewed stdlib release publisher to `main`. Its activation transaction stages the new immutable release locally, links all enabled skills for Codex, Claude, and Hermes, then moves only managed junctions pointing at the prior active release but absent from the new manifest into the existing backup root. Rollback restores every changed link if an install or stale-link step fails.

**Tech Stack:** Python standard library, `unittest`, Windows junctions, existing `manifests/skill-set.json` and `manifests/targets.json`.

## Global Constraints

- Never use `scripts/update.ps1` or direct copies for verified release activation.
- Treat the release source as a clean committed Git worktree.
- Reconcile only a stale junction resolving inside the immediately prior immutable release; preserve unmanaged folders.
- Move, never delete, a reconciled stale link into the target backup root.
- Verify all three target layouts and run self-checks after activation.

---

### Task 1: Add the release publisher and its regression coverage

**Files:**
- Create: `scripts/skill_release.py`
- Create: `tests/test_verified_skill_release.py`

**Interfaces:**
- Produces `publish`, `activate`, and `verify` subcommands.
- `publish` creates `release_root/releases/<HEAD>` and atomically updates `release_root/active.json`.
- `activate --target all` consumes that active release and creates target junctions.

- [ ] **Step 1: Write the failing compatibility test**

```python
def test_main_manifest_preflight_accepts_six_enabled_shared_skills(self):
    skills, targets = skill_release.enabled_skills(REPO_ROOT)
    skill_release.semantic_preflight(skills, targets)
    self.assertEqual([item["name"] for item in skills], EXPECTED_SHARED_SKILLS)
```

- [ ] **Step 2: Run test to verify it fails because the module is absent**

Run: `python -B -m unittest tests.test_verified_skill_release.ReleasePreflightTests.test_main_manifest_preflight_accepts_six_enabled_shared_skills -v`

Expected: import failure for `scripts.skill_release`.

- [ ] **Step 3: Copy the reviewed stdlib-only publisher and its regression tests from commit `e1bc8c870cd0f153d45019781851aea72ca674de`**

```powershell
git checkout e1bc8c870cd0f153d45019781851aea72ca674de -- scripts/skill_release.py tests/test_verified_skill_release.py
```

- [ ] **Step 4: Run compatibility and imported release tests**

Run: `python -B -m unittest tests.test_verified_skill_release -v`

Expected: all imported tests pass before stale-link behavior is added.

### Task 2: Reconcile removed managed junctions transactionally

**Files:**
- Modify: `scripts/skill_release.py`
- Modify: `tests/test_verified_skill_release.py`

**Interfaces:**
- Add a helper that receives previous/new release manifests, selected targets, and link plans.
- It returns reversible backup changes only for destinations omitted from the new manifest whose resolved junction source is inside the previous active release.

- [ ] **Step 1: Write failing stale-link tests**

```python
def test_activate_moves_only_prior_release_junction_omitted_by_new_manifest(self):
    # Prior release contains 110; new release omits it; target link resolves to prior release.
    # Assert target 110 link is moved to backup and is absent after activation.

def test_activate_preserves_unmanaged_directory_omitted_by_new_manifest(self):
    # An ordinary local folder named like an omitted skill must not be moved.
```

- [ ] **Step 2: Run the two tests and confirm they fail because stale links remain**

Run: `python -B -m unittest tests.test_verified_skill_release.ReleaseActivationTests.test_activate_moves_only_prior_release_junction_omitted_by_new_manifest tests.test_verified_skill_release.ReleaseActivationTests.test_activate_preserves_unmanaged_directory_omitted_by_new_manifest -v`

Expected: the stale managed link is still present; unmanaged preservation baseline remains explicit.

- [ ] **Step 3: Implement minimal stale-link planning and rollback**

```python
if omitted_name not in expected_names and paths_equal(destination, prior_release / "skills" / omitted_name):
    changes.append(backup_existing(destination, backup_root, omitted_name))
```

Integrate the reversible backup change into the same activation `try/except` transaction used for new links. Do not scan or move a directory unless it resolves to the immediately prior release.

- [ ] **Step 4: Re-run stale-link tests and all release tests**

Run: `python -B -m unittest tests.test_verified_skill_release -v`

Expected: stale prior-release link is backed up; unmanaged folder is untouched; all tests pass.

### Task 3: Verify scope and publish readiness

**Files:**
- Modify: `docs/superpowers/specs/2026-08-09-verified-runtime-release-reconciliation-design.md`
- Modify: `docs/superpowers/plans/2026-08-09-verified-runtime-release-reconciliation.md`

- [ ] **Step 1: Run source preflight against `manifests/skill-set.json`**

Run: `python -B scripts/skill_release.py publish --dry-run`

Expected: clean committed source is required and exactly six shared skills are selected.

- [ ] **Step 2: Check only intended paths changed**

Run: `git diff --check origin/main...HEAD` and `git diff --name-only origin/main...HEAD`

Expected: release script, its test, and these two reviewed design records only.

- [ ] **Step 3: Commit the verified source patch**

```powershell
git add scripts/skill_release.py tests/test_verified_skill_release.py docs/superpowers/specs/2026-08-09-verified-runtime-release-reconciliation-design.md docs/superpowers/plans/2026-08-09-verified-runtime-release-reconciliation.md
git commit -m "feat(skills): restore verified runtime release activation"
```

- [ ] **Step 4: Obtain independent read-only review before merge**

Review stale-link selection, rollback, manifest scope, focused tests, and diff scope. Merge only after review has no blocking findings.
