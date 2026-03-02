# Convert simplified chatlog JSON to readable Markdown.
# Example:
# .\chatlog_export_markdown.ps1 -InputPaths "D:\exports\xxx_simple.json" -OutDir "D:\exports"

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string[]]$InputPaths,

  [string]$OutDir = ".\\exports"
)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

foreach ($inputPath in $InputPaths) {
  $items = Get-Content -Raw -Path $inputPath | ConvertFrom-Json
  if (-not $items) { continue }

  $baseName = [System.IO.Path]::GetFileNameWithoutExtension($inputPath)
  $outFile = Join-Path $OutDir ("{0}.md" -f $baseName)

  $sorted = $items | Sort-Object { [datetime]$_.time }

  $lines = @()
  $lines += "# Chatlog Backup"
  $lines += ""
  $lines += "Source: $baseName"
  $lines += ""

  foreach ($item in $sorted) {
    $time = $item.time
    $sender = if ([string]::IsNullOrWhiteSpace($item.senderName)) { "(system)" } else { $item.senderName }
    $content = if ($null -eq $item.content) { "" } else { $item.content }
    $id = if ($null -eq $item.id) { "" } else { $item.id }

    if ($id -ne "") {
      $lines += "- [$time] **$sender**: $content  ``id:$id``"
    } else {
      $lines += "- [$time] **$sender**: $content"
    }
  }

  $lines | Set-Content -Path $outFile
}
