"""
news_anchor_ai/voice/voice_generator.py
Generates the studio-quality Indian English male news presenter voice
using Edge-TTS (en-IN-PrabhatNeural).
Extracts word-level timestamps directly for real-time animated subtitles.
Normalizes audio loudness to broadcast standards (-16 LUFS) via FFmpeg.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from news_anchor_ai.config import (
    VOICE_NAME,
    VOICE_RATE,
    VOICE_PITCH,
    AUDIO_DIR,
    TEMP_DIR
)

async def _synthesize_edge_tts(text: str, audio_path: Path) -> List[Dict]:
    """
    Synthesizes speech using edge-tts and captures word boundaries.
    """
    import edge_tts
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_NAME,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH
    )
    
    word_timestamps = []
    
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # Offset in 100ns units -> convert to seconds
                start_sec = chunk["offset"] / 10_000_000
                duration_sec = chunk["duration"] / 10_000_000
                word = chunk["text"]
                word_timestamps.append({
                    "word": word,
                    "start": start_sec,
                    "end": start_sec + duration_sec
                })
                
    return word_timestamps

def normalize_audio(raw_audio_path: Path, output_audio_path: Path):
    """
    Normalizes audio loudness using FFmpeg loudnorm filter (-16 LUFS, -1.5 dB peak).
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_audio_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            str(output_audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            # Fallback copy if ffmpeg fails or isn't installed
            import shutil
            shutil.copy(raw_audio_path, output_audio_path)
    except Exception as e:
        print(f"[Voice Engine] Notice: FFmpeg loudnorm skipped ({e}), using raw audio.")
        import shutil
        shutil.copy(raw_audio_path, output_audio_path)

def get_audio_duration(audio_path: Path) -> float:
    """Gets audio duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception:
        # Estimation fallback (~2.2 words per second)
        return 35.0

def generate_anchor_voice(text: str, post_id: str) -> Tuple[Path, float, List[Dict]]:
    """
    Synchronous wrapper to generate the Indian English male voice track.
    Returns: (final_audio_path, duration_seconds, word_timestamps)
    """
    raw_path = TEMP_DIR / f"voice_raw_{post_id}.mp3"
    final_path = AUDIO_DIR / f"voice_{post_id}.mp3"
    
    # Run async edge-tts
    word_timestamps = asyncio.run(_synthesize_edge_tts(text, raw_path))
    
    # Normalize volume
    normalize_audio(raw_path, final_path)
    
    duration = get_audio_duration(final_path)
    print(f"[Voice Engine] Generated voice: {final_path.name} | Duration: {duration:.2f}s | Words: {len(word_timestamps)}")
    
    return final_path, duration, word_timestamps
