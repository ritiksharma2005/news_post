"""
news_anchor_ai/ai/news_extractor.py
Extracts news content from:
1. Instagram Post URL (via Meta Graph API)
2. Direct image/screenshot file uploads (Telegram Fallback)
"""

import os
import re
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple

from news_anchor_ai.config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    TEMP_DIR
)
from news_anchor_ai.extractor.instagram_fetcher import (
    resolve_instagram_user_id,
    extract_headline_from_caption
)

def extract_from_instagram_url(post_url: str) -> Optional[Dict]:
    """
    Extracts post caption and high-resolution image from Instagram post URL
    using Meta Graph API for connected @news.nit_iit account.
    """
    # Extract shortcode e.g. https://www.instagram.com/p/DB12345/ -> DB12345
    match = re.search(r'/p/([A-Za-z0-9_-]+)', post_url)
    shortcode = match.group(1) if match else None

    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_USER_ID:
        print("[News Extractor] Meta Graph credentials not configured.")
        return None

    user_id = resolve_instagram_user_id(INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID)
    url = f"https://graph.facebook.com/v19.0/{user_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,children{media_url,media_type}",
        "limit": 25,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    try:
        resp = requests.get(url, params=params, timeout=20).json()
        items = resp.get("data", [])

        target_item = None
        for item in items:
            permalink = item.get("permalink", "")
            if (shortcode and shortcode in permalink) or (post_url.strip("/") in permalink):
                target_item = item
                break

        # If not exact match, fall back to newest post
        if not target_item and items:
            print(f"[News Extractor] Shortcode {shortcode} not in recent 25 posts, taking latest post.")
            target_item = items[0]

        if not target_item:
            return None

        media_id = target_item.get("id")
        caption = target_item.get("caption", "")
        permalink = target_item.get("permalink", post_url)
        media_type = target_item.get("media_type")

        # Resolve image URL
        image_url = None
        if media_type == "IMAGE":
            image_url = target_item.get("media_url")
        elif media_type == "CAROUSEL_ALBUM":
            children = target_item.get("children", {}).get("data", [])
            for c in children:
                if c.get("media_type") == "IMAGE" and c.get("media_url"):
                    image_url = c.get("media_url")
                    break

        # Download image
        local_img_path = TEMP_DIR / f"news_post_{media_id}.jpg"
        if image_url:
            img_bytes = requests.get(image_url, timeout=25).content
            with open(local_img_path, "wb") as f:
                f.write(img_bytes)

        headline = extract_headline_from_caption(caption)
        return {
            "media_id": media_id,
            "headline": headline,
            "caption": caption,
            "permalink": permalink,
            "image_path": str(local_img_path) if local_img_path.exists() else None,
            "image_url": image_url
        }

    except Exception as e:
        print(f"[News Extractor] Error querying Instagram Graph API: {e}")
        return None


def extract_from_direct_upload(image_path: Path, user_caption: str = "") -> Dict:
    """
    Telegram Fallback: Handles direct image/screenshot uploads when an Instagram URL
    is third-party, private, or cannot be queried via API.
    """
    media_id = f"upload_{int(image_path.stat().st_mtime)}"
    headline = extract_headline_from_caption(user_caption) if user_caption else "Breaking Student & Campus News"

    return {
        "media_id": media_id,
        "headline": headline,
        "caption": user_caption,
        "permalink": "Direct Telegram Submission",
        "image_path": str(image_path),
        "image_url": None
    }
