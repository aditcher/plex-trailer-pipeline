#!/bin/zsh
# batch_convert.sh
# Plex Trailer Pipeline - Batch MKV to MOV Converter
# Author: Aaron Ditcher (@aditcher)
# https://github.com/aditcher/plex-trailer-pipeline
#
# Recursively finds all .mkv files inside Trailers/ subfolders
# and re-encodes them to H.264 MOV for Plex Direct Play compatibility.
#
# Usage:
#   ./batch_convert.sh /Volumes/Movies
#   ./batch_convert.sh (defaults to /Volumes/Movies if no path given)

MOVIES_PATH="${1:-/Volumes/Movies}"

echo "🎬 Plex Trailer Pipeline - Batch Converter"
echo "==========================================="
echo "📁 Scanning: $MOVIES_PATH"
echo ""

# Count total files
TOTAL=$(find "$MOVIES_PATH" -path "*/Trailers/*.mkv" -not -path "*/#recycle/*" | wc -l | tr -d ' ')

if [ "$TOTAL" -eq 0 ]; then
  echo "✅ No MKV files found in Trailers folders. Nothing to do!"
  exit 0
fi

echo "📊 Found $TOTAL MKV file(s) to convert"
echo ""

COUNT=0
SKIPPED=0
SUCCESS=0

while IFS= read -r -d '' f; do
  COUNT=$((COUNT + 1))
  out="${f%.mkv}.mov"
  filename=$(basename "$f")
  
  echo "--------------------------------------------"
  echo "[$COUNT/$TOTAL] Converting: $filename"
  echo "--------------------------------------------"
  
  gtimeout 600 ffmpeg -y -nostdin -stats -loglevel error \
    -i "$f" \
    -c:v libx264 -crf 18 -preset fast \
    -pix_fmt yuv420p \
    -c:a aac -b:a 192k \
    "$out"
    
  if [ $? -eq 0 ]; then
    rm "$f"
    echo "✅ Done: $(basename "$out")"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "❌ SKIPPED (failed or timed out): $filename"
    SKIPPED=$((SKIPPED + 1))
  fi
  
done < <(find "$MOVIES_PATH" -path "*/Trailers/*.mkv" -not -path "*/#recycle/*" -print0)

echo ""
echo "==========================================="
echo "🎬 Batch Conversion Complete!"
echo "✅ Converted: $SUCCESS files"
echo "❌ Skipped:   $SKIPPED files"
echo "==========================================="

if [ "$SKIPPED" -gt 0 ]; then
  echo ""
  echo "⚠️  Skipped files still exist as .mkv and were NOT deleted."
  echo "   You can re-run this script to retry them."
fi
