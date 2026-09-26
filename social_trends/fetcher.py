"""
social_trends/fetcher.py
Data Fetcher for Reddit Public JSON Endpoints & Twitter / Social Feeds
Downloads attached source images for Telegram delivery.
"""

import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import (
    SUBREDDITS,
    TWITTER_SOURCES,
    OUTPUT_DIR,
    GOOGLE_TRENDS_INDIA_RSS,
    GOOGLE_NEWS_INDIA_RSS,
    GOOGLE_NEWS_INDIA_TOPICS,
)
from .database import is_post_processed

# Playwright sync API
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def download_source_image(image_url: str, post_id: str) -> Optional[str]:
    """Downloads attached source photo to local temp folder for Telegram broadcast."""
    if not image_url or not image_url.startswith("http"):
        return None
        
    temp_dir = OUTPUT_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_path = temp_dir / f"social_{post_id}.jpg"
    
    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return str(out_path)
    except Exception as e:
        print(f"  [Fetcher] Failed to download photo for '{post_id}': {e}")
        
    return None


def scrape_reddit_with_playwright(subreddits: List[str], limit_per_sub: int = 5) -> List[Dict[str, Any]]:
    """Scrapes top trending Reddit posts using Playwright headless browser."""
    if not PLAYWRIGHT_AVAILABLE:
        return []
        
    print(f"  [Playwright] Scraping target subreddits...")
    results = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            for sub in subreddits:
                try:
                    page = context.new_page()
                    url = f"https://www.reddit.com/r/{sub}/hot/"
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)
                    
                    # Query post elements
                    posts = page.query_selector_all("shreddit-post, div[data-testid='post-container']")
                    print(f"  r/{sub}: Found {len(posts)} posts via browser context.")
                    
                    for idx, post in enumerate(posts[:limit_per_sub]):
                        title = post.get_attribute("post-title") or ""
                        post_id = post.get_attribute("id") or f"{sub}_{idx}"
                        author_name = post.get_attribute("author") or post.get_attribute("author-name") or ""
                        author_str = f"u/{author_name}" if author_name else "Reddit Community"
                        
                        permalink = post.get_attribute("permalink") or ""
                        if permalink and not permalink.startswith("http"):
                            permalink = f"https://www.reddit.com{permalink}"
                            
                        # Image URL
                        image_url = post.get_attribute("content-href") or ""
                        if not image_url or not re.search(r'\.(jpg|jpeg|png|webp)', image_url, re.I):
                            img_elem = post.query_selector("img")
                            if img_elem:
                                image_url = img_elem.get_attribute("src") or ""
                                
                        if not title:
                            continue
                            
                        # Skip pinned meta threads, rules, and community hubs
                        skip_meta = ["community hub", "weekly thread", "daily discussion", "megathread", "rules & faq", "welcome to r/"]
                        if any(kw in title.lower() for kw in skip_meta):
                            continue
                            
                        if is_post_processed(post_id, title):
                            continue
                            
                        results.append({
                            "platform": f"Reddit (r/{sub})",
                            "author": author_str,
                            "post_id": post_id,
                            "title": title,
                            "selftext": title,
                            "source_url": permalink or f"https://www.reddit.com/r/{sub}/",
                            "image_url": image_url,
                            "score": 110 - idx,
                            "subreddit": sub
                        })
                    page.close()
                except Exception as pe:
                    print(f"  [Playwright Notice] Error for r/{sub}: {pe}")
                    
            browser.close()
    except Exception as e:
        print(f"  [Playwright Notice] Reddit scraping skipped: {e}")
        
    return results


