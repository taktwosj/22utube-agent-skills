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

Single-skill update:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\agent-skills\scripts\update.ps1" -Target all -Only 000brainstorm,111-politics-longform
```
