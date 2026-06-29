# Portable Install

The source of truth is the Git repo:

```text
$HOME\agent-skills\skills\00utube-lm-production-agent
```

Each Windows PC needs local runtime installs under:

```text
%USERPROFILE%\.codex\skills
```

Run from PowerShell:

```powershell
if (-not (Test-Path "$HOME\agent-skills\.git")) {
  git clone https://github.com/taktwosj/22utube-agent-skills.git "$HOME\agent-skills"
}
cd "$HOME\agent-skills"
git pull --ff-only
powershell -ExecutionPolicy Bypass -File scripts\update.ps1 -Target all -Strict
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Target all -Strict
```

Do not use OneDrive skill source or mirror folders. OneDrive remains for
production files and handoff packages only.

For office/Windows client PCs, the production console and n8n server are the Mac mini by default. Use the Mac mini Tailscale IP, not the current PC's Tailscale IP:

```text
http://{Mac mini Tailscale IP}:47831/?v=.
http://{Mac mini Tailscale IP}:5678
```

Remote access requires the office PC and Mac mini to be on the same Tailscale account, the Mac mini to be online, and the Mac mini console/n8n server to be running. File edits happen in the current PC's OneDrive sync folder; CapCut drafts are local to the PC that creates them.

After installing, start a new Codex chat and invoke:

```text
[$00utube-lm-production-agent]
```
