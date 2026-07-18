param(
  [int]$DebounceMilliseconds = 1200,
  [string]$LogPath = (Join-Path $HOME ".codex\logs\skill-runtime-sync.log")
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$skillsRoot = Join-Path $repoRoot "skills"
$syncScript = Join-Path $PSScriptRoot "sync_changed_runtime_skills.ps1"
$logParent = Split-Path -Parent $LogPath
New-Item -ItemType Directory -Path $logParent -Force | Out-Null

function Write-SyncLog([string]$Message) {
  $line = "{0} {1}" -f (Get-Date).ToString("o"), $Message
  Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

$mutex = New-Object System.Threading.Mutex($false, "Local\22utube-skill-runtime-watcher")
$lockAcquired = $mutex.WaitOne(0)
if (-not $lockAcquired) {
  Write-SyncLog "WATCHER_ALREADY_RUNNING"
  $mutex.Dispose()
  exit 0
}

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $skillsRoot
$watcher.Filter = "*"
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]'FileName, DirectoryName, LastWrite, Size'
$watcher.EnableRaisingEvents = $true

$prefix = "22utube-skill-save-" + [guid]::NewGuid().ToString("N")
$identifiers = @(
  "$prefix-changed",
  "$prefix-created",
  "$prefix-deleted",
  "$prefix-renamed"
)

Register-ObjectEvent -InputObject $watcher -EventName Changed -SourceIdentifier $identifiers[0] | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Created -SourceIdentifier $identifiers[1] | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Deleted -SourceIdentifier $identifiers[2] | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Renamed -SourceIdentifier $identifiers[3] | Out-Null

Write-SyncLog "WATCHER_STARTED repo=$repoRoot debounce_ms=$DebounceMilliseconds"

try {
  while ($true) {
    $firstEvent = Wait-Event -Timeout 1
    if (-not $firstEvent) { continue }
    if ($identifiers -notcontains $firstEvent.SourceIdentifier) {
      Remove-Event -EventIdentifier $firstEvent.EventIdentifier -ErrorAction SilentlyContinue
      continue
    }

    $paths = New-Object "System.Collections.Generic.HashSet[string]" ([System.StringComparer]::OrdinalIgnoreCase)
    if ($firstEvent.SourceEventArgs.FullPath) { [void]$paths.Add($firstEvent.SourceEventArgs.FullPath) }
    if ($firstEvent.SourceEventArgs.OldFullPath) { [void]$paths.Add($firstEvent.SourceEventArgs.OldFullPath) }
    Remove-Event -EventIdentifier $firstEvent.EventIdentifier -ErrorAction SilentlyContinue

    Start-Sleep -Milliseconds $DebounceMilliseconds
    foreach ($queued in @(Get-Event | Where-Object { $identifiers -contains $_.SourceIdentifier })) {
      if ($queued.SourceEventArgs.FullPath) { [void]$paths.Add($queued.SourceEventArgs.FullPath) }
      if ($queued.SourceEventArgs.OldFullPath) { [void]$paths.Add($queued.SourceEventArgs.OldFullPath) }
      Remove-Event -EventIdentifier $queued.EventIdentifier -ErrorAction SilentlyContinue
    }

    $changedPaths = @($paths)
    if ($changedPaths.Count -eq 0) { continue }
    Write-SyncLog ("CHANGE_DETECTED count={0}" -f $changedPaths.Count)
    try {
      $output = & $syncScript -ChangedPath $changedPaths 2>&1
      foreach ($line in @($output)) { Write-SyncLog ([string]$line) }
      if ($LASTEXITCODE -ne 0) {
        Write-SyncLog "SYNC_FAILED exit_code=$LASTEXITCODE"
      }
    } catch {
      Write-SyncLog ("SYNC_EXCEPTION " + $_.Exception.Message)
    }
  }
} finally {
  foreach ($identifier in $identifiers) {
    Unregister-Event -SourceIdentifier $identifier -ErrorAction SilentlyContinue
  }
  $watcher.Dispose()
  if ($lockAcquired) {
    try { [void]$mutex.ReleaseMutex() } catch {}
  }
  $mutex.Dispose()
  Write-SyncLog "WATCHER_STOPPED"
}
