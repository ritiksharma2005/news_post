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

# Target Indian Subreddits covering Student, Campus, Exams & Career/Placement Affairs
SUBREDDITS = [
    "JEENEETards",
    "CUETards",
    "btechtards",
    "developersIndia",
    "Indian_Academia",
    "IndianEngineers",
    "UPSC",
    "studentsphile",
    "legaladviceindia",
    "india",
    "IndiaSpeaks",
    "bihar",
    "Delhi",
    "mumbai"
]

# Twitter / Social Handles
TWITTER_SOURCES = [
    "ANI",
    "NDTV",
    "LiveMint",
    "IndianExpress",
    "TimesOfIndia"
]

# Google Trends & Google News India RSS Endpoints
GOOGLE_TRENDS_INDIA_RSS = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"
GOOGLE_NEWS_INDIA_RSS = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
GOOGLE_NEWS_INDIA_TOPICS = [
    ("India Education & Exams", "https://news.google.com/rss/search?q=student+exam+JEE+NEET+placement+IIT+India&hl=en-IN&gl=IN&ceid=IN:en"),
    ("India Tech & Hiring", "https://news.google.com/rss/search?q=hiring+layoffs+placements+company+career+India&hl=en-IN&gl=IN&ceid=IN:en"),
    ("India Campus & Youth", "https://news.google.com/rss/search?q=college+campus+protest+university+ragging+safety+India&hl=en-IN&gl=IN&ceid=IN:en"),
]

# Import root config.py safely without module shadowing
import sys
import importlib.util

root_config_path = BASE_DIR / "config.py"
spec = importlib.util.spec_from_file_location("root_config", root_config_path)
root_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(root_config)

clean_env = root_config.clean_env
clean_bot_token = root_config.clean_bot_token

# API Credentials & Keys
GEMINI_API_KEY = clean_env("GEMINI_API_KEY") or clean_env("TRENDING_GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = clean_bot_token("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = clean_env("TELEGRAM_CHAT_ID")
