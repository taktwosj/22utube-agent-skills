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
$configPath = Join-Path $HermesHome "config.yaml"
$channelDirectoryPath = Join-Path $HermesHome "channel_directory.json"
$gatewayStatePath = Join-Path $HermesHome "gateway_state.json"

Write-Output "telegram-hermes doctor"
Write-Output "repo=$repoRoot"
Write-Output "commands_manifest=$commandsPath"
Write-Output "hermes_home=$HermesHome"
Write-Output ("commands_manifest_exists={0}" -f (Test-Path -LiteralPath $commandsPath))
Write-Output ("hermes_home_exists={0}" -f (Test-Path -LiteralPath $HermesHome))
Write-Output ("env_file_exists={0}" -f (Test-Path -LiteralPath $envPath))
Write-Output ("config_exists={0}" -f (Test-Path -LiteralPath $configPath))
Write-Output ("channel_directory_exists={0}" -f (Test-Path -LiteralPath $channelDirectoryPath))
Write-Output ("gateway_state_exists={0}" -f (Test-Path -LiteralPath $gatewayStatePath))

if (Test-Path -LiteralPath $commandsPath) {
  $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $commandsPath | ConvertFrom-Json
  Write-Output ("allowed_commands={0}" -f @($manifest.allowed_commands).Count)
  Write-Output ("blocked_commands={0}" -f @($manifest.blocked_commands).Count)
}

$envText = ""
if (Test-Path -LiteralPath $envPath) {
  $envText = Get-Content -Raw -Encoding UTF8 -LiteralPath $envPath
}

foreach ($key in @("TELEGRAM_BOT_TOKEN", "HONCHO_API_KEY")) {
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

$allowedChatsSet = $false
if (Test-Path -LiteralPath $configPath) {
  $configText = Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath
  $match = [regex]::Match($configText, "(?m)^\s*allowed_chats:\s*(.*?)\s*$")
  if ($match.Success) {
    $value = $match.Groups[1].Value.Trim().Trim("'").Trim('"')
    $allowedChatsSet = -not [string]::IsNullOrWhiteSpace($value) -and $value -ne "[]"
  }
}
Write-Output ("telegram_allowed_chats_config={0}" -f ($(if ($allowedChatsSet) { "set" } else { "unset" })))

$knownTelegramChats = 0
if (Test-Path -LiteralPath $channelDirectoryPath) {
  $channelDirectory = Get-Content -Raw -Encoding UTF8 -LiteralPath $channelDirectoryPath | ConvertFrom-Json
  if ($channelDirectory.platforms -and $channelDirectory.platforms.telegram) {
    $knownTelegramChats = @($channelDirectory.platforms.telegram).Count
  }
}
Write-Output "telegram_known_chats_count=$knownTelegramChats"

$telegramGatewayState = "unknown"
if (Test-Path -LiteralPath $gatewayStatePath) {
  $gatewayState = Get-Content -Raw -Encoding UTF8 -LiteralPath $gatewayStatePath | ConvertFrom-Json
  if ($gatewayState.platforms -and $gatewayState.platforms.telegram -and $gatewayState.platforms.telegram.state) {
    $telegramGatewayState = [string]$gatewayState.platforms.telegram.state
  }
}
Write-Output "telegram_gateway_state=$telegramGatewayState"

Write-Output "DONE telegram-hermes doctor"
