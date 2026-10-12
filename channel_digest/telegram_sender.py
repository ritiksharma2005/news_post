"""
channel_digest/telegram_sender.py
Delivers prepared daily news roundups to Telegram for review and one-tap copying.
Uses Telegram Bot API with link preview suppression for clean, readable layout.
"""

import time
import requests
from typing import List
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(
    text: str,
    disable_web_page_preview: bool = True
) -> bool:
    """
    Sends a single text message to the configured Telegram chat.
    Returns True if successfully received by Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️ Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=20)
        result = resp.json()
        if result.get("ok"):
            return True
        else:
            print(f"  ❌ Telegram API error: {result.get('description', result)}")
            return False
    except Exception as e:
        print(f"  ❌ Telegram connection error: {e}")
        return False


def send_roundup_to_telegram(
    roundup_messages: List[str],
    roundup_date: str,
    post_count: int,
    dry_run: bool = False
) -> bool:
    """
    Sends notification header followed by the ready-to-copy daily roundup messages to Telegram.
    """
    print("\n" + "=" * 60)
    print(f"📤 SENDING DAILY ROUNDUP TO TELEGRAM ({roundup_date} IST)")
    print("=" * 60)
    
    if dry_run:
        print("  🔒 [DRY RUN ACTIVE] Telegram delivery skipped. Message preview:\n")
        for idx, msg in enumerate(roundup_messages, 1):
            print(f"--- [Message Part {idx}/{len(roundup_messages)}] ---")
            print(msg)
            print("-" * 50)
        return True
        
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured. Skipping delivery.")
        return False
        
    # 1. Send review header notification
    header_note = (
        "📢 [DAILY INSTAGRAM BROADCAST DIGEST READY]\n"
        f"📅 Date: {roundup_date} (IST)\n"
        f"📊 Posts Included: {post_count}\n\n"
        "👇 Copy the message below and paste directly into your Instagram Broadcast Channel:"
    )
    send_telegram_message(header_note, disable_web_page_preview=True)
    time.sleep(1)
    
    # 2. Send ready-to-copy roundup parts
    all_sent = True
    for idx, msg in enumerate(roundup_messages, 1):
        print(f"  Sending part {idx}/{len(roundup_messages)} to Telegram...")
        success = send_telegram_message(msg, disable_web_page_preview=True)
        if not success:
            all_sent = False
        time.sleep(1)
        
    if all_sent:
        print(f"  🎉 Daily roundup successfully delivered to Telegram!")
    else:
        print(f"  ⚠️ One or more messages failed during Telegram delivery.")
        
    return all_sent
