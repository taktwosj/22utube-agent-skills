param(
  [ValidateSet("repo", "all", "codex", "claude", "hermes")]
  [string]$Target = "repo"
)

$ErrorActionPreference = "Stop"
$script:Errors = New-Object System.Collections.Generic.List[string]
$script:Warnings = New-Object System.Collections.Generic.List[string]

function Add-Error([string]$Message) {
  $script:Errors.Add($Message)
  Write-Output "FAIL $Message"
}

function Add-Warning([string]$Message) {
  $script:Warnings.Add($Message)
  Write-Output "WARN $Message"
}

function Get-RepoRoot {
  return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

function Read-JsonFile([string]$Path) {
  try {
    return Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json
  } catch {
    Add-Error "Invalid JSON: $Path"
    return $null
  }
}

function Expand-ManagedPath([string]$PathValue) {
  if ($PathValue.StartsWith('$HOME')) {
    $suffix = $PathValue.Substring(5).TrimStart('/', '\')
    return [System.IO.Path]::GetFullPath((Join-Path $HOME $suffix))
  }
  return [System.IO.Path]::GetFullPath($PathValue)
}

function Get-RelativePath([string]$BasePath, [string]$FullPath) {
  $base = [System.IO.Path]::GetFullPath($BasePath).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
  $target = [System.IO.Path]::GetFullPath($FullPath)
  $baseUri = New-Object System.Uri($base)
  $targetUri = New-Object System.Uri($target)
  return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}

function Get-SelectedTargets([string]$SelectedTarget) {
  if ($SelectedTarget -eq "all") { return @("codex", "claude", "hermes") }
  if ($SelectedTarget -eq "repo") { return @() }
  return @($SelectedTarget)
}

function Get-Frontmatter([string]$SkillFile) {
  $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $SkillFile
  $match = [regex]::Match($text, "(?s)^---\r?\n(.*?)\r?\n---")
  if (-not $match.Success) { return $null }
  $map = @{}
  foreach ($line in ($match.Groups[1].Value -split "\r?\n")) {
    if ($line -match "^\s*([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$") {
      $map[$matches[1]] = $matches[2].Trim().Trim('"')
    }
  }
  return $map
}

function Get-DirectoryHash([string]$Path) {
  $files = Get-ChildItem -LiteralPath $Path -File -Recurse -Force |
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

function Test-ForbiddenContent([string]$RepoRoot, [string]$RelativeRoot, [bool]$ErrorOnHit) {
  $root = Join-Path $RepoRoot $RelativeRoot
  if (-not (Test-Path -LiteralPath $root)) { return }
  $patterns = @(
    ("C:" + "\Users\"),
    ("C:" + "/" + "Users/"),
    ("/" + "Users/"),
    ("/" + "home/"),
    ("/" + "Volumes/")
  )
  $files = Get-ChildItem -LiteralPath $root -File -Recurse -Force
  foreach ($file in $files) {
    $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $file.FullName -ErrorAction SilentlyContinue
    foreach ($pattern in $patterns) {
      if ($text.Contains($pattern)) {
        $rel = Get-RelativePath $RepoRoot $file.FullName
        if ($ErrorOnHit) { Add-Error "blocked absolute path in $rel pattern=$pattern" }
        else { Add-Warning "absolute path example in $rel pattern=$pattern" }
        break
      }
    }
  }
}

function Test-ForbiddenNames([string]$RepoRoot) {
  $forbiddenExtensions = @(".mp4", ".mov", ".mkv", ".avi", ".wav", ".mp3", ".m4a", ".aac", ".zip", ".7z", ".rar", ".tar", ".gz")
  $forbiddenDirNames = @("node_modules", "skills_backups", ".DS_Store")
  $secretPattern = "(?i)(^\.env$|(^|[._-])(env|key|token|cookie|session|secret|credential)([._-]|$))"
  foreach ($item in Get-ChildItem -LiteralPath $RepoRoot -Recurse -Force) {
    $rel = Get-RelativePath $RepoRoot $item.FullName
    if ($item.PSIsContainer) {
      if ($item.Name -like "_backup*" -or $item.Name -like "*_backup*" -or $forbiddenDirNames -contains $item.Name) {
        Add-Error "forbidden directory: $rel"
      }
    } else {
      if ($forbiddenExtensions -contains $item.Extension.ToLowerInvariant()) {
        Add-Error "forbidden binary/archive file: $rel"
      }
      if ($item.Name -match $secretPattern) {
        Add-Error "secret-like file name: $rel"
      }
    }
  }
}

function Test-Repo($RepoRoot, $SkillSet, $Targets) {
  if (-not $SkillSet) { return }
  if ($SkillSet.repo_name -ne "22utube-agent-skills") {
    Add-Error "repo_name must be 22utube-agent-skills"
  }
  $skillsRoot = Join-Path $RepoRoot "skills"
  foreach ($skill in @($SkillSet.skills | Where-Object { $_.enabled -eq $true })) {
    $skillDir = Join-Path $skillsRoot $skill.name
    $skillFile = Join-Path $skillDir "SKILL.md"
    if (-not (Test-Path -LiteralPath $skillDir)) {
      Add-Error "missing skill folder: $($skill.name)"
      continue
    }
    if (-not (Test-Path -LiteralPath $skillFile)) {
      Add-Error "missing SKILL.md: $($skill.name)"
      continue
    }
    $frontmatter = Get-Frontmatter $skillFile
    if (-not $frontmatter) {
      Add-Error "missing YAML frontmatter: $($skill.name)"
    } else {
      if (-not $frontmatter.ContainsKey("name")) { Add-Error "missing frontmatter name: $($skill.name)" }
      if (-not $frontmatter.ContainsKey("description")) { Add-Error "missing frontmatter description: $($skill.name)" }
      if ($frontmatter.ContainsKey("name") -and $frontmatter["name"] -ne $skill.name) {
        Add-Error "frontmatter name mismatch: folder=$($skill.name) name=$($frontmatter["name"])"
      }
    }
    $skillMdCount = @(Get-ChildItem -LiteralPath $skillDir -Filter "SKILL.md" -File -Recurse -Force).Count
    if ($skillMdCount -ne 1) {
      Add-Error "nested or missing SKILL.md count=$skillMdCount skill=$($skill.name)"
    }
  }
  Test-ForbiddenNames $RepoRoot
  Test-ForbiddenContent $RepoRoot "scripts" $true
  Test-ForbiddenContent $RepoRoot "skills" $true
  Test-ForbiddenContent $RepoRoot "docs" $false
  $readme = Join-Path $RepoRoot "README.md"
  if (Test-Path -LiteralPath $readme) {
    foreach ($pattern in @(
      ("C:" + "\Users\"),
      ("C:" + "/" + "Users/"),
      ("/" + "Users/"),
      ("/" + "home/"),
      ("/" + "Volumes/")
    )) {
      $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $readme
      if ($text.Contains($pattern)) { Add-Warning "absolute path example in README.md pattern=$pattern" }
    }
  }
}

function Get-TargetSkillPath($TargetConfig, [string]$SkillName) {
  $root = Expand-ManagedPath $TargetConfig.path
  if ($TargetConfig.layout -eq "category") {
    return Join-Path (Join-Path $root $TargetConfig.default_category) $SkillName
  }
  return Join-Path $root $SkillName
}

function Test-Target($RepoRoot, $SkillSet, $Targets, [string]$TargetName) {
  $targetConfig = $Targets.targets.$TargetName
  if (-not $targetConfig) {
    Add-Error "missing target config: $TargetName"
    return
  }
  $root = Expand-ManagedPath $targetConfig.path
  if (-not (Test-Path -LiteralPath $root)) {
    Add-Error "missing target root: $TargetName path=$root"
    return
  }
  foreach ($skill in @($SkillSet.skills | Where-Object { $_.enabled -eq $true -and $_.targets -contains $TargetName })) {
    $dest = Get-TargetSkillPath $targetConfig $skill.name
    $skillFile = Join-Path $dest "SKILL.md"
    $markerPath = Join-Path $dest $targetConfig.state_file
    if (-not (Test-Path -LiteralPath $skillFile)) {
      Add-Error "missing target SKILL.md target=$TargetName skill=$($skill.name)"
      continue
    }
    if (-not (Test-Path -LiteralPath $markerPath)) {
      Add-Error "missing managed marker target=$TargetName skill=$($skill.name)"
      continue
    }
    $marker = Read-JsonFile $markerPath
    if ($marker) {
      if ($marker.repo -ne $SkillSet.repo_name) { Add-Error "marker repo mismatch target=$TargetName skill=$($skill.name)" }
      if ($marker.skill -ne $skill.name) { Add-Error "marker skill mismatch target=$TargetName skill=$($skill.name)" }
      if ($marker.target -ne $TargetName) { Add-Error "marker target mismatch target=$TargetName skill=$($skill.name)" }
    }
    $sourceHash = Get-DirectoryHash (Join-Path (Join-Path $RepoRoot "skills") $skill.name)
    Write-Output "SHA256 target=$TargetName skill=$($skill.name) source=$sourceHash"
  }
}

$repoRoot = Get-RepoRoot
$skillSet = Read-JsonFile (Join-Path $repoRoot "manifests/skill-set.json")
$targets = Read-JsonFile (Join-Path $repoRoot "manifests/targets.json")

Test-Repo $repoRoot $skillSet $targets
foreach ($targetName in Get-SelectedTargets $Target) {
  Test-Target $repoRoot $skillSet $targets $targetName
}

if ($script:Errors.Count -gt 0) {
  Write-Output "VERIFY FAIL errors=$($script:Errors.Count) warnings=$($script:Warnings.Count)"
  exit 1
}

Write-Output "VERIFY PASS warnings=$($script:Warnings.Count)"
