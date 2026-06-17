"""
YouTube URL Downloader
------------------
Paste a YouTube URL, pick a local working folder and a destination folder
(NAS, second drive, or anywhere), hit Download.

The app downloads via yt-dlp, re-encodes to H.264/AAC MKV with ffmpeg,
then moves the finished file to your destination folder automatically.

Requires: Python 3.8+, yt-dlp, ffmpeg  (auto-detected on launch)
"""

import tkinter as tk
from tkinter import filedialog, font as tkfont
import subprocess
import threading
import shutil
import json
import os
import sys
import re
from pathlib import Path

# ── Platform detection ─────────────────────────────────────────────────────────
_IS_WIN  = sys.platform == 'win32'
_IS_MAC  = sys.platform == 'darwin'

FONT_MONO = "Courier New" if _IS_WIN else "Menlo"
FONT_SANS = "Segoe UI"    if _IS_WIN else ".AppleSystemUIFont"

# Windows: prevent subprocess calls from flashing a black console window
_SUBPROCESS_FLAGS = {}
if _IS_WIN:
    _SUBPROCESS_FLAGS['creationflags'] = subprocess.CREATE_NO_WINDOW

# ── Persistent settings ───────────────────────────────────────────────────────
SETTINGS_FILE = Path.home() / ".trailer_downloader_settings.json"

def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# ── Colour palette ─────────────────────────────────────────────────────────────
BG          = "#1c1c1c"
BG_DARK     = "#0f0f0f"
BG_TERM     = "#0a0a0a"
BG_INPUT    = "#0f0f0f"
BG_BTN      = "#252525"
BG_DEST     = "#0e1810"

BORDER      = "#383838"
BORDER_DEST = "#1e3028"
DIVIDER     = "#272727"

FG          = "#d0d0d0"
FG_DIM      = "#3e3e3e"
FG_GRAY     = "#666666"
FG_LABEL    = "#ffffff"
FG_BLUE     = "#4a9eff"
FG_GREEN    = "#4caf82"
FG_YELLOW   = "#e5a443"
FG_RED      = "#e05252"
FG_TEAL     = "#38b6a8"
FG_DEST     = "#3d6b50"

BLUE_BTN    = "#0a7aff"

# ── Dependency check ───────────────────────────────────────────────────────────
def _find_tool(name):
    """Find a tool by name, checking PyInstaller bundle, PATH, and common install locations."""

    # 1. PyInstaller frozen bundle — bundled binaries live in sys._MEIPASS
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        exe_name = name + ('.exe' if _IS_WIN else '')
        bundled  = os.path.join(sys._MEIPASS, exe_name)
        if os.path.exists(bundled):
            return bundled

    # 2. Check PATH (works on both platforms)
    found = shutil.which(name)
    if found:
        return found

    # 3. macOS Homebrew fallbacks
    if _IS_MAC:
        for mac_path in (f"/usr/local/bin/{name}", f"/opt/homebrew/bin/{name}"):
            if os.path.exists(mac_path):
                return mac_path

    # 4. Windows Chocolatey / Scoop fallbacks
    if _IS_WIN:
        userprofile = os.environ.get('USERPROFILE', '')
        for win_path in (
            fr"C:\ProgramData\chocolatey\bin\{name}.exe",
            os.path.join(userprofile, 'scoop', 'shims', f"{name}.exe"),
            fr"C:\Program Files\{name}\{name}.exe",
        ):
            if os.path.exists(win_path):
                return win_path

    return name  # last resort — let subprocess fail naturally

def _tool_found(name):
    """Return True if the tool is actually locatable (not just the bare name fallback)."""
    path = _find_tool(name)
    # _find_tool returns bare name when nothing was found; check absolute path or shutil.which
    return path != name or bool(shutil.which(name))

def check_deps():
    missing = []
    for name in ("yt-dlp", "ffmpeg"):
        if not _tool_found(name):
            missing.append(name)
    return missing

def _install_hint():
    if _IS_WIN:
        return "Install via winget:  winget install yt-dlp ffmpeg"
    return "Install via Homebrew:  brew install yt-dlp ffmpeg"

YTDLP   = _find_tool("yt-dlp")
FFMPEG  = _find_tool("ffmpeg")
FFPROBE = _find_tool("ffprobe")

