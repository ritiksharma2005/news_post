"""
news_anchor_ai/extractor/instagram_fetcher.py
Fetches recent posts from @news.nit_iit via the Meta Instagram Graph API.
Strictly sorts by publication timestamp (ignoring pinned sequence order)
and filters out posts that have already been converted to videos.
"""

import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

from news_anchor_ai.config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    TEMP_DIR,
    INSTAGRAM_ACCOUNT
)
from news_anchor_ai.database import is_post_processed, mark_post_status

GRAPH_API_VERSION = "v19.0"

def parse_iso_timestamp(ts_str: str) -> datetime:
    """Parses ISO-8601 timestamp string from Instagram API."""
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def resolve_instagram_user_id(token: str, user_id: str) -> str:
    """
    Auto-resolves Facebook Page ID to connected Instagram Business Account ID (178414...).
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
        print(f"  [Instagram ID Notice] {e}")
    return user_id

def extract_headline_from_caption(caption: str) -> str:
    """Extracts a clean, punchy headline from the post caption."""
    if not caption:
        return "Latest Student & Exam Update"
    
    # Split into lines
    lines = [line.strip() for line in caption.split("\n") if line.strip()]
    for line in lines:
        # Avoid hashtag lines, call-to-actions, or purely emoji lines
        if line.startswith("#") or "follow" in line.lower() or "swipe" in line.lower():
            continue
        cleaned = line.replace("📌", "").replace("🚨", "").replace("📢", "").replace("🔥", "").strip()
        if len(cleaned) >= 15:
            # Truncate to reasonable headline length
            return cleaned[:90].strip()
            
    return lines[0][:90].strip() if lines else "Student & Education News"

def fetch_latest_posts(limit: int = 15) -> List[Dict]:
    """
    Fetches posts from Meta Graph API, sorts by publication date,
    and returns un-processed candidate posts for video generation.
    """
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_USER_ID:
        print("[Instagram Fetcher] Error: INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID not configured.")
        return []

    user_id = resolve_instagram_user_id(INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{user_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,children{media_url,media_type}",
        "limit": limit,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
    except Exception as e:
        print(f"[Instagram Fetcher] Network error contacting Graph API: {e}")
        return []

    if "error" in data:
        err = data['error']
        print(f"[Instagram Fetcher] Graph API Error ({err.get('code')}): {err.get('message')}")
        return []

    items = data.get("data", [])
    print(f"  [Instagram Fetcher] Graph API query returned {len(items)} raw media objects.")
    if not items:
        print(f"[Instagram Fetcher] No media items returned for {INSTAGRAM_ACCOUNT}")
        return []

    # Sort strictly by publication timestamp descending (newest first, ignoring pinned posts)
    items.sort(key=lambda x: parse_iso_timestamp(x.get("timestamp", "")), reverse=True)

    candidates = []
    for item in items:
        media_id = item.get("id")
        if not media_id or is_post_processed(media_id):
            continue

        caption = item.get("caption", "")
        permalink = item.get("permalink", "")
        media_type = item.get("media_type", "")
        timestamp = item.get("timestamp", "")

        # Get direct image URL
        image_url = None
        if media_type == "IMAGE":
            image_url = item.get("media_url")
        elif media_type == "CAROUSEL_ALBUM":
            children = item.get("children", {}).get("data", [])
            for child in children:
                if child.get("media_type") == "IMAGE" and child.get("media_url"):
                    image_url = child.get("media_url")
                    break

        if not image_url:
            continue

        headline = extract_headline_from_caption(caption)
        candidates.append({
            "media_id": media_id,
            "headline": headline,
            "caption": caption,
            "permalink": permalink,
            "image_url": image_url,
            "image_path": str(TEMP_DIR / f"post_{media_id}.jpg"),
            "timestamp": timestamp,
            "formatted_date": parse_iso_timestamp(timestamp).strftime("%d %b, %I:%M %p")
        })

        if len(candidates) >= 4:
            break

    print(f"[Instagram Fetcher] Found {len(candidates)} fresh candidate posts for video generation.")
    return candidates
