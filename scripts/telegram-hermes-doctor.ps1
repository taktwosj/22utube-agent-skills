param(
  [string]$HermesHome = ""
)

$ErrorActionPreference = "Stop"

if (-not $HermesHome) {
  if ($env:HERMES_HOME) {
    $HermesHome = $env:HERMES_HOME
  } elseif ($env:LOCALAPPDATA) {
    $HermesHome = Join-Path $env:LOCALAPPDATA "Hermes"
  } else {
    $HermesHome = Join-Path $HOME ".hermes"
  }
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$commandsPath = Join-Path $repoRoot "manifests/telegram-hermes.commands.json"
$envPath = Join-Path $HermesHome ".env"

Write-Output "telegram-hermes doctor"
Write-Output "repo=$repoRoot"
Write-Output "commands_manifest=$commandsPath"
Write-Output "hermes_home=$HermesHome"
Write-Output ("commands_manifest_exists={0}" -f (Test-Path -LiteralPath $commandsPath))
Write-Output ("hermes_home_exists={0}" -f (Test-Path -LiteralPath $HermesHome))
Write-Output ("env_file_exists={0}" -f (Test-Path -LiteralPath $envPath))

if (Test-Path -LiteralPath $commandsPath) {
  $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $commandsPath | ConvertFrom-Json
  Write-Output ("allowed_commands={0}" -f @($manifest.allowed_commands).Count)
  Write-Output ("blocked_commands={0}" -f @($manifest.blocked_commands).Count)
}

$envText = ""
if (Test-Path -LiteralPath $envPath) {
  $envText = Get-Content -Raw -Encoding UTF8 -LiteralPath $envPath
}

foreach ($key in @("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_CHAT_IDS", "HONCHO_API_KEY")) {
  $isSet = $false
  if ($envText -and $envText -match ("(?m)^\s*" + [regex]::Escape($key) + "\s*=")) {
    $isSet = $true
  } elseif ([System.Environment]::GetEnvironmentVariable($key)) {
    $isSet = $true
  }
  if ($isSet) {
    Write-Output "$key=set"
  } else {
    Write-Output "$key=unset"
  }
}

Write-Output "DONE telegram-hermes doctor"
