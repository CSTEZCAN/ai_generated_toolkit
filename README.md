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

| Program | Description | Features |
| :--- | :--- | :--- |
| **Simple PDF Reader (GUI)** | A basic Qt GUI application for viewing PDF documents. | Functionalities include **Zoom In/Out**, navigation via **Previous/Next buttons**, and support for **keyboard shortcuts** (Up/Down/PageUp/PageDown) for page browsing. |
