# InstaTranscribe Hindi 🇮🇳 • Reels Audio to Written Hindi Web App

A web application designed to take Instagram videos (either uploaded files or pasted Instagram Reel/Post links), extract audio, transcribe the speech using local Whisper AI, and translate the text into written **Hindi (हिन्दी)** in beautiful Devanagari script with timestamped subtitles.

---

## ✨ Key Features

- 📁 **Direct Video Upload**: Drag and drop `.mp4`, `.mov`, `.webm` videos downloaded from Instagram.
- 🔗 **Instagram Link Fetching**: Paste any public Instagram Reel URL to download and process automatically.
- 🎵 **Audio Extraction**: Automatic 16kHz mono WAV extraction using bundled FFmpeg (no external setup required).
- 🎙️ **Local Speech-to-Text**: Powered by `faster-whisper` (fast, private, no cloud API required).
- 🇮🇳 **Written Hindi Translation**: Translates spoken words into fluent Devanagari Hindi text.
- ⏱️ **Timestamped Subtitle Sync**: Interactive segments let you click any line to seek the video player to that exact moment.
- 🔊 **Hindi Speech Synthesis**: Listen to the generated Hindi text via browser text-to-speech.
- ⬇️ **Multiple Export Formats**:
  - `.SRT` Subtitles (ready for Premiere Pro, CapCut, Instagram Captions)
  - `.TXT` clean text document
  - `.JSON` complete timestamp metadata
  - One-click copy to clipboard

---

## 🚀 How to Run the Website

### Option 1: Double-Click (Easiest)
Simply double-click the **`run.bat`** file in the project folder.  
It will automatically launch the server and open the web app in your default browser at `http://localhost:8000`.

### Option 2: From the Terminal (PowerShell / Command Prompt)
Run the following command inside this directory:
```powershell
.\.venv\Scripts\python.exe run.py
```
Then open your web browser at:
**[http://localhost:8000](http://localhost:8000)**

---

## 🛠️ Optional Settings
Click the **Settings** icon on the top right of the web app to:
- Select Whisper Model: `tiny` (blazingly fast), `base` (recommended default), or `small` (high accuracy).
- Add an optional **Gemini API Key** if you'd like nuanced translation for complex Hindi/Hinglish slang.

