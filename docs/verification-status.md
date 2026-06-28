# Verification Status

Current source of truth:

- Repo: `https://github.com/taktwosj/22utube-agent-skills.git`
- Local working repo: `$HOME/agent-skills`
- Skill source: `skills/<skill>`
- OneDrive role: production data and legacy cache only, not skill authority

## Verified On This Windows Machine

The following checks are required before claiming the local Windows setup is
current:

```powershell
git -C "$HOME\agent-skills" status --short --branch
git -C "$HOME\agent-skills" rev-parse --short HEAD
git -C "$HOME\agent-skills" rev-parse --short origin/main
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target all
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\telegram-hermes-doctor.ps1"
```

Expected minimum result:

```text
HEAD matches origin/main
VERIFY PASS warnings=0
telegram_gateway_state=connected
TELEGRAM_BOT_TOKEN=set
HONCHO_API_KEY=set
```

Do not print bot tokens, chat IDs, API keys, cookies, sessions, or auth files.
Telegram reports should print only set/unset values, counts, and connection
state.

## Cross-Platform Dry Run

Before relying on a pushed commit from another machine, clone the remote into a
temporary directory and run both Windows and POSIX checks:

```powershell
$tmpRoot = Join-Path $env:TEMP ('agent-skills-clone-test-' + (Get-Date -Format 'yyyyMMddHHmmss'))
git clone https://github.com/taktwosj/22utube-agent-skills.git $tmpRoot
powershell -ExecutionPolicy Bypass -File (Join-Path $tmpRoot 'scripts\verify.ps1') -Target repo
powershell -ExecutionPolicy Bypass -File (Join-Path $tmpRoot 'scripts\install.ps1') -Target all -DryRun
```

```bash
cd "$HOME/agent-skills"
bash scripts/verify.sh --target repo
bash scripts/install.sh --target all --dry-run
bash scripts/update.sh --target all --prune --dry-run
```

## Mac Mini Live Check

Windows-side WSL or POSIX dry-runs prove script compatibility, not that the Mac
mini has actually installed the latest skill set. On the Mac mini, run:

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
bash "$HOME/agent-skills/scripts/install.sh" --target all
bash "$HOME/agent-skills/scripts/verify.sh" --target all
bash "$HOME/agent-skills/scripts/telegram-hermes-doctor.sh"
```

If the repo already exists:

```bash
cd "$HOME/agent-skills"
git pull --ff-only
bash scripts/update.sh --target all --prune
bash scripts/verify.sh --target all
bash scripts/telegram-hermes-doctor.sh
```

Minimum live PASS:

```text
VERIFY PASS warnings=0
Codex target under $HOME/.codex/skills has managed markers
Claude target under $HOME/.claude/skills has managed markers
Hermes target under $HOME/.hermes/skills/22utube has managed markers
Telegram-Hermes doctor prints no secrets
```

Restart the target agent or open a new session if a newly installed skill list is
not visible immediately.
