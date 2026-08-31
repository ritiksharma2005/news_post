"""
trending_news/config.py
Central Configuration for Trend India Project (@news.nit_iit)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================================================
# 1. INSTAGRAM SOURCES CONFIGURATION
# ==================================================
# Adding a new Instagram news lead source only requires appending username here
INSTAGRAM_SOURCES = [
    "thetatvaindia",
    "theinformly",
    "forbesindia",
    "thebetterindia"
]

# ==================================================
# 2. RUN SCHEDULE & TIME WINDOW CONFIGURATION (IST)
# ==================================================
# Morning Run: 9:00 AM IST (Window: Previous day 8:00 PM to Current day 9:00 AM IST)
# Evening Run: 8:00 PM IST (Window: Current day 9:00 AM to Current day 8:00 PM IST)
RUN_SCHEDULE = {
    "morning": {
        "run_hour_ist": 9,
        "run_minute_ist": 0,
        "window_hours_back": 13  # 8 PM prev day to 9 AM today = 13 hours
    },
    "evening": {
        "run_hour_ist": 20,
        "run_minute_ist": 0,
        "window_hours_back": 11  # 9 AM today to 8 PM today = 11 hours
    }
}

# Maximum posters generated per run (Morning: 2, Evening: 2 -> Max 4 per day)
MAX_POSTERS_PER_RUN = 2

# ==================================================
# 3. NEWS RANKING WEIGHTS (Total: 100%)
# ==================================================
RANKING_WEIGHTS = {
    "public_interest": 0.25,
    "trending_potential": 0.20,
    "news_importance": 0.20,
    "freshness": 0.15,
    "indian_relevance": 0.10,
    "student_relevance": 0.10
}

# Minimum score threshold to qualify for selection (0 - 100)
MIN_QUALIFYING_SCORE = 55.0

# ==================================================
# 4. API CREDENTIALS & KEYS
# ==================================================
# Dedicated Gemini & Groq API keys for Trending News project
TRENDING_GEMINI_API_KEY = os.getenv("TRENDING_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")
TRENDING_GROQ_API_KEY = os.getenv("TRENDING_GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")
TRENDING_APIFY_TOKEN = os.getenv("TRENDING_APIFY_TOKEN") or os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN", "")
APIFY_TOKEN = TRENDING_APIFY_TOKEN
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID", "")

# Image source preference (Prioritize original Instagram source photo)
USE_ORIGINAL_SOURCE_IMAGE = True

# Gemini model preference
GEMINI_MODEL = "gemini-3.6-flash"

# ==================================================
# 5. POSTER CANVAS & BRANDING DESIGN
# ==================================================
# 4:5 Instagram Portrait Dimensions
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350

BRAND_HANDLE = "@news.nit_iit"
BRAND_HANDLE_WITH_ICON = "📸 @news.nit_iit"
BRAND_NAME = "NEWS.NIT_IIT"
DEFAULT_HEADER_LABEL = "THE LATEST"

# Brand Color Palette
BRAND_COLOR_ACCENT = "#F97316"    # Vibrant Orange Accent
BRAND_HEADER_BG = "#FDFBF7"       # Very Light Warm Cream / Off-White
BRAND_HEADER_TEXT = "#0F172A"     # Dark Navy / Black
BRAND_BORDER_LINE = "#E2E8F0"     # Subtle 1-2px Separator Line

# Fonts Directory
BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "fonts"

# Data & Output Paths
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "trending_news.db"
OUTPUT_DIR = BASE_DIR / "output" / "trending"

# Ensure required folders exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
