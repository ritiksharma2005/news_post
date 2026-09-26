"""
social_trends/config.py
Configuration for India Social Trends Project (Reddit + Twitter -> Telegram)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "social_trends"
DB_PATH = DATA_DIR / "social_trends.db"

# Ensure output directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "temp").mkdir(parents=True, exist_ok=True)

# Output count per run (3 to 4 stories)
STORIES_PER_RUN = 4

# Target Indian Subreddits covering overall trends (politics, protests, students, entertainment, sports, crime, state news)
SUBREDDITS = [
    "india",
    "IndianNews",
    "IndianModerate",
    "UPSC",
    "studentsphile",
    "bollywood",
    "Cricket",
    "bihar"
]

# Twitter / Social Handles or Google News India RSS Fallbacks
TWITTER_SOURCES = [
    "ANI",
    "NDTV",
    "LiveMint",
    "IndianExpress",
    "TimesOfIndia"
]

# Add root to sys.path for config import
import sys
sys.path.append(str(BASE_DIR))
from config import clean_env, clean_bot_token

# API Credentials & Keys
GEMINI_API_KEY = clean_env("GEMINI_API_KEY") or clean_env("TRENDING_GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = clean_bot_token("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = clean_env("TELEGRAM_CHAT_ID")
