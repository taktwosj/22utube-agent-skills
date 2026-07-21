# Git Down Guide

Use this guide on the office Windows PC and Mac mini to receive the official
22utube skill set from Git.

Repo:

```text
https://github.com/taktwosj/22utube-agent-skills.git
```

Minimum required implementation commit:

```text
9e98c27f5401 or newer
```

Skill authority rule:

```text
Git is the constitution for skills.
OneDrive skill-source or skill-sync mirrors are forbidden.
If another PC still has old OneDrive skill mirrors, delete them and do not
restore them through OneDrive sync.
Local runtime folders are installed from Git only.
```

## Office Windows

First install:

```powershell
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME\agent-skills"
cd "$HOME\agent-skills"
powershell -ExecutionPolicy Bypass -File scripts\update.ps1 -Target all -Strict
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target all -Strict
```

Existing repo update:

```powershell
cd "$HOME\agent-skills"
git pull --ff-only
powershell -ExecutionPolicy Bypass -File scripts\update.ps1 -Target all -Strict
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target all -Strict
```

Expected result:

```text
VERIFY PASS warnings=0
Codex marker source_commit = 9e98c27f5401 or newer
Claude marker source_commit = 9e98c27f5401 or newer
Hermes marker source_commit = 9e98c27f5401 or newer
```

## Mac Mini

First install:

```bash
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME/agent-skills"
cd "$HOME/agent-skills"
bash scripts/update.sh --target all --strict
bash scripts/verify.sh --target all --strict
```

Existing repo update:

```bash
cd "$HOME/agent-skills"
git pull --ff-only
bash scripts/update.sh --target all --strict
bash scripts/verify.sh --target all --strict
```

Expected result:

```text
VERIFY PASS warnings=0
Codex marker source_commit = 9e98c27f5401 or newer
Claude marker source_commit = 9e98c27f5401 or newer
Hermes marker source_commit = 9e98c27f5401 or newer
```

## Optional Telegram Hermes Check

Windows:

```powershell
cd "$HOME\agent-skills"
powershell -ExecutionPolicy Bypass -File scripts\telegram-hermes-doctor.ps1
```

Mac mini:

```bash
cd "$HOME/agent-skills"
bash scripts/telegram-hermes-doctor.sh
```

Do not print tokens, chat IDs, cookies, API keys, sessions, or auth files.

## What This Installs

The Git-managed skill set is installed into:

```text
Codex  -> ~/.codex/skills
Claude -> ~/.claude/skills
Hermes -> ~/.hermes/skills/22utube on macOS
Hermes -> %LOCALAPPDATA%\Hermes\skills\22utube on Windows
```

The install scripts copy official Git skills into runtime folders and write
managed marker files. Runtime folders are not edit targets.

## Current Shorts Factory Rule

```text
DRAFT_FAST is default.
FINAL_LOCK runs only when explicitly requested.
Official CapCut template defaults are black and insta white.
Korean mojibake in draft_content.json is a KOREAN_TEXT_FAST_GATE failure.
```
