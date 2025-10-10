import sys, os, re, json, time, threading, urllib.parse, requests
from urllib.parse import urlparse, parse_qs
import yt_dlp
from yt_dlp.utils import ExtractorError, DownloadError

# ── Qt imports ─────────────────────────────────────────────────────────────────
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QLabel, QMessageBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
# ───────────────────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
#  Core helpers
# ══════════════════════════════════════════════════════════════════════════════
def _iter_channel_playlists(channel_url: str) -> list[str]:
    """
    Return *full* playlist URLs that belong to a YouTube channel.
    If the channel has no Playlists tab, returns [] without raising.
    """
    pl_url = channel_url.rstrip("/") + "/playlists"
    opts   = {'extract_flat': True, 'skip_download': True, 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(pl_url, download=False)
            return [
                f"https://www.youtube.com/playlist?list={e['id']}"
                for e in info.get("entries", [])
                if e.get("ie_key") == "YoutubePlaylist"
            ]
    except (ExtractorError, DownloadError) as e:
        if "does not have a playlists tab" in str(e):
            return []
        raise


def download_youtube_video(url: str, folder: str, quality: str) -> bool:
    """
    Download a video or playlist. 
    Always save playlists under <playlist title>\\<video title>.<ext>.
    """
    if not url:
        return False

    # ── 0. Resolve default folder ────────────────────────────────────────────
    if not folder or folder.startswith("YT25"):
        folder = os.getcwd()

    parsed   = urlparse(url)
    qs       = parse_qs(parsed.query)
    is_playlist = "list" in qs

    # ── 1. Build sub-folder template ──────────────────────────────────────────
    if is_playlist:
        subdir = "%(playlist_title,NA)s"
    else:
        subdir = ""

    rel_path = os.path.join(subdir, "%(uploader)s - %(title)s.%(ext)s") if subdir else "%(uploader)s - %(title)s.%(ext)s"


    ydl_opts = {
        "outtmpl"    : os.path.join(folder, rel_path),
        "noplaylist" : not is_playlist,   # only follow playlists if they are explicitly passed
        "ignoreerrors": True,
    }

    # ── 2. Quality / format switch ────────────────────────────────────────────
    if quality == "2160p":
        ydl_opts["format"] = "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]"
    elif quality == "1080p":
        ydl_opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]"
    elif quality == "720p":
        ydl_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]"
    elif quality == "Audio Only":
        ydl_opts["format"] = "bestaudio/best"

    # ── 3. Fire download ───────────────────────────────────────────────────────
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"✘ {url} → {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  GUI helpers
# ══════════════════════════════════════════════════════════════════════════════
def select_folder():
    folder = QFileDialog.getExistingDirectory(window, "Select Folder")
    if folder:
        folder_label.setText(f"Download Folder: {folder}")



def download_video_thread(url, folder, quality):
    ok = download_youtube_video(url, folder, quality)
    print(("✔" if ok else "✘"), url)


def on_download_clicked():
    urls   = [e.text().strip() for e in url_entries if e.text().strip()]
    folder = folder_label.text().replace("Download Folder: ", "").strip()
    if not folder or folder.startswith("#not set"):
        folder = os.getcwd()

    qmode  = download_mode_group.checkedButton().text()

    for url in urls:
        threading.Thread(
            target=download_video_thread,
            args=(url, folder, qmode),
            daemon=True
        ).start()

    #QMessageBox.information(
    #    window, "Download started",
    #    "Downloads are running in the background. Watch the terminal for progress."
    #)


# ══════════════════════════════════════════════════════════════════════════════
#  Qt UI
# ══════════════════════════════════════════════════════════════════════════════
app    = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("YouTube Downloader")
window.setGeometry(100, 100, 200, 400)

url_label   = QLabel("YouTube URL(s):")
folder_label = QLabel("Download Folder: <not set>")

folder_button = QPushButton("Select Folder")
download_button = QPushButton("Download")

download_mode_group = QButtonGroup()
video_2160p_radio    = QRadioButton("2160p")
video_1080p_radio   = QRadioButton("1080p")
video_720p_radio    = QRadioButton("720p")
audio_radio         = QRadioButton("Audio Only")
video_720p_radio.setChecked(True)

for rb in (video_2160p_radio, video_1080p_radio, video_720p_radio, audio_radio):
    download_mode_group.addButton(rb)

url_entries = [QLineEdit() for _ in range(25)]

# ── Layout --------------------------------------------------------------------
main  = QVBoxLayout()
u_v   = QVBoxLayout()
f_h   = QHBoxLayout()
r_v   = QVBoxLayout()

u_v.addWidget(url_label)
for e in url_entries:
    u_v.addWidget(e)

f_h.addWidget(folder_label)
f_h.addWidget(folder_button)

for rb in (video_2160p_radio, video_1080p_radio, video_720p_radio, audio_radio):
    r_v.addWidget(rb)

main.addLayout(u_v)
main.addLayout(r_v)
main.addLayout(f_h)
main.addWidget(download_button)

# ── Signals -------------------------------------------------------------------
folder_button.clicked.connect(select_folder)
download_button.clicked.connect(on_download_clicked)

window.setLayout(main)
window.show()
sys.exit(app.exec_())
