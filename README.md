# Plex Trailer Pipeline

A simple shell-based workflow for macOS that downloads YouTube videos and trailers and converts them to a format that Plex can play directly — no buffering, no stuttering.

## The Problem

YouTube serves video using the **VP9** (or AV1) codec. While great for web streaming, VP9 is not natively supported for Direct Play by many Plex clients — including Samsung smart TVs. When Plex encounters a VP9 file, it falls back to **transcoding** on the fly. On low-power NAS hardware like the Synology DS423+ (Intel Celeron J4125), real-time 4K transcoding is simply too much, resulting in constant stuttering and buffering even on a gigabit local network.

## The Solution

Download the video from YouTube using **yt-dlp**, then immediately re-encode the video track from VP9 to **H.264** using **ffmpeg**, keeping the file in an **MKV container**. Plex can Direct Play H.264/MKV natively on virtually every client device, including Samsung TVs, with zero transcoding overhead.

The `ytdl` shell function handles this automatically in one command. Before running it, find the highest resolution version of the video on YouTube — if a 4K version exists, find it and copy that URL. `ytdl` will always download the best quality stream available at that URL, so starting with the best source gives you the best result.

## Requirements

- macOS (zsh)
- [Homebrew](https://brew.sh)
- yt-dlp
- ffmpeg

Install dependencies:

```bash
brew install yt-dlp ffmpeg
```

## Setup

Run the setup script to add the `ytdl` function to your `~/.zprofile`:

```bash
chmod +x ytdl_setup.sh
./ytdl_setup.sh
```

Or manually add the contents of `ytdl_setup.sh` to your `~/.zprofile` and run `source ~/.zprofile`.

## Usage

1. On YouTube, find the video you want — look for the **4K or highest resolution version** available
2. Copy the URL from your browser
3. Open **Terminal** and paste the command with your URL in quotes:

```bash
ytdl "https://www.youtube.com/watch?v=76b5nfuGpG4"
```

The script will download the highest quality stream available and re-encode it to H.264 automatically. Output is saved to `~/Movies` as an MKV file, ready to move to your Plex library.

## Batch Convert Existing Files

If you already have VP9/AV1 MKV trailers in your Plex library that were downloaded before this fix, use the batch converter to re-encode them all at once:

```bash
chmod +x batch_convert.sh
./batch_convert.sh /Volumes/Movies
```

This recursively finds all `.mkv` files inside `Trailers/` subfolders on your NAS and re-encodes them to H.264 in place. Original files are deleted after successful conversion.

## Plex Folder Structure

For Plex to recognize local trailers, place them in a `Trailers/` subfolder next to the movie:

```
/Movies/
  Blade Runner 2049/
    Blade Runner 2049.mkv
    Trailers/
      Blade Runner 2049 - Official Trailer.mkv
```

For TV shows (requires Plex Pass), place trailers at the show root level:

```
/TV Shows/
  The Mandalorian/
    Trailers/
      The Mandalorian - Season 1 Trailer.mkv
    Season 01/
      ...
```

## Notes

- The `ytdl` function always downloads the **highest resolution stream available** at the URL you provide — 4K, 1440p, 1080p, whatever YouTube offers. For the best result, find the highest quality version of the video on YouTube before copying the URL. If a 4K version exists, use that link. The video track is then re-encoded to H.264 and the audio to AAC at 192k.
- Encoding is done using `libx264` (software) with CRF 18 for high quality. On a Mac Pro with Apple Silicon or a fast Intel CPU this is quick; on older hardware larger files may take a few minutes.
- The `ytdl1080` and `ytdl1440` variants download raw MKV without re-encoding, useful when you want the original stream for non-Plex use.

## Author

Aaron Ditcher — [github.com/aditcher](https://github.com/aditcher)
