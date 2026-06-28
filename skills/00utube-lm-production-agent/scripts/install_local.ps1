param(
  [string]$SourceRoot = "",
  [string]$TargetRoot = "",
  [bool]$InstallRouter = $true
)

$ErrorActionPreference = "Stop"

function Resolve-22utubeRoot {
  $candidates = @()
  if ($env:OneDrive) { $candidates += (Join-Path $env:OneDrive "22utube") }
  if ($env:OneDriveCommercial) { $candidates += (Join-Path $env:OneDriveCommercial "22utube") }
  $candidates += (Join-Path $env:USERPROFILE "OneDrive\22utube")

  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }

  throw "Could not find OneDrive 22utube root. Pass -SourceRoot explicitly."
}

if (-not $SourceRoot) {
  $SourceRoot = Join-Path (Resolve-22utubeRoot) "codex_skills\00utube-lm-production-agent"
}

if (-not $TargetRoot) {
  $TargetRoot = Join-Path $env:USERPROFILE ".codex\skills\00utube-lm-production-agent"
}

if (-not (Test-Path -LiteralPath (Join-Path $SourceRoot "SKILL.md"))) {
  throw "Source skill not found: $SourceRoot"
}

$targetParent = Split-Path -Parent $TargetRoot
New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
$backupRoot = Join-Path $env:USERPROFILE ".codex\skill_backups"
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

if (Test-Path -LiteralPath $TargetRoot) {
  $backup = Join-Path $backupRoot ("00utube-lm-production-agent.backup_$(Get-Date -Format yyyyMMdd_HHmmss)")
  Move-Item -LiteralPath $TargetRoot -Destination $backup
  Write-Host "Backed up existing skill to $backup"
}

Copy-Item -LiteralPath $SourceRoot -Destination $TargetRoot -Recurse -Force
Write-Host "Installed 00utube-lm-production-agent to $TargetRoot"

if ($InstallRouter) {
  $sourceParent = Split-Path -Parent $SourceRoot
  $routerSource = Join-Path $sourceParent "22utube-production-agent"
  $routerTarget = Join-Path $env:USERPROFILE ".codex\skills\22utube-production-agent"

  if (Test-Path -LiteralPath (Join-Path $routerSource "SKILL.md")) {
    if (Test-Path -LiteralPath $routerTarget) {
      $routerBackup = Join-Path $backupRoot ("22utube-production-agent.backup_$(Get-Date -Format yyyyMMdd_HHmmss)")
      Move-Item -LiteralPath $routerTarget -Destination $routerBackup
      Write-Host "Backed up existing router skill to $routerBackup"
    }
    Copy-Item -LiteralPath $routerSource -Destination $routerTarget -Recurse -Force
    Write-Host "Installed 22utube-production-agent router patch to $routerTarget"
  } else {
    Write-Host "Router skill source not found, skipped: $routerSource"
  }
}
