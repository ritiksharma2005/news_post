"""
instagram_digest/main_digest.py
Main Runner for Campus Digest Workflow:
1. Fetch latest posts from target accounts (@iit__nit__iiit)
2. AI selects the best post and rewrites it
3. Downloads the original post photo
4. Generates branded 1080x1080 Campus Digest poster
5. Publishes to Telegram & Instagram
"""

import sys
import os
import requests
import json

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fetch_ig_source
import rewrite_digest
import design_digest_post
import telegram_bot
import instagram_publisher

ENABLE_INSTAGRAM_POSTING = True


def download_source_image(media_url, output_path):
    """Downloads the original image from the source Instagram post."""
    if not media_url:
        return None
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        res = requests.get(media_url, timeout=15)
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(res.content)
            print(f"  Downloaded source image successfully: {output_path}")
            return output_path
    except Exception as e:
        print(f"  Image download notice: {e}")
    return None


def run_digest_pipeline():
    print("=" * 50)
    print("🎓 STEP 1: Scraping target Instagram profiles...")
    print("=" * 50)
    fetch_ig_source.fetch_all_sources()

    print("\n" + "=" * 50)
    print("🎓 STEP 2: AI Selection & Rewriting...")
    print("=" * 50)
    digest_data = rewrite_digest.rewrite_latest_digest()

    if not digest_data:
        print("  No new digest story generated.")
        return

    # Retrieve source image URL from raw database
    raw_path = "output/raw_ig_digest.json"
    source_image_local = None
    
    if os.path.exists(raw_path):
        try:
            with open(raw_path, "r", encoding="utf-8") as f:
                raw_posts = json.load(f)
            
            selected_idx = digest_data.get("selected_index", 1) - 1
            if 0 <= selected_idx < len(raw_posts):
                selected_raw_post = raw_posts[selected_idx]
                media_url = selected_raw_post.get("media_url")
                if media_url:
                    print(f"\n📥 Downloading original post photo from source...")
                    source_image_local = download_source_image(media_url, "output/images/digest_source.jpg")
        except Exception as e:
            print(f"  Could not load source image: {e}")

    print("\n" + "=" * 50)
    print("🎓 STEP 3: Rendering Campus Digest Poster...")
    print("=" * 50)
    card_path = design_digest_post.create_digest_card(
        headline=digest_data.get("headline", ""),
        bullets=digest_data.get("bullets", []),
        why_it_matters=digest_data.get("why_it_matters", ""),
        image_path=source_image_local,
        output_path="output/cards/digest_today.png"
    )

    caption_text = (
        f"{digest_data.get('headline')}\n\n"
        + "\n".join(digest_data.get("bullets", [])) + "\n\n"
        f"💡 Why it matters:\n{digest_data.get('why_it_matters')}\n\n"
        f"📲 Join @news.nit_iit on Telegram for daily campus alerts!\n\n"
        f"#IIT #NIT #CampusNews #Engineering #Placements #news_nit_iit"
    )

    story_obj = {
        "card_path": card_path,
        "caption": caption_text,
        "hashtags": []
    }

    print("\n" + "=" * 50)
    print("🎓 STEP 4: Sending Digest to Telegram")
    print("=" * 50)
    telegram_bot.send_story(story_obj)

    print("\n" + "=" * 50)
    print("🎓 STEP 5: Publishing Digest to Instagram")
    print("=" * 50)
    if ENABLE_INSTAGRAM_POSTING:
        instagram_publisher.publish_story(story_obj)
    else:
        print("🔒 [DRY RUN ACTIVE] Instagram publishing paused.")

    print("\n" + "=" * 50)
    print("🎓 CAMPUS DIGEST PIPELINE COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    run_digest_pipeline()
    