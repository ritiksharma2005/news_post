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


def get_clean_bot_token() -> str:
    token = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN") or ""
    token = token.strip()
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        token = token[1:-1].strip()
    if token.lower().startswith("bot") and ":" in token:
        token = token[3:].strip()
    return token


def get_clean_chat_id() -> str:
    chat_id = TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID") or ""
    chat_id = chat_id.strip()
    if (chat_id.startswith('"') and chat_id.endswith('"')) or (chat_id.startswith("'") and chat_id.endswith("'")):
        chat_id = chat_id[1:-1].strip()
    return chat_id


def send_telegram_message(text: str) -> bool:
    """Sends a plain text message to Telegram channel/chat."""
    token = get_clean_bot_token()
    chat_id = get_clean_chat_id()
    
    if not token or not chat_id:
        print("  [Telegram Notifier] Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing or empty in secrets.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        resp = requests.post(url, data=payload, timeout=20)
        res = resp.json()
        if res.get("ok"):
            print("  ✅ Telegram text message sent successfully.")
            return True
        else:
            print(f"  [Telegram Error] sendMessage failed: {res} (Token length: {len(token)}, Chat ID: {chat_id})")
    except Exception as e:
        print(f"  [Telegram Error] Exception sending message: {e}")
    return False


def send_telegram_photo(image_path: str, caption: str = "") -> bool:
    """Sends a photo with caption to Telegram channel/chat."""
    token = get_clean_bot_token()
    chat_id = get_clean_chat_id()
    
    if not token or not chat_id:
        print("  [Telegram Notifier] Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing or empty in secrets.")
        return False
        
    if not image_path or not os.path.exists(image_path):
        return send_telegram_message(caption)
        
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    short_enough = len(caption) <= TELEGRAM_CAPTION_LIMIT
    photo_caption = caption if short_enough else caption[:980] + "\n\n...(full details below)"
    
    try:
        with open(image_path, "rb") as photo_file:
            files = {"photo": photo_file}
            data = {"chat_id": chat_id, "caption": photo_caption}
            resp = requests.post(url, data=data, files=files, timeout=35)
            res = resp.json()
            if res.get("ok"):
                print("  ✅ Telegram photo & caption sent successfully.")
                if not short_enough:
                    send_telegram_message(caption)
                return True
            else:
                print(f"  [Telegram Notice] sendPhoto failed: {res}. Falling back to text message...")
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
