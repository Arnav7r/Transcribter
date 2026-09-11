import re
import json
import time
import httpx
from typing import List, Dict, Any, Optional
from deep_translator import GoogleTranslator, MyMemoryTranslator

# Language mapping for MyMemory fallback
MYMEMORY_LANG_MAP = {
    "te": "telugu",
    "en": "english",
    "hi": "hindi",
    "ta": "tamil",
    "kn": "kannada",
    "ml": "malayalam",
    "mr": "marathi",
    "bn": "bengali",
    "pa": "punjabi",
    "gu": "gujarati",
}

def is_valid_translation(text: Optional[str]) -> bool:
    """Check if the translation result is actual content rather than a rate-limit error message."""
    if not text or not text.strip():
        return False
    error_signatures = [
        "error 500",
        "that’s an error",
        "that's an error",
        "please try again later",
        "server error",
        "invalid source language",
        "rate limit",
        "too many requests"
    ]
    lower = text.lower()
    return not any(sig in lower for sig in error_signatures)

def translate_single_text_safe(text: str, source_lang: Optional[str] = None) -> str:
    """Translate a text block with multiple fallback engines to prevent 429/500 errors."""
    if not text or not text.strip():
        return ""

    clean_text = text.strip()

    # 1. Primary: Google Translator
    try:
        res = GoogleTranslator(source='auto', target='hi').translate(clean_text)
        if is_valid_translation(res):
            return res.strip()
    except Exception as e:
        print(f"[Translate] Google Translate error: {e}")

    # 2. Secondary Fallback: MyMemory Translator
    try:
        src = MYMEMORY_LANG_MAP.get((source_lang or "").lower(), "english")
        res = MyMemoryTranslator(source=src, target='hindi').translate(clean_text)
        if is_valid_translation(res):
            return res.strip()
    except Exception as e:
        print(f"[Translate] MyMemory fallback error: {e}")

    # If all translation fails, return the original text rather than an error string
    return clean_text

def translate_segments_to_hindi(
    segments: List[Dict[str, Any]],
    detected_lang: Optional[str] = None,
    gemini_api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Translates a list of timestamped segments into Hindi.
    Appends 'hindi_text' to each segment.
    """
    if not segments:
        return []

    # If Gemini API key is provided, use Gemini for contextual translation
    if gemini_api_key and gemini_api_key.strip():
        try:
            return translate_with_gemini(segments, gemini_api_key.strip())
        except Exception as e:
            print(f"[Translate] Gemini translation failed, falling back to local multi-engine: {e}")

    # Cache translations for duplicate segments/phrases to minimize web calls
    cache: Dict[str, str] = {}
    result_segments: List[Dict[str, Any]] = []

    for seg in segments:
        orig = seg.get("text", "").strip()
        if not orig:
            result_segments.append({**seg, "hindi_text": ""})
            continue

        if orig in cache:
            hindi = cache[orig]
        else:
            hindi = translate_single_text_safe(orig, source_lang=detected_lang)
            cache[orig] = hindi
            # Brief gentle pause to prevent rate limiting
            time.sleep(0.15)

        result_segments.append({
            **seg,
            "hindi_text": hindi
        })

    return result_segments

def translate_with_gemini(segments: List[Dict[str, Any]], api_key: str) -> List[Dict[str, Any]]:
    """Use Gemini Flash to translate segments into high-fidelity, natural Hindi."""
    prompt = (
        "You are an expert translator specializing in social media and Instagram Reels. "
        "Translate the following transcript segments into natural, fluent, written Hindi (Devanagari script). "
        "Preserve modern conversational nuances, idioms, tone, and numbers/prices accurately. "
        "Return ONLY a valid JSON array of objects with keys: 'id' and 'hindi_text'.\n\n"
        "Input Segments:\n" +
        json.dumps([{"id": s["id"], "text": s["text"]} for s in segments], ensure_ascii=False)
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)

        hindi_map = {item["id"]: item["hindi_text"] for item in parsed}
        return [{**s, "hindi_text": hindi_map.get(s["id"], s["text"])} for s in segments]
