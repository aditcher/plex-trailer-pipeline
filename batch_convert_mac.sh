#!/bin/zsh
# batch_convert.sh
# Plex Trailer Pipeline - Batch MKV Re-encoder
# Re-encodes VP9/AV1 MKV trailers to H.264 MKV for Plex Direct Play compatibility.
#
# Recursively finds all .mkv files inside Trailers/ subfolders and re-encodes
# the video track to H.264. Audio is converted to AAC. Original files are
# deleted after successful conversion.
#
# Usage:
#   ./batch_convert.sh /Volumes/Movies
#   ./batch_convert.sh             (defaults to /Volumes/Movies)

MOVIES_PATH="${1:-/Volumes/Movies}"

echo "🎬 Plex Trailer Pipeline - Batch Converter"
echo "==========================================="
echo "📁 Scanning: $MOVIES_PATH"
echo ""

TOTAL=$(find "$MOVIES_PATH" -path "*/Trailers/*.mkv" -not -path "*/#recycle/*" | wc -l | tr -d ' ')

if [ "$TOTAL" -eq 0 ]; then
  echo "✅ No MKV files found in Trailers folders. Nothing to do!"
  exit 0
fi

echo "📊 Found $TOTAL MKV file(s) to convert"
echo ""

COUNT=0
SUCCESS=0
SKIPPED=0

while IFS= read -r -d '' f; do
  COUNT=$((COUNT + 1))
  out="${f%.mkv}_h264.mkv"
  filename=$(basename "$f")

  echo "--------------------------------------------"
  echo "[$COUNT/$TOTAL] Converting: $filename"
  echo "--------------------------------------------"

  ffmpeg -y -nostdin -stats -loglevel error \
    -i "$f" \
    -c:v libx264 -crf 18 -preset fast \
    -pix_fmt yuv420p \
    -c:a aac -b:a 192k \
    "$out"

  if [ $? -eq 0 ]; then
    rm "$f"
    mv "$out" "${f}"
    echo "✅ Done: $filename"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "❌ SKIPPED (conversion failed): $filename"
    [ -f "$out" ] && rm "$out"
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
  echo "⚠️  Skipped files were NOT deleted. Re-run this script to retry them."
fi
