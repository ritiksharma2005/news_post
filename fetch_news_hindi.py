"""
fetch_news_hindi.py
Fetches Hindi news from:
1. NewsAPI (using NEWSAPI_API_KEY, language=hi)
2. Aaj Tak homepage scraper (Devanagari text > 30 chars)
3. Dainik Jagran homepage scraper (Devanagari text > 30 chars)
4. Newspinch homepage scraper (Devanagari text > 30 chars)
Merges and saves raw stories to data/raw_hindi_news.json
"""

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def fetch_newsapi():
    """Fetches Hindi articles from NewsAPI."""
    api_key = os.getenv("NEWSAPI_API_KEY")
    if not api_key:
        print("  [NewsAPI] NEWSAPI_API_KEY not found in env.")
        return []

    url = f"https://newsapi.org/v2/top-headlines?language=hi&apiKey={api_key}"
    articles = []
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for art in data.get("articles", []):
                title = art.get("title")
                desc = art.get("description") or ""
                link = art.get("url")
                source = art.get("source", {}).get("name", "NewsAPI")
                if title and link:
                    articles.append({
                        "title": title,
                        "description": desc,
                        "url": link,
                        "source": source
                    })
            print(f"  [NewsAPI] Fetched {len(articles)} Hindi articles.")
    except Exception as e:
        print(f"  [NewsAPI] Error: {e}")
    return articles


def scrape_homepage_stories(url, name):
    """Scrapes news headlines from the target homepage containing Hindi text (> 30 characters)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"  [{name}] Failed to fetch (HTTP {res.status_code})")
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a"):
            txt = a.text.strip()
            href = a.get("href", "")
            # Clean spaces
            txt = re.sub(r"\s+", " ", txt)

            # Match Devanagari text length > 30 characters
            if txt and href and len(txt) > 30 and re.search(r"[\u0900-\u097f]", txt):
                # Resolve relative URLs
                if href.startswith("/"):
                    if url.endswith("/"):
                        href = url[:-1] + href
                    else:
                        href = url + href
                
                # Filter category/tag index pages
                if "category" in href or "tag" in href:
                    continue

                articles.append({
                    "title": txt,
                    "description": "",
                    "url": href,
                    "source": name
                })
        print(f"  [{name}] Scraped {len(articles)} potential stories.")
    except Exception as e:
        print(f"  [{name}] Error: {e}")
    return articles


def fetch_all():
    print("Fetching Hindi news sources...")
    
    # 1. NewsAPI
    newsapi_stories = fetch_newsapi()
    
    # 2. Aaj Tak
    aajtak_stories = scrape_homepage_stories("https://www.aajtak.in/", "AajTak")
    
    # 3. Dainik Jagran
    jagran_stories = scrape_homepage_stories("https://www.jagran.com/", "DainikJagran")
    
    # 4. Newspinch
    newspinch_stories = scrape_homepage_stories("https://newspinch.in/", "Newspinch")
    
    # Merge and deduplicate by title
    all_stories = newsapi_stories + aajtak_stories + jagran_stories + newspinch_stories
    seen_titles = set()
    deduplicated = []
    
    for s in all_stories:
        title_key = re.sub(r"\s+", "", s["title"]).lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduplicated.append(s)
            
    print(f"Total merged and deduplicated stories: {len(deduplicated)}")
    
    # Save raw stories
    os.makedirs("data", exist_ok=True)
    output_path = "data/raw_hindi_news.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(deduplicated, f, indent=2, ensure_ascii=False)
        
    print(f"Saved raw Hindi news to {output_path}")
    return deduplicated


if __name__ == "__main__":
    fetch_all()
