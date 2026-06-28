# Telegram Hermes

Telegram is a remote control and status channel for Hermes. It is not the skill source of truth.

## Roles

- Git repo: official skill source and install/update/verify scripts.
- Hermes: local execution bridge and memory/rule context.
- Telegram: allowlisted commands and status reports only.
- Honcho: long-term preference/rule memory.
- Paperclip: per-job artifact/log/evidence bundle tracking when available.

## Secrets

Never commit bot tokens, chat IDs, API keys, cookies, sessions, or auth files.

Expected secret locations are machine-local only:

```text
Windows Hermes env: %LOCALAPPDATA%\Hermes\.env
macOS Hermes env: $HOME/.hermes/.env
```

Required:

```text
TELEGRAM_BOT_TOKEN
```

Recommended:

```text
HONCHO_API_KEY
```

Reports must say only `set` or `unset`; never print secret values.

For Telegram group/supergroup whitelisting, use local Hermes config:

```text
telegram.allowed_chats
```

DM chat IDs and channel names may appear in `channel_directory.json`; reports should summarize only counts or state, not print private chat identifiers.

## Allowed Commands

The canonical command manifest is:

```text
manifests/telegram-hermes.commands.json
```

Keep Telegram commands mapped to fixed actions. Do not allow arbitrary shell execution from Telegram.

## Verification

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\telegram-hermes-doctor.ps1"
```

macOS:

```bash
bash "$HOME/agent-skills/scripts/telegram-hermes-doctor.sh"
```

The doctor output is intentionally non-secret. It must not print token values.
