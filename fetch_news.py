"""
fetch_news.py
Pulls raw articles from three sources:
- NewsData.io: pure category-based, genuine country=in filtering (no keywords)
- GNews: keyword search using tiered priority lists (JEE/NEET/paper-leak etc.)
- Guardian: keyword search (structurally required, no native India filter)
Normalizes them into one common format, removes duplicate/near-duplicate
stories, and saves the result to output/raw_articles.json.

Run directly to test: python fetch_news.py
"""

import json
import os
import re
import requests

import config


def fetch_newsdata():
    """
    Fetch articles from NewsData.io using pure category-based fetching —
    NewsData's own curated "top stories" across several categories, in ONE
    combined request. No keyword-guessing: this reflects what's actually
    trending in India today per NewsData's own ranking.
    """
    articles = []
    url = "https://newsdata.io/api/1/latest"

    params = {
        "apikey": config.NEWSDATA_API_KEY,
        "country": "in",
        "language": "en",
        "category": config.NEWSDATA_CATEGORIES,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("results", []):
            articles.append({
                "source": "NewsData",
                "query": f"categories:{config.NEWSDATA_CATEGORIES}",
                "title": (item.get("title") or "").strip(),
                "description": (item.get("description") or "").strip(),
                "url": item.get("link"),
                "image": item.get("image_url"),
                "published_at": item.get("pubDate"),
            })
    except requests.exceptions.RequestException as e:
        print(f"[NewsData] Error fetching categories '{config.NEWSDATA_CATEGORIES}': {e}")
        if e.response is not None:
            print(f"[NewsData] Full error response: {e.response.text[:500]}")

    return articles


def fetch_gnews():
    """Fetch articles from GNews's search endpoint using the combined tiered keyword lists."""
    articles = []
    for query in config.GNEWS_QUERIES:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": query,
            "lang": "en",
            "country": "in",
            "max": config.ARTICLES_PER_QUERY,
            "apikey": config.GNEWS_API_KEY,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("articles", []):
                articles.append({
                    "source": "GNews",
                    "query": query,
                    "title": item.get("title", "").strip(),
                    "description": item.get("description", "").strip(),
                    "url": item.get("url"),
                    "image": item.get("image"),
                    "published_at": item.get("publishedAt"),
                })
        except requests.exceptions.RequestException as e:
            print(f"[GNews] Error fetching query '{query}': {e}")
    return articles


def fetch_guardian():
    """Fetch articles from The Guardian by searching for the configured topic keywords."""
    articles = []
    for query in config.GUARDIAN_QUERIES:
        url = "https://content.guardianapis.com/search"
        params = {
            "q": query,
            "show-fields": "trailText,thumbnail,bodyText",
            "page-size": config.ARTICLES_PER_QUERY,
            "api-key": config.GUARDIAN_API_KEY,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("response", {}).get("results", []):
                fields = item.get("fields", {})
                articles.append({
                    "source": "Guardian",
                    "query": query,
                    "title": item.get("webTitle", "").strip(),
                    "description": fields.get("trailText", "").strip(),
                    "url": item.get("webUrl"),
                    "image": fields.get("thumbnail"),
                    "published_at": item.get("webPublicationDate"),
                })
        except requests.exceptions.RequestException as e:
            print(f"[Guardian] Error fetching query '{query}': {e}")
    return articles





# Common words that don't help identify whether two headlines are about
# the same story (skip them when comparing).
STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "to", "of", "for", "and", "or",
    "is", "are", "was", "were", "with", "by", "as", "amid", "over", "its",
}


def title_words(title):
    """Extract meaningful lowercase words from a title, dropping stopwords."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def title_similarity(a, b):
    """
    Return a 0-1 similarity score between two titles using word overlap
    (Jaccard similarity). This handles headlines that describe the same
    event with different wording/order much better than character diffing.
    e.g. "India wins cricket match against Australia" vs
         "India defeats Australia in cricket match" -> high overlap
    """
    words_a, words_b = title_words(a), title_words(b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def dedupe_articles(articles, threshold=0.45):
    """
    Remove near-duplicate stories (same event reported by multiple outlets
    or matched by more than one query). Keeps the first occurrence.
    """
    unique = []
    for article in articles:
        if not article["title"]:
            continue
        is_duplicate = any(
            title_similarity(article["title"], existing["title"]) >= threshold
            for existing in unique
        )
        if not is_duplicate:
            unique.append(article)
    return unique


def fetch_all():
    """Fetch from all sources, dedupe, and save to disk."""
    print("Fetching from NewsData.io (India-only, category-based)...")
    newsdata_articles = fetch_newsdata()
    print(f"  -> {len(newsdata_articles)} articles")

    print("Fetching from GNews (keyword tiers)...")
    gnews_articles = fetch_gnews()
    print(f"  -> {len(gnews_articles)} articles")

    print("Fetching from The Guardian (keyword topics)...")
    guardian_articles = fetch_guardian()
    print(f"  -> {len(guardian_articles)} articles")

    all_articles = newsdata_articles + gnews_articles + guardian_articles
    print(f"Total before dedupe: {len(all_articles)}")

    deduped = dedupe_articles(all_articles)
    print(f"Total after dedupe: {len(deduped)}")

    os.makedirs(os.path.dirname(config.RAW_ARTICLES_PATH), exist_ok=True)
    with open(config.RAW_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"Saved to {config.RAW_ARTICLES_PATH}")
    return deduped


if __name__ == "__main__":
    fetch_all()
