# ytdl_setup_windows.ps1
# Plex Trailer Pipeline - Windows PowerShell Setup
# Adds a ytdl function to your PowerShell profile for downloading
# YouTube videos and re-encoding them to H.264 MKV for Plex Direct Play.
#
# Run this script once to install. Then use ytdl "URL" in any PowerShell window.
#
# Requirements:
#   yt-dlp and ffmpeg must be installed and available in your PATH.
#   Install via: winget install yt-dlp && winget install ffmpeg
#
# If you get an execution policy error, run this first (as Administrator):
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

Write-Host "Plex Trailer Pipeline - Windows Setup" -ForegroundColor Cyan
Write-Host "======================================="

# Check for yt-dlp
if (-not (Get-Command yt-dlp -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: yt-dlp not found. Install it with: winget install yt-dlp" -ForegroundColor Red
  exit 1
}

# Check for ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: ffmpeg not found. Install it with: winget install ffmpeg" -ForegroundColor Red
  exit 1
}

# Create PowerShell profile if it doesn't exist
if (-not (Test-Path $PROFILE)) {
  New-Item -ItemType File -Path $PROFILE -Force | Out-Null
  Write-Host "Created PowerShell profile at $PROFILE" -ForegroundColor Green
}

# Backup existing profile
Copy-Item $PROFILE "$PROFILE.backup" -Force
Write-Host "Backed up profile to $PROFILE.backup" -ForegroundColor Green

# Append ytdl function to profile
$functionBlock = @'

# ==============================================
# Plex Trailer Pipeline - YouTube Download Tools
# https://github.com/aditcher/plex-trailer-pipeline
# ==============================================

# Download best available quality and re-encode to H.264 MKV for Plex Direct Play
function ytdl {
  param([string]$url)
  $videosPath = "$env:USERPROFILE\Videos"
  Set-Location $videosPath
  yt-dlp --cookies-from-browser firefox -f "bestvideo+bestaudio" --merge-output-format mkv -o "%(title)s_temp.mkv" $url
  $latest = Get-ChildItem "$videosPath\*_temp.mkv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  $output = $latest.FullName -replace "_temp\.mkv$", ".mkv"
  ffmpeg -y -nostdin -stats -loglevel error -i $latest.FullName -c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k $output
  Remove-Item $latest.FullName
  Write-Host "Done: $output" -ForegroundColor Green
}

# Download raw MKV capped at 1080p (no re-encode)
function ytdl1080 {
  param([string]$url)
  Set-Location "$env:USERPROFILE\Videos"
  yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mkv $url
}

# Download raw MKV at exactly 1440p 60fps (no re-encode)
function ytdl1440 {
  param([string]$url)
  Set-Location "$env:USERPROFILE\Videos"
  yt-dlp -f "bv*[height=1440][fps>=60]+ba/b[height=1440]" --merge-output-format mkv $url
}
'@

Add-Content -Path $PROFILE -Value $functionBlock
Write-Host "Functions added to PowerShell profile" -ForegroundColor Green

# Reload profile
. $PROFILE
Write-Host "Profile reloaded" -ForegroundColor Green
Write-Host ""
Write-Host "Ready! Usage:" -ForegroundColor Cyan
Write-Host '  ytdl "https://www.youtube.com/watch?v=XXXXXXXXXXX"'
Write-Host ""
Write-Host "Output will be saved to $env:USERPROFILE\Videos as a Plex-compatible H.264 MKV file." -ForegroundColor Green
