"""
instagram_publisher.py
Publishes poster cards + captions to Instagram via Meta Graph API.
"""

import os
import time
import requests
from typing import Optional
import config


def resolve_instagram_user_id(token: str, user_id: str) -> str:
    """
    If user_id is a Facebook Page ID instead of an Instagram Business Account ID (178414...),
    queries Meta Graph API to auto-resolve the connected instagram_business_account.id.
    """
    if not user_id or not token:
        return user_id
        
    if user_id.startswith("178414"):
        return user_id
        
    try:
        url = f"https://graph.facebook.com/v19.0/{user_id}?fields=instagram_business_account&access_token={token}"
        resp = requests.get(url, timeout=10).json()
        if "instagram_business_account" in resp and "id" in resp["instagram_business_account"]:
            ig_id = resp["instagram_business_account"]["id"]
            print(f"  💡 Auto-resolved Instagram Business Account ID: {ig_id} from Page object {user_id}", flush=True)
            return ig_id
            
        accounts_url = f"https://graph.facebook.com/v19.0/me/accounts?fields=instagram_business_account&access_token={token}"
        acc_resp = requests.get(accounts_url, timeout=10).json()
        if "data" in acc_resp:
            for item in acc_resp["data"]:
                if "instagram_business_account" in item and "id" in item["instagram_business_account"]:
                    ig_id = item["instagram_business_account"]["id"]
                    print(f"  💡 Auto-resolved Instagram Business Account ID from me/accounts: {ig_id}", flush=True)
                    return ig_id
    except Exception as e:
        print(f"  [IG ID Resolve Notice] {e}", flush=True)
        
    return user_id


def publish_photo(image_url, caption=""):
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN") or getattr(config, "INSTAGRAM_ACCESS_TOKEN", "")
    raw_user_id = os.getenv("INSTAGRAM_USER_ID") or getattr(config, "INSTAGRAM_USER_ID", "")

    if not token or not raw_user_id:
        print("  ⚠️ Skipping Instagram: INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID missing in config/secrets.", flush=True)
        return False

    user_id = resolve_instagram_user_id(token, raw_user_id)
    base_url = f"https://graph.facebook.com/v19.0/{user_id}"

    try:
        print(f"  Creating Instagram media container for ID {user_id}...", flush=True)
        container_url = f"{base_url}/media"
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": token
        }

        resp = requests.post(container_url, data=payload, timeout=30)
        result = resp.json()

        if "id" not in result:
            print(f"  ❌ Instagram container creation failed: {result}", flush=True)
            return False

        creation_id = result["id"]
        print(f"  Container created! ID: {creation_id}. Waiting for Meta to fetch image...", flush=True)

        time.sleep(5)

        publish_url = f"{base_url}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": token
        }

        pub_resp = requests.post(publish_url, data=publish_payload, timeout=30)
        pub_result = pub_resp.json()

        if "id" in pub_result:
            print(f"  🎉 Published successfully to Instagram! Post ID: {pub_result['id']}", flush=True)
            return True
        else:
            print(f"  ❌ Failed to publish to Instagram: {pub_result}", flush=True)
            return False

    except Exception as e:
        print(f"  ❌ Exception during Instagram publish: {e}", flush=True)
        return False


def upload_to_catbox(file_path: str) -> Optional[str]:
    """Uploads a local image poster to Catbox.moe to obtain a public HTTP image URL for Meta Graph API."""
    try:
        url = "https://catbox.moe/user/api.php"
        with open(file_path, "rb") as f:
            resp = requests.post(url, data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=25)
            if resp.status_code == 200 and resp.text.startswith("http"):
                pub_url = resp.text.strip()
                print(f"  ✅ Uploaded poster to public host: {pub_url}", flush=True)
                return pub_url
    except Exception as e:
        print(f"  [Catbox Upload Error] {e}", flush=True)
    return None


def publish_story(story):
    image_url = story.get("public_image_url")
    card_path = story.get("card_path")
    
    if not image_url and card_path and os.path.exists(card_path):
        image_url = upload_to_catbox(card_path)
        if image_url:
            story["public_image_url"] = image_url

    if not image_url:
        print("  ⚠️ No public_image_url or valid local card_path found for story. Skipping Instagram publish.", flush=True)
        return False

    caption_text = story.get("caption", "")
    hashtags = story.get("hashtags", [])
    if hashtags:
        caption_text += "\n\n" + " ".join(hashtags)

    headline = story.get("new_headline", story.get("headline", story.get("title", "")))[:60]
    print(f"  Publishing to IG: {headline}...", flush=True)
    return publish_photo(image_url, caption_text)


def publish_all(stories):
    try:
        print(f"\nPublishing {len(stories)} stories to Instagram...", flush=True)
        published = 0
        for story in stories:
            if publish_story(story):
                published += 1
        print(f"Done. Published {published}/{len(stories)} stories to Instagram.", flush=True)
        return published
    except Exception as e:
        print(f"❌ Error in publish_all: {e}", flush=True)
        return 0
            
