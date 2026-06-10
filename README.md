# 🎬 Plex Trailer Pipeline

A streamlined shell-based workflow for downloading YouTube trailers in 4K and automatically converting them to a format that plays perfectly on Plex with Direct Play — no transcoding, no buffering, no hesitation.

---

## 🖥️ Environment

| Component | Details |
|---|---|
| **Server** | Apple Mac Pro 7,1 (2019) — 16-Core Intel Xeon W, 96GB RAM |
| **NAS** | Synology DS423+ — 4×12TB WD Red Plus (SHR), 32.7TB |
| **Media Server** | Plex Media Server |
| **TV Client** | Samsung 85" QN90BD Neo QLED 4K (2022) |
| **Network** | Tachus 1Gbps Symmetrical |
| **OS** | macOS Tahoe |

---

## 🔧 The Problem

YouTube serves 4K video in **VP9** or **AV1** codec formats. While these are efficient for web streaming, Samsung smart TVs and many Plex clients cannot **Direct Play** these codecs natively. This forces the Plex server (in this case a Synology NAS with a low-power Intel Celeron J4125) to **transcode** the stream in real time — which it cannot handle at 4K resolution, resulting in constant stuttering and buffering.

---

## ✅ The Solution

A single shell function (`ytdl`) that:

1. Downloads the best available quality stream from YouTube (4K if available)
2. Automatically re-encodes it to **H.264 + AAC inside a `.mov` container** using `ffmpeg`
3. Delivers a file that Plex can **Direct Play** natively on Samsung TVs — zero transcoding, zero stutter

---

## 📦 Dependencies

Install via [Homebrew](https://brew.sh):

```bash
brew install yt-dlp ffmpeg coreutils
```

---

## 🚀 Setup

Add the following functions to your `~/.zprofile`:

```bash
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
```

Then reload your profile:

```bash
source ~/.zprofile
```

---

## 🎯 Usage

```bash
ytdl "https://www.youtube.com/watch?v=XXXXXXXXXXX"
```

The downloaded `.mov` file will appear in `~/Movies`, ready to move to your Plex library.

### Plex Folder Structure

```
/Movies
  /Movie Name (Year)
    /Trailers
      Trailer.mov
```

---

## 🔄 Batch Conversion

If you have existing `.mkv` trailer files that need converting to Plex-compatible format, use the included `batch_convert.sh` script:

```bash
chmod +x batch_convert.sh
./batch_convert.sh
```

This will:
- Recursively find all `.mkv` files inside `Trailers/` subfolders
- Re-encode each one to H.264 MOV using `libx264`
- Delete the original MKV after successful conversion
- Skip any file that fails or times out (10 minute timeout per file)
- Show clear progress for each file

---

## 💡 Why H.264 + MOV?

| Codec | Samsung TV Direct Play | DS423+ Transcode |
|---|---|---|
| VP9 (YouTube 4K) | ❌ No | ❌ Too slow |
| AV1 (YouTube 4K) | ❌ No | ❌ Too slow |
| H.265/HEVC | ⚠️ Sometimes | ❌ Too slow |
| **H.264 (this pipeline)** | ✅ **Always** | ✅ **Not needed** |

H.264 inside a `.mov` container is universally supported by Samsung Tizen Plex app and requires zero server-side processing — the NAS simply serves the file.

---

## 👤 Author

**Aaron Ditcher**
Senior Data & SEO Manager | Home Lab Enthusiast
- 13+ years experience in data analytics, BI, SQL, and ETL development
- Home media stack: Plex, Synology NAS, Docker, AdGuard Home, Tailscale
- GitHub: [@aditcher](https://github.com/aditcher)
