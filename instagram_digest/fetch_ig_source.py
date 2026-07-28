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


def fetch_via_rapidapi(target_username):
    """Fetches latest posts using APIDojo Instagram Scraper on RapidAPI."""
    rapidapi_key = getattr(config, "RAPIDAPI_KEY", os.getenv("RAPIDAPI_KEY", ""))

    if not rapidapi_key:
        print("  ⚠️ RAPIDAPI_KEY is missing. Check your local .env or GitHub Secrets.")
        return []

    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/user_posts"
    querystring = {"username_or_id_or_url": target_username}
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"
    }

    try:
        print(f"  Querying RapidAPI for @{target_username} posts...")
        response = requests.get(url, headers=headers, params=querystring, timeout=20)
        
        if response.status_code != 200:
            print(f"  RapidAPI returned status code: {response.status_code} ({response.text})")
            return []

        res_json = response.json()
        items = res_json.get("data", {}).get("items", [])
        posts = []
        
        for item in items[:6]:
            caption_text = item.get("caption", {}).get("text", "")
            
            # Extract highest quality image version
            image_items = item.get("image_versions", {}).get("items", [])
            media_url = image_items[0].get("url") if image_items else None
            
            # Shortcode link
            shortcode = item.get("code")
            permalink = f"https://www.instagram.com/p/{shortcode}/" if shortcode else f"https://www.instagram.com/{target_username}/"
            
            # Timestamp conversion
            taken_at = item.get("taken_at")
            timestamp = str(datetime.date.fromtimestamp(taken_at)) if taken_at else str(datetime.date.today())

            if caption_text:
                posts.append({
                    "source_account": f"@{target_username}",
                    "caption": caption_text.strip(),
                    "media_url": media_url,
                    "permalink": permalink,
                    "timestamp": timestamp
                })
                
        print(f"  🎉 Success! Fetched {len(posts)} posts via RapidAPI.")
        return posts
    except Exception as e:
        print(f"  RapidAPI check notice: {e}")
        return []


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
    