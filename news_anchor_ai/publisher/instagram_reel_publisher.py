"""
news_anchor_ai/publisher/instagram_reel_publisher.py
Official Meta Instagram Graph API publisher for Instagram Reels (video/mp4).
Follows Meta's official 2-step async container & publish workflow.
"""

import time
import requests
from pathlib import Path
from news_anchor_ai.config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_USER_ID,
    INSTAGRAM_ACCOUNT
)

GRAPH_API_VERSION = "v19.0"

def publish_video_reel(video_url: str, caption: str) -> bool:
    """
    Publishes a vertical video as an Instagram Reel to @news.nit_iit.
    Requires a publicly accessible video_url (e.g. from Telegram or cloud storage).
    """
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_USER_ID:
        print("[Reel Publisher] Error: INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID not configured.")
        return False

    print(f"[Reel Publisher] Initiating Reel container for {INSTAGRAM_ACCOUNT}...")

    # Step 1: Create media container for REELS
    container_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_USER_ID}/media"
    container_payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": True,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    try:
        resp = requests.post(container_url, data=container_payload, timeout=30)
        data = resp.json()
    except Exception as e:
        print(f"[Reel Publisher] Error creating media container: {e}")
        return False

    creation_id = data.get("id")
    if not creation_id:
        print(f"[Reel Publisher] Failed to create container: {data}")
        return False

    print(f"[Reel Publisher] Container created: {creation_id}. Waiting for Meta video processing...")

    # Step 2: Poll container status until FINISHED
    status_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{creation_id}"
    status_params = {
        "fields": "status_code",
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    max_retries = 15
    for attempt in range(max_retries):
        time.sleep(6)
        try:
            status_resp = requests.get(status_url, params=status_params, timeout=15).json()
            code = status_resp.get("status_code")
            print(f"  Container status check {attempt + 1}/{max_retries}: {code}")
            if code == "FINISHED":
                break
            elif code in ["ERROR", "EXPIRED"]:
                print(f"[Reel Publisher] Video processing failed on Meta servers: {status_resp}")
                return False
        except Exception as e:
            print(f"  Status query warning: {e}")

    # Step 3: Publish the container
    publish_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_USER_ID}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }

    try:
        pub_resp = requests.post(publish_url, data=publish_payload, timeout=30).json()
        if "id" in pub_resp:
            print(f"[Reel Publisher] 🚀 SUCCESS! Reel published live with ID: {pub_resp['id']}")
            return True
        else:
            print(f"[Reel Publisher] Publish error: {pub_resp}")
            return False
    except Exception as e:
        print(f"[Reel Publisher] Publish request failed: {e}")
        return False
