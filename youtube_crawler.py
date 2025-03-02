import sys
import yt_dlp
import threading
import time
import os
import re
import json
import urllib.parse
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QMessageBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
import urllib.parse
import requests
from bs4 import BeautifulSoup

def search_youtube(query):
    """Search for the most viewed YouTube video matching the query."""
    query_encoded = urllib.parse.quote(query)
    search_url = f"https://www.youtube.com/results?search_query={query_encoded}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Extract JSON data embedded in the HTML response
        match = re.search(r'var ytInitialData = ({.*?});', response.text)
        if not match:
            print(f"Failed to find JSON data for: {query}")
            return None

        data = json.loads(match.group(1))  # Parse extracted JSON

        # Navigate JSON to locate video details
        videos = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        for section in videos:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                if "videoRenderer" in item:
                    video_id = item["videoRenderer"]["videoId"]
                    return f"https://www.youtube.com/watch?v={video_id}"

        print(f"No valid video found for: {query}")
        return None

    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return None
        
def download_youtube_video(url, folder, download_mode):
    if not url:
        return False

    ydl_opts = {
        'outtmpl': f'{folder}/%(title)s.%(ext)s',
        'noplaylist': True,
                                                                     
    }

    if download_mode == "1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]'
    elif download_mode == "720p":
        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]'
    elif download_mode == "480p":
        ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]'
    elif download_mode == "Audio Only":
        ydl_opts['format'] = 'bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def select_folder():
    folder = QFileDialog.getExistingDirectory(window, "Select Folder")
    if folder:
        folder_label.setText(f"Download Folder: {folder}")
        return folder
    return ""

def load_urls_from_file():
    file_path, _ = QFileDialog.getOpenFileName(window, "Select URL File", "", "Text Files (*.txt)")
    if file_path:
        with open(file_path, "r") as file:
            urls = file.read().splitlines()
        for i, url in enumerate(urls[:len(url_entries)]):
            url_entries[i].setText(url)

def search_and_download():
    search_terms_file, _ = QFileDialog.getOpenFileName(window, "Select Song Name File", "", "Text Files (*.txt)")
    if search_terms_file:
        try:
            with open(search_terms_file, "r", encoding="utf-8") as file:
                song_names = file.read().splitlines()
        except UnicodeDecodeError:
            QMessageBox.critical(window, "Error", "Failed to read the file. Ensure it's UTF-8 encoded.")
            return

        folder = folder_label.text().replace("Download Folder: ", "")
        download_mode = download_mode_group.checkedButton().text()

        # **DEBUG: Print how many songs we're processing**
        print(f"Processing {len(song_names)} songs...")

        max_threads = 5  # **Limit concurrent downloads**
        active_threads = []

        for song in song_names:
            print(f"Searching YouTube for: {song}")
            video_url = search_youtube(song)

            if video_url:
                print(f"Found: {video_url} -> Starting download...")
                thread = threading.Thread(target=download_video_thread, args=(video_url, folder, download_mode), daemon=True)
                thread.start()
                active_threads.append(thread)

                # **Throttle downloads to avoid overload**
                if len(active_threads) >= max_threads:
                    print("Waiting for active downloads to finish...")
                    for t in active_threads:
                        t.join()  # Wait for current downloads
                    active_threads = []  # Reset thread list

            else:
                print(f"No results found for: {song}")

            time.sleep(1)  # **Avoid spamming YouTube search**

        QMessageBox.information(window, "Download Started", "Songs are being downloaded. Check the terminal for progress.")  
def on_download_clicked():
    urls = [entry.text().strip() for entry in url_entries if entry.text().strip()]
    folder = folder_label.text().replace("Download Folder: ", "")
    download_mode = download_mode_group.checkedButton().text()
    
    for url in urls:
        threading.Thread(target=download_video_thread, args=(url, folder, download_mode), daemon=True).start()
    
    QMessageBox.information(window, "Download Started", "Downloads are running in the background. Check terminal for progress.")

def download_video_thread(url, folder, download_mode):
    success = download_youtube_video(url, folder, download_mode)
    if success:
        print(f"Successfully downloaded: {url}")
    else:
        print(f"Failed to download: {url}")

# Set up main window
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("YouTube Downloader")
window.setGeometry(100, 100, 600, 500)

url_label = QLabel("YouTube Video URL(s):")
folder_label = QLabel("Download Folder: youtube downloads")
folder_button = QPushButton("Select Folder")
load_urls_button = QPushButton("Load URLs from File")
search_and_download_button = QPushButton("Search & Download from File")

download_mode_group = QButtonGroup()
video_1080p_radio = QRadioButton("1080p")
video_720p_radio = QRadioButton("720p")
video_480p_radio = QRadioButton("480p")
audio_radio = QRadioButton("Audio Only")

video_1080p_radio.setChecked(True)

download_mode_group.addButton(video_1080p_radio)
download_mode_group.addButton(video_720p_radio)
download_mode_group.addButton(video_480p_radio)
download_mode_group.addButton(audio_radio)

download_button = QPushButton("Download")

url_entries = [QLineEdit() for _ in range(10)]

layout = QVBoxLayout()
url_layout = QVBoxLayout()
folder_layout = QHBoxLayout()
radio_layout = QVBoxLayout()
file_buttons_layout = QHBoxLayout()

url_layout.addWidget(url_label)
for entry in url_entries:
    url_layout.addWidget(entry)

folder_layout.addWidget(folder_label)
folder_layout.addWidget(folder_button)

radio_layout.addWidget(video_1080p_radio)
radio_layout.addWidget(video_720p_radio)
radio_layout.addWidget(video_480p_radio)
radio_layout.addWidget(audio_radio)

file_buttons_layout.addWidget(load_urls_button)
file_buttons_layout.addWidget(search_and_download_button)

layout.addLayout(url_layout)
layout.addLayout(radio_layout)
layout.addLayout(folder_layout)
layout.addLayout(file_buttons_layout)
layout.addWidget(download_button)

folder_button.clicked.connect(select_folder)
download_button.clicked.connect(on_download_clicked)
load_urls_button.clicked.connect(load_urls_from_file)
search_and_download_button.clicked.connect(search_and_download)

window.setLayout(layout)
window.show()

sys.exit(app.exec_())
