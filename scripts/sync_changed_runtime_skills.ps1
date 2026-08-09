param(
  [Parameter(Mandatory = $true)]
  [string[]]$ChangedPath,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
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

function Expand-ManagedPath([string]$PathValue) {
  if ($PathValue.StartsWith('$LOCALAPPDATA')) {
    $suffix = $PathValue.Substring(13).TrimStart('/', '\')
    return [System.IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA $suffix))
  }
  if ($PathValue.StartsWith('$HOME')) {
    $suffix = $PathValue.Substring(5).TrimStart('/', '\')
    return [System.IO.Path]::GetFullPath((Join-Path $HOME $suffix))
  }
  return [System.IO.Path]::GetFullPath($PathValue)
}

function Get-TargetRoot($TargetConfig) {
  if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT -and $TargetConfig.windows_path) {
    return Expand-ManagedPath $TargetConfig.windows_path
  }
  return Expand-ManagedPath $TargetConfig.path
}

function Get-TargetSkillPath($TargetConfig, [string]$SkillName) {
  $root = Get-TargetRoot $TargetConfig
  if ($TargetConfig.layout -eq "category") {
    return Join-Path (Join-Path $root $TargetConfig.default_category) $SkillName
  }
  return Join-Path $root $SkillName
}

function Write-Result($Payload) {
  Write-Output ("SYNC_RESULT_JSON=" + ($Payload | ConvertTo-Json -Depth 8 -Compress))
}

$repoRoot = Get-RepoRoot
$skillsRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "skills")).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
$skillSet = Read-JsonFile (Join-Path $repoRoot "manifests/skill-set.json")
$targets = Read-JsonFile (Join-Path $repoRoot "manifests/targets.json")

$enabled = @{}
foreach ($skill in @($skillSet.skills | Where-Object { $_.enabled -eq $true })) {
  $enabled[$skill.name] = $true
}

$selected = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($candidate in $ChangedPath) {
  if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
  $fullPath = $candidate
  if (-not [System.IO.Path]::IsPathRooted($fullPath)) {
    $fullPath = Join-Path $repoRoot $fullPath
  }
  $fullPath = [System.IO.Path]::GetFullPath($fullPath)
  if (-not $fullPath.StartsWith($skillsRoot, [System.StringComparison]::OrdinalIgnoreCase)) { continue }
  $relative = $fullPath.Substring($skillsRoot.Length)
  $parts = $relative -split '[\\/]'
  if ($parts.Count -lt 1 -or -not $parts[0]) { continue }
  $skillName = $parts[0]
  if (-not $enabled.ContainsKey($skillName)) { continue }
  if (-not (Test-Path -LiteralPath (Join-Path (Join-Path $skillsRoot $skillName) "SKILL.md"))) { continue }
  [void]$selected.Add($skillName)
}

$skillNames = @($selected | Sort-Object)
$targetNames = @("codex", "claude", "hermes")
if ($skillNames.Count -eq 0) {
  Write-Result ([ordered]@{
      status = "NO_MANAGED_SKILL_CHANGE"
      skills = @()
      targets = $targetNames
      dirty_worktree_allowed = $true
    })
  exit 0
}

$mutex = New-Object System.Threading.Mutex($false, "Local\22utube-runtime-save-sync")
$lockAcquired = $false
try {
  $lockAcquired = $mutex.WaitOne(0)
  if (-not $lockAcquired) {
    Write-Result ([ordered]@{
        status = "SKIPPED_LOCKED"
        skills = $skillNames
        targets = $targetNames
        dirty_worktree_allowed = $true
      })
    exit 0
  }

  $installScript = Join-Path $PSScriptRoot "install.ps1"
  & $installScript -Target all -Only $skillNames -DryRun:$DryRun
  $installSucceeded = $?
  if (-not $installSucceeded) { throw "install.ps1 failed" }

  if ($DryRun) {
    Write-Result ([ordered]@{
        status = "DRYRUN"
        skills = $skillNames
        targets = $targetNames
        dirty_worktree_allowed = $true
      })
    exit 0
  }

  $verification = New-Object System.Collections.Generic.List[object]
  $mismatchCount = 0
  foreach ($skillName in $skillNames) {
    $sourcePath = Join-Path (Join-Path $repoRoot "skills") $skillName
    $sourceHash = Get-DirectoryHash $sourcePath
    foreach ($targetName in $targetNames) {
      $targetConfig = $targets.targets.$targetName
      $destinationPath = Get-TargetSkillPath $targetConfig $skillName
      $markerPath = Join-Path $destinationPath $targetConfig.state_file
      $markerHash = $null
      $runtimeHash = $null
      $status = "FAIL"
      $reason = ""
      if (-not (Test-Path -LiteralPath $destinationPath)) {
        $reason = "runtime skill directory missing"
      } elseif (-not (Test-Path -LiteralPath $markerPath)) {
        $reason = "runtime marker missing"
      } else {
        $marker = Read-JsonFile $markerPath
        $markerHash = [string]$marker.source_sha256
        $runtimeHash = Get-DirectoryHash $destinationPath $targetConfig.state_file
        if ($sourceHash -eq $markerHash -and $sourceHash -eq $runtimeHash) {
          $status = "PASS"
        } else {
          $reason = "source, marker, and runtime SHA256 differ"
        }
      }
      if ($status -ne "PASS") { $mismatchCount += 1 }
      $verification.Add([ordered]@{
          skill = $skillName
          target = $targetName
          status = $status
          source_sha256 = $sourceHash
          marker_sha256 = $markerHash
          runtime_sha256 = $runtimeHash
          reason = $reason
        })
    }
  }

  $finalStatus = if ($mismatchCount -eq 0) { "PASS" } else { "FAIL_RUNTIME_SHA_MISMATCH" }
  Write-Result ([ordered]@{
      status = $finalStatus
      skills = $skillNames
      targets = $targetNames
      dirty_worktree_allowed = $true
      verification = $verification.ToArray()
    })
  if ($mismatchCount -ne 0) { exit 1 }
} catch {
  Write-Result ([ordered]@{
      status = "FAIL"
      skills = $skillNames
      targets = $targetNames
      dirty_worktree_allowed = $true
      error = $_.Exception.Message
    })
  exit 1
} finally {
  if ($lockAcquired) {
    try { [void]$mutex.ReleaseMutex() } catch {}
  }
  $mutex.Dispose()
}
