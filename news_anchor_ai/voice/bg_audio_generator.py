"""
news_anchor_ai/voice/bg_audio_generator.py
Synthesizes an authentic broadcast-news ambient background bed:
- Low-frequency 55Hz cinematic sub-bass drone
- 112 BPM rhythmic news ticker pulses
- Subtle ambient suspense sheen
- Auto-mixed under voiceover at -22 dB
"""

import wave
import math
import struct
from pathlib import Path
from news_anchor_ai.config import PROJECT_DIR

AUDIO_ASSETS_DIR = PROJECT_DIR / "assets" / "audio"
DEFAULT_BG_MUSIC = AUDIO_ASSETS_DIR / "news_bg_tone.wav"

def ensure_background_music(duration: float = 60.0) -> Path:
    """Generates the background news bed if not present."""
    AUDIO_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if DEFAULT_BG_MUSIC.exists() and DEFAULT_BG_MUSIC.stat().st_size > 1000:
        return DEFAULT_BG_MUSIC

    sample_rate = 44100
    n_samples = int(sample_rate * duration)

    with wave.open(str(DEFAULT_BG_MUSIC), "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        samples = bytearray()
        bpm = 112
        beat_interval = 60.0 / bpm

        for i in range(n_samples):
            t = i / sample_rate

            # 1. Warm low-frequency drone (55 Hz & 110 Hz)
            drone = 0.12 * math.sin(2 * math.pi * 55 * t) + 0.06 * math.sin(2 * math.pi * 110 * t)

            # 2. News ticker rhythmic pulse (every beat)
            beat_phase = (t % beat_interval) / beat_interval
            pulse_env = math.exp(-beat_phase * 18)
            pulse = 0.08 * math.sin(2 * math.pi * 880 * t) * pulse_env

            # 3. High atmospheric sheen (440 Hz soft shimmer)
            sheen = 0.03 * math.sin(2 * math.pi * 440 * t + 0.5 * math.sin(2 * math.pi * 0.2 * t))

            val = (drone + pulse + sheen) * 0.45
            val = max(-1.0, min(1.0, val))
            int_val = int(val * 32767)
            samples.extend(struct.pack("<hh", int_val, int_val))

        wav.writeframes(samples)

    print(f"[Audio Bed] Synthesized broadcast news ambient track: {DEFAULT_BG_MUSIC.name}")
    return DEFAULT_BG_MUSIC
