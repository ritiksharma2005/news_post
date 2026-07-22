"""
instagram_digest/main_digest.py
Main Runner for Campus Digest Workflow:
1. Fetch latest posts from target accounts (@iit__nit__iiit)
2. AI rewrites headline, bullet points, & caption
3. Generate branded Campus Digest poster
4. Send to Telegram & Publish to Instagram
"""

import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fetch_ig_source
import rewrite_digest
import design_digest_post
import telegram_bot
import instagram_publisher

ENABLE_INSTAGRAM_POSTING = True


def run_digest_pipeline():
    print("=" * 50)
    print("🎓 STEP 1: Scraping target Instagram profiles...")
    print("=" * 50)
    fetch_ig_source.fetch_all_sources()

    print("\n" + "=" * 50)
    print("🎓 STEP 2: AI Rewriting Campus Digest...")
    print("=" * 50)
    digest_data = rewrite_digest.rewrite_latest_digest()

    if not digest_data:
        print("  No new digest story generated.")
        return

    print("\n" + "=" * 50)
    print("🎓 STEP 3: Rendering Campus Digest Poster...")
    print("=" * 50)
    card_path = design_digest_post.create_digest_card(
        headline=digest_data.get("headline", ""),
        bullets=digest_data.get("bullets", []),
        why_it_matters=digest_data.get("why_it_matters", ""),
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
    