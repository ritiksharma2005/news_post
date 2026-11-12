"""
news_anchor_ai/config.py
Configuration settings for AI News Anchor – NEWS NIT IIT
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def _clean(val: str) -> str:
    if not val:
        return ""
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1].strip()
    return val

# API Credentials
GEMINI_API_KEY = _clean(os.getenv("GEMINI_API_KEY", ""))
TELEGRAM_BOT_TOKEN = _clean(os.getenv("TELEGRAM_BOT_TOKEN", ""))
TELEGRAM_CHAT_ID = _clean(os.getenv("TELEGRAM_CHAT_ID", ""))
INSTAGRAM_ACCESS_TOKEN = _clean(os.getenv("INSTAGRAM_ACCESS_TOKEN", ""))
INSTAGRAM_USER_ID = _clean(os.getenv("INSTAGRAM_USER_ID", ""))

# Account info
INSTAGRAM_ACCOUNT = "@news.nit_iit"
BRAND_NAME = "NEWS NIT IIT"

# Directories
PROJECT_DIR = ROOT_DIR / "news_anchor_ai"
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"
TEMP_DIR = OUTPUT_DIR / "temp"
REELS_DIR = OUTPUT_DIR / "reels"
AUDIO_DIR = OUTPUT_DIR / "audio"
BACKGROUNDS_DIR = PROJECT_DIR / "assets" / "backgrounds"
FONTS_DIR = ROOT_DIR / "fonts"

# Anchor Assets
ANCHOR_DIR = ROOT_DIR / "assets" / "anchor"
ANCHOR_SCARF_IMAGE = ANCHOR_DIR / "anchor_scarf.jpg"
ANCHOR_GAITER_IMAGE = ANCHOR_DIR / "anchor_gaiter.jpg"

# Fonts
FONT_BOLD = FONTS_DIR / "NotoSans-Bold.ttf"
FONT_REGULAR = FONTS_DIR / "NotoSans-Regular.ttf"

# Video Specifications (Instagram Reel 9:16)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Voice settings (Permanent Signature Voice: Mature Indian English Male)
# Locked permanently across all videos for consistent brand identity
VOICE_NAME = "en-IN-PrabhatNeural"
VOICE_RATE = "+1%"   # Measured, authoritative news delivery cadence
VOICE_PITCH = "-3Hz"  # Deeper, mature broadcast tone with commanding presence

# Target Timing (30–45s total)
MIN_DURATION = 30
MAX_DURATION = 45

# Create necessary directories
for p in [DATA_DIR, OUTPUT_DIR, TEMP_DIR, REELS_DIR, AUDIO_DIR, BACKGROUNDS_DIR]:
    p.mkdir(parents=True, exist_ok=True)
