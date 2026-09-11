import os
import sys
import shutil
from pathlib import Path

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

import imageio_ffmpeg

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
AUDIO_DIR = BASE_DIR / "temp_audio"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIR = APP_DIR / "static"

for folder in [UPLOAD_DIR, AUDIO_DIR, OUTPUT_DIR, STATIC_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Setup FFmpeg Executable and ensure standard ffmpeg.exe exists
try:
    raw_ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe())
    ffmpeg_dir = raw_ffmpeg.parent
    standard_ffmpeg = ffmpeg_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    
    if not standard_ffmpeg.exists():
        shutil.copyfile(raw_ffmpeg, standard_ffmpeg)
        
    scripts_ffmpeg = Path(sys.prefix) / "Scripts" / "ffmpeg.exe"
    if scripts_ffmpeg.parent.exists() and not scripts_ffmpeg.exists():
        shutil.copyfile(raw_ffmpeg, scripts_ffmpeg)
        
    FFMPEG_PATH = str(standard_ffmpeg)
    FFMPEG_DIR = str(ffmpeg_dir)
    
    # Prepend to PATH so yt-dlp and child processes locate ffmpeg immediately
    os.environ["PATH"] = f"{FFMPEG_DIR}{os.pathsep}{scripts_ffmpeg.parent}{os.pathsep}" + os.environ.get("PATH", "")
except Exception as e:
    print(f"Warning setting up FFmpeg: {e}")
    FFMPEG_PATH = "ffmpeg"
    FFMPEG_DIR = None

# Whisper Config
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = "int8" if DEVICE == "cpu" else "float16"
