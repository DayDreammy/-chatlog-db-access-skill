# Export text-only chat logs for all talkers.
# Defaults to include contacts, chatrooms, and sessions.
# Example:
# .\chatlog_export_all_text.ps1 -OutDir D:\exports -StartDate 2000-01-01 -EndDate 2026-01-21

[CmdletBinding()]
param(
  [string]$BaseUrl = 'http://127.0.0.1:5030',

  [string]$OutDir = '.\exports',

  # Inclusive date range.
  [string]$StartDate = '2000-01-01',
  [string]$EndDate = '2100-01-01',

  [int]$Limit = 1000,

  # Message types to include. For plain text, type 1 is typical.
  [int[]]$IncludeTypes = @(1),

  # Optional log file path. If set, log progress to this file and stdout.
  [string]$LogPath = "",

  # Skip talkers that already have an output file (resume mode).
  [switch]$Resume,

  [switch]$IncludeSystem,

  [switch]$NoContacts,
  [switch]$NoChatrooms,
  [switch]$NoSessions
)

if ($IncludeSystem) {
  $IncludeTypes += 10000
}

$includeSet = New-Object 'System.Collections.Generic.HashSet[int]'
foreach ($t in $IncludeTypes) { [void]$includeSet.Add([int]$t) }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Write-Log {
  param([string]$Message)
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$ts] $Message"
  Write-Output $line
  if ($LogPath -and $LogPath.Trim().Length -gt 0) {
    $dir = Split-Path -Parent $LogPath
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Add-Content -Path $LogPath -Value $line
  }
}

function Get-TalkerIds {
  param([string]$Uri)

  $resp = @()
  try {
    $resp = Invoke-RestMethod -Uri $Uri
  } catch {
    return @()
  }

  if (-not $resp) { return @() }

  if ($resp -is [string]) {
    $firstLine = ($resp -split "\r?\n")[0]
    if ($firstLine -match ',') {
      $resp = $resp | ConvertFrom-Csv
    } else {
      # Session endpoint returns plain text. Extract ids inside parentheses.
      $ids = @()
      foreach ($line in ($resp -split "\r?\n")) {
        if (-not $line) { continue }
        $m = [regex]::Match($line, '\(([^)]+)\)')
        if ($m.Success) { $ids += $m.Groups[1].Value }
      }
      return $ids
    }
  }

  $list = @()
  foreach ($item in @($resp)) {
    $props = $item.PSObject.Properties.Name
    $candidates = @('talker','wxid','id','userName','username','chatroomId','chatroom_id','roomId')
    $id = $null
    foreach ($p in $candidates) {
      if ($props -contains $p) {
        $val = $item.$p
        if ($val) { $id = $val; break }
      }
    }
    if ($id) { $list += $id }
  }
  return $list
}

function Export-ChatlogText {
  param(
    [string]$Talker,
    [string]$BaseUrl,
    [string]$OutDir,
    [string]$StartDate,
    [string]$EndDate,
    [int]$Limit,
    [System.Collections.Generic.HashSet[int]]$IncludeSet
  )

  $offset = 0
  $safeName = $Talker.Replace('@', '_')
  $outFile = Join-Path $OutDir ("{0}_text.json" -f $safeName)
  $written = 0

  if ($Resume -and (Test-Path $outFile)) {
    Write-Log ("skip: {0} (exists)" -f $Talker)
    return 0
  }

  if (Test-Path $outFile) { Remove-Item $outFile -Force }
  Add-Content -Path $outFile -Value '['
  $first = $true
  $wroteAny = $false

  while ($true) {
    $encodedTalker = [uri]::EscapeDataString($Talker)
    $uri = "$BaseUrl/api/v1/chatlog?time=$StartDate~$EndDate&talker=$encodedTalker&format=json&limit=$Limit&offset=$offset"

    $batch = Invoke-RestMethod -Uri $uri
    if (-not $batch) { break }

    $items = if ($batch -is [System.Array]) { $batch } else { @($batch) }
    if ($items.Count -eq 0) { break }

    foreach ($item in $items) {
      $t = $item.type
      if ($null -ne $t -and $IncludeSet.Contains([int]$t)) {
        $json = $item | ConvertTo-Json -Depth 8 -Compress
        if (-not $first) { Add-Content -Path $outFile -Value ',' }
        Add-Content -Path $outFile -Value $json
        $first = $false
        $wroteAny = $true
        $written += 1
      }
    }

    $offset += $items.Count
    if ($items.Count -lt $Limit) { break }
  }

  Add-Content -Path $outFile -Value ']'
  if (-not $wroteAny) { Remove-Item $outFile -Force }
  return $written
}

$talkers = @()
if (-not $NoContacts) { $talkers += Get-TalkerIds "$BaseUrl/api/v1/contact" }
if (-not $NoChatrooms) { $talkers += Get-TalkerIds "$BaseUrl/api/v1/chatroom" }
if (-not $NoSessions) { $talkers += Get-TalkerIds "$BaseUrl/api/v1/session" }

$talkers = $talkers | Where-Object { $_ } | Select-Object -Unique

Write-Log ("start: talkers={0}, range={1}~{2}" -f $talkers.Count, $StartDate, $EndDate)

foreach ($talker in $talkers) {
  Write-Log ("talker: {0}" -f $talker)
  $written = Export-ChatlogText -Talker $talker -BaseUrl $BaseUrl -OutDir $OutDir -StartDate $StartDate -EndDate $EndDate -Limit $Limit -IncludeSet $includeSet
  Write-Log ("done: {0}, written={1}" -f $talker, $written)
}

Write-Log "complete"
