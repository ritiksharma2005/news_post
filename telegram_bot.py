import requests
import config

TELEGRAM_CAPTION_LIMIT = 1024


def get_telegram_file_url(file_id):
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url, timeout=15).json()
        if resp.get("ok"):
            file_path = resp["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{config.TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"  Error fetching Telegram file URL: {e}", flush=True)
    return None


def send_photo(image_path, caption=""):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
    short_enough = len(caption) <= TELEGRAM_CAPTION_LIMIT
    photo_caption = caption if short_enough else caption[:100] + "... (full caption below)"

    with open(image_path, "rb") as photo_file:
        files = {"photo": photo_file}
        data = {"chat_id": config.TELEGRAM_CHAT_ID, "caption": photo_caption}
        resp = requests.post(url, data=data, files=files, timeout=30)

    result = resp.json()
    if not result.get("ok"):
        print(f"  Failed to send photo: {result}", flush=True)
        return False, None

    public_url = None
    if "result" in result and "photo" in result["result"]:
        highest_res_photo = result["result"]["photo"][-1]
        file_id = highest_res_photo["file_id"]
        public_url = get_telegram_file_url(file_id)

    if not short_enough:
        send_message(caption)

    return True, public_url


def send_message(text):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": text}
    resp = requests.post(url, data=payload, timeout=15)
    result = resp.json()
    if not result.get("ok"):
        print(f"  Failed to send message: {result}", flush=True)
        return False
    return True


def send_story(story):
    caption_text = story.get("caption", "")
    hashtags = story.get("hashtags", [])
    if hashtags:
        caption_text += "\n\n" + " ".join(hashtags)

    card_path = story.get("card_path")
    if not card_path:
        print("  No card_path found for this story, skipping.", flush=True)
        return False

    print(f"  Sending to Telegram: {story.get('new_headline', story.get('title', ''))[:60]}...", flush=True)
    success, public_url = send_photo(card_path, caption_text)

    if success and public_url:
        story["public_image_url"] = public_url

    return success


def send_all(stories):
    print(f"Sending {len(stories)} stories to Telegram...", flush=True)
    sent = 0
    for story in stories:
        if send_story(story):
            sent += 1
    print(f"Done. Sent {sent}/{len(stories)} stories to Telegram.", flush=True)
    return sent
