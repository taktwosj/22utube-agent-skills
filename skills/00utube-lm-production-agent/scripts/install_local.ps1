param(
  [string]$RepoRoot = "",
  [bool]$InstallRouter = $true
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
  $RepoRoot = Join-Path $HOME "agent-skills"
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
  git clone https://github.com/taktwosj/22utube-agent-skills.git $RepoRoot
  if ($LASTEXITCODE -ne 0) { throw "git clone failed" }
}

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
git -C $RepoRoot pull --ff-only
if ($LASTEXITCODE -ne 0) { throw "git pull --ff-only failed" }

$install = Join-Path $RepoRoot "scripts\install.ps1"
$verify = Join-Path $RepoRoot "scripts\verify.ps1"
$only = @("00utube-lm-production-agent")
if ($InstallRouter) { $only += "22utube-production-agent" }

$installArgs = @("-ExecutionPolicy", "Bypass", "-File", $install, "-Target", "codex", "-Only") + $only
powershell @installArgs
if ($LASTEXITCODE -ne 0) { throw "Git skill install failed" }

powershell -ExecutionPolicy Bypass -File $verify -Target codex
if ($LASTEXITCODE -ne 0) { throw "Git skill verify failed" }

Write-Host "Installed Git-managed skills from $RepoRoot"
