param(
  [ValidateSet("Install", "Uninstall", "Status")]
  [string]$Action = "Install",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$taskName = "22utube Skill Runtime Save Sync"
$watcher = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "watch_runtime_skills.ps1")).Path
$powerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$watcher`""

if ($Action -eq "Status") {
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if (-not $task) {
    Write-Output "STATUS NOT_INSTALLED task=$taskName"
    exit 1
  }
  Write-Output "STATUS $($task.State) task=$taskName"
  exit 0
}

if ($Action -eq "Uninstall") {
  if ($DryRun) {
    Write-Output "DRYRUN UNREGISTER task=$taskName"
    exit 0
  }
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($task) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
  }
  Write-Output "UNINSTALLED task=$taskName"
  exit 0
}

if ($DryRun) {
  Write-Output "DRYRUN REGISTER task=$taskName"
  Write-Output "DRYRUN ACTION execute=$powerShellExe arguments=$arguments"
  Write-Output "DRYRUN TRIGGER New-ScheduledTaskTrigger -AtLogOn"
  exit 0
}

$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskAction = New-ScheduledTaskAction -Execute $powerShellExe -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -MultipleInstances IgnoreNew `
  -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask `
  -TaskName $taskName `
  -Action $taskAction `
  -Trigger $trigger `
  -Principal $principal `
  -Settings $settings `
  -Description "Sync saved Git workspace skills to Codex, Claude, and Hermes and verify SHA256." `
  -Force | Out-Null

Start-ScheduledTask -TaskName $taskName
Write-Output "INSTALLED_AND_STARTED task=$taskName watcher=$watcher"
