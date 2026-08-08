# Verified Skill Release Guide

Use this procedure for Home Windows, Office Windows, and Mac mini. Runtime folders never link to the mutable Git checkout or OneDrive release store.

## 1. Publish Once From The Clean Authority

Run inside `<factory-root>/agent-skills` after the approved skill changes are committed and the worktree is clean.

```text
python -B scripts/skill_release.py publish --dry-run
python -B scripts/skill_release.py publish
```

On macOS, use `python3` when `python` is unavailable. Publish creates the sibling store below and updates its central pointer only after validation succeeds.

```text
<factory-root>/agent-skills-runtime/
  active.json
  releases/<full-git-commit>/
    manifest.json
    READY
    skills/<enabled-skill>/...
```

Wait for OneDrive to finish syncing `active.json` and the referenced immutable release before activating another machine.

## 2. Activate Each Machine

Run inside the synced `<factory-root>/agent-skills` checkout on Home Windows, Office Windows, and Mac mini.

```text
python -B scripts/skill_release.py activate --target all --dry-run
python -B scripts/skill_release.py activate --target all
python -B scripts/skill_release.py verify --target all
```

Activation validates the central release, copies it into the machine-local verified cache, validates the copy, backs up replaced per-skill runtime destinations, and links only manifest-owned skills. The local `active.json` changes after every requested runtime link passes readback.

Default local cache:

```text
Windows: %LOCALAPPDATA%/22utube/agent-skills-runtime
macOS:   ${XDG_CACHE_HOME:-$HOME/.cache}/22utube/agent-skills-runtime
```

Runtime destinations:

```text
Codex:  $HOME/.codex/skills/<skill>
Claude: $HOME/.claude/skills/<skill>
Hermes Windows: $LOCALAPPDATA/Hermes/skills/22utube/<skill>
Hermes macOS:   $HOME/.hermes/skills/22utube/<skill>
```

## 3. Pass Criteria

```text
PUBLISH PASS
ACTIVATE PASS
VERIFY PASS
```

`verify` must confirm the local active pointer, manifest SHA, every payload hash, `SKILL.md`, immutable seal, and every runtime link target. Add `--self-check` only when per-skill self-check execution is wanted.

Do not use `install.ps1`, `install.sh`, `update.ps1`, `update.sh`, or `link-managed-skill.ps1` for production activation. The direct link helper is restricted to explicitly guarded isolated development roots.
