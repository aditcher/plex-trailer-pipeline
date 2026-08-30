# 🪟 Plex Trailer Pipeline — Windows

A PowerShell-based workflow for Windows that downloads YouTube videos and trailers and converts them to a format that Plex can play directly — no buffering, no stuttering.

## The Problem

YouTube serves video using the **VP9** (or AV1) codec. While great for web streaming, VP9 is not natively supported for Direct Play by many Plex clients — including Samsung smart TVs. When Plex encounters a VP9 file, it falls back to **transcoding** on the fly. On low-power NAS hardware like the Synology DS423+ (Intel Celeron J4125), real-time 4K transcoding is simply too much, resulting in constant stuttering and buffering even on a gigabit local network.

## The Solution

Download the video from YouTube using **yt-dlp**, then immediately re-encode the video track from VP9 to **H.264** using **ffmpeg**, keeping the file in an **MKV container**. Plex can Direct Play H.264/MKV natively on virtually every client device, including Samsung TVs, with zero transcoding overhead.

Before running the script, find the **highest resolution version** of the video on YouTube — if a 4K version exists, find it and copy that URL. The script will always download the best quality stream available at that URL, so starting with the best source gives you the best result.

---

## Requirements

- Windows 10 or 11
- PowerShell 5.1 or later (built into Windows)
- yt-dlp
- ffmpeg

## Install Dependencies

Open **PowerShell as Administrator** and run:

```powershell
winget install yt-dlp
winget install ffmpeg
```

Then allow PowerShell scripts to run (one-time setup):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Setup

```powershell
.\ytdl_setup_windows.ps1
```

---

## Usage

1. On YouTube, find the video you want — look for the **4K or highest resolution version** available
2. Copy the URL from your browser
3. Open **PowerShell** and paste the command with your URL in quotes:

```powershell
ytdl "https://www.youtube.com/watch?v=76b5nfuGpG4"
```

Output is saved to `%USERPROFILE%\Videos` as an H.264 MKV file, ready to move to your Plex library.

---

## Batch Convert Existing Files

If you already have VP9/AV1 MKV trailers in your Plex library that were downloaded before this fix, use the batch converter to re-encode them all at once.

For a NAS network path:

```powershell
.\batch_convert_windows.ps1 -MoviesPath "\\NAS\Movies"
```

For a local drive path:

```powershell
.\batch_convert_windows.ps1 -MoviesPath "D:\Plex\Movies"
```

This recursively finds all `.mkv` files inside `Trailers\` subfolders and re-encodes them to H.264 in place. Original files are deleted after successful conversion.

---

## Plex Folder Structure

For Plex to recognize local trailers, place them in a `Trailers\` subfolder next to the movie:

```
\Movies\
  Blade Runner 2049\
    Blade Runner 2049.mkv
    Trailers\
      Blade Runner 2049 - Official Trailer.mkv
```

For TV shows (requires Plex Pass), place trailers at the show root level:

```
\TV Shows\
  The Mandalorian\
    Trailers\
      The Mandalorian - Season 1 Trailer.mkv
    Season 01\
      ...
```

---

## Notes

- The `ytdl` function always downloads the **highest resolution stream available** at the URL you provide — 4K, 1440p, 1080p, whatever YouTube offers. The video track is then re-encoded to H.264 and the audio to AAC at 192k.
- Encoding uses `libx264` with CRF 18 for high quality. Larger files may take a few minutes depending on your hardware.
- The `ytdl1080` and `ytdl1440` variants download raw MKV without re-encoding, useful when you want the original stream for non-Plex use.
- If `winget` is not available on your system, download yt-dlp and ffmpeg manually from their official websites and add them to your system PATH.

---

[← Back to main README](README.md) | [macOS instructions →](README_mac.md)
