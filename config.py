"""
Central configuration for the news pipeline.
Loads secrets from .env and defines what we search for.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def clean_env(name):
    """
    Get an environment variable and strip any accidental whitespace or
    newline characters.
    """
    value = os.getenv(name)
    return value.strip() if value else value


# ---- API Keys (loaded from .env / GitHub Secrets) ----
GNEWS_API_KEY = clean_env("GNEWS_API_KEY")
GUARDIAN_API_KEY = clean_env("GUARDIAN_API_KEY")
NEWSDATA_API_KEY = clean_env("NEWSDATA_API_KEY")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY")
GROQ_API_KEY = clean_env("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = clean_env("TELEGRAM_CHAT_ID")
INSTAGRAM_ACCESS_TOKEN = clean_env("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = clean_env("INSTAGRAM_USER_ID")

# AI Models
GEMINI_MODEL = "gemini-3.1-flash-lite"
GROQ_MODEL = "llama-3.1-8b-instant"

# How many top stories to keep after ranking (Set to 3)
TOP_STORIES_COUNT = 3

ARTICLES_PER_RANKING_BATCH = 25
RANKING_BATCH_DELAY_SECONDS = 3

# ---- NewsData.io Settings ----
NEWSDATA_CATEGORIES = "top,education,sports,crime,domestic"
NEWSDATA_TIMEFRAME_HOURS = 24

# ---- GNews Keywords ----
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

GNEWS_PRIORITY_2 = [
    "Artificial Intelligence",
    "ChatGPT",
    "Technology India",
    "Startup India",
    "Government jobs India",
    "Internship India",
    "Scholarship India",
]

GNEWS_PRIORITY_3 = [
    "India politics",
    "Government policy India",
    "Supreme Court India",
    "Economy India",
    "Stock market India",
    "India cricket",
]

GNEWS_QUERIES = GNEWS_PRIORITY_1 + GNEWS_PRIORITY_2 + GNEWS_PRIORITY_3

# ---- The Guardian Keywords ----
GUARDIAN_QUERIES = [
    "India",
    "India education",
    "India politics",
    "India government",
    "India economy",
    "Artificial Intelligence",
    "Startup",
]

ARTICLES_PER_QUERY = 10

# Output paths
RAW_ARTICLES_PATH = "output/raw_articles.json"
RANKED_ARTICLES_PATH = "output/ranked_articles.json"
REWRITTEN_ARTICLES_PATH = "output/rewritten_articles.json"
CAPTIONED_ARTICLES_PATH = "output/captioned_articles.json"

# 🔹 Student & Career RSS Feeds (Free & Official)
RSS_FEEDS = {
    "Govt_PIB": "https://pib.gov.in/RssMain.aspx?ModId=6",  # Official Govt Policies & Schemes
    "Govt_Jobs": "https://www.jagranjosh.com/rss/josh/jobs.xml",  # Govt Job Alerts (UPSC, SSC, Banking)
    "ISRO_Official": "https://www.isro.gov.in/rss_news.xml",  # ISRO Space & Science News
    "Student_Opportunities": "https://unstop.com/blog/feed/",  # Hackathons, Internships, Hiring Drives
}