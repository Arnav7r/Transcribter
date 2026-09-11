import uuid
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel

from app.config import UPLOAD_DIR, AUDIO_DIR, STATIC_DIR, DEFAULT_WHISPER_MODEL
from app.services.video_service import extract_audio_from_video, download_instagram_video
from app.services.transcribe_service import transcribe_audio
from app.services.translate_service import translate_segments_to_hindi
from app.services.subtitle_service import generate_srt, generate_vtt, generate_txt

app = FastAPI(title="Insta Hindi Transcriber & Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job state
jobs: Dict[str, Dict[str, Any]] = {}

class UrlRequest(BaseModel):
    url: str
    model_size: Optional[str] = DEFAULT_WHISPER_MODEL
    source_lang: Optional[str] = "auto"
    gemini_api_key: Optional[str] = None

def run_transcription_pipeline(
    job_id: str,
    video_path: Optional[Path],
    url: Optional[str],
    model_size: str,
    source_lang: Optional[str],
    gemini_api_key: Optional[str]
):
    try:
        # Step 1: Download or locate video
        if url:
            jobs[job_id]["status"] = "downloading"
            jobs[job_id]["message"] = "Fetching video from Instagram..."
            jobs[job_id]["progress"] = 15
            video_path = download_instagram_video(url, job_id)
            jobs[job_id]["video_path"] = str(video_path)

        if not video_path or not video_path.exists():
            raise FileNotFoundError("Video file not available.")

        # Step 2: Extract audio
        jobs[job_id]["status"] = "extracting"
        jobs[job_id]["message"] = "Extracting audio track with FFmpeg..."
        jobs[job_id]["progress"] = 35
        audio_path = AUDIO_DIR / f"{job_id}.wav"
        extract_audio_from_video(video_path, audio_path)

        # Step 3: Transcribe with Whisper
        jobs[job_id]["status"] = "transcribing"
        lang_label = f" ({source_lang})" if source_lang and source_lang != "auto" else ""
        jobs[job_id]["message"] = f"Transcribing speech using Whisper ({model_size}){lang_label}..."
        jobs[job_id]["progress"] = 60
        transcription = transcribe_audio(audio_path, model_size=model_size, language=source_lang)

        # Step 4: Translate to Hindi
        jobs[job_id]["status"] = "translating"
        jobs[job_id]["message"] = "Translating transcript to written Hindi (Devanagari)..."
        jobs[job_id]["progress"] = 85
        translated_segments = translate_segments_to_hindi(
            transcription["segments"],
            detected_lang=transcription.get("language") or source_lang,
            gemini_api_key=gemini_api_key
        )

        full_hindi = " ".join(seg.get("hindi_text", "") for seg in translated_segments)

        # Finished
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Completed successfully!"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["result"] = {
            "job_id": job_id,
            "language": transcription["language"],
            "language_probability": transcription["language_probability"],
            "duration": transcription["duration"],
            "original_full_text": transcription["full_text"],
            "hindi_full_text": full_hindi,
            "segments": translated_segments,
            "has_video": video_path.exists()
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = f"Processing failed: {str(e)}"
        jobs[job_id]["progress"] = 0

@app.post("/api/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model_size: str = Form(DEFAULT_WHISPER_MODEL),
    source_lang: str = Form("auto"),
    gemini_api_key: Optional[str] = Form(None)
):
    job_id = str(uuid.uuid4())[:8]
    file_ext = Path(file.filename).suffix or ".mp4"
    save_path = UPLOAD_DIR / f"{job_id}{file_ext}"
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Video uploaded, starting pipeline...",
        "progress": 5,
        "video_path": str(save_path),
        "result": None
    }

    background_tasks.add_task(
        run_transcription_pipeline,
        job_id=job_id,
        video_path=save_path,
        url=None,
        model_size=model_size,
        source_lang=source_lang,
        gemini_api_key=gemini_api_key
    )

    return {"job_id": job_id, "status": "queued"}

@app.post("/api/process-url")
async def process_url(
    req: UrlRequest,
    background_tasks: BackgroundTasks
):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="Please provide a valid URL.")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Queued for download...",
        "progress": 5,
        "video_path": None,
        "result": None
    }

    background_tasks.add_task(
        run_transcription_pipeline,
        job_id=job_id,
        video_path=None,
        url=req.url.strip(),
        model_size=req.model_size or DEFAULT_WHISPER_MODEL,
        source_lang=req.source_lang or "auto",
        gemini_api_key=req.gemini_api_key
    )

    return {"job_id": job_id, "status": "queued"}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/api/video/{job_id}")
async def get_video(job_id: str):
    if job_id not in jobs or not jobs[job_id].get("video_path"):
        raise HTTPException(status_code=404, detail="Video not found")
    path = Path(jobs[job_id]["video_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file does not exist")
    return FileResponse(path, media_type="video/mp4")

@app.get("/api/export/{job_id}")
async def export_transcript(job_id: str, format: str = "srt", field: str = "hindi"):
    if job_id not in jobs or not jobs[job_id].get("result"):
        raise HTTPException(status_code=404, detail="Result not ready or job not found")
    
    result = jobs[job_id]["result"]
    segments = result["segments"]
    segment_field = "hindi_text" if field == "hindi" else "text"

    if format == "srt":
        content = generate_srt(segments, field=segment_field)
        return Response(
            content=content,
            media_type="application/x-subrip",
            headers={"Content-Disposition": f'attachment; filename="transcript_{job_id}_{field}.srt"'}
        )
    elif format == "vtt":
        content = generate_vtt(segments, field=segment_field)
        return Response(
            content=content,
            media_type="text/vtt",
            headers={"Content-Disposition": f'attachment; filename="transcript_{job_id}_{field}.vtt"'}
        )
    elif format == "txt":
        content = generate_txt(segments, include_original=(field == "both"))
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="transcript_{job_id}_{field}.txt"'}
        )
    elif format == "json":
        return JSONResponse(
            content=result,
            headers={"Content-Disposition": f'attachment; filename="transcript_{job_id}.json"'}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use srt, vtt, txt, or json.")

# Mount static files for the frontend
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

