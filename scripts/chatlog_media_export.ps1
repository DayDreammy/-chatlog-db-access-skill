# chatlog_media_export.ps1
# Export chatlog images via HTTP API and convert to JPG with ffmpeg. Also export thumbs.

param(
  [Parameter(Mandatory=$true)]
  [string]$JsonPath,
  [Parameter(Mandatory=$true)]
  [string]$OutDir,
  [string]$BaseUrl = "http://127.0.0.1:5030",
  [string]$FfmpegPath = ""
)

$ProgressPreference = 'SilentlyContinue'

if (-not (Test-Path $JsonPath)) {
  throw "JsonPath not found: $JsonPath"
}

if (-not (Test-Path $OutDir)) {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}

$raw = Get-Content -Raw -Path $JsonPath
$imgFiles = [regex]::Matches($raw, '"imgfile"\s*:\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
$thumbs = [regex]::Matches($raw, '"thumb"\s*:\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique

$thumbDir = Join-Path $OutDir "thumbs"
New-Item -ItemType Directory -Force -Path $thumbDir | Out-Null

# Export thumbs (already JPG)
foreach ($rel in $thumbs) {
  $relUrl = $rel -replace '\\','/'
  $url = "$BaseUrl/data/$relUrl"
  $stem = [System.IO.Path]::GetFileNameWithoutExtension($rel)
  $out = Join-Path $thumbDir ($stem + '.jpg')
  if (-not (Test-Path $out)) {
    try {
      Invoke-WebRequest -Uri $url -MaximumRedirection 5 -UseBasicParsing -OutFile $out -ErrorAction Stop | Out-Null
    } catch {
      # Ignore missing media
    }
  }
}

# Resolve ffmpeg
if ([string]::IsNullOrWhiteSpace($FfmpegPath)) {
  $ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
  if ($ff) { $FfmpegPath = $ff.Source }
}

if ([string]::IsNullOrWhiteSpace($FfmpegPath) -or -not (Test-Path $FfmpegPath)) {
  throw "ffmpeg not found. Set -FfmpegPath to the ffmpeg.exe path."
}

$tmpDir = Join-Path $OutDir "tmp"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

foreach ($rel in $imgFiles) {
  $relUrl = $rel -replace '\\','/'
  $url = "$BaseUrl/data/$relUrl"
  $stem = [System.IO.Path]::GetFileNameWithoutExtension($rel)
  $tmp = Join-Path $tmpDir ($stem + '.heic')
  $out = Join-Path $OutDir ($stem + '.jpg')
  if (-not (Test-Path $out)) {
    try {
      Invoke-WebRequest -Uri $url -MaximumRedirection 5 -UseBasicParsing -OutFile $tmp -ErrorAction Stop | Out-Null
    } catch {
      # Ignore missing media
    }

    $ok = $false
    if (Test-Path $tmp) {
      $len = (Get-Item $tmp).Length
      $ok = $len -gt 0
    }

    if ($ok) {
      try {
        & $FfmpegPath -y -loglevel error -i $tmp -frames:v 1 $out | Out-Null
      } catch {
      }
    }

    if (Test-Path $tmp) {
      Remove-Item $tmp -ErrorAction SilentlyContinue
    }
  }
}

# Best-effort cleanup
Remove-Item $tmpDir -ErrorAction SilentlyContinue

Write-Host "done"
