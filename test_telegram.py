"""
test_telegram.py
One-time test to confirm your bot token + chat ID actually work together.
Sends a simple confirmation message to your Telegram.

Run: python test_telegram.py
"""

import requests
import config


def send_test_message():
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": "✅ Bot connected! Your news pipeline can reach you here.",
    }

    resp = requests.post(url, data=payload, timeout=15)
    data = resp.json()

    if data.get("ok"):
        print("Success! Check your Telegram — you should see the message.")
    else:
        print("Something went wrong:")
        print(data)


if __name__ == "__main__":
    send_test_message()