# ── Main app ───────────────────────────────────────────────────────────────────
class _MacBtn(tk.Frame):
    """Frame+Label button — macOS respects fg color on Labels, not Buttons."""
    def __init__(self, parent, text, bg, fg, command=None, font=None,
                 cursor="hand2", state="normal", **kw):
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self._cmd     = command
        self._fg_on   = fg
        self._fg_off  = "#777777"
        self._cursor  = cursor
        self._enabled = (state == "normal")
        self._lbl = tk.Label(self, text=text, bg=bg,
                             fg=fg if self._enabled else self._fg_off,
                             font=font, cursor=cursor if self._enabled else "arrow",
                             padx=16, pady=10)
        self._lbl.pack(fill="both", expand=True)
        self._lbl.bind("<Button-1>", self._click)
        self.bind("<Button-1>", self._click)
    def _click(self, _=None):
        if self._enabled and self._cmd:
            self._cmd()
    def config(self, **kw):
        if "state" in kw:
            self._enabled = (kw["state"] == "normal")
            self._lbl.config(
                fg=self._fg_on if self._enabled else self._fg_off,
                cursor=self._cursor if self._enabled else "arrow",
            )
        if "text"   in kw: self._lbl.config(text=kw["text"])
        if "cursor" in kw:
            self._cursor = kw["cursor"]
            if self._enabled: self._lbl.config(cursor=kw["cursor"])
        if "fg"     in kw:
            self._fg_on = kw["fg"]
            if self._enabled: self._lbl.config(fg=kw["fg"])
        if "bg"     in kw:
            self.configure(bg=kw["bg"])
            self._lbl.config(bg=kw["bg"])

class TrailerDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube URL Downloader")
        self.resizable(True, True)
        self.minsize(660, 420)
        self.configure(bg=BG)

        mono   = tkfont.Font(family=FONT_MONO, size=11)
        mono_s = tkfont.Font(family=FONT_MONO, size=10)
        sans   = tkfont.Font(family=FONT_SANS, size=12)
        sans_s = tkfont.Font(family=FONT_SANS, size=10)
        sans_xs= tkfont.Font(family=FONT_SANS, size=9)

        self._mono   = mono
        self._mono_s = mono_s
        self._sans   = sans
        self._sans_s = sans_s
        self._sans_xs= sans_xs

        settings         = load_settings()
        self._url_var    = tk.StringVar(value=settings.get("last_url", ""))
        self._local_var  = tk.StringVar(value=settings.get("local_folder", str(Path.home() / "Movies" / "Trailers")))
        self._status_var = tk.StringVar(value="Ready")
        self._running    = False

        self._build_ui()
        self._check_deps_on_start()

        self.update_idletasks()
        self.geometry("1020x555+200+200")

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        pad = dict(padx=18, pady=0)

        self._section_label("YouTube URL", pady_top=14)
        url_frame = tk.Frame(self, bg=BG)
        url_frame.pack(fill="x", padx=18, pady=(4, 0))

        self._url_entry = tk.Entry(
            url_frame,
            textvariable=self._url_var,
            bg=BG_INPUT, fg=FG,
            insertbackground=FG,
            relief="flat",
            font=self._mono_s,
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=FG_BLUE,
        )
        self._url_entry.pack(side="left", fill="x", expand=True, ipady=13, ipadx=8)

        clear_btn = tk.Button(
            url_frame, text="✕",
            bg=BG_BTN, fg=FG_GRAY,
            activebackground="#333", activeforeground=FG,
            relief="flat", bd=0,
            font=self._sans_s,
            cursor="hand2",
            command=self._clear_url,
            highlightthickness=1,
            highlightbackground=BORDER,
            width=3,
        )
        clear_btn.pack(side="left", padx=(6, 0), ipady=5)

        self._divider(pady=10)

        self._sublabel("💻  Local working folder", pady_top=0)
        self._folder_row(self._local_var, is_dest=False)

        arrow = tk.Label(self, text="↓", bg=BG, fg="#555555", font=tkfont.Font(size=14))
        arrow.pack(pady=(6, 2))


        self._divider(pady=10)

        self._section_label("Output log", pady_top=0)
        log_frame = tk.Frame(self, bg=BG_TERM,
                             highlightthickness=1, highlightbackground="#2a2a2a")
        log_frame.pack(fill="x", expand=False, padx=18, pady=(4, 0))

        self._log = tk.Text(
            log_frame,
            bg=BG_TERM, fg=FG_DIM,
            insertbackground=FG,
            relief="flat", bd=0,
            font=self._mono_s,
            state="disabled",
            wrap="none",
            cursor="arrow",
            padx=10, pady=8,
            height=15,
        )
        self._log.pack(fill="both", expand=False)

        self._log.tag_config("dim",    foreground=FG_DIM)
        self._log.tag_config("gray",   foreground=FG_GRAY)
        self._log.tag_config("blue",   foreground=FG_BLUE)
        self._log.tag_config("green",  foreground=FG_GREEN)
        self._log.tag_config("yellow", foreground=FG_YELLOW)
        self._log.tag_config("red",    foreground=FG_RED)
        self._log.tag_config("teal",   foreground=FG_TEAL)

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=18, pady=16)

        self._dot = tk.Label(bottom, text="●", bg=BG, fg=FG_GRAY,
                             font=tkfont.Font(size=9))
        self._dot.pack(side="left")

        self._status_lbl = tk.Label(bottom,
                                    textvariable=self._status_var,
                                    bg=BG, fg=FG_GRAY,
                                    font=self._sans_xs)
        self._status_lbl.pack(side="left", padx=(4, 0))

        self._result_icon = tk.Label(bottom, text="", bg=BG,
                                     font=tkfont.Font(size=13))
        self._result_icon.pack(side="left", padx=(6, 0))
        self._retry_btn = _MacBtn(
            bottom, text="↻  Retry",
            bg="#555555", fg="#ffffff",
            font=tkfont.Font(family=FONT_SANS, size=13, weight="bold"),
            cursor="hand2", state="disabled",
            command=self._retry,
        )
        self._retry_btn.pack(side="right", padx=(8, 0))
        self._dl_btn = _MacBtn(
            bottom, text="⬇  Download",
            bg="#0a7aff", fg="#ffffff",
            font=tkfont.Font(family=FONT_SANS, size=13, weight="bold"),
            cursor="hand2", state="normal",
            command=self._start_download,
        )
        self._dl_btn.pack(side="right")

    def _section_label(self, text, pady_top=8):
        lbl = tk.Label(self, text=text.upper(),
                       bg=BG, fg=FG_LABEL,
                       font=tkfont.Font(family=FONT_SANS, size=12, weight="bold"),
                       anchor="w")
        lbl.pack(fill="x", padx=18, pady=(pady_top, 0))

    def _sublabel(self, text, color=FG_LABEL, pady_top=4):
        lbl = tk.Label(self, text=text,
                       bg=BG, fg=color,
                       font=tkfont.Font(family=FONT_SANS, size=12, weight="bold"),
                       anchor="w")
        lbl.pack(fill="x", padx=18, pady=(pady_top, 2))

    def _folder_row(self, var, is_dest=False):
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="x", padx=18, pady=(0, 0))

        entry = tk.Entry(
            frame,
            textvariable=var,
            bg=BG_DEST if is_dest else BG_INPUT,
            fg=FG_DEST if is_dest else FG_GRAY,
            insertbackground=FG,
            relief="flat", bd=0,
            font=self._mono_s,
            highlightthickness=1,
            highlightbackground=BORDER_DEST if is_dest else BORDER,
            highlightcolor=FG_TEAL if is_dest else FG_BLUE,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=13, ipadx=8)

        btn_color = FG_DEST if is_dest else FG_GRAY
        btn_bg    = BG_DEST if is_dest else BG_BTN
        btn_bdr   = BORDER_DEST if is_dest else BORDER

        def _browse(v=var):
            folder = filedialog.askdirectory(initialdir=v.get() or Path.home())
            if folder:
                v.set(folder)
                self._persist()

        browse = tk.Button(
            frame, text="📂  Browse…",
            bg=btn_bg, fg=btn_color,
            activebackground="#1a2a1a" if is_dest else "#2e2e2e",
            activeforeground=FG_GREEN if is_dest else FG,
            relief="flat", bd=0,
            font=self._sans_s,
            cursor="hand2",
            command=_browse,
            highlightthickness=1,
            highlightbackground=btn_bdr,
            padx=10, pady=5,
        )
        browse.pack(side="left", padx=(6, 0))

    def _divider(self, pady=8):
        line = tk.Frame(self, bg=DIVIDER, height=1)
        line.pack(fill="x", padx=18, pady=pady)

    def _log_write(self, text, tag="gray"):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _set_status(self, text, color=FG_GRAY, dot_color=FG_GRAY, icon=""):
        self._status_var.set(text)
        self._status_lbl.config(fg=color)
        self._dot.config(fg=dot_color)
        self._result_icon.config(text=icon,
                                 fg=FG_GREEN if "✓" in icon else FG_RED)

    def _set_ready(self):
        self._set_status("Ready", FG_GRAY, FG_GRAY, "")

    def _set_success(self):
        self._set_status("Last download succeeded", FG_GREEN, FG_GREEN, "✓")

    def _set_failed(self):
        self._set_status("Last download failed", FG_RED, FG_RED, "✕")
        self._retry_btn.config(
            state="normal", cursor="hand2",
            fg=FG_YELLOW, highlightbackground="#3d2e00", bg="#150f00"
        )

    def _check_deps_on_start(self):
        missing = check_deps()
        if missing:
            self._log_write(
                f"[warn]    Missing tools: {', '.join(missing)}", "yellow")
            self._log_write(
                f"[warn]    {_install_hint()}", "yellow")
        else:
            self._log_write("$ YouTube URL Downloader ready.", "dim")
            self._log_write("[check]   yt-dlp found  ✓", "green")
            self._log_write("[check]   ffmpeg found  ✓", "green")
            self._log_write("─" * 56, "dim")
            self._log_write("[info]    Paste a YouTube URL and click Download.", "gray")

    def _clear_url(self):
        self._url_var.set("")
        self._url_entry.focus_set()

    def _persist(self):
        save_settings({
            "last_url":      self._url_var.get(),
            "local_folder":  self._local_var.get(),
        })

    def _retry(self):
        self._retry_btn.config(state="disabled", cursor="arrow",
                               fg="#444444", highlightbackground=BORDER, bg=BG_BTN)
        self._start_download()

    def _start_download(self):
        if self._running:
            return

        url       = self._url_var.get().strip()
        local_dir = self._local_var.get().strip()

        if not url:
            self._log_clear()
            self._log_write("[error]   No URL entered. Paste a YouTube link above.", "red")
            self._set_failed()
            return

        if not local_dir:
            self._log_clear()
            self._log_write("[error]   No local working folder selected.", "red")
            self._set_failed()
            return

        missing = check_deps()
        if missing:
            self._log_clear()
            self._log_write(f"[error]   Cannot run — missing: {', '.join(missing)}", "red")
            self._log_write(f"[hint]    {_install_hint()}", "yellow")
            self._set_failed()
            return

        Path(local_dir).mkdir(parents=True, exist_ok=True)
        self._persist()

        self._running = True
        self._dl_btn.config(state="disabled")
        self._log_clear()
        self._set_status("Downloading…", FG_BLUE, FG_BLUE, "")

        thread = threading.Thread(
            target=self._download_worker,
            args=(url, local_dir),
            daemon=True
        )
        thread.start()

    def _download_worker(self, url, local_dir):
        try:
            import os as _os
            _env = _os.environ.copy()
            # On macOS, prepend Homebrew paths so yt-dlp can find Node for n-challenge
            if _IS_MAC:
                _env["PATH"] = (
                    "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:"
                    + _env.get("PATH", "")
                )

            self._log_ui(f"$ ytdl \"{url[:60]}…\"", "dim")
            self._log_ui("[yt-dlp]  Fetching metadata…", "gray")

            import datetime
            temp_mkv = os.path.join(
                local_dir,
                f"_temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mkv"
            )

            ytdlp_cmd = [
                YTDLP,
                "-f", "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                "--merge-output-format", "mkv",
                "--cookies-from-browser", "firefox",
                "-o", temp_mkv,
                "--no-playlist",
                url,
            ]

            self._log_ui("[yt-dlp]  Downloading…", "blue")
            result = subprocess.run(
                ytdlp_cmd, capture_output=True, text=True, env=_env,
                **_SUBPROCESS_FLAGS
            )

            if result.returncode != 0 and "firefox" in result.stderr.lower():
                ytdlp_cmd_clean = [c for c in ytdlp_cmd
                                   if c not in ("--cookies-from-browser", "firefox")]
                result = subprocess.run(
                    ytdlp_cmd_clean, capture_output=True, text=True, env=_env,
                    **_SUBPROCESS_FLAGS
                )

            if result.returncode != 0:
                for line in result.stderr.strip().splitlines()[-4:]:
                    self._log_ui(f"[error]   {line}", "red")
                self._log_ui("─" * 56, "dim")
                self._log_ui("[hint]    Check your internet connection, then click Retry", "yellow")
                self._log_ui("[hint]    — or try a different URL.", "yellow")
                self._finish(success=False)
                return

            if not os.path.exists(temp_mkv):
                candidates = sorted(
                    Path(local_dir).glob("*.mkv"),
                    key=lambda p: p.stat().st_mtime, reverse=True
                )
                if not candidates:
                    self._log_ui("[error]   Downloaded file not found.", "red")
                    self._finish(success=False)
                    return
                temp_mkv = str(candidates[0])

            probe_title = subprocess.run(
                [YTDLP, "--get-title", "--no-playlist", url],
                capture_output=True, text=True, env=_env,
                **_SUBPROCESS_FLAGS
            )
            filename = probe_title.stdout.strip() or Path(temp_mkv).stem
            out_mkv  = os.path.join(local_dir, f"{filename}.mkv")

            self._log_ui(f"[yt-dlp]  Downloaded: {Path(temp_mkv).name}", "blue")

            # ── Smart codec check ─────────────────────────────────────
            probe = subprocess.run(
                [FFPROBE, "-v", "error",
                 "-select_streams", "v:0",
                 "-show_entries", "stream=codec_name",
                 "-of", "default=noprint_wrappers=1:nokey=1",
                 temp_mkv],
                capture_output=True, text=True,
                **_SUBPROCESS_FLAGS
            )
            codec    = probe.stdout.strip().lower()
            is_h264  = (codec == "h264")
            enc_mkv  = os.path.join(local_dir, f"{filename}_enc.mkv")

            if is_h264:
                self._log_ui("[ffprobe] Codec: H.264 ✓ — remuxing (fast, no re-encode)", "green")
                self._ui_status("Remuxing…", FG_GREEN, FG_GREEN)
                ffmpeg_cmd = [
                    FFMPEG, "-y",
                    "-i", temp_mkv,
                    "-c", "copy",
                    "-movflags", "+faststart",
                    enc_mkv,
                ]
            else:
                self._log_ui(f"[ffprobe] Codec: {codec.upper()} — re-encoding to H.264…", "yellow")
                self._log_ui("[ffmpeg]  Re-encoding → libx264 / AAC / yuv420p…", "yellow")
                self._ui_status("Re-encoding…", FG_YELLOW, FG_YELLOW)
                ffmpeg_cmd = [
                    FFMPEG, "-y",
                    "-i", temp_mkv,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    enc_mkv,
                ]

            ff = subprocess.run(
                ffmpeg_cmd, capture_output=True, text=True,
                **_SUBPROCESS_FLAGS
            )

            if ff.returncode != 0:
                for line in ff.stderr.strip().splitlines()[-4:]:
                    self._log_ui(f"[error]   {line}", "red")
                self._finish(success=False)
                return

            try:
                os.remove(temp_mkv)
            except Exception:
                pass
            os.replace(enc_mkv, out_mkv)

            self._log_ui(f"[done]    {Path(out_mkv).name}  ✓", "green")
            self._log_ui("─" * 56, "dim")
            self._log_ui(f"[ready]   Saved to: {out_mkv}  ✓", "green")

            self._finish(success=True)

        except Exception as e:
            self._log_ui(f"[error]   Unexpected error: {e}", "red")
            self._finish(success=False)

    def _log_ui(self, text, tag="gray"):
        self.after(0, lambda: self._log_write(text, tag))

    def _ui_status(self, text, color, dot_color, icon=""):
        self.after(0, lambda: self._set_status(text, color, dot_color, icon))

    def _finish(self, success: bool):
        self._running = False
        if success:
            self.after(0, self._set_success)
        else:
            self.after(0, self._set_failed)
        self.after(0, lambda: self._dl_btn.config(state="normal"))

if __name__ == "__main__":
    app = TrailerDownloader()
    app.lift()
    app.focus_force()
    app.mainloop()
