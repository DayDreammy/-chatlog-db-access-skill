# List chatlog entities (contacts, chatrooms, sessions).
# Examples:
# .\chatlog_list.ps1 -Type chatroom -OutFile .\chatrooms.json
# .\chatlog_list.ps1 -Type contact

[CmdletBinding()]
param(
  [ValidateSet('contact','chatroom','session')]
  [string]$Type = 'chatroom',

  [string]$BaseUrl = 'http://127.0.0.1:5030',

  [string]$OutFile = ''
)

$uri = "$BaseUrl/api/v1/$Type"
$resp = Invoke-RestMethod -Uri $uri

if ($resp -is [string]) {
  $firstLine = ($resp -split "\r?\n")[0]
  if ($firstLine -match ',') {
    # Some endpoints return CSV text.
    $resp = $resp | ConvertFrom-Csv
  } else {
    # Session endpoint returns plain text. Extract ids inside parentheses.
    $rows = @()
    foreach ($line in ($resp -split "\r?\n")) {
      if (-not $line) { continue }
      $m = [regex]::Match($line, '\(([^)]+)\)')
      if ($m.Success) {
        $rows += [pscustomobject]@{ id = $m.Groups[1].Value; line = $line }
      }
    }
    $resp = $rows
  }
}

if ($OutFile -and $OutFile.Trim().Length -gt 0) {
  $dir = Split-Path -Parent $OutFile
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $resp | ConvertTo-Json -Depth 8 | Set-Content -Path $OutFile -Encoding UTF8
} else {
  $resp | ConvertTo-Json -Depth 8
}
