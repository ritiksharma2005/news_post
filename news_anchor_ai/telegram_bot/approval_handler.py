"""
news_anchor_ai/telegram_bot/approval_handler.py
Delivers the rendered 30–45s News Reel to Telegram with interactive
[Approve & Publish Reel] and [Reject] buttons.
Handles Telegram callback actions and coordinates publishing.
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional

from news_anchor_ai.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    BRAND_NAME,
    INSTAGRAM_ACCOUNT
)
from news_anchor_ai.database import mark_post_status, get_post_metadata
from news_anchor_ai.publisher.instagram_reel_publisher import publish_video_reel

def get_telegram_file_url(file_id: str) -> Optional[str]:
    """Gets direct download URL from Telegram CDN."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url, timeout=15).json()
        if resp.get("ok"):
            file_path = resp["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"[Approval Handler] Error retrieving Telegram file URL: {e}")
    return None

def send_reel_for_approval(video_path: Path, post_id: str, metadata: Dict) -> bool:
    """
    Sends the completed 9:16 vertical Reel to Telegram for final human approval.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Approval Handler] Telegram bot credentials missing.")
        return False

    caption_text = (
        f"🎥 *YOUR NEWS REEL IS READY FOR REVIEW!*\n\n"
        f"📌 *Headline*: {metadata.get('headline', '')}\n"
        f"⏱️ *Duration*: {metadata.get('duration', 0):.1f}s\n"
        f"👤 *Anchor*: Masked Anchor ({metadata.get('anchor_type', 'scarf').capitalize()})\n\n"
        f"📝 *Instagram Caption & Tags*:\n{metadata.get('reel_caption', '')[:400]}...\n\n"
        f"Tap below to authorize publishing to {INSTAGRAM_ACCOUNT}:"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve & Publish Reel", "callback_data": f"pub_reel:{post_id}"},
                {"text": "❌ Discard", "callback_data": f"del_reel:{post_id}"}
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    
    try:
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_text,
                "parse_mode": "Markdown",
                "supports_streaming": True,
                "reply_markup": json.dumps(reply_markup)
            }
            resp = requests.post(url, data=data, files=files, timeout=120)
            result = resp.json()

        if not result.get("ok"):
            print(f"[Approval Handler] Failed to send video: {result}")
            return False

        # Extract public Telegram CDN video URL for Instagram Graph API
        public_url = None
        if "result" in result and "video" in result["result"]:
            file_id = result["result"]["video"]["file_id"]
            public_url = get_telegram_file_url(file_id)

        print(f"[Approval Handler] Reel delivered to Telegram! Public URL: {public_url}")

        mark_post_status(post_id, "ready_for_approval", {
            "public_video_url": public_url,
            "reel_caption": metadata.get("reel_caption", ""),
            "headline": metadata.get("headline", ""),
            "video_path": str(video_path)
        })
        return True

    except Exception as e:
        print(f"[Approval Handler] Exception delivering video: {e}")
        return False


def execute_publish_action(post_id: str) -> bool:
    """
    Called when user taps [ ✅ Approve & Publish Reel ] on Telegram.
    Publishes to Instagram and updates post state.
    """
    meta = get_post_metadata(post_id)
    public_url = meta.get("public_video_url")
    caption = meta.get("reel_caption", "")

    if not public_url:
        print(f"[Approval Handler] Error: No public video URL found for {post_id}")
        return False

    success = publish_video_reel(public_url, caption)
    if success:
        mark_post_status(post_id, "published")
    return success
