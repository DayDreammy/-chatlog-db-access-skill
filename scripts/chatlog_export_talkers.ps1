# Export full chat logs for one or more talkers to JSON arrays.
# Example:
# .\chatlog_export_talkers.ps1 -Talkers "1234567890@chatroom","9876543210@chatroom" -OutDir "D:\exports"

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string[]]$Talkers,

  [string]$BaseUrl = "http://127.0.0.1:5030",

  [string]$OutDir = ".\\exports",

  # Inclusive date range.
  [string]$StartDate = "2000-01-01",
  [string]$EndDate = "2100-01-01",

  [int]$Limit = 1000
)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Export-Chatlog {
  param(
    [string]$Talker,
    [string]$BaseUrl,
    [string]$OutDir,
    [string]$StartDate,
    [string]$EndDate,
    [int]$Limit
  )

  $offset = 0
  $safeName = $Talker.Replace("@", "_")
  $outFile = Join-Path $OutDir ("{0}_chatlog.json" -f $safeName)

  if (Test-Path $outFile) { Remove-Item $outFile -Force }
  Add-Content -Path $outFile -Value "["
  $first = $true

  while ($true) {
    $encodedTalker = [uri]::EscapeDataString($Talker)
    $uri = "$BaseUrl/api/v1/chatlog?time=$StartDate~$EndDate&talker=$encodedTalker&format=json&limit=$Limit&offset=$offset"

    $batch = Invoke-RestMethod -Uri $uri
    if (-not $batch) { break }

    if ($batch -is [System.Array]) {
      $items = $batch
    } else {
      $items = @($batch)
    }

    if ($items.Count -eq 0) { break }

    foreach ($item in $items) {
      $json = $item | ConvertTo-Json -Depth 8 -Compress
      if (-not $first) { Add-Content -Path $outFile -Value "," }
      Add-Content -Path $outFile -Value $json
      $first = $false
    }

    $offset += $items.Count
    if ($items.Count -lt $Limit) { break }
  }

  Add-Content -Path $outFile -Value "]"
}

foreach ($talker in $Talkers) {
  Export-Chatlog -Talker $talker -BaseUrl $BaseUrl -OutDir $OutDir -StartDate $StartDate -EndDate $EndDate -Limit $Limit
}
