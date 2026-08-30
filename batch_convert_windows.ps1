# batch_convert_windows.ps1
# Plex Trailer Pipeline - Windows Batch MKV Re-encoder
# Re-encodes VP9/AV1 MKV trailers to H.264 MKV for Plex Direct Play compatibility.
#
# Recursively finds all .mkv files inside Trailers\ subfolders and re-encodes
# the video track to H.264. Audio is converted to AAC. Original files are
# deleted after successful conversion.
#
# Usage:
#   .\batch_convert_windows.ps1 -MoviesPath "\\NAS\Movies"
#   .\batch_convert_windows.ps1 -MoviesPath "D:\Plex\Movies"
#   .\batch_convert_windows.ps1              (prompts for path if not provided)
#
# Requirements:
#   ffmpeg must be installed and available in your PATH.
#   Install via: winget install ffmpeg

param(
  [string]$MoviesPath = ""
)

# Prompt if no path provided
if (-not $MoviesPath) {
  $MoviesPath = Read-Host "Enter the path to your Movies folder (e.g. \\NAS\Movies or D:\Plex\Movies)"
}

Write-Host ""
Write-Host "Plex Trailer Pipeline - Windows Batch Converter" -ForegroundColor Cyan
Write-Host "================================================="
Write-Host "Scanning: $MoviesPath" -ForegroundColor Yellow
Write-Host ""

# Check ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: ffmpeg not found. Install it with: winget install ffmpeg" -ForegroundColor Red
  exit 1
}

# Find all MKV files in Trailers subfolders
$files = Get-ChildItem -Path $MoviesPath -Recurse -Filter "*.mkv" |
         Where-Object { $_.DirectoryName -match "\\Trailers$" }

$total = $files.Count

if ($total -eq 0) {
  Write-Host "No MKV files found in Trailers folders. Nothing to do!" -ForegroundColor Green
  exit 0
}

Write-Host "Found $total MKV file(s) to convert" -ForegroundColor Yellow
Write-Host ""

$count = 0
$success = 0
$skipped = 0

foreach ($file in $files) {
  $count++
  $input = $file.FullName
  $tempOutput = $input -replace "\.mkv$", "_h264.mkv"
  $filename = $file.Name

  Write-Host "--------------------------------------------"
  Write-Host "[$count/$total] Converting: $filename" -ForegroundColor Cyan
  Write-Host "--------------------------------------------"

  ffmpeg -y -nostdin -stats -loglevel error `
    -i $input `
    -c:v libx264 -crf 18 -preset fast `
    -pix_fmt yuv420p `
    -c:a aac -b:a 192k `
    $tempOutput

  if ($LASTEXITCODE -eq 0) {
    Remove-Item $input
    Rename-Item $tempOutput $input
    Write-Host "Done: $filename" -ForegroundColor Green
    $success++
  } else {
    Write-Host "SKIPPED (conversion failed): $filename" -ForegroundColor Red
    if (Test-Path $tempOutput) { Remove-Item $tempOutput }
    $skipped++
  }
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Batch Conversion Complete!" -ForegroundColor Cyan
Write-Host "Converted: $success files" -ForegroundColor Green
Write-Host "Skipped:   $skipped files" -ForegroundColor Red
Write-Host "=================================================" -ForegroundColor Cyan

if ($skipped -gt 0) {
  Write-Host ""
  Write-Host "Skipped files were NOT deleted. Re-run this script to retry them." -ForegroundColor Yellow
}
