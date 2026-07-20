import os
import time
import requests
import config


def publish_photo(image_url, caption=""):
    token = getattr(config, "INSTAGRAM_ACCESS_TOKEN", os.getenv("EAAWH0f4vts8BSEEJCqfJRChHAFmZBTkJJ65m8aGTL3eqtNqkEU5yykIaDAQry8O7dopDHp4ETXoKrpCX3eFI3rZBXkKMJPChqgxseCs0XmOCjbIZCaqmfeTF5GLhe4MRvNtCBp5ib83sYOXrHLHfcHvIZBBamXUWB4fz4RdAYf4Y4jJsnbNVZArERFTCI", ""))
    user_id = getattr(config, "INSTAGRAM_USER_ID", os.getenv("1237139552813418", ""))

    if not token or not user_id:
        print("  ⚠️ Skipping Instagram: INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID missing in config/secrets.", flush=True)
        return False

    base_url = f"https://graph.facebook.com/v19.0/{user_id}"

    try:
        print("  Creating Instagram media container...", flush=True)
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


def publish_story(story):
    image_url = story.get("public_image_url")
    if not image_url:
        print("  ⚠️ No public_image_url found for story. Skipping Instagram publish.", flush=True)
        return False

    caption_text = story.get("caption", "")
    hashtags = story.get("hashtags", [])
    if hashtags:
        caption_text += "\n\n" + " ".join(hashtags)

    headline = story.get("new_headline", story.get("title", ""))[:60]
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
