"""
social_trends/telegram_notifier.py
Telegram Broadcaster for India Social Trends
Sends raw source photos with text summary captions or text messages directly to Telegram.
"""

import os
import requests
from typing import Dict, Any, Tuple
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_CAPTION_LIMIT = 1024


def send_telegram_message(text: str) -> bool:
    """Sends a plain text message to Telegram channel/chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [Telegram Notifier] Notice: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        resp = requests.post(url, data=payload, timeout=20)
        res = resp.json()
        if res.get("ok"):
            return True
        else:
            print(f"  [Telegram Error] sendMessage failed: {res}")
    except Exception as e:
        print(f"  [Telegram Error] Exception sending message: {e}")
    return False


def send_telegram_photo(image_path: str, caption: str = "") -> bool:
    """Sends a photo with caption to Telegram channel/chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  [Telegram Notifier] Notice: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return False
        
    if not image_path or not os.path.exists(image_path):
        return send_telegram_message(caption)
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    short_enough = len(caption) <= TELEGRAM_CAPTION_LIMIT
    photo_caption = caption if short_enough else caption[:980] + "\n\n...(full details below)"
    
    try:
        with open(image_path, "rb") as photo_file:
            files = {"photo": photo_file}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": photo_caption}
            resp = requests.post(url, data=data, files=files, timeout=35)
            res = resp.json()
            if res.get("ok"):
                if not short_enough:
                    send_telegram_message(caption)
                return True
            else:
                print(f"  [Telegram Notice] sendPhoto response: {res}. Falling back to text message...")
                return send_telegram_message(caption)
    except Exception as e:
        print(f"  [Telegram Notice] sendPhoto exception: {e}. Falling back to text message...")
        return send_telegram_message(caption)


def broadcast_trend_to_telegram(story: Dict[str, Any], caption_text: str, dry_run: bool = False) -> bool:
    """Master broadcast wrapper sending trend photo/text to Telegram."""
    image_path = story.get("image_path")
    headline = story.get("headline", story.get("title", ""))
    
    print(f"\n📤 Sending trend to Telegram: '{headline[:60]}...'")
    if dry_run:
        print("  🔒 [DRY RUN ACTIVE] Telegram broadcast skipped for preview.")
        print(f"  Image Path: {image_path}")
        print(f"  Caption Draft:\n{caption_text}")
        return True
        
    if image_path and os.path.exists(image_path):
        return send_telegram_photo(image_path, caption_text)
    else:
        return send_telegram_message(caption_text)
