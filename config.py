"""
Central configuration for the news pipeline.
Loads secrets from .env and defines what we search for.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---- API Keys (loaded from .env) ----
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Free-tier Gemini model — good daily quota, no billing required.
GEMINI_MODEL = "gemini-3.1-flash-lite"

# How many top stories to keep after ranking
TOP_STORIES_COUNT = 5

# ---- NewsData.io: pure category-based, genuine country=in filtering ----
# No keyword-guessing — this is NewsData's own curated "top stories" across
# several categories in ONE combined request. "crime" and "domestic" are
# included because paper-leak scandals and student protests often get filed
# under those categories rather than "education" specifically.
NEWSDATA_CATEGORIES = "top,education,sports,technology,politics,crime,domestic"
NEWSDATA_TIMEFRAME_HOURS = 24

# ---- GNews: keyword-based search, tiered by importance/refresh frequency ----
# NOTE: fetch_news.py currently runs ALL tiers combined every time it's
# called — there's no scheduler yet that runs Tier 1 hourly and Tier 3 only
# 3-4x/day. That's a real feature to build later (e.g. a --tier flag or
# separate GitHub Actions cron schedules); for now treat these labels as
# "how important/fresh this topic is" rather than an active schedule.
# Combined, this is 21 GNews requests per run — GNews free tier is 100/day,
# so don't run this combined list more than ~4-5x/day once GNews is working.

# Tier 1 (ideally hourly) — highest priority, most time-sensitive
GNEWS_PRIORITY_1 = [
    "JEE",
    "NEET",
    "UPSC",
    "SSC",
    "Paper leak India",
    "College admission India",
    "Campus placement India",
    "Student protest India",
]

# Tier 2 (ideally every 2-3 hours)
GNEWS_PRIORITY_2 = [
    "Artificial Intelligence",
    "ChatGPT",
    "Technology India",
    "Startup India",
    "Government jobs India",
    "Internship India",
    "Scholarship India",
]

# Tier 3 (ideally 3-4x/day)
GNEWS_PRIORITY_3 = [
    "India politics",
    "Government policy India",
    "Supreme Court India",
    "Economy India",
    "Stock market India",
    "India cricket",
]

# Combined list actually used by fetch_gnews() until differential
# scheduling is built.
GNEWS_QUERIES = GNEWS_PRIORITY_1 + GNEWS_PRIORITY_2 + GNEWS_PRIORITY_3

# ---- The Guardian: keyword-based (structurally required — UK paper, no
# native India filter), scoped to topics relevant to your audience ----
GUARDIAN_QUERIES = [
    # India
    "India",
    "India education",
    "India politics",
    "India government",
    "India economy",
    "India stock market",
    "India Supreme Court",
    "India election",
    "India protest",
    # Education
    "JEE",
    "NEET",
    "IIT",
    "NIT",
    "University India",
    "Student India",
    # Technology
    "Artificial Intelligence",
    "ChatGPT",
    "OpenAI",
    "Google AI",
    "Microsoft AI",
    "Apple",
    "Cybersecurity",
    # Business & Markets
    "Stock market",
    "Wall Street",
    "NASDAQ",
    "Nifty",
    "Sensex",
    "Global economy",
    "Startup",
    # Global Politics
    "United States politics",
    "China",
    "Russia Ukraine",
    "Middle East",
    "United Nations",
    "Climate change",
    # Sports
    "India cricket",
    "Olympics",
]

# How many articles to pull per query/section before ranking
ARTICLES_PER_QUERY = 10

# Output paths
RAW_ARTICLES_PATH = "output/raw_articles.json"
RANKED_ARTICLES_PATH = "output/ranked_articles.json"
REWRITTEN_ARTICLES_PATH = "output/rewritten_articles.json"
CAPTIONED_ARTICLES_PATH = "output/captioned_articles.json"
