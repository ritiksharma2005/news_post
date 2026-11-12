"""
news_anchor_ai/telegram_bot/candidate_notifier.py
Sends the latest 3–4 candidate posts to Telegram with interactive inline buttons
so the user can tap which post to convert into an Instagram Reel.
"""

import json
import requests
from news_anchor_ai.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BRAND_NAME
from news_anchor_ai.extractor.instagram_fetcher import fetch_latest_posts
from news_anchor_ai.database import mark_post_status

def notify_candidates_on_telegram():
    """
    Checks for fresh published posts on @news.nit_iit and sends
    an interactive selection menu to the user's Telegram.
    """
    print(f"[Candidate Notifier] Initiating candidate check for {BRAND_NAME}...")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Candidate Notifier] ⚠️ Error: Telegram token or Chat ID missing.")
        return

    candidates = fetch_latest_posts(limit=15)
    if not candidates:
        print("[Candidate Notifier] ℹ️ No fresh candidate posts found (or all recent posts already processed).")
        return

    print(f"[Candidate Notifier] Preparing Telegram message with {len(candidates)} candidate options...")

    # Build the Telegram message
    message_lines = [
        f"📺 *{BRAND_NAME} — SELECT POST FOR VIDEO REEL*\n",
        "Found fresh updates from @news.nit_iit. Which one would you like to turn into a 30–45s News Reel?\n"
    ]

    inline_keyboard = []

    for idx, c in enumerate(candidates, 1):
        message_lines.append(f"*{idx}️⃣ {c['formatted_date']}*\n📌 {c['headline']}\n🔗 [View Original Post]({c['permalink']})\n")
        inline_keyboard.append([{
            "text": f"🎬 Generate Reel #{idx}",
            "callback_data": f"make_reel:{c['media_id']}"
        }])

    # Add skip button
    inline_keyboard.append([{"text": "⏭️ Skip For Now", "callback_data": "skip_all"}])

    full_text = "\n".join(message_lines)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)
        data = resp.json()
        if data.get("ok"):
            print(f"[Candidate Notifier] Successfully sent {len(candidates)} candidates to Telegram.")
            for c in candidates:
                mark_post_status(c["media_id"], "candidate_sent", {
                    "headline": c["headline"],
                    "permalink": c["permalink"],
                    "image_path": c["image_path"],
                    "caption": c["caption"]
                })
        else:
            print(f"[Candidate Notifier] Telegram send error: {data}")
    except Exception as e:
        print(f"[Candidate Notifier] Failed to notify Telegram: {e}")

if __name__ == "__main__":
    notify_candidates_on_telegram()
