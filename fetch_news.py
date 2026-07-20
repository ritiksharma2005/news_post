"""
fetch_news.py
Pulls raw articles & updates from 4 sources:
- NewsData.io (India national categories)
- GNews (Tiered queries for exams/tech)
- RSS Feeds (PIB Govt announcements, Govt Jobs, ISRO, Unstop Opportunities)
- Guardian (International context)

Normalizes them into one common format and saves to output/raw_articles.json.
"""

import json
import os
import re
import requests
import feedparser

import config


def fetch_newsdata():
    """Fetch top India stories from NewsData.io."""
    articles = []
    url = "https://newsdata.io/api/1/latest"
    params = {
        "apikey": getattr(config, "NEWSDATA_API_KEY", os.getenv("NEWSDATA_API_KEY", "")),
        "country": "in",
        "language": "en",
        "category": getattr(config, "NEWSDATA_CATEGORIES", "education,technology,business,science"),
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("results", []):
            articles.append({
                "source": "NewsData",
                "bucket": "CurrentAffairs",
                "title": (item.get("title") or "").strip(),
                "description": (item.get("description") or "").strip(),
                "url": item.get("link"),
                "published_at": item.get("pubDate"),
            })
    except Exception as e:
        print(f"[NewsData] Error: {e}")

    return articles


def fetch_gnews():
    """Fetch articles from GNews search."""
    articles = []
    queries = getattr(config, "GNEWS_QUERIES", ["India engineering college", "JEE NEET exam", "AI technology India"])
    for query in queries:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "country": "in",
            "max": 5,
            "apikey": getattr(config, "GNEWS_API_KEY", os.getenv("GNEWS_API_KEY", "")),
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("articles", []):
                articles.append({
                    "source": "GNews",
                    "bucket": "StudentNews",
                    "title": (item.get("title") or "").strip(),
                    "description": (item.get("description") or "").strip(),
                    "url": item.get("url"),
                    "published_at": item.get("publishedAt"),
                })
        except Exception as e:
            print(f"[GNews] Error for query '{query}': {e}")

    return articles


def fetch_rss_feeds():
    """Fetch official notices, Govt Job alerts, and Student opportunities via RSS."""
    articles = []
    rss_dict = getattr(config, "RSS_FEEDS", {})

    for feed_name, feed_url in rss_dict.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Take top 5 entries per RSS feed
                title = entry.get("title", "").strip()
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", entry.get("description", ""))).strip()

                bucket = "CareerJobs" if "Jobs" in feed_name or "Opportunities" in feed_name else "GovtPolicy"

                articles.append({
                    "source": f"RSS_{feed_name}",
                    "bucket": bucket,
                    "title": title,
                    "description": summary[:300],
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                })
            print(f"[RSS] Successfully fetched {len(feed.entries[:5])} items from {feed_name}")
        except Exception as e:
            print(f"[RSS] Error fetching {feed_name}: {e}")

    return articles


def fetch_all():
    """Fetch all sources and save to output/raw_articles.json."""
    print("Fetching raw articles from APIs and RSS feeds...")
    all_articles = []
    all_articles.extend(fetch_newsdata())
    all_articles.extend(fetch_gnews())
    all_articles.extend(fetch_rss_feeds())

    os.makedirs("output", exist_ok=True)
    out_path = "output/raw_articles.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)

    print(f"Total fetched: {len(all_articles)} items saved to {out_path}")
    return all_articles


if __name__ == "__main__":
    fetch_all()