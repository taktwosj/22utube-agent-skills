param(
  [ValidateSet("all", "codex", "claude", "hermes")]
  [string]$Target = "all",
  [string[]]$Only = @(),
  [switch]$Prune,
  [switch]$Strict,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ($Only.Count -gt 0 -and $Prune) {
  throw "-Only and -Prune cannot be used together."
}
if ($Only.Count -gt 0 -and $Strict) {
  throw "-Only and -Strict cannot be used together."
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$status = git -C $repoRoot status --porcelain
if ($status) {
  throw "Dirty worktree. Commit or discard local changes before update."
}

$remote = git -C $repoRoot remote 2>$null
if ($remote) {
  if ($DryRun) {
    Write-Output "DRYRUN git pull --ff-only"
  } else {
    git -C $repoRoot pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw "git pull --ff-only failed" }
  }
} else {
  Write-Output "NO_REMOTE skip git pull"
}

$install = Join-Path $PSScriptRoot "install.ps1"
$verify = Join-Path $PSScriptRoot "verify.ps1"
$powerShellExe = $null
foreach ($candidate in @("pwsh", "pwsh.exe", "powershell", "powershell.exe")) {
  $command = Get-Command $candidate -ErrorAction SilentlyContinue
  if ($command) {
    $powerShellExe = $command.Source
    break
  }
}
if (-not $powerShellExe) {
  throw "No PowerShell executable found for install/verify subprocesses."
}

$installArgs = @("-ExecutionPolicy", "Bypass", "-File", $install, "-Target", $Target)
if ($Only.Count -gt 0) { $installArgs += "-Only"; $installArgs += $Only }
if ($Prune) { $installArgs += "-Prune" }
if ($Strict) { $installArgs += "-Strict" }
if ($DryRun) { $installArgs += "-DryRun" }

& $powerShellExe @installArgs
if ($LASTEXITCODE -ne 0) { throw "install failed" }

if ($DryRun) {
  Write-Output "DRYRUN skip target verify"
} else {
  $verifyArgs = @("-ExecutionPolicy", "Bypass", "-File", $verify, "-Target", $Target)
  if ($Strict) { $verifyArgs += "-Strict" }
  & $powerShellExe @verifyArgs
  if ($LASTEXITCODE -ne 0) { throw "verify failed" }
}

Write-Output "DONE update target=$Target dry_run=$($DryRun.IsPresent)"
