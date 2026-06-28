# Hermes Install

Hermes skills are installed under the 22utube category:

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
