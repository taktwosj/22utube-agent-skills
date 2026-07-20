param(
  [Parameter(Mandatory = $true)]
  [string]$VideoUrl,

  [string]$Title = "untitled_shorts",

  [string]$OutputDir = "",

  [switch]$Force,

  [switch]$AllowUnverified
)

$ErrorActionPreference = "Stop"

function ConvertTo-SafeFileStem([string]$Value) {
  $normalized = $Value.Trim()
  if ([string]::IsNullOrWhiteSpace($normalized)) {
    $normalized = "untitled_shorts"
  }
  $invalid = [System.IO.Path]::GetInvalidFileNameChars()
  foreach ($ch in $invalid) {
    $normalized = $normalized.Replace([string]$ch, "_")
  }
  $normalized = [regex]::Replace($normalized, "\s+", "_")
  $normalized = [regex]::Replace($normalized, "_+", "_").Trim("_")
  if ($normalized.Length -gt 80) {
    $normalized = $normalized.Substring(0, 80).Trim("_")
  }
  if ([string]::IsNullOrWhiteSpace($normalized)) {
    $normalized = "untitled_shorts"
  }
  return $normalized
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    throw "USERPROFILE is not set."
  }
  $OutputDir = Join-Path $env:USERPROFILE "OneDrive\22utube\22factory_20260628\01_shorts_factory\germini"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$analysis = Get-Clipboard -Raw
if ([string]::IsNullOrWhiteSpace($analysis)) {
  throw "Clipboard is empty. Copy the Gemini output first."
}

$finalWarningNeedle = "STT/OCR/프레임 검증으로 확정해야 한다"
if (-not $AllowUnverified -and -not $analysis.Contains($finalWarningNeedle)) {
  throw "Clipboard does not include Gemini final_warning_ko. Copy the completed Gemini raw JSON first."
}

$date = Get-Date -Format "yyyyMMdd"
$safeTitle = ConvertTo-SafeFileStem $Title
$fileName = "{0}_{1}_gemini_raw.md" -f $date, $safeTitle
$outPath = Join-Path $OutputDir $fileName

if ((Test-Path -LiteralPath $outPath) -and -not $Force) {
  $i = 1
  do {
    $candidateName = "{0}_{1}_gemini_raw_{2:D2}.md" -f $date, $safeTitle, $i
    $candidatePath = Join-Path $OutputDir $candidateName
    $i++
  } while (Test-Path -LiteralPath $candidatePath)
  $outPath = $candidatePath
}

$body = @"
# $Title

- 영상주소: $VideoUrl
- 저장일: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
- 저장 기준 경로: `%USERPROFILE%\\OneDrive\\22utube\\22factory_20260628\\01_shorts_factory\\germini
- 상태: Gemini raw analysis, Codex 검증 전

## 분석내용

````json
$analysis
````
"@

Set-Content -LiteralPath $outPath -Value $body -Encoding UTF8

$check = Get-Content -LiteralPath $outPath -Raw -Encoding UTF8
[PSCustomObject]@{
  Path = $outPath
  Bytes = (Get-Item -LiteralPath $outPath).Length
  HasUrl = $check.Contains($VideoUrl)
  HasFinalWarning = $check.Contains($finalWarningNeedle)
  OutputDir = $OutputDir
} | Format-List
