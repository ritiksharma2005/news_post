"""
get_chat_id.py
Run this ONCE, after you've sent any message to your bot on Telegram,
to find your chat ID. Paste the chat ID it prints into your .env file
as TELEGRAM_CHAT_ID.

Run: python get_chat_id.py
"""

import requests
import config

def get_chat_id():
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    resp = requests.get(url, timeout=15)
    data = resp.json()

    if not data.get("ok"):
        print("Error from Telegram API:", data)
        return

    results = data.get("result", [])
    if not results:
        print("No messages found yet.")
        print("Make sure you've sent a message to your bot on Telegram, then run this again.")
        return

    # Show every unique chat ID found (usually just one — yours)
    seen = set()
    for update in results:
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        name = chat.get("first_name", chat.get("title", "Unknown"))
        text = message.get("text", "")
        if chat_id and chat_id not in seen:
            seen.add(chat_id)
            print(f"Chat ID: {chat_id}  (from: {name}, message: '{text}')")

    print("\nCopy the Chat ID above into your .env file as TELEGRAM_CHAT_ID")


if __name__ == "__main__":
    get_chat_id()
