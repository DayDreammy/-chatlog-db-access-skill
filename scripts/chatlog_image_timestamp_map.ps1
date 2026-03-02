# chatlog_image_timestamp_map.ps1
# Build a CSV mapping decoded image filenames to send time and sender info.

param(
  [Parameter(Mandatory=$true)]
  [string]$JsonPath,
  [Parameter(Mandatory=$true)]
  [string]$ImageDir,
  [Parameter(Mandatory=$true)]
  [string]$OutCsv
)

if (-not (Test-Path $JsonPath)) { throw "JsonPath not found: $JsonPath" }
if (-not (Test-Path $ImageDir)) { throw "ImageDir not found: $ImageDir" }

# Collect decoded image stems (jpg)
$imgStems = Get-ChildItem -Path $ImageDir -Filter *.jpg | ForEach-Object { $_.BaseName } | Sort-Object -Unique
$imgSet = @{}
foreach ($s in $imgStems) { $imgSet[$s] = $true }

# Parse JSON and map imgfile to time/sender
$data = Get-Content -Raw -Path $JsonPath | ConvertFrom-Json
$rows = foreach ($m in $data) {
  if ($null -ne $m.contents -and $null -ne $m.contents.imgfile) {
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($m.contents.imgfile)
    if ($imgSet.ContainsKey($stem)) {
      [PSCustomObject]@{
        filename = "$stem.jpg"
        time = $m.time
        sender = $m.sender
        senderName = $m.senderName
        talker = $m.talker
      }
    }
  }
}

$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
Write-Host "done"
