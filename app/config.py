import os
import sys
import shutil
import stat
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

# Setup FFmpeg Executable cross-platform (Windows & Linux/Render)
FFMPEG_PATH = None
FFMPEG_DIR = None

# 1. Check if system ffmpeg exists and is executable
sys_ffmpeg = shutil.which("ffmpeg")
if sys_ffmpeg:
    FFMPEG_PATH = sys_ffmpeg
    FFMPEG_DIR = str(Path(sys_ffmpeg).parent)

# 2. If not, use imageio-ffmpeg bundled binary and guarantee chmod +x permissions
if not FFMPEG_PATH:
    try:
        raw_ffmpeg = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ffmpeg_dir = raw_ffmpeg.parent
        is_windows = os.name == "nt"
        binary_name = "ffmpeg.exe" if is_windows else "ffmpeg"
        standard_ffmpeg = ffmpeg_dir / binary_name

        # Ensure executable permissions on the raw binary
        if not is_windows:
            try:
                raw_ffmpeg.chmod(0o755)
            except Exception:
                pass

        if not standard_ffmpeg.exists():
            shutil.copyfile(raw_ffmpeg, standard_ffmpeg)

        if not is_windows:
            try:
                standard_ffmpeg.chmod(0o755)
            except Exception:
                pass

        # Also copy/link into venv bin (Linux) or Scripts (Windows)
        venv_bin = Path(sys.prefix) / ("Scripts" if is_windows else "bin")
        if venv_bin.exists():
            dest = venv_bin / binary_name
            if not dest.exists():
                try:
                    shutil.copyfile(raw_ffmpeg, dest)
                except Exception:
                    pass
            if not is_windows and dest.exists():
                try:
                    dest.chmod(0o755)
                except Exception:
                    pass

        FFMPEG_PATH = str(standard_ffmpeg)
        FFMPEG_DIR = str(ffmpeg_dir)

        # Prepend to PATH so yt-dlp and child processes locate ffmpeg immediately
        bin_paths = [FFMPEG_DIR]
        if venv_bin.exists():
            bin_paths.append(str(venv_bin))
        os.environ["PATH"] = os.pathsep.join(bin_paths) + os.pathsep + os.environ.get("PATH", "")
    except Exception as e:
        print(f"Warning setting up FFmpeg: {e}")
        FFMPEG_PATH = "ffmpeg"
        FFMPEG_DIR = None

# Whisper Config
DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = "int8" if DEVICE == "cpu" else "float16"
