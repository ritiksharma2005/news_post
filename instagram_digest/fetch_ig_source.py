"""
instagram_digest/fetch_ig_source.py
Monitors trusted target Instagram profiles (e.g. @iit__nit__iiit) using:
1. Meta Graph API (Official, immune to Cloudflare blocks)
2. Resilient RSSHub Fallback Loop
3. Pixwox & Picnob Mirror Fallbacks
"""

import sys
import os

# 🔹 PATH RESOLVER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import re
import datetime
import requests
import feedparser
import config

TARGET_ACCOUNTS = ["iit__nit__iiit"]


def fetch_via_graph_api(target_username):
    """Uses Meta Graph API Business Discovery (Official & immune to Cloudflare blocks)."""
    access_token = getattr(config, "INSTAGRAM_ACCESS_TOKEN", os.getenv("INSTAGRAM_ACCESS_TOKEN", ""))
    ig_user_id = getattr(config, "INSTAGRAM_USER_ID", os.getenv("INSTAGRAM_USER_ID", ""))

    if not access_token or not ig_user_id:
        print("  Graph API credentials missing. Skipping Graph API check.")
        return []

    url = f"https://graph.facebook.com/v19.0/{ig_user_id}"
    params = {
        "fields": f"business_discovery.username({target_username}){{media{{caption,media_url,timestamp,permalink}}}}",
        "access_token": access_token
    }

    try:
        print(f"  Querying Meta Graph API for @{target_username}...")
        res = requests.get(url, params=params, timeout=20)
        res_json = res.json()
        
        if "error" in res_json:
            print(f"  Meta API notice: {res_json['error'].get('message')}")
            return []

        media_list = res_json.get("business_discovery", {}).get("media", {}).get("data", [])
        posts = []
        for m in media_list:
            caption = m.get("caption", "")
            if caption:
                posts.append({
                    "source_account": f"@{target_username}",
                    "caption": caption.strip(),
                    "media_url": m.get("media_url", ""),
                    "permalink": m.get("permalink", ""),
                    "timestamp": m.get("timestamp", "")
                })
        print(f"  🎉 Success! Fetched {len(posts)} posts via Meta Graph API.")
        return posts
    except Exception as e:
        print(f"  Meta Graph API check notice: {e}")
        return []


def fetch_via_resilient_rsshub(target_username):
    """Fetches public posts via multiple global public RSSHub fallback instances."""
    instances = [
        "https://rsshub.rssforever.com",
        "https://moeyy.cn/rsshub",
        "https://rsshub.imiku.me",
        "https://rsshub.y1y.me",
        "https://rsshub.app"
    ]
    
    posts = []
    for base_url in instances:
        url = f"{base_url}/instagram/user/{target_username}"
        print(f"  Trying RSSHub instance: {base_url}...")
        try:
            feed = feedparser.parse(url, response_headers={"Referer": "https://google.com"})
            if feed.entries:
                for entry in feed.entries[:8]:
                    caption = entry.get("summary", "") or entry.get("title", "")
                    clean_caption = re.sub(r'<[^>]+>', '', caption).strip()
                    if len(clean_caption) > 20:
                        posts.append({
                            "source_account": f"@{target_username}",
                            "caption": clean_caption,
                            "permalink": entry.get("link", f"https://www.instagram.com/{target_username}/"),
                            "timestamp": str(datetime.date.today())
                        })
                if posts:
                    print(f"  🎉 Success! Fetched {len(posts)} posts from {base_url}")
                    return posts
        except Exception as e:
            continue
    return []


def fetch_all_sources():
    """Orchestrates multi-fallback public post gathering."""
    print("🔍 Monitoring trusted target Instagram pages...")
    os.makedirs("output", exist_ok=True)
    all_posts = []

    for username in TARGET_ACCOUNTS:
        print(f"  Scraping @{username}...")
        
        # 1. Try Official Meta Graph API first
        posts = fetch_via_graph_api(username)
        
        # 2. Try Resilient RSSHub instances if API failed or returned 0
        if not posts:
            posts = fetch_via_resilient_rsshub(username)

        all_posts.extend(posts)

    save_path = "output/raw_ig_digest.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"  Successfully gathered {len(all_posts)} posts from target Instagram profiles!")
    return all_posts


if __name__ == "__main__":
    fetch_all_sources()