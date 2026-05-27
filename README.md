I'll be adding some simple AI generated (Gemini, ChatGPT, DeepSeek, BlackBox) codes to this folder.

---
Here is a complete, polished, and unified **README.md** for your `ai_generated_toolkit` repository. It cleanly organizes all 8 scripts with brief descriptions, key features, and quick usage instructions in a standard, professional GitHub markdown style.

---

# 🤖 AI-Generated Toolkit

A collection of practical, efficient, and highly specialized automation scripts and desktop utilities designed to streamline file management, media processing, and data scraping.

---

## 📁 Repository Overview

| Tool | Category | Key Feature |
| --- | --- | --- |
| [💾 SMR Safe Drive Cloner](https://www.google.com/search?q=%231-smr-safe-drive-cloner) | File Management | Dynamic SMR cache throttling & multi-threaded copy |
| [🔄 Absolutely Free Sync](https://www.google.com/search?q=%232-absolutely-free-sync) | File Management | Multi-threaded local directory mirroring |
| [⏱️ Speed Adjustable Copy](https://www.google.com/search?q=%233-speed-adjustable-copy) | File Management | Manual, slider-controlled I/O throttling |
| [🖼️ HEIC to JPG Converter](https://www.google.com/search?q=%234-heic-to-jpg-converter) | Media Processing | Multi-threaded conversion preserving full EXIF data |
| [📹 Presentation Frame Extractor](https://www.google.com/search?q=%235-presentation-frame-extractor) | Media Processing | SSIM-based unique slide/frame extraction from video |
| [🔻 YT Downloader GUI](https://www.google.com/search?q=%236-yt-downloader-gui) | Media & Web | High-quality YouTube video/audio ripping via `yt-dlp` |
| [🕷️ YouTube Crawler](https://www.google.com/search?q=%237-youtube-crawler) | Media & Web | Selenium-driven video URL metadata harvester |
| [📖 PDF Audio Reader](https://www.google.com/search?q=%238-pdf-audio-reader) | Accessibility | GUI-based PDF text-to-speech reader |

---

## 🛠️ Tool-by-Tool Guide

### 1. SMR Safe Drive Cloner

`copy2smrQT_pause_CRC.py`
A PyQt5-based directory backup utility engineered to handle the unique write-speed drops of **SMR (Shingled Magnetic Recording)** hard drives.

* **Features:** Dynamic transfer speed monitoring, strategic "cool-down" periods when drive cache saturates, low-overhead 100-interval `zlib.crc32` file validation, and thread-safe pause/resume.
* **How to Use:**
```bash
pip install PyQt5
python copy2smrQT_pause_CRC.py

```



### 2. Absolutely Free Sync

`absolutelyfreesync.py`
A lightweight, high-performance alternative to commercial directory mirroring tools.

* **Features:** Multi-threaded folder analysis, automated file comparison (size, modification time, and CRC32 checks), non-blocking GUI updates, and granular progress reporting.
* **How to Use:**
```bash
pip install PyQt5
python absolutelyfreesync.py

```



### 3. Speed Adjustable Copy

`speed_adjustable_copy.py`
A granular file transfer utility that allows you to control system resource consumption manually.

* **Features:** Live slider-based I/O throttling, real-time bandwidth consumption metrics, thread-isolated copying, and instantaneous pause capabilities.
* **How to Use:**
```bash
pip install PyQt5
python speed_adjustable_copy.py

```



### 4. HEIC to JPG Converter

`heic_to_jpg_with_exif.py`
An efficient batch converter for modern Apple photo formats (`.HEIC`) to standard web-friendly JPEGs.

* **Features:** Preserves all camera metadata (EXIF, orientation, timestamps), utilizes multi-threaded workers for batch jobs, and features an integrated directory selector.
* **How to Use:**
```bash
pip install Pillow pillow-heif PyQt5
python heic_to_jpg_with_exif.py

```



### 5. Presentation Frame Extractor

`extract_different_frames_from_presentation_recordings.py`
Extracts static presentation slides or clear notes out of continuous long video recordings.

* **Features:** Uses Structural Similarity Index (**SSIM**) via OpenCV to analyze visual drift, skipping transitions and rendering only unique keyframes to save storage space.
* **How to Use:**
```bash
pip install opencv-python scikit-image PyQt5
python extract_different_frames_from_presentation_recordings.py

```



### 6. YT Downloader GUI

`YT_Downloader_GUI.py`
A feature-rich desktop client interface wrapped around the robust `yt-dlp` multimedia engine.

* **Features:** Separated video and audio stream ripping, custom resolution selection, dynamic live progress bars, and background process decoupling.
* **How to Use:**
```bash
pip install yt-dlp PyQt5
python YT_Downloader_GUI.py

```



### 7. YouTube Crawler

`youtube_crawler.py`
An automated data miner built to compile extensive lists of video metadata from target YouTube channels or search terms.

* **Features:** Headless Selenium infinite scroll handling, asynchronous content loading, and comprehensive Excel (`.xlsx`) structured document exporting.
* **How to Use:**
```bash
pip install selenium pandas openpyxl BeautifulSoup4
python youtube_crawler.py

```



### 8. PDF Audio Reader

`pdf_reader.py`
A simple desktop utility that reads your digital books and documents aloud.

* **Features:** Native offline text-to-speech rendering engines, layout parsing to remove header/footer noise, simple visual reading progress tracking.
* **How to Use:**
```bash
pip install pypdf pyttsx3 PyQt5
python pdf_reader.py

```
