I'll be adding some simple AI generated (Gemini, ChatGPT, DeepSeek, BlackBox) codes to this folder.

---

### 📂 Current Utilities

This folder currently contains a set of utilities primarily focused on media download and document/video processing:

#### 📹 YouTube Utilities (`youtube_crawler.py`, `YT_Downloader_GUI.py`)

| Program | Description | Features |
| :--- | :--- | :--- |
| **YouTube Crawler** | A command-line utility (with a basic QT interface) designed for **batch searching and downloading** videos. | Takes a `.txt` file of search terms (e.g., song names) and finds the most viewed YouTube video for each, then downloads it. |
| **YouTube Downloader (GUI)** | A Qt GUI application for downloading individual YouTube videos, playlists, or channel content. | Supports multi-threaded downloading, quality selection (**2160p, 1080p, 720p, Audio Only**), and organization of downloaded files into playlist subfolders. |

> ⚠️ **IMPORTANT WARNING:** Downloading entire **channels or large playlists** may lead to your IP address being temporarily or permanently **blacklisted by YouTube**. Please use this feature responsibly and in moderation.

---

#### 🎥 Video Processing (`extract_different_frames_from_presentation_recordings.py`)

| Program | Description | Use Case |
| :--- | :--- | :--- |
| **Presentation Slide Extractor** | A script that acts as a change detection video browser. It automatically extracts frames from a video only when the **visual content changes significantly** (e.g., when a new slide is shown). | I use this for grabbing distinct **slides** from old presentation and lecture recordings. |

---

#### 📄 Document Viewer (`pdf_reader.py`)



---

# 💾 SMR Safe Drive Cloner

An intelligent, GUI-based directory cloning and backup utility written in Python using **PyQt5**. This tool is specifically engineered to handle the unique challenges of backing up large datasets to **SMR (Shingled Magnetic Recording)** hard drives, which are notorious for severe write-speed drops once their PMR/Drive cache is saturated.

Unlike standard file copy utilities that crash or freeze when a drive becomes unresponsive, this toolkit safely monitors transfer rates and forces strategic "cool-down" periods to keep your hardware stable and your data safe.

---

## ✨ Features

* **📦 SMR Cache-Saturated Mitigation:** Dynamically tracks real-time write speeds. If the speed drops below a configurable threshold (e.g., 50 MB/s) for consecutive ticks, the script enters escalating cool-down stages to let the SMR drive flush its internal cache before continuing.
* **⏸️ True Mid-Chunk Pause & Resume:** Implements low-level thread synchronization (`QMutex` and `QWaitCondition`) allowing you to pause and resume transfers seamlessly at any moment—even mid-file copy or during long validation queues—without breaking file integrity.
* **🔍 Fast Sampled CRC Verification:** Performs rapid, low-overhead structural dimension checks and smart uniform 100-interval `zlib.crc32` hashing. It validates existing target files before copying to skip duplicates, and checks newly written files immediately post-copy to ensure no data corruption occurred.
* **🧵 Non-Blocking Async Multi-Threading:** Offloads heavy file I/O operations and disk scanning to an isolated `QThread` worker, ensuring the PyQt5 user interface remains highly responsive, smooth, and never shows an *"Application Not Responding"* freeze.
* **📊 Dual-Mode Logging:** Keeps you updated with live text streams in the GUI interface and simultaneously generates a persistent `copy_log.txt` on the destination drive, complete with timestamps and auto-calculated average transfer speeds per file.

---

## 🛠️ Configuration & Customization

At the top of the file, you can easily adjust performance thresholds to match your specific hardware setup:

```python
# --- CONFIGURATION DEFAULTS ---
SPEED_THRESHOLD_MB = 50.0      # Minimum acceptable write speed before flagging saturation
CHUNK_SIZE = 1024 * 1024 * 4   # 4MB chunks for balanced, smooth buffer streaming
COOL_DOWN_STAGES = [10, 20, 30, 120]  # Progressive sleep intervals (in seconds) if slowdown persists

```

---

## 🚀 Getting Started

### Prerequisites

You will need Python 3.x along with the `PyQt5` library. You can install it via pip:

```bash
pip install PyQt5

```

### Running the Application

Simply execute the script to launch the GUI interface:

```bash
python copy2smrQT_pause_CRC.py

```

1. Select your **Source** and **Destination** directories using the built-in folder browser.
2. Click **Start Transfer** to initiate the scanning and copying pipeline.
3. Use the **Pause** and **Stop Transfer** buttons to gracefully manage execution at any time.

| Program | Description | Features |
| :--- | :--- | :--- |
| **Simple PDF Reader (GUI)** | A basic Qt GUI application for viewing PDF documents. | Functionalities include **Zoom In/Out**, navigation via **Previous/Next buttons**, and support for **keyboard shortcuts** (Up/Down/PageUp/PageDown) for page browsing. |