def fetch_google_trends_india_rss(limit: int = 12) -> List[Dict[str, Any]]:
    """Fetches real-time trending search queries & news in India via Google Trends RSS."""
    print("  [Google Trends IN] Fetching daily trending search queries in India...")
    results = []
    try:
        resp = requests.get(GOOGLE_TRENDS_INDIA_RSS, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is not None:
                items = channel.findall("item")
                print(f"  [Google Trends IN] Parsed {len(items)} trending topics.")
                for idx, item in enumerate(items[:limit]):
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    title = title_elem.text if title_elem is not None else ""
                    link = link_elem.text if link_elem is not None else ""
                    
                    # Namespace search for ht:picture or image tags
                    image_url = ""
                    for child in item:
                        if child.tag.endswith("picture") and child.text:
                            image_url = child.text
                            break
                            
                    if not title:
                        continue
                        
                    post_id = f"gtrend_{hash(title) & 0xffffffff}"
                    if is_post_processed(post_id, title):
                        continue
                        
                    results.append({
                        "platform": "Google Trends (India)",
                        "post_id": post_id,
                        "title": f"Trending in India: {title}",
                        "selftext": title,
                        "source_url": link or "https://trends.google.com/trends/trendingsearches/daily?geo=IN",
                        "image_url": image_url,
                        "score": 98 - idx
                    })
    except Exception as e:
        print(f"  [Google Trends IN Error] Failed fetching Google Trends: {e}")
        
    return results


def fetch_google_news_india_rss(limit: int = 15) -> List[Dict[str, Any]]:
    """Fetches breaking Indian news trends via Google News RSS feed & topic channels."""
    print("  [RSS Fetcher] Querying Google News India RSS feed...")
    results = []
    
    feed_urls = [
        ("Google News India", GOOGLE_NEWS_INDIA_RSS),
    ] + GOOGLE_NEWS_INDIA_TOPICS
    
    for feed_name, rss_url in feed_urls:
        try:
            resp = requests.get(rss_url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")
                    for idx, item in enumerate(items[:limit]):
                        title_elem = item.find("title")
                        link_elem = item.find("link")
                        pubdate_elem = item.find("pubDate")
                        
                        title = title_elem.text if title_elem is not None else ""
                        link = link_elem.text if link_elem is not None else ""
                        pub_date = pubdate_elem.text if pubdate_elem is not None else ""
                        
                        if not title:
                            continue
                            
                        # Extract source publisher e.g. "Title - NDTV News"
                        publisher = feed_name
                        if " - " in title:
                            parts = title.rsplit(" - ", 1)
                            title_clean = parts[0]
                            publisher = parts[1]
                        else:
                            title_clean = title
                            
                        post_id = f"rss_{hash(title_clean) & 0xffffffff}"
                        if is_post_processed(post_id, title_clean):
                            continue
                            
                        # Extract image URL if present in description
                        desc_elem = item.find("description")
                        desc_text = desc_elem.text if desc_elem is not None else ""
                        image_url = ""
                        img_match = re.search(r'src=["\'](https?://[^"\']+)["\']', desc_text)
                        if img_match:
                            image_url = img_match.group(1)
                            
                        results.append({
                            "platform": f"India Social / {publisher}",
                            "post_id": post_id,
                            "title": title_clean,
                            "selftext": title_clean,
                            "source_url": link,
                            "image_url": image_url,
                            "score": 90 - idx,
                            "pub_date": pub_date
                        })
        except Exception as e:
            print(f"  [RSS Error] Failed fetching '{feed_name}': {e}")
            
    return results


def fetch_all_social_trends() -> List[Dict[str, Any]]:
    """Master collection coordinator combining Google Trends IN, Reddit & Twitter/Social RSS feeds."""
    candidates = []
    
    # 1. Fetch Google Trends India daily search queries
    gtrends_candidates = fetch_google_trends_india_rss(limit=10)
    candidates.extend(gtrends_candidates)
    
    # 2. Fetch Reddit trends via Playwright
    reddit_candidates = scrape_reddit_with_playwright(SUBREDDITS, limit_per_sub=4)
    candidates.extend(reddit_candidates)
    
    # 3. Fetch Breaking Social/Twitter news trends via India RSS feeds
    rss_candidates = fetch_google_news_india_rss(limit=10)
    candidates.extend(rss_candidates)
    
    # Sort candidates by upvote/importance score
    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Download attached source photos or fetch/generate fallback relevant image for candidates
    print(f"\n📥 [Fetcher] Downloading/Ensuring attached source photos for {len(candidates)} candidates...")
    for c in candidates:
        if c.get("image_url"):
            local_img = download_source_image(c["image_url"], c["post_id"])
            c["image_path"] = local_img
        else:
            c["image_path"] = None
            
        # Fallback real image web search or AI generation if no direct image attached
        if not c.get("image_path"):
            query_text = c.get("title", "")
            temp_out = OUTPUT_DIR / "temp" / f"social_{c.get('post_id')}.jpg"
            try:
                from generate_image import fetch_search_image, generate_image
                search_q = f"{query_text[:50]} student India news photo"
                img_path = fetch_search_image(search_q, str(temp_out))
                if not img_path:
                    img_path = generate_image(query_text[:80], headline=query_text[:80], output_path=str(temp_out))
                if img_path and os.path.exists(img_path):
                    c["image_path"] = str(img_path)
            except Exception as ie:
                print(f"  [Image Engine Notice] Fallback image search/gen notice for '{c.get('post_id')}': {ie}")
            
    return candidates
