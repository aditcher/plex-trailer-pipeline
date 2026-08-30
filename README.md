# 🎬 Plex Trailer Pipeline

A simple workflow for downloading YouTube videos and trailers and converting them to a format that Plex can play directly — no buffering, no stuttering.

## The Problem

YouTube serves 4K video using the **VP9** (or AV1) codec. Many Plex clients — including Samsung smart TVs — cannot Direct Play VP9, forcing the Plex server to transcode in real time. On low-power NAS hardware this results in constant stuttering and buffering even on a fast local network.

## The Solution

Download from YouTube using **yt-dlp** and re-encode the video track to **H.264** using **ffmpeg**, keeping the file in an MKV container. Plex can Direct Play H.264/MKV natively on virtually every device — zero transcoding, zero stutter.

---

## 📖 Platform Instructions

| Platform | Setup Guide |
|----------|-------------|
| 🍎 macOS | [README_mac.md](README_mac.md) |
| 🪟 Windows | [README_windows.md](README_windows.md) |

---

## Author

Aaron Ditcher — [github.com/aditcher](https://github.com/aditcher)
