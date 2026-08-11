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
    """Fetches latest posts using thetechguy32744's Instagram Scraper Stable API on RapidAPI."""
    rapidapi_key = getattr(config, "RAPIDAPI_KEY", os.getenv("RAPIDAPI_KEY", ""))

    if not rapidapi_key:
        print("  ⚠️ RAPIDAPI_KEY is missing. Check your local .env or GitHub Secrets.")
        return []

    url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_posts.php"
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "username_or_url": target_username,
        "amount": "12",
        "pagination_token": ""
    }

    try:
        print(f"  Querying RapidAPI for @{target_username} posts...")
        response = requests.post(url, headers=headers, data=payload, timeout=20)
        
        if response.status_code != 200:
            print(f"  RapidAPI returned status code: {response.status_code} ({response.text})")
            return []

        res_json = response.json()
        items = res_json.get("posts", [])
        posts = []
        
        for item in items[:6]:
            node = item.get("node", item) if isinstance(item, dict) else {}
            
            # Extract caption
            caption_text = ""
            caption_obj = node.get("caption") or {}
            if isinstance(caption_obj, dict):
                caption_text = caption_obj.get("text", "")
            elif isinstance(caption_obj, str):
                caption_text = caption_obj
                
            if not caption_text and isinstance(node.get("edge_media_to_caption"), dict):
                edges = node["edge_media_to_caption"].get("edges", [])
                if edges and isinstance(edges[0], dict):
                    caption_text = edges[0].get("node", {}).get("text", "")

            # Extract highest quality image version
            media_url = node.get("display_url") or node.get("image")
            if not media_url and isinstance(node.get("image_versions2"), dict):
                candidates = node["image_versions2"].get("candidates", [])
                if candidates:
                    media_url = candidates[0].get("url")
            
            # Shortcode link
            shortcode = node.get("code")
            permalink = f"https://www.instagram.com/p/{shortcode}/" if shortcode else f"https://www.instagram.com/{target_username}/"
            
            # Timestamp conversion
            taken_at = node.get("taken_at")
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
    