"""
channel_digest/collector.py
Retrieves Instagram posts published by @news.nit_iit for a specific calendar day in IST.
Uses the official Meta Graph API as the primary data source with automatic fallback to scraper.
"""

import os
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    INSTAGRAM_USERNAME,
    IST_TZ
)
from .database import is_post_in_roundup


def parse_timestamp_to_ist(timestamp_str_or_epoch: Any) -> Optional[datetime]:
    """
    Parses an ISO 8601 string or Unix epoch integer to a timezone-aware datetime in Asia/Kolkata (IST).
    """
    if not timestamp_str_or_epoch:
        return None
        
    try:
        if isinstance(timestamp_str_or_epoch, (int, float)):
            dt_utc = datetime.fromtimestamp(timestamp_str_or_epoch, tz=timezone.utc)
            return dt_utc.astimezone(IST_TZ)
            
        ts_str = str(timestamp_str_or_epoch).strip()
        # Handle trailing 'Z' or '+0000'
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        elif re.search(r'\+\d{4}$', ts_str):
            ts_str = ts_str[:-5] + ts_str[-5:-2] + ":" + ts_str[-2:]
            
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST_TZ)
    except Exception as e:
        print(f"  [Collector Warning] Failed to parse timestamp '{timestamp_str_or_epoch}': {e}")
        return None


def resolve_instagram_user_id(token: str, user_id: str) -> str:
    """
    Auto-resolves Facebook Page ID to connected Instagram Business Account ID (178414...) if needed.
    """
    if not user_id or not token:
        return user_id
        
    if user_id.startswith("178414"):
        return user_id
        
    try:
        url = f"https://graph.facebook.com/v19.0/{user_id}?fields=instagram_business_account&access_token={token}"
        resp = requests.get(url, timeout=12).json()
        if "instagram_business_account" in resp and "id" in resp["instagram_business_account"]:
            ig_id = resp["instagram_business_account"]["id"]
            print(f"  💡 Auto-resolved Instagram Business Account ID: {ig_id} from Page {user_id}")
            return ig_id
            
        accounts_url = f"https://graph.facebook.com/v19.0/me/accounts?fields=instagram_business_account&access_token={token}"
        acc_resp = requests.get(accounts_url, timeout=12).json()
        if "data" in acc_resp:
            for item in acc_resp["data"]:
                if "instagram_business_account" in item and "id" in item["instagram_business_account"]:
                    ig_id = item["instagram_business_account"]["id"]
                    print(f"  💡 Auto-resolved Instagram Business Account ID from me/accounts: {ig_id}")
                    return ig_id
    except Exception as e:
        print(f"  [Collector Notice] Instagram ID resolution exception: {e}")
        
    return user_id


