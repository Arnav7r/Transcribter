import os
import subprocess
from pathlib import Path
import yt_dlp
from app.config import FFMPEG_PATH, FFMPEG_DIR, UPLOAD_DIR, AUDIO_DIR

def extract_audio_from_video(video_path: Path, output_audio_path: Path) -> Path:
    """Extract audio from video file and convert to 16kHz mono WAV for Whisper."""
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure executable permissions on Linux/Unix systems
    if os.name != "nt":
        try:
            Path(FFMPEG_PATH).chmod(0o755)
        except Exception:
            pass

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(output_audio_path)
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")
    
    if not output_audio_path.exists() or output_audio_path.stat().st_size == 0:
        raise RuntimeError("Extracted audio file is empty or missing.")
        
    return output_audio_path

def download_instagram_video(url: str, job_id: str) -> Path:
    """Download video from Instagram post/reel using yt-dlp."""
    output_template = str(UPLOAD_DIR / f"{job_id}_%(id)s.%(ext)s")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }
    
    if FFMPEG_DIR:
        ydl_opts['ffmpeg_location'] = FFMPEG_DIR
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        filepath = Path(filename)
        if not filepath.exists():
            mp4_path = filepath.with_suffix('.mp4')
            if mp4_path.exists():
                return mp4_path
            # Check if any file starting with job_id was created
            matching = list(UPLOAD_DIR.glob(f"{job_id}_*"))
            if matching:
                return matching[0]
            raise FileNotFoundError(f"Downloaded file not found for {url}")
        return filepath
