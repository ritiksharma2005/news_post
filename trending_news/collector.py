"""
trending_news/collector.py
Instagram News Lead Collector (Playwright + Apify Fallback)
"""

import os
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import INSTAGRAM_SOURCES, APIFY_TOKEN, OUTPUT_DIR
from .parser import parse_raw_post
from .time_filter import get_run_time_window, is_within_time_window
from .database import is_post_processed, get_last_run_timestamp

# Playwright sync API
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def download_lead_image(image_url: str, post_id: str) -> Optional[str]:
    """Downloads source post image for Gemini multimodal analysis."""
    if not image_url or not image_url.startswith("http"):
        return None
        
    temp_dir = OUTPUT_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_path = temp_dir / f"lead_{post_id}.jpg"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(image_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return str(out_path)
    except Exception as e:
        print(f"  [Collector] Failed to download image for '{post_id}': {e}")
        
    return None


def scrape_with_playwright(username: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Scrapes target Instagram profile using Playwright browser context."""
    if not PLAYWRIGHT_AVAILABLE:
        return []
        
    print(f"  [Playwright] Launching browser for '@{username}'...")
    scraped_posts = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            url = f"https://www.instagram.com/{username}/"
            page.goto(url, wait_until="networkidle", timeout=25000)
            time.sleep(3)
            
            # Extract links to posts
            links = page.query_selector_all("a[href*='/p/']")
            post_codes = set()
            for link in links:
                href = link.get_attribute("href")
                if href and "/p/" in href:
                    parts = href.split("/p/")[1].split("/")[0]
                    if parts:
                        post_codes.add(parts)
                        if len(post_codes) >= limit:
                            break
                            
            for code in list(post_codes)[:limit]:
                # Navigate to individual post page to fetch full caption & image
                post_url = f"https://www.instagram.com/p/{code}/"
                try:
                    page.goto(post_url, wait_until="domcontentloaded", timeout=15000)
                    time.sleep(2)
                    
                    # Extract OG meta tags for clean caption and image
                    caption = ""
                    image_url = ""
                    
                    og_desc = page.query_selector("meta[property='og:description']")
                    if og_desc:
                        caption = og_desc.get_attribute("content") or ""
                        
                    og_img = page.query_selector("meta[property='og:image']")
                    if og_img:
                        image_url = og_img.get_attribute("content") or ""
                        
                    time_elem = page.query_selector("time")
                    timestamp = ""
                    if time_elem:
                        timestamp = time_elem.get_attribute("datetime") or ""
                        
                    scraped_posts.append({
                        "id": code,
                        "code": code,
                        "url": post_url,
                        "caption": caption,
                        "image_url": image_url,
                        "timestamp": timestamp
                    })
                except Exception as pe:
                    print(f"  [Playwright] Error fetching post '{code}': {pe}")
                    
            browser.close()
    except Exception as e:
        print(f"  [Playwright Notice] Failed for '@{username}': {e}")
        
    return scraped_posts


def scrape_with_apify(username: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fallback Instagram scraper using Apify API actor."""
    if not APIFY_TOKEN:
        print("  [Apify Scraper] APIFY_TOKEN is missing. Skipping fallback.")
        return []
        
    print(f"  [Apify Fallback] Scraping posts for '@{username}'...")
    actor_id = "apify~instagram-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"
    input_data = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsLimit": limit,
        "resultsType": "posts"
    }
    
    try:
        res = requests.post(run_url, json=input_data, timeout=25)
        if res.status_code in [200, 201]:
            run_id = res.json().get("data", {}).get("id")
            if run_id:
                for _ in range(15):
                    time.sleep(4)
                    status_res = requests.get(f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}", timeout=15)
                    if status_res.status_code == 200:
                        run_info = status_res.json().get("data", {})
                        if run_info.get("status") == "SUCCEEDED":
                            dataset_id = run_info.get("defaultDatasetId")
                            items_res = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}", timeout=15)
                            if items_res.status_code == 200:
                                raw_items = items_res.json()
                                results = []
                                for item in raw_items:
                                    results.append({
                                        "id": item.get("id") or item.get("shortCode"),
                                        "code": item.get("shortCode"),
                                        "url": item.get("url"),
                                        "caption": item.get("caption", ""),
                                        "image_url": item.get("displayUrl") or (item.get("images", [""])[0] if item.get("images") else ""),
                                        "timestamp": item.get("timestamp")
                                    })
                                return results
                        elif run_info.get("status") in ["FAILED", "ABORTED"]:
                            break
    except Exception as e:
        print(f"  [Apify Error] Exception for '@{username}': {e}")
        
    return []


def collect_leads_for_run(run_type: str = "morning") -> List[Dict[str, Any]]:
    """
    Master collection coordinator:
    1. Determines current run's (start_utc, end_utc) window.
    2. Scrapes target accounts using Playwright (or Apify fallback).
    3. Filters out already processed posts from DB.
    4. Filters posts by timestamp window.
    5. Downloads candidate lead images to local temp folder.
    """
    print(f"\n📡 [Collector] Starting lead collection for {run_type.upper()} RUN...")
    
    last_run_ts = get_last_run_timestamp(run_type)
    start_utc, end_utc = get_run_time_window(run_type, last_run_timestamp=last_run_ts)
    
    print(f"  [Window] Filtering posts published between:")
    print(f"    Start: {start_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"    End:   {end_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    
    collected_leads = []
    
    for username in INSTAGRAM_SOURCES:
        print(f"\n🔍 Scraping target source: @{username}")
        raw_posts = scrape_with_playwright(username, limit=10)
        if not raw_posts:
            print("  [Fallback] Playwright returned 0 posts. Invoking Apify fallback...")
            raw_posts = scrape_with_apify(username, limit=10)
            
        print(f"  Fetched {len(raw_posts)} raw items from @{username}.")
        
        source_leads = []
        for p in raw_posts:
            parsed = parse_raw_post(p, username)
            post_id = parsed["source_post_id"]
            
            # Check Level 1 deduplication
            if is_post_processed(post_id):
                print(f"  [Skip - DB Duplicate] Post '{post_id}' already processed.")
                continue
                
            # Check Time Window
            if not is_within_time_window(parsed["posted_at"], start_utc, end_utc):
                print(f"  [Skip - Out of Window] Post '{post_id}' timestamp '{parsed['posted_at']}' outside target window.")
                continue
                
            # Download image for Gemini analysis
            if parsed["image_url"]:
                img_path = download_lead_image(parsed["image_url"], post_id)
                parsed["image_path"] = img_path
            else:
                parsed["image_path"] = None
                
            source_leads.append(parsed)
            print(f"  ✅ Qualified candidate lead: '{post_id}' from @{username}")
            
        # Fallback for this specific account if strict time window yielded 0 posts
        if not source_leads and raw_posts:
            print(f"  ⚠️ [Collector Notice] Strict window yielded 0 posts for @{username}. Using latest unprocessed post as fallback...")
            for p in raw_posts:
                parsed = parse_raw_post(p, username)
                post_id = parsed["source_post_id"]
                if is_post_processed(post_id):
                    continue
                if parsed["image_url"]:
                    parsed["image_path"] = download_lead_image(parsed["image_url"], post_id)
                else:
                    parsed["image_path"] = None
                source_leads.append(parsed)
                print(f"  ✅ Qualified candidate lead (Account Fallback): '{post_id}' from @{username}")
                break
                
        collected_leads.extend(source_leads)
            
    print(f"\n📡 [Collector Complete] Collected {len(collected_leads)} valid lead stories for processing.")
    return collected_leads
