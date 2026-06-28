# Claude Install

Claude runtime skills are installed to:

```text
$HOME/.claude/skills/<skill>
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\install.ps1" -Target claude
```

or:

```bash
bash "$HOME/agent-skills/scripts/install.sh" --target claude
```

Edit only the Git repo copy under `skills/<skill>`.
