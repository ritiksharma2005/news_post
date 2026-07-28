"""
config.py
Central configuration for the news pipeline.
Loads secrets from .env / GitHub Secrets and defines search queries, RSS feeds, and 3 Buckets.
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
RAPIDAPI_KEY = clean_env("RAPIDAPI_KEY")

# AI Models
GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

# How many top stories to keep after ranking (Set to 3)
TOP_STORIES_COUNT = 3

ARTICLES_PER_RANKING_BATCH = 25
RANKING_BATCH_DELAY_SECONDS = 3

# ---- NewsData.io Settings ----
NEWSDATA_CATEGORIES = "top,politics,education,domestic"
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

# 🏛️ ENHANCED INDIAN POLITICS KEYWORDS (BJP, Congress, Parliament, Supreme Court)
GNEWS_PRIORITY_3 = [
    "BJP Congress India politics",
    "Lok Sabha Parliament news India",
    "Supreme Court Verdict India",
    "Election Commission India",
    "Government policy India",
    "New Bill Parliament India",
]

GNEWS_QUERIES = GNEWS_PRIORITY_1 + GNEWS_PRIORITY_2 + GNEWS_PRIORITY_3

# ---- The Guardian Keywords ----
GUARDIAN_QUERIES = [
    "India politics",
    "India government",
    "India education",
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

# 🔹 3 BUCKET RSS FEEDS (Politics, Student, Tech)
RSS_FEEDS = {
    # 🏛️ Bucket 1: Indian Politics & Govt (NDTV, Times of India, Indian Express, PIB)
    "NDTV_Politics": "https://feeds.feedburner.com/ndtvnews-india-news",
    "TOI_Politics": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "TheHindu_National": "https://www.thehindu.com/news/national/feeder/default.rss",
    "IndianExpress_India": "https://indianexpress.com/section/india/feed/",
    "Govt_PIB": "https://pib.gov.in/RssMain.aspx?ModId=6",

    # 📚 Bucket 2: Student, Exams & Placements (Jagran Josh, Unstop)
    "Govt_Jobs": "https://www.jagranjosh.com/rss/josh/jobs.xml",
    "Student_Opportunities": "https://unstop.com/blog/feed/",

    # 🚀 Bucket 3: Tech, AI & ISRO (ISRO Official)
    "ISRO_Official": "https://www.isro.gov.in/rss_news.xml",
}

# 🔹 Content Pillars / Buckets
BUCKETS = ["IndianPolitics", "StudentEducation", "TechInnovation"]