def fetch_posts_via_graph_api(token: str, raw_user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves media posts published by the connected Instagram Business account using Meta Graph API.
    """
    user_id = resolve_instagram_user_id(token, raw_user_id)
    endpoint = f"https://graph.facebook.com/v19.0/{user_id}/media"
    params = {
        "fields": "id,caption,permalink,timestamp,media_type,media_url",
        "access_token": token,
        "limit": limit
    }
    
    print(f"  [Graph API] Fetching up to {limit} recent posts for Instagram Account ID: {user_id}...")
    try:
        resp = requests.get(endpoint, params=params, timeout=25)
        if resp.status_code != 200:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = error_data.get("error", {}).get("message", resp.text)
            print(f"  ❌ [Graph API Error] Status {resp.status_code}: {err_msg}")
            return []
            
        data = resp.json()
        raw_items = data.get("data", [])
        print(f"  [Graph API] Received {len(raw_items)} media items.")
        
        parsed_posts = []
        for item in raw_items:
            m_id = str(item.get("id", "")).strip()
            permalink = item.get("permalink", "")
            if not m_id or not permalink:
                continue
                
            raw_ts = item.get("timestamp")
            dt_ist = parse_timestamp_to_ist(raw_ts)
            
            parsed_posts.append({
                "media_id": m_id,
                "id": m_id,
                "caption": item.get("caption", "").strip(),
                "permalink": permalink,
                "media_type": item.get("media_type", "IMAGE"),
                "media_url": item.get("media_url", ""),
                "published_dt_ist": dt_ist,
                "published_date_ist": dt_ist.strftime("%Y-%m-%d") if dt_ist else "",
                "published_at_ist": dt_ist.strftime("%Y-%m-%d %H:%M:%S IST") if dt_ist else "",
                "source": "Meta Graph API"
            })
            
        return parsed_posts
    except Exception as e:
        print(f"  ❌ [Graph API Exception] Connection failure: {e}")
        return []


def fetch_posts_via_scraper_fallback(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Fallback mechanism to fetch posts using existing scrapers if Graph API credentials are not active.
    """
    print(f"  [Fallback Scraper] Attempting to retrieve posts for @{INSTAGRAM_USERNAME}...")
    try:
        from scrapers.instagram_scraper import fetch_instagram_posts
        raw_posts = fetch_instagram_posts(INSTAGRAM_USERNAME, limit=limit)
        parsed_posts = []
        for p in raw_posts:
            code = p.get("code")
            p_id = str(p.get("id") or code or "").strip()
            permalink = f"https://www.instagram.com/p/{code}/" if code else ""
            if not permalink:
                continue
                
            raw_ts = p.get("taken_at")
            dt_ist = parse_timestamp_to_ist(raw_ts)
            if not dt_ist and p.get("date"):
                try:
                    dt_ist = parse_timestamp_to_ist(p.get("date") + "T12:00:00+05:30")
                except Exception:
                    pass
                    
            parsed_posts.append({
                "media_id": p_id,
                "id": p_id,
                "caption": p.get("caption", "").strip(),
                "permalink": permalink,
                "media_type": "IMAGE",
                "media_url": p.get("image_url", ""),
                "published_dt_ist": dt_ist,
                "published_date_ist": dt_ist.strftime("%Y-%m-%d") if dt_ist else "",
                "published_at_ist": dt_ist.strftime("%Y-%m-%d %H:%M:%S IST") if dt_ist else "",
                "source": "Instagram Scraper Fallback"
            })
        print(f"  [Fallback Scraper] Retrieved {len(parsed_posts)} posts.")
        return parsed_posts
    except Exception as e:
        print(f"  [Fallback Scraper Notice] Fallback unavailable: {e}")
        return []


def collect_daily_posts(
    target_date_ist: Optional[str] = None,
    force: bool = False
) -> List[Dict[str, Any]]:
    """
    Collects eligible Instagram posts published by @news.nit_iit on `target_date_ist` (YYYY-MM-DD in IST).
    Excludes duplicates and posts already included in previous roundups unless `force=True`.
    
    Returns posts sorted newest-first.
    """
    if not target_date_ist or target_date_ist.strip().lower() in ["", "today", "now", "default", "current"]:
        target_date_ist = datetime.now(IST_TZ).strftime("%Y-%m-%d")
    else:
        target_date_ist = target_date_ist.strip()
        
    print("=" * 60)
    print(f"📥 COLLECTING INSTAGRAM POSTS FOR TARGET DATE: {target_date_ist} (IST)")
    print("=" * 60)
    
    all_posts = []
    
    # 1. Primary method: Official Meta Graph API
    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID:
        all_posts = fetch_posts_via_graph_api(INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID, limit=50)
    else:
        print("  ⚠️ Meta Graph API credentials not configured in environment. Checking fallback...")
        
    # 2. Secondary method: Scraper fallback if primary returned 0 posts
    if not all_posts:
        all_posts = fetch_posts_via_scraper_fallback(limit=25)
        
    print(f"\n📊 Total fetched posts from all sources: {len(all_posts)}")
    
    # 3. Filter for target calendar date in IST and deduplicate
    eligible_posts = []
    seen_media_ids = set()
    skipped_previous_days = 0
    skipped_already_processed = 0
    
    for post in all_posts:
        m_id = post.get("media_id", "")
        post_date = post.get("published_date_ist", "")
        
        # Deduplicate within batch
        if m_id in seen_media_ids:
            continue
        seen_media_ids.add(m_id)
        
        # Date filter (Asia/Kolkata calendar day match)
        if post_date != target_date_ist:
            skipped_previous_days += 1
            continue
            
        # Check if already processed in prior completed roundups
        if not force and is_post_in_roundup(m_id):
            skipped_already_processed += 1
            continue
            
        eligible_posts.append(post)
        
    print(f"  ✅ Filtered for {target_date_ist}: {len(eligible_posts)} eligible posts found.")
    print(f"  ⏭️ Skipped non-matching dates: {skipped_previous_days}")
    print(f"  ⏭️ Skipped already-processed posts: {skipped_already_processed}")
    
    # 4. Sort posts newest-first (descending timestamp)
    def sort_key(p):
        dt = p.get("published_dt_ist")
        return dt.timestamp() if dt else 0
        
    eligible_posts.sort(key=sort_key, reverse=True)
    return eligible_posts
