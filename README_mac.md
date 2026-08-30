# Plex Trailer Pipeline — macOS

A desktop app for macOS that downloads YouTube videos and trailers and converts them to a format Plex can play directly — no buffering, no stuttering. It can also extract just the audio from a video, in your choice of format.

## The Problem

YouTube serves video using the VP9 (or AV1) codec. While great for web streaming, VP9 is not natively supported for Direct Play by many Plex clients — including Samsung smart TVs. When Plex encounters a VP9 file, it falls back to transcoding on the fly. On low-power NAS hardware like the Synology DS423+ (Intel Celeron J4125), real-time 4K transcoding is simply too much, resulting in constant stuttering and buffering even on a gigabit local network.

## The Solution

The app downloads the video from YouTube using yt-dlp, checks the video codec with ffprobe, and only re-encodes when it actually needs to:

- If the source is already H.264, the app just remuxes it into an MKV container (fast, no quality loss).
- If the source is VP9/AV1 (the YouTube default), the app re-encodes the video track to H.264 with ffmpeg, keeping the file in an MKV container.

Either way, the result is an H.264/MKV file that Plex can Direct Play natively on virtually every client device, including Samsung TVs, with zero transcoding overhead.

## Getting the App

Download the latest .dmg from the Releases page on GitHub (github.com/aditcher/plex-trailer-pipeline/releases) — pick Apple Silicon (M1/M2/M3/M4 Macs) or Intel, matching your machine. Open the DMG and drag YouTubeURLDownloader to your Applications folder.

yt-dlp, ffmpeg, and ffprobe are bundled inside the app — no separate install needed.

## Usage

1. Open YouTubeURLDownloader
2. Paste a YouTube URL into the YouTube URL field
3. Choose a Format:

   - Full Video — H.264/MKV video, ready for Plex. Remuxes if already H.264, otherwise re-encodes.
   - MP3 — Audio only, .mp3. Transcoded, since MP3 isn't YouTube's native codec.
   - AAC (M4A) — Audio only, .m4a. Usually a direct stream copy, matching YouTube's native audio, with no quality loss.
   - FLAC — Audio only, .flac. Transcoded to lossless FLAC.
   - Opus — Audio only, .opus. Usually a direct stream copy, matching YouTube's native audio, with no quality loss.

   Each audio format always downloads at that format's maximum quality — there's no bitrate to configure.

4. Choose (or confirm) your local working folder — this is where the finished file is saved
5. Click Download

The output log at the bottom shows live progress, and turns green with a "Saved to:" line when the file is ready. If a download fails, click Retry.

## Batch Convert Existing Files

If you already have VP9/AV1 MKV trailers in your Plex library from before this fix, use the batch converter to re-encode them all at once:

chmod +x batch_convert_mac.sh
./batch_convert_mac.sh /Volumes/Movies

This recursively finds all .mkv files inside Trailers/ subfolders on your NAS and re-encodes them to H.264 in place. Original files are deleted after successful conversion.

## Plex Folder Structure

For Plex to recognize local trailers, place them in a Trailers/ subfolder next to the movie:

/Movies/
  Blade Runner 2049/
    Blade Runner 2049.mkv
    Trailers/
      Blade Runner 2049 - Official Trailer.mkv

For TV shows (requires Plex Pass), place trailers at the show root level:

/TV Shows/
  The Mandalorian/
    Trailers/
      The Mandalorian - Season 1 Trailer.mkv
    Season 01/
      ...

## Notes

- Full Video mode always downloads the highest resolution stream available at the URL you provide — 4K, 1440p, 1080p, whatever YouTube offers.
- Video re-encoding (when needed) uses libx264 (software) with CRF 18 for high quality, audio at AAC 192k. On Apple Silicon or a fast Intel CPU this is quick; on older hardware larger files may take a few minutes.
- M4A and Opus are YouTube's own native audio codecs, so extracting to either format is typically an instant copy of the original stream — not a re-encode, and no quality loss. MP3 and FLAC don't match YouTube's source codec, so those two genuinely transcode.

## Author

Aaron Ditcher — github.com/aditcher
