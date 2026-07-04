---
name: skil-down
description: Install or update 22utube/11utube agent skills from the Git source repo into the current machine's runtime skill folders. Use when the user says $skil down, $skill down, 스킬 다운, 맥미니 스킬 받기, skill download, install agent skills, update agent-skills, or refresh Codex/Claude/Hermes skills on macOS or Windows.
---

# Skil Down

Use this skill to install or refresh 22utube/11utube agent skills from the Git source repo into the current machine's local runtime skill folders.

## Source And Target

- Source of truth: `$HOME/agent-skills/skills`
- Codex runtime target: `$HOME/.codex/skills`
- Claude runtime target: `$HOME/.claude/skills`
- Hermes runtime target on Windows: `%LOCALAPPDATA%\Hermes\skills\22utube`
- Hermes runtime target on macOS/default Unix: `$HOME/.hermes/skills/22utube`
- Backup targets: the target-specific backup folders from `manifests/targets.json`
- Only sync folders that contain `SKILL.md`
- Do not edit runtime folders directly. Edit `$HOME/agent-skills/skills/<skill>` and run install/update/verify.

## OS Rule

Use the Python command and path style for the machine that is running the command:

```text
Windows: py -3
macOS / Mac mini: python3
```

Common source locations:

```text
Windows: $HOME\agent-skills\skills
macOS / Mac mini: $HOME/agent-skills/skills
Legacy OneDrive cache: $env:UTUBE_ROOT\codex_skills_source
```

If an operational document shows `py -3`, use `python3` on the Mac mini. If it shows `python3`, use `py -3` on this Windows PC.

## First Install On Mac Mini

If the Mac mini does not have this skill yet, clone the Git repo and run the repo installer:

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
bash "$HOME/agent-skills/scripts/install.sh" --target all
bash "$HOME/agent-skills/scripts/verify.sh" --target all
```

If the repo already exists, update it:

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune --dry-run
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune
```

After the first install, start a new Codex chat and invoke `$skil down` for future updates.

## Normal Update Workflow

1. Identify the current OS.
2. Resolve the Git source folder. Prefer `$HOME/agent-skills`.
3. Sync skills into the selected local runtime folder.
4. Report the source, target, synced skill names, and backup location.
5. Tell the user to restart the target agent or open a new chat if newly installed skills do not appear immediately.

## Multi-Machine Sync With Local Commits Or Edits

When syncing Mac mini, home Windows, and office Windows after one machine pushed skill changes, do not blindly run pull/install if another machine reports local ahead commits or uncommitted skill edits.

Required sequence:

1. On every machine, start with `git status --short --branch`, local short HEAD, and remote branch HEAD.
2. If the working tree is dirty, inspect and preserve meaningful skill edits. Do not `reset --hard`, `git restore`, or stash-and-forget unless the user explicitly says to discard them.
3. If a machine is ahead and also has important uncommitted edits, commit the local edit first, then `git fetch origin` and rebase onto the remote branch. Resolve conflicts by preserving both the remote split-skill changes and the local safety/contract additions.
4. Push from that integrating machine only after `git diff --check`, repo verify, unittest, install all, and verify all pass.
5. Other machines then fast-forward pull the final remote HEAD, run install/update with prune, and verify all runtime targets.
6. Completion requires local/remote parity and runtime source=target SHA256 parity for Codex, Claude, and Hermes.

Use concrete required-content checks for important contract additions before declaring PASS, for example `07_DRAFT_FAST_REPORT_CONTRACT.md` routing or `Mandatory CapCut Media Settings — HARNESS LOCK` tokens when those were part of the sync.

Preferred existing scripts:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune -DryRun
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune
```

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune --dry-run
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune
```

Bundled cross-platform fallback:

```powershell
py -3 $HOME\.codex\skills\skil-down\scripts\skil_down.py --source "$HOME\agent-skills\skills"
```

```bash
python3 ~/.codex/skills/skil-down/scripts/skil_down.py --source $HOME/agent-skills/skills
```

To sync only selected skills:

```bash
python3 ~/.codex/skills/skil-down/scripts/skil_down.py --source $HOME/agent-skills/skills --skill 000short-production-agent --skill 000brainstorm
```

## Safety Rules

- Stop if the source folder cannot be found or contains no child skill folders with `SKILL.md`.
- Stop if source and target resolve to the same folder, or if copying would place a skill inside itself.
- Back up any existing local skill folder before overwriting it.
- Do not delete backups.
- Do not sync `.system`, built-in library skills, or random project folders unless they are explicitly present as child skill folders under the Git source.
- Do not continue production work in the same response after installing skills unless the user explicitly asked for both.

## Expected Report

Keep the result short:

```text
skil-down complete
- source: ...
- target: ...
- synced: ...
- backups: ...
- next: restart Codex/open a new chat if the skill list is stale
```
