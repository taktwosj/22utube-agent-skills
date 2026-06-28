# Portable Install

The OneDrive source copy is:

```text
{OneDrive}\22utube\codex_skills\00utube-lm-production-agent
```

Each Windows PC needs a local Codex skill install at:

```text
%USERPROFILE%\.codex\skills\00utube-lm-production-agent
```

Run from PowerShell:

```powershell
$installer = @(
  "$env:OneDrive\22utube\codex_skills\00utube-lm-production-agent\scripts\install_local.ps1",
  "$env:OneDriveCommercial\22utube\codex_skills\00utube-lm-production-agent\scripts\install_local.ps1",
  "$env:USERPROFILE\OneDrive\22utube\codex_skills\00utube-lm-production-agent\scripts\install_local.ps1"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1

if (-not $installer) { throw "install_local.ps1 not found in OneDrive 22utube" }
powershell -ExecutionPolicy Bypass -File $installer
```

If none of those paths exists, replace the OneDrive path with the actual synced OneDrive path for that PC.

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
