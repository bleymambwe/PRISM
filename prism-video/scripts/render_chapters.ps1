$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$filmPath = Join-Path $projectRoot 'src\data\film.json'
$outputDirectory = Join-Path $projectRoot 'renders\chapters'
$film = Get-Content -LiteralPath $filmPath -Raw | ConvertFrom-Json

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$chapters = $film.scenes |
  Where-Object { -not $_.isEpilogue } |
  Select-Object -ExpandProperty chapter -Unique

foreach ($chapter in $chapters) {
  $slug = $chapter -replace '[^A-Za-z0-9-]', '-'
  $compositionId = "PRISM-$slug"
  $outputPath = Join-Path $outputDirectory "$slug.mp4"

  & npx remotion render src/index.ts $compositionId $outputPath `
    --codec=h264 `
    --crf=17 `
    --concurrency=6

  if ($LASTEXITCODE -ne 0) {
    throw "Chapter render failed for $compositionId"
  }
}
