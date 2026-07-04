param(
  [ValidateSet("all", "codex", "claude", "hermes")]
  [string]$Target = "all",
  [string[]]$Only = @(),
  [switch]$Prune,
  [switch]$Strict,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

function Enable-GitHooks([string]$RepoRoot, [switch]$DryRun) {
  $hooksDir = Join-Path $RepoRoot ".githooks"
  if (-not (Test-Path -LiteralPath $hooksDir)) { return }
  if ($DryRun) {
    Write-Output "DRYRUN HOOKS git config core.hooksPath .githooks"
    return
  }
  git -C $RepoRoot config core.hooksPath .githooks
  if ($LASTEXITCODE -ne 0) { throw "git config core.hooksPath failed" }
  Write-Output "HOOKS core.hooksPath=.githooks"
}

function Test-IsWindowsHost {
  return [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
}

function Expand-ManagedPath([string]$PathValue) {
  if ($PathValue.StartsWith('$LOCALAPPDATA')) {
    if (-not $env:LOCALAPPDATA) { throw "LOCALAPPDATA is not set for path: $PathValue" }
    $suffix = $PathValue.Substring(13).TrimStart('/', '\')
    return [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA $suffix))
  }
  if ($PathValue.StartsWith('$HERMES_HOME')) {
    if (-not $env:HERMES_HOME) { throw "HERMES_HOME is not set for path: $PathValue" }
    $suffix = $PathValue.Substring(12).TrimStart('/', '\')
    return [System.IO.Path]::GetFullPath((Join-Path $env:HERMES_HOME $suffix))
  }
  if ($PathValue.StartsWith('$HOME')) {
    $suffix = $PathValue.Substring(5).TrimStart('/', '\')
    return [System.IO.Path]::GetFullPath((Join-Path $HOME $suffix))
  }
  return [System.IO.Path]::GetFullPath($PathValue)
}

function Get-TargetRoot($TargetConfig) {
  if ((Test-IsWindowsHost) -and $TargetConfig.windows_path) {
    return Expand-ManagedPath $TargetConfig.windows_path
  }
  return Expand-ManagedPath $TargetConfig.path
}

function Get-BackupRoot($TargetConfig) {
  if ((Test-IsWindowsHost) -and $TargetConfig.windows_backup_path) {
    return Expand-ManagedPath $TargetConfig.windows_backup_path
  }
  return Expand-ManagedPath $TargetConfig.backup_path
}

function Read-JsonFile([string]$Path) {
  return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json
}

function Get-RelativePath([string]$BasePath, [string]$FullPath) {
  $base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
  $target = [System.IO.Path]::GetFullPath($FullPath)
  $baseUri = New-Object System.Uri($base)
  $targetUri = New-Object System.Uri($target)
  return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Get-SelectedTargets($TargetsObject, [string]$SelectedTarget) {
  if ($SelectedTarget -eq "all") {
    return @("codex", "claude", "hermes")
  }
  return @($SelectedTarget)
}

function Get-EnabledSkills($SkillSet, [string[]]$OnlyNames) {
  $skills = @($SkillSet.skills | Where-Object { $_.enabled -eq $true })
  if ($OnlyNames.Count -gt 0) {
    $requested = @{}
    foreach ($name in $OnlyNames) { $requested[$name] = $true }
    $skills = @($skills | Where-Object { $requested.ContainsKey($_.name) })
    foreach ($name in $OnlyNames) {
      if (-not ($skills | Where-Object { $_.name -eq $name })) {
        throw "Unknown or disabled skill in -Only: $name"
      }
    }
  }
  return $skills
}

function Get-DirectoryHash([string]$Path, [string]$ExcludeFileName = "") {
  $files = Get-ChildItem -LiteralPath $Path -File -Recurse -Force |
    Where-Object { -not $ExcludeFileName -or $_.Name -ne $ExcludeFileName } |
    Sort-Object FullName
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($file in $files) {
    $relative = (Get-RelativePath $Path $file.FullName).Replace('\', '/')
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    $lines.Add("$relative`t$hash")
  }
  $joined = [string]::Join("`n", $lines)
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($joined)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  return ([System.BitConverter]::ToString($sha.ComputeHash($bytes)) -replace "-", "")
}

function Get-SourceCommit([string]$RepoRoot) {
  try {
    $commit = git -C $RepoRoot rev-parse --short HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $commit) {
      $value = $commit.Trim()
      $status = git -C $RepoRoot status --porcelain 2>$null
      if ($status) { $value = "$value-dirty" }
      return $value
    }
  } catch {}
  return "uncommitted"
}

function Get-TargetSkillPath($TargetConfig, [string]$SkillName) {
  $root = Get-TargetRoot $TargetConfig
  if ($TargetConfig.layout -eq "category") {
    return Join-Path (Join-Path $root $TargetConfig.default_category) $SkillName
  }
  return Join-Path $root $SkillName
}

function Backup-Existing([string]$ExistingPath, [string]$BackupRoot, [string]$SkillName, [string]$Stamp, [switch]$DryRun) {
  if (-not (Test-Path -LiteralPath $ExistingPath)) { return }
  $backup = Join-Path $BackupRoot ("{0}_{1}" -f $SkillName, $Stamp)
  if ($DryRun) {
    Write-Output "DRYRUN BACKUP $ExistingPath -> $backup"
    return
  }
  New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
  Move-Item -LiteralPath $ExistingPath -Destination $backup
  Write-Output "BACKUP $ExistingPath -> $backup"
}

function Copy-Skill([string]$SourcePath, [string]$DestinationPath, [switch]$DryRun) {
  $parent = Split-Path -Parent $DestinationPath
  if ($DryRun) {
    Write-Output "DRYRUN COPY $SourcePath -> $DestinationPath"
    return
  }
  New-Item -ItemType Directory -Path $parent -Force | Out-Null
  Copy-Item -LiteralPath $SourcePath -Destination $parent -Recurse -Force
  Write-Output "SYNCED $DestinationPath"
}

function Write-ManagedMarker($TargetConfig, [string]$DestinationPath, [string]$RepoName, [string]$SkillName, [string]$TargetName, [string]$Commit, [string]$SourceHash, [switch]$DryRun) {
  $markerPath = Join-Path $DestinationPath $TargetConfig.state_file
  $marker = [ordered]@{
    repo = $RepoName
    skill = $SkillName
    target = $TargetName
    installed_at = (Get-Date).ToString("o")
    source_commit = $Commit
    source_sha256 = $SourceHash
  }
  if ($DryRun) {
    Write-Output "DRYRUN MARKER $markerPath"
    return
  }
  $marker | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $markerPath -Encoding UTF8
  Write-Output "MARKER $markerPath"
}

function Invoke-Prune($TargetConfig, [string]$TargetName, $ExpectedSkills, [string]$Stamp, [switch]$DryRun) {
  $root = Get-TargetRoot $TargetConfig
  $scanRoot = $root
  if ($TargetConfig.layout -eq "category") {
    $scanRoot = Join-Path $root $TargetConfig.default_category
  }
  if (-not (Test-Path -LiteralPath $scanRoot)) { return }

  $expected = @{}
  foreach ($name in $ExpectedSkills) { $expected[$name] = $true }
  $backupRoot = Get-BackupRoot $TargetConfig
  $markerName = $TargetConfig.state_file

  foreach ($dir in Get-ChildItem -LiteralPath $scanRoot -Directory -Force) {
    if ($expected.ContainsKey($dir.Name)) { continue }
    $markerPath = Join-Path $dir.FullName $markerName
    if (-not (Test-Path -LiteralPath $markerPath)) { continue }
    $backup = Join-Path $backupRoot ("PRUNED_{0}_{1}" -f $dir.Name, $Stamp)
    if ($DryRun) {
      Write-Output "DRYRUN PRUNE $($dir.FullName) -> $backup"
      continue
    }
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Move-Item -LiteralPath $dir.FullName -Destination $backup
    Write-Output "PRUNED $($dir.FullName) -> $backup"
  }
}

function Invoke-StrictDisable($TargetConfig, [string]$TargetName, $ExpectedSkills, [string]$Stamp, [switch]$DryRun) {
  $root = Get-TargetRoot $TargetConfig
  $scanRoot = $root
  if ($TargetConfig.layout -eq "category") {
    $scanRoot = Join-Path $root $TargetConfig.default_category
  }
  if (-not (Test-Path -LiteralPath $scanRoot)) { return }

  $expected = @{}
  foreach ($name in $ExpectedSkills) { $expected[$name] = $true }
  $backupRoot = Get-BackupRoot $TargetConfig

  foreach ($dir in Get-ChildItem -LiteralPath $scanRoot -Directory -Force) {
    if ($expected.ContainsKey($dir.Name)) { continue }
    if (-not (Test-Path -LiteralPath (Join-Path $dir.FullName "SKILL.md"))) { continue }
    $backup = Join-Path $backupRoot ("DISABLED_{0}_{1}" -f $dir.Name, $Stamp)
    if ($DryRun) {
      Write-Output "DRYRUN STRICT_DISABLE $($dir.FullName) -> $backup"
      continue
    }
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Move-Item -LiteralPath $dir.FullName -Destination $backup
    Write-Output "STRICT_DISABLED $($dir.FullName) -> $backup"
  }
}

if ($Only.Count -gt 0 -and $Prune) {
  throw "-Only and -Prune cannot be used together."
}
if ($Only.Count -gt 0 -and $Strict) {
  throw "-Only and -Strict cannot be used together."
}

$repoRoot = Get-RepoRoot
$skillSet = Read-JsonFile (Join-Path $repoRoot "manifests/skill-set.json")
$targets = Read-JsonFile (Join-Path $repoRoot "manifests/targets.json")
$selectedTargets = Get-SelectedTargets $targets $Target
$skills = Get-EnabledSkills $skillSet $Only
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$commit = Get-SourceCommit $repoRoot

foreach ($targetName in $selectedTargets) {
  $targetConfig = $targets.targets.$targetName
  if (-not $targetConfig) { throw "Missing target config: $targetName" }
  $targetSkills = @($skills | Where-Object { $_.targets -contains $targetName })
  foreach ($skill in $targetSkills) {
    $sourcePath = Join-Path (Join-Path $repoRoot "skills") $skill.name
    if (-not (Test-Path -LiteralPath (Join-Path $sourcePath "SKILL.md"))) {
      throw "Missing source skill: $($skill.name)"
    }
    $destinationPath = Get-TargetSkillPath $targetConfig $skill.name
    $backupRoot = Get-BackupRoot $targetConfig
    $sourceHash = Get-DirectoryHash $sourcePath

    Backup-Existing $destinationPath $backupRoot $skill.name $stamp -DryRun:$DryRun
    Copy-Skill $sourcePath $destinationPath -DryRun:$DryRun
    Write-ManagedMarker $targetConfig $destinationPath $skillSet.repo_name $skill.name $targetName $commit $sourceHash -DryRun:$DryRun
  }
  if ($Prune) {
    Invoke-Prune $targetConfig $targetName @($targetSkills | ForEach-Object { $_.name }) $stamp -DryRun:$DryRun
  }
  if ($Strict) {
    Invoke-StrictDisable $targetConfig $targetName @($targetSkills | ForEach-Object { $_.name }) $stamp -DryRun:$DryRun
  }
}

Enable-GitHooks $repoRoot -DryRun:$DryRun

Write-Output "DONE install target=$Target dry_run=$($DryRun.IsPresent)"
