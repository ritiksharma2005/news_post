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
    """Sends a single detailed text message to Telegram channel/chat."""
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
            print("  ✅ Telegram text news message sent successfully (1 single message).")
            return True
        else:
            print(f"  [Telegram Error] sendMessage failed: {res} (Token length: {len(token)}, Chat ID: {chat_id})")
    except Exception as e:
        print(f"  [Telegram Error] Exception sending message: {e}")
    return False


def broadcast_trend_to_telegram(story: Dict[str, Any], caption_text: str, dry_run: bool = False) -> bool:
    """Master broadcast wrapper sending a single text-only news story with full details to Telegram."""
    headline = story.get("headline", story.get("title", ""))
    
    print(f"\n📤 Sending detailed news update to Telegram: '{headline[:60]}...'")
    if dry_run:
        print("  🔒 [DRY RUN ACTIVE] Telegram broadcast skipped for preview.")
        print(f"  News Message Draft:\n{caption_text}")
        return True
        
    return send_telegram_message(caption_text)
