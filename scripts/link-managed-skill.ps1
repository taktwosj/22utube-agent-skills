param(
  [Parameter(Mandatory = $true)]
  [string]$FactoryRoot,
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^[a-z0-9][a-z0-9-]*$')]
  [string]$SkillName,
  [Parameter(Mandatory = $true)]
  [ValidateSet('codex', 'claude', 'hermes')]
  [string]$Target,
  [string]$RuntimeRoot = '',
  [switch]$AllowTestRuntimeRoot,
  [string]$BackupRoot = '',
  [string]$SelfCheckRelativePath = 'scripts/self-check.ps1',
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Test-IsWindowsHost {
  return [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
}

function Get-DefaultRuntimeRoot([string]$TargetName) {
  switch ($TargetName) {
    'codex' { return Join-Path $HOME '.codex/skills' }
    'claude' { return Join-Path $HOME '.claude/skills' }
    'hermes' {
      if (Test-IsWindowsHost) {
        if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is not set.' }
        return Join-Path $env:LOCALAPPDATA 'Hermes/skills/22utube'
      }
      return Join-Path $HOME '.hermes/skills/22utube'
    }
  }
}

function Get-DefaultBackupRoot([string]$TargetName, [string]$ResolvedRuntimeRoot) {
  if ($RuntimeRoot) { return "${ResolvedRuntimeRoot}_backups" }
  switch ($TargetName) {
    'codex' { return Join-Path $HOME '.codex/skills_backups' }
    'claude' { return Join-Path $HOME '.claude/skills_backups' }
    'hermes' {
      if (Test-IsWindowsHost) { return Join-Path $env:LOCALAPPDATA 'Hermes/skills_backups' }
      return Join-Path $HOME '.hermes/skills_backups'
    }
  }
}

$protectedSkillNames = @(
  'imagegen',
  'openai-docs',
  'plugin-creator',
  'skill-creator',
  'skill-installer'
)
if ($protectedSkillNames -contains $SkillName) {
  throw "Refusing runtime-owned system/plugin skill name: $SkillName"
}

$resolvedFactoryRoot = [System.IO.Path]::GetFullPath($FactoryRoot)
$managedRepoRoot = [System.IO.Path]::GetFullPath((Join-Path $resolvedFactoryRoot 'agent-skills'))
$manifestPath = Join-Path $managedRepoRoot 'manifests/skill-set.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw "Managed skill manifest is missing: $manifestPath"
}
$skillSet = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
$managedSkill = @($skillSet.skills | Where-Object {
  $_.name -eq $SkillName -and $_.enabled -eq $true -and $_.targets -contains $Target
})
if ($managedSkill.Count -ne 1) {
  throw "Skill is not enabled for target $Target in manifests/skill-set.json: $SkillName"
}

$source = [System.IO.Path]::GetFullPath((Join-Path $managedRepoRoot "skills/$SkillName"))
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
  throw "Managed skill source is missing SKILL.md: $source"
}

$resolvedRuntimeRoot = if ($RuntimeRoot) {
  if (-not $AllowTestRuntimeRoot -or $env:AGENT_SKILLS_TEST_RUNTIME_OVERRIDE -ne '1') {
    throw 'RuntimeRoot is test-only and requires -AllowTestRuntimeRoot plus AGENT_SKILLS_TEST_RUNTIME_OVERRIDE=1.'
  }
  [System.IO.Path]::GetFullPath($RuntimeRoot)
} else {
  if ($AllowTestRuntimeRoot) { throw '-AllowTestRuntimeRoot requires -RuntimeRoot.' }
  [System.IO.Path]::GetFullPath((Get-DefaultRuntimeRoot $Target))
}
$runtimeSegments = @($resolvedRuntimeRoot -split '[\\/]' | Where-Object { $_ })
if (@($runtimeSegments | Where-Object { $_ -in @('.system', '.plugins', 'plugins', 'plugin-cache') }).Count -gt 0) {
  throw "Refusing runtime-owned system/plugin path: $resolvedRuntimeRoot"
}
$resolvedBackupRoot = if ($BackupRoot) {
  [System.IO.Path]::GetFullPath($BackupRoot)
} else {
  [System.IO.Path]::GetFullPath((Get-DefaultBackupRoot $Target $resolvedRuntimeRoot))
}
$destination = [System.IO.Path]::GetFullPath((Join-Path $resolvedRuntimeRoot $SkillName))
$stamp = Get-Date -Format 'yyyyMMdd-HHmmssfff'
$backup = [System.IO.Path]::GetFullPath((Join-Path $resolvedBackupRoot "${SkillName}_${stamp}"))

