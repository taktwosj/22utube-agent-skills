# 22utube Agent Skills v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local `22utube-agent-skills` Git repo and install/update/verify scripts for Codex, Claude, and Hermes, covering the active 22utube agent stack plus HyperFrames/video-production support skills.

**Architecture:** `skills/` is the only editable source. `install` copies enabled skills to target runtimes and writes managed markers. `update` performs a dirty-check, optional fast-forward pull, install, and verify. `verify` enforces repo and target rules.

**Tech Stack:** PowerShell for Windows, Bash plus Python 3 for macOS, Git, JSON manifests.

---

### Task 1: Scaffold Repository

**Files:**
- Create: `manifests/skill-set.json`
- Create: `manifests/targets.json`
- Create: `manifests/machines.example.json`
- Create: `README.md`
- Create: `.gitignore`
- Create: `docs/*.md`

- [x] Create the repo structure under `$HOME/agent-skills`.
- [x] Initialize Git.
- [x] Copy active skills from OneDrive legacy source into `skills/`.

### Task 2: Implement Scripts

**Files:**
- Create: `scripts/install.ps1`
- Create: `scripts/verify.ps1`
- Create: `scripts/update.ps1`
- Create: `scripts/install.sh`
- Create: `scripts/verify.sh`
- Create: `scripts/update.sh`

- [x] Implement copy-only install with backups and markers.
- [x] Implement repo/target verification.
- [x] Implement dirty-check, `git pull --ff-only`, install, and verify update flow.

### Task 3: Clean Migrated Skills

**Files:**
- Modify: `skills/*`

- [x] Remove backup/runtime garbage from copied skills.
- [x] Replace machine-specific user paths in skills with environment-variable based references.
- [x] Confirm `scripts/` and `skills/` contain no blocked user-home absolute paths.

### Task 4: Verify

**Files:**
- Test: `scripts/verify.ps1`
- Test: `scripts/install.ps1`

- [x] Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -Target repo`.
- [x] Run `powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -Target all -DryRun`.
- [x] Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -Target all` only after install.
