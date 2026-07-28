# Windows Install

```powershell
git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME\agent-skills"
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\install.ps1" -Target all
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target all
```

Update:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune -DryRun
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Prune
```

Claude exact match:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target claude -Prune -Strict
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\verify.ps1" -Target claude -Strict
```

The manifest installs the current managed set, including `001short-production-agent` as the sole general Shorts production skill.
