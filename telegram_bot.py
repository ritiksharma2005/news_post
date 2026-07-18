"""
telegram_bot.py
Sends a finished poster (image) + its caption/hashtags to your Telegram,
one story at a time, so you can review and post manually.

Run directly to test: python telegram_bot.py
"""

import requests

import config


TELEGRAM_CAPTION_LIMIT = 1024  # Telegram's hard limit for photo captions


def send_photo(image_path, caption=""):
    """
    Send a single photo with a caption to your Telegram chat.
    If the caption is too long for Telegram's limit, send the photo with a
    short caption and follow up with the full caption as a separate message.
    """
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"

    short_enough = len(caption) <= TELEGRAM_CAPTION_LIMIT
    photo_caption = caption if short_enough else caption[:100] + "... (full caption below)"

    with open(image_path, "rb") as photo_file:
        files = {"photo": photo_file}
        data = {"chat_id": config.TELEGRAM_CHAT_ID, "caption": photo_caption}
        resp = requests.post(url, data=data, files=files, timeout=30)

    result = resp.json()
    if not result.get("ok"):
        print(f"  Failed to send photo: {result}")
        return False

    if not short_enough:
        send_message(caption)

    return True


def send_message(text):
    """Send a plain text message to your Telegram chat."""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": text}
    resp = requests.post(url, data=payload, timeout=15)
    result = resp.json()
    if not result.get("ok"):
        print(f"  Failed to send message: {result}")
        return False
    return True


def send_story(story):
    """
    Send one fully-processed story to Telegram: the poster card image,
    followed by its caption + hashtags.
    story must have: card_path, caption, hashtags (list)
    """
    caption_text = story.get("caption", "")
    hashtags = story.get("hashtags", [])
    if hashtags:
        caption_text += "\n\n" + " ".join(hashtags)

    card_path = story.get("card_path")
    if not card_path:
        print("  No card_path found for this story, skipping.")
        return False

    print(f"  Sending: {story.get('new_headline', story.get('title', ''))[:60]}...")
    return send_photo(card_path, caption_text)


def send_all(stories):
    """Send a list of fully-processed stories to Telegram, one by one."""
    print(f"Sending {len(stories)} stories to Telegram...")
    sent = 0
    for story in stories:
        if send_story(story):
            sent += 1
    print(f"Done. Sent {sent}/{len(stories)} stories successfully.")
    return sent


if __name__ == "__main__":
    # Simple connectivity test — sends a plain text message
    success = send_message("✅ telegram_bot.py test — if you see this, sending works.")
    print("Test message sent!" if success else "Test failed — check your bot token/chat ID.")
