"""
Central configuration for the news pipeline.
Loads secrets from .env and defines what we search for.
"""
import os 
TELEGRAM_BOT_TOKEN = os.getenv("EAAWH0f4vts8BSEEJCqfJRChHAFmZBTkJJ65m8aGTL3eqtNqkEU5yykIaDAQry8O7dopDHp4ETXoKrpCX3eFI3rZBXkKMJPChqgxseCs0XmOCjbIZCaqmfeTF5GLhe4MRvNtCBp5ib83sYOXrHLHfcHvIZBBamXUWB4fz4RdAYf4Y4jJsnbNVZArERFTCI", "")
TELEGRAM_CHAT_ID = os.getenv("1237139552813418", "")

import os
from dotenv import load_dotenv

load_dotenv()


def clean_env(name):
    """
    Get an environment variable and strip any accidental whitespace or
    newline characters. This matters because copy-pasting secrets (e.g.
    into GitHub Actions secrets, or from a .env file) can easily include
    a trailing newline, which silently corrupts the value and causes
    confusing 401/authentication errors that look like a "wrong key" but
    are actually just a stray \\n character at the end.
    """
    value = os.getenv(name)
    return value.strip() if value else value


# ---- API Keys (loaded from .env, whitespace/newlines stripped) ----
GNEWS_API_KEY = clean_env("GNEWS_API_KEY")
GUARDIAN_API_KEY = clean_env("GUARDIAN_API_KEY")
NEWSDATA_API_KEY = clean_env("NEWSDATA_API_KEY")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY")
GROQ_API_KEY = clean_env("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = clean_env("TELEGRAM_CHAT_ID")

# Free-tier Gemini model — good daily quota, no billing required.
GEMINI_MODEL = "gemini-3.1-flash-lite"

# Fallback model on Groq if Gemini is unavailable (e.g. the ongoing AQ.-prefix
# key bug). llama-3.1-8b-instant has the most generous free-tier limits
# (14,400 requests/day) and is capable enough for ranking/rewriting/captions.
GROQ_MODEL = "llama-3.1-8b-instant"

# How many top stories to keep after ranking
TOP_STORIES_COUNT = 5

# Batched ranking: instead of discarding most fetched articles to fit one
# small prompt (which hurt content quality — random sampling could easily
# miss good education/national stories), the full article pool gets split
# into batches of this size, each ranked separately, then merged and sorted
# for the true top N. Based on observed Groq behavior, ~25 articles per
# batch keeps each response comfortably within its default output limit.
ARTICLES_PER_RANKING_BATCH = 25

# Small pause between ranking batches to stay well within Groq's 30
# requests/minute free-tier limit.
RANKING_BATCH_DELAY_SECONDS = 3

# ---- NewsData.io: pure category-based, genuine country=in filtering ----
# No keyword-guessing — this is NewsData's own curated "top stories" across
# several categories in ONE combined request. "crime" and "domestic" are
# included because paper-leak scandals and student protests often get filed
# under those categories rather than "education" specifically.
# NOTE: NewsData.io's free tier allows a MAXIMUM of 5 categories per query
# (this was previously 7 and caused a 422 error). Trimmed to the 5 that best
# match your actual priorities: general national news, IIT/NIT/student/exam
# news, paper-leak/scandal coverage, protests/social issues, and sports.
# Dropped "politics" (already your lowest-weighted tier) and "technology"
# (nice-to-have but not a core priority) to fit the limit.
NEWSDATA_CATEGORIES = "top,education,sports,crime,domestic"
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
