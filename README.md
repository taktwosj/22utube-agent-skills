# 22utube Agent Skills

Git source of truth for 22utube/11utube agent and video-production skills.

## Roles

- Git repo: official skill source under `skills/<skill>`.
- Codex runtime: copy installed to `$HOME/.codex/skills`.
- Claude runtime: copy installed to `$HOME/.claude/skills`.
- Hermes runtime: copy installed to `%LOCALAPPDATA%/Hermes/skills/22utube` on Windows and `$HOME/.hermes/skills/22utube` on macOS/default Unix hosts.
- OneDrive: production data only, including video sources, evidence, renders, CapCut drafts, and upload copy.

Runtime folders are install targets, not edit targets. Edit skills in this repo, then run install/update/verify.

## Managed Skill Set

Core production skills:

```text
000brainstorm
00-tikitaka
000short-production-agent
00script-writer
00utube-lm-production-agent
0shrt-korea-production-agent
111-politics-longform
```

Conditional and support production skills:

```text
11short-gemini-remake-factory
11short-reple-agent
22utube-production-agent
josun-historychoon-production-agent
humanize-korean
watch
skil-down
```

`manifests/skill-set.json` is the authoritative install list.
`manifests/capcut-template-set.json` records CapCut template identities and
verification requirements. The CapCut draft bundles themselves stay in
OneDrive/CapCut storage, not in Git.

## First Install

Windows:

```powershell
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME\agent-skills"
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\install.ps1" -Target all
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target all
```

macOS:

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
bash "$HOME/agent-skills/scripts/install.sh" --target all
bash "$HOME/agent-skills/scripts/verify.sh" --target all
```

## Update

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune
```

macOS:

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune
```

## Strict Claude Match

Claude CLI should not keep old 22utube production skills beside the Git-managed
set. Use strict mode to make Claude's runtime match `manifests/skill-set.json`
exactly:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target claude -Prune -Strict
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target claude -Strict
```

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target claude --prune --strict
bash "$HOME/agent-skills/scripts/verify.sh" --target claude --strict
```

Strict mode moves unmanaged skill folders with `SKILL.md` into the configured
backup folder as `DISABLED_<skill>_<timestamp>`. It does not delete them.

Use dry-run before prune:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune -DryRun
```

```bash
bash "$HOME/agent-skills/scripts/update.sh" --target all --prune --dry-run
```

## Safety Rules

- Copy install only; symlink install is not supported.
- `update` refuses dirty worktrees.
- `git pull` uses `--ff-only`.
- Automatic stash is not supported.
- `--only` and `--prune` cannot be combined.
- `--only` and strict mode cannot be combined.
- Prune removes only folders with a managed marker file.
- Strict mode disables any unmanaged skill folder under the selected target.
- Existing runtime folders are backed up before overwrite.
- `verify` failure makes update fail.

## Verification Status

See `docs/verification-status.md` for the current evidence checklist and the
minimum live check required on another Windows PC or the Mac mini.

## Current Reports And Handoff

- `docs/work-report-2026-06-29-draft-fast-final-lock.md`: latest cleanup report
  for DRAFT_FAST / FINAL_LOCK, Korean text gate, and CapCut report rules.
- `docs/git-down-guide.md`: copy-paste update guide for office Windows and Mac
  mini.

## Telegram Hermes

Telegram-Hermes integration is an allowlisted command bridge. Bot tokens, chat IDs, and auth files stay outside Git. See `docs/install-telegram-hermes.md` and `manifests/telegram-hermes.commands.json`.
