#!/bin/zsh
# ytdl_setup.sh
# Plex Trailer Pipeline - Shell Function Setup
# Author: Aaron Ditcher (@aditcher)
# https://github.com/aditcher/plex-trailer-pipeline
#
# Adds ytdl functions to ~/.zprofile for downloading and
# converting YouTube trailers to Plex-compatible format.

echo "🎬 Plex Trailer Pipeline - Setup"
echo "================================="

# Backup existing zprofile
if [ -f ~/.zprofile ]; then
  cp ~/.zprofile ~/.zprofile.backup
  echo "✅ Backed up ~/.zprofile to ~/.zprofile.backup"
fi

# Write functions to zprofile
cat >> ~/.zprofile << 'EOF'

# ==============================================
# Plex Trailer Pipeline - YouTube Download Tools
# https://github.com/aditcher/plex-trailer-pipeline
# ==============================================

# Download best available quality (4K if offered) and convert to Plex-compatible MOV
ytdl() {
  cd ~/Movies
  yt-dlp --cookies-from-browser firefox -f "bestvideo+bestaudio" --merge-output-format mkv -o "%(title)s_temp.mkv" "$1"
  local latest=$(ls -t ~/Movies/*_temp.mkv | head -1)
  local output="${latest/_temp.mkv/.mov}"
  ffmpeg -y -nostdin -stats -loglevel error -i "$latest" -c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p -c:a aac -b:a 192k "$output"
  rm "$latest"
  echo "Done: $output"
}

# Download at exactly 1440p 60fps
ytdl1440() {
  cd ~/Movies && yt-dlp -f "bv*[height=1440][fps>=60]+ba/b[height=1440]" --merge-output-format mkv "$1"
}

# Download capped at 1080p
ytdl1080() {
  cd ~/Movies && yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mkv "$1"
}
EOF

echo "✅ Functions added to ~/.zprofile"

# Reload profile
source ~/.zprofile
echo "✅ Profile reloaded"
echo ""
echo "🎯 Ready! Usage:"
echo '   ytdl "https://www.youtube.com/watch?v=XXXXXXXXXXX"'
echo ""
echo "Output will be saved to ~/Movies as a .mov file"
