"""
instagram_digest/fetch_ig_source.py
Monitors trusted target Instagram profiles (e.g. @iit__nit__iiit)
using Pixwox & Picnob public web mirrors to bypass 403 blocks.
"""

import sys
import os

# 🔹 PATH RESOLVER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import re
import datetime
import requests
from bs4 import BeautifulSoup
import config

TARGET_ACCOUNTS = ["iit__nit__iiit"]


def fetch_via_pixwox_and_picnob(target_username):
    """Fetches recent posts from Pixwox & Picnob Instagram mirrors."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    posts = []

    # 1. Primary Mirror: Pixwox
    try:
        url = f"https://www.pixwox.com/profile/{target_username}/"
        print(f"  Fetching public posts for @{target_username} via Pixwox...")
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.find_all("div", class_="item")
            for item in items[:8]:
                txt_div = item.find("div", class_="txt") or item.find("img")
                caption = ""
                if txt_div:
                    caption = txt_div.text if hasattr(txt_div, 'text') else txt_div.get("alt", "")
                
                clean_cap = caption.strip()
                if clean_cap and len(clean_cap) > 20:
                    posts.append({
                        "source_account": f"@{target_username}",
                        "caption": clean_cap,
                        "permalink": f"https://www.instagram.com/{target_username}/",
                        "timestamp": str(datetime.date.today())
                    })
    except Exception as e:
        print(f"  Pixwox notice: {e}")

    # 2. Secondary Mirror: Picnob (if Pixwox returned 0)
    if not posts:
        try:
            url = f"https://www.picnob.com/profile/{target_username}/"
            print(f"  Fetching public posts for @{target_username} via Picnob...")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                sums = soup.find_all("div", class_="sum") or soup.find_all("div", class_="txt")
                for s in sums[:8]:
                    caption = s.text.strip()
                    if caption and len(caption) > 20:
                        posts.append({
                            "source_account": f"@{target_username}",
                            "caption": caption,
                            "permalink": f"https://www.instagram.com/{target_username}/",
                            "timestamp": str(datetime.date.today())
                        })
        except Exception as e:
            print(f"  Picnob notice: {e}")

    return posts


def fetch_via_graph_api(target_username):
    """Uses Meta Graph API Business Discovery if target is a registered Creator account."""
    access_token = getattr(config, "INSTAGRAM_ACCESS_TOKEN", os.getenv("INSTAGRAM_ACCESS_TOKEN", ""))
    ig_user_id = getattr(config, "INSTAGRAM_USER_ID", os.getenv("INSTAGRAM_USER_ID", ""))

    if not access_token or not ig_user_id:
        return []

    url = f"https://graph.facebook.com/v19.0/{ig_user_id}"
    params = {
        "fields": f"business_discovery.username({target_username}){{media{{caption,media_url,timestamp,permalink}}}}",
        "access_token": access_token
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        res_json = res.json()
        media_list = res_json.get("business_discovery", {}).get("media", {}).get("data", [])
        posts = []
        for m in media_list:
            caption = m.get("caption", "")
            if caption:
                posts.append({
                    "source_account": f"@{target_username}",
                    "caption": caption,
                    "media_url": m.get("media_url", ""),
                    "permalink": m.get("permalink", ""),
                    "timestamp": m.get("timestamp", "")
                })
        return posts
    except Exception as e:
        return []


def fetch_all_sources():
    """Fetches candidate posts from target accounts."""
    print("🔍 Monitoring trusted target Instagram pages...")
    os.makedirs("output", exist_ok=True)
    all_posts = []

    for username in TARGET_ACCOUNTS:
        print(f"  Scraping @{username}...")
        
        # 1. Try Graph API first
        posts = fetch_via_graph_api(username)
        
        # 2. Fall back to Pixwox & Picnob mirrors
        if not posts:
            posts = fetch_via_pixwox_and_picnob(username)

        all_posts.extend(posts)

    save_path = "output/raw_ig_digest.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"  Successfully fetched {len(all_posts)} posts from target Instagram profiles!")
    return all_posts


if __name__ == "__main__":
    fetch_all_sources()
    