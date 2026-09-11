from typing import List, Dict, Any

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def generate_srt(segments: List[Dict[str, Any]], field: str = "hindi_text") -> str:
    """Generate SubRip (.srt) subtitle file content."""
    lines = []
    for i, seg in enumerate(segments, start=1):
        start_str = format_timestamp_srt(seg["start"])
        end_str = format_timestamp_srt(seg["end"])
        text = seg.get(field) or seg.get("text", "")
        lines.append(f"{i}\n{start_str} --> {end_str}\n{text}\n")
    return "\n".join(lines)

def generate_vtt(segments: List[Dict[str, Any]], field: str = "hindi_text") -> str:
    """Generate WebVTT (.vtt) format for HTML5 video player."""
    lines = ["WEBVTT\n"]
    for seg in segments:
        start_str = format_timestamp_vtt(seg["start"])
        end_str = format_timestamp_vtt(seg["end"])
        text = seg.get(field) or seg.get("text", "")
        lines.append(f"{start_str} --> {end_str}\n{text}\n")
    return "\n".join(lines)

def generate_txt(segments: List[Dict[str, Any]], include_original: bool = False) -> str:
    """Generate clean readable text document."""
    if not include_original:
        return "\n\n".join(seg.get("hindi_text", seg.get("text", "")) for seg in segments)
    
    blocks = []
    for seg in segments:
        hindi = seg.get("hindi_text", "")
        orig = seg.get("text", "")
        blocks.append(f"[{seg['start']}s - {seg['end']}s]\nHindi: {hindi}\nOriginal: {orig}")
    return "\n\n".join(blocks)

