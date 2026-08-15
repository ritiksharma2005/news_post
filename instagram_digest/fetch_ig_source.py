"""
instagram_digest/fetch_ig_source.py
Monitors trusted target Instagram profiles (e.g. @iit__nit__iiit)
using RapidAPI APIDojo Instagram Scraper for 100% reliability.
"""

import sys
import os
import datetime

# 🔹 PATH RESOLVER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import requests
import config

TARGET_ACCOUNTS = ["iit__nit__iiit"]


from scrapers.instagram_scraper import fetch_instagram_posts

def fetch_via_rapidapi(target_username):
    """Fetches latest posts using the unified scraper parsing logic."""
    raw_posts = fetch_instagram_posts(target_username, limit=5)
    posts = []
    
    for p in raw_posts:
        caption = p.get("caption", "").strip()
        if caption:
            shortcode = p.get("code")
            permalink = f"https://www.instagram.com/p/{shortcode}/" if shortcode else f"https://www.instagram.com/{target_username}/"
            posts.append({
                "source_account": f"@{target_username}",
                "caption": caption,
                "media_url": p.get("image_url"),
                "permalink": permalink,
                "timestamp": p.get("date") or str(datetime.date.today()),
                "shortcode": shortcode
            })
            
    print(f"  🎉 Success! Fetched {len(posts)} posts via RapidAPI.")
    return posts


def fetch_all_sources():
    """Orchestrates public post gathering."""
    print("🔍 Monitoring trusted target Instagram pages via RapidAPI...")
    os.makedirs("output", exist_ok=True)
    all_posts = []

    for username in TARGET_ACCOUNTS:
        print(f"  Scraping @{username}...")
        posts = fetch_via_rapidapi(username)
        all_posts.extend(posts)

    save_path = "output/raw_ig_digest.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"  Successfully gathered {len(all_posts)} posts from target Instagram profiles!")
    return all_posts


if __name__ == "__main__":
    fetch_all_sources()
    