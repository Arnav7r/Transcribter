from pathlib import Path
from typing import Dict, Any, List, Optional
from faster_whisper import WhisperModel
from app.config import DEFAULT_WHISPER_MODEL, DEVICE, COMPUTE_TYPE

_models: Dict[str, WhisperModel] = {}

def get_whisper_model(model_size: str = DEFAULT_WHISPER_MODEL) -> WhisperModel:
    """Retrieve or load cached Whisper model."""
    if model_size not in _models:
        print(f"Loading Whisper model '{model_size}' on {DEVICE} ({COMPUTE_TYPE})...")
        _models[model_size] = WhisperModel(model_size, device=DEVICE, compute_type=COMPUTE_TYPE)
    return _models[model_size]

def transcribe_audio(audio_path: Path, model_size: str = DEFAULT_WHISPER_MODEL, language: Optional[str] = None) -> Dict[str, Any]:
    """Transcribe audio file and return language info and timestamped segments."""
    model = get_whisper_model(model_size)
    
    # If language is 'auto' or empty, pass None so Whisper auto-detects
    lang = language.strip().lower() if language and language.strip().lower() not in ["auto", ""] else None
    
    # Run transcription with anti-hallucination guardrails
    segments, info = model.transcribe(
        str(audio_path),
        language=lang,
        beam_size=5,
        word_timestamps=True,
        condition_on_previous_text=False,
        compression_ratio_threshold=2.2,
        no_speech_threshold=0.6,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400)
    )
    
    segment_list: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []
    
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        full_text_parts.append(text)
        segment_list.append({
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": text,
        })
        
    return {
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
        "duration": round(info.duration, 2),
        "full_text": " ".join(full_text_parts),
        "segments": segment_list
    }