if ($DryRun) {
  Write-Output "DRYRUN SOURCE $source"
  Write-Output "DRYRUN DESTINATION $destination"
  Write-Output "DRYRUN BACKUP $backup"
  exit 0
}

$destinationParent = Split-Path -Parent $destination
New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null

$existing = Get-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
$backupCreated = $false
if ($existing) {
  New-Item -ItemType Directory -Path $resolvedBackupRoot -Force | Out-Null
  Move-Item -LiteralPath $destination -Destination $backup
  $backupCreated = $true
  Write-Output "BACKUP $destination -> $backup"
} else {
  Write-Output "BACKUP NONE $destination"
}

try {
  $linkType = if (Test-IsWindowsHost) { 'Junction' } else { 'SymbolicLink' }
  New-Item -ItemType $linkType -Path $destination -Target $source | Out-Null
  Write-Output "LINKED $destination -> $source type=$linkType"

  $linkedItem = Get-Item -LiteralPath $destination -Force
  $targetValue = @($linkedItem.Target)[0]
  if (-not $targetValue) { throw "Link target readback is empty: $destination" }
  if (-not [System.IO.Path]::IsPathRooted($targetValue)) {
    $targetValue = Join-Path $destinationParent $targetValue
  }
  $readback = [System.IO.Path]::GetFullPath($targetValue)
  Write-Output "READBACK $destination -> $readback"

  $comparison = if (Test-IsWindowsHost) {
    [System.StringComparison]::OrdinalIgnoreCase
  } else {
    [System.StringComparison]::Ordinal
  }
  if (-not [string]::Equals($source.TrimEnd('\', '/'), $readback.TrimEnd('\', '/'), $comparison)) {
    throw "Link readback mismatch: expected=$source actual=$readback"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $destination 'SKILL.md') -PathType Leaf)) {
    throw "Linked skill readback is missing SKILL.md: $destination"
  }
  $sourceSkillHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'SKILL.md')).Hash
  $destinationSkillHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $destination 'SKILL.md')).Hash
  if ($sourceSkillHash -ne $destinationSkillHash) {
    throw "Linked SKILL.md hash mismatch: source=$sourceSkillHash destination=$destinationSkillHash"
  }
  Write-Output "HASH PASS algorithm=SHA256 source=$sourceSkillHash destination=$destinationSkillHash"

  $selfCheckPath = [System.IO.Path]::GetFullPath((Join-Path $destination $SelfCheckRelativePath))
  $destinationPrefix = $destination.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
  if (-not $selfCheckPath.StartsWith($destinationPrefix, $comparison)) {
    throw "Self-check must stay inside the managed skill: $SelfCheckRelativePath"
  }
  if (Test-Path -LiteralPath $selfCheckPath -PathType Leaf) {
    if ([System.IO.Path]::GetExtension($selfCheckPath) -ne '.ps1') {
      throw "Self-check must be a PowerShell script: $SelfCheckRelativePath"
    }
    $powerShellExe = (Get-Process -Id $PID).Path
    Push-Location -LiteralPath $destination
    try {
      & $powerShellExe -NoProfile -ExecutionPolicy Bypass -File $selfCheckPath
      if ($LASTEXITCODE -ne 0) {
        throw "Skill self-check failed with exit code $LASTEXITCODE`: $SelfCheckRelativePath"
      }
    } finally {
      Pop-Location
    }
    Write-Output "SELF_CHECK PASS $SelfCheckRelativePath"
  } else {
    Write-Output "SELF_CHECK SKIP $SelfCheckRelativePath"
  }
  Write-Output "VERIFY PASS source=$source destination=$destination"
} catch {
  $failedDestination = Get-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
  if ($failedDestination) { Remove-Item -LiteralPath $destination -Force }
  if ($backupCreated -and (Test-Path -LiteralPath $backup)) {
    Move-Item -LiteralPath $backup -Destination $destination
    Write-Output "ROLLBACK RESTORED $backup -> $destination"
  }
  throw
}
