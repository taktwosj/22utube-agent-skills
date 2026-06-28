# Hermes Install

Hermes skills are installed under the 22utube category.

Windows Hermes native path:

```text
%LOCALAPPDATA%\Hermes\skills\22utube\<skill>
```

macOS/default path:

```text
$HOME/.hermes/skills/22utube/<skill>
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\install.ps1" -Target hermes
```

or:

```bash
bash "$HOME/agent-skills/scripts/install.sh" --target hermes
```

Secrets and Honcho state are not stored in this repository. Report secret status only as `set` or `unset`.

Telegram-Hermes command policy is documented in `docs/install-telegram-hermes.md`.
