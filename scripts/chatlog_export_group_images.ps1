# Export JPG images for a specific chatroom within a time range.
# Example:
# .\chatlog_export_group_images.ps1 -Talker "1234567890@chatroom" -StartDate "2025-01-01" -EndDate "2025-12-31" -OutDir "D:\exports\group_images" -FfmpegPath "D:\ffmpeg\bin\ffmpeg.exe"

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Talker,

  [Parameter(Mandatory = $true)]
  [string]$StartDate,

  [Parameter(Mandatory = $true)]
  [string]$EndDate,

  [Parameter(Mandatory = $true)]
  [string]$OutDir,

  [string]$BaseUrl = "http://127.0.0.1:5030",

  [string]$FfmpegPath = ""
)

$ProgressPreference = 'SilentlyContinue'

if (-not (Test-Path $OutDir)) {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}

$tempDir = Join-Path $OutDir "_tmp"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
$tempJson = Join-Path $tempDir "chatlog.json"

# Fetch chat logs with pagination
$offset = 0
$limit = 1000
$first = $true
if (Test-Path $tempJson) { Remove-Item $tempJson -Force }
Add-Content -Path $tempJson -Value "["

while ($true) {
  $talkerEncoded = [uri]::EscapeDataString($Talker)
  $uri = "$BaseUrl/api/v1/chatlog?time=$StartDate~$EndDate&talker=$talkerEncoded&format=json&limit=$limit&offset=$offset"
  $batch = Invoke-RestMethod -Uri $uri
  if (-not $batch) { break }

  if ($batch -is [System.Array]) { $items = $batch } else { $items = @($batch) }
  if ($items.Count -eq 0) { break }

  foreach ($item in $items) {
    $json = $item | ConvertTo-Json -Depth 8 -Compress
    if (-not $first) { Add-Content -Path $tempJson -Value "," }
    Add-Content -Path $tempJson -Value $json
    $first = $false
  }

  $offset += $items.Count
  if ($items.Count -lt $limit) { break }
}

Add-Content -Path $tempJson -Value "]"

# Export images and convert to JPG
$mediaOut = Join-Path $OutDir "images"
$mediaExportScript = Join-Path $PSScriptRoot "chatlog_media_export.ps1"
& $mediaExportScript `
  -JsonPath $tempJson `
  -OutDir $mediaOut `
  -BaseUrl $BaseUrl `
  -FfmpegPath $FfmpegPath

# Cleanup temp
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "done"
