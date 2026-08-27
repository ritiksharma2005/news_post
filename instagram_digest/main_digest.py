"""
instagram_digest/main_digest.py
Main Runner for Campus Digest Workflow:
1. Fetch latest posts from target accounts (@iit__nit__iiit)
2. AI selects the best post and rewrites it
3. Downloads the original post photo
4. Generates branded 1080x1080 Campus Digest poster
5. Publishes to Telegram & Instagram (Skipped in Dry Run mode)
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


def run_digest_pipeline(dry_run=False):
    print("=" * 50)
    print("🎓 STEP 1: Scraping target Instagram profiles...")
    print("=" * 50)
    fetch_ig_source.fetch_all_sources()

    print("\n" + "=" * 50)
    print("🎓 STEP 2: AI Selection & Rewriting...")
    print("=" * 50)
    digest_items = rewrite_digest.rewrite_latest_digest()

    if not digest_items:
        print("  No new digest stories generated.")
        return

    # Load raw posts to get source image URLs
    raw_path = "output/raw_ig_digest.json"
    raw_posts = []
    if os.path.exists(raw_path):
        try:
            with open(raw_path, "r", encoding="utf-8") as f:
                raw_posts = json.load(f)
        except Exception as e:
            print(f"  Error loading raw IG posts: {e}")

    for idx, item in enumerate(digest_items):
        print(f"\n🧠 Processing Digest Item {idx+1}/{len(digest_items)}...")
        
        # Download source image matching selected shortcode
        source_image_local = None
        shortcode = item.get("selected_shortcode")
        if shortcode and raw_posts:
            matching_posts = [p for p in raw_posts if p.get("shortcode") == shortcode]
            if matching_posts:
                media_url = matching_posts[0].get("media_url")
                if media_url:
                    print(f"📥 Downloading original post photo for '{shortcode}'...")
                    source_image_local = download_source_image(media_url, f"output/images/digest_source_{idx}.jpg")
        
        # Determine output paths
        card_path = f"output/cards/digest_today_{idx}.png"
        
        print(f"🎨 Rendering Campus Digest Card {idx+1}...")
        card_path = design_digest_post.create_digest_card(
            headline=item.get("headline", ""),
            summary=item.get("summary", ""),
            image_path=source_image_local,
            output_path=card_path
        )

        caption_text = (
            f"{item.get('headline')}\n\n"
            f"{item.get('summary')}\n\n"
            f"📲 Join our Instagram Community (Link in Bio): https://www.instagram.com/channel/AbYg9NWAeNaKS8gf/\n\n"
            f"#IIT #NIT #CampusNews #Engineering #Placements #news_nit_iit"
        )

        story_obj = {
            "card_path": card_path,
            "caption": caption_text,
            "hashtags": []
        }

        if dry_run:
            print(f"🔒 [DRY RUN ACTIVE] Card generated at: {card_path}")
            print(f"Caption draft:\n{caption_text}")
            continue

        # Real publish
        print(f"🎓 Sending Digest {idx+1} to Telegram...")
        telegram_bot.send_story(story_obj)

        print(f"🎓 Publishing Digest {idx+1} to Instagram...")
        if ENABLE_INSTAGRAM_POSTING:
            instagram_publisher.publish_story(story_obj)
        else:
            print("🔒 [DRY RUN ACTIVE] Instagram publishing paused.")

        # Record shortcode to history
        if shortcode:
            try:
                from workflow.history_manager import add_published_insta
                add_published_insta(shortcode)
                print(f"  [History] Recorded post code '{shortcode}' to database/local history.")
            except Exception as e:
                print(f"  [History] Error recording post code: {e}")

    print("\n" + "=" * 50)
    print("🎓 CAMPUS DIGEST PIPELINE COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    run_digest_pipeline(dry_run)