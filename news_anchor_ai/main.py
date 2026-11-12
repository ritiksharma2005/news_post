"""
news_anchor_ai/main.py
Master Pipeline Coordinator for AI News Anchor – NEWS NIT IIT (@news.nit_iit)
Commands:
- python news_anchor_ai/main.py --check-candidates
- python news_anchor_ai/main.py --generate <media_id>
- python news_anchor_ai/main.py --publish <media_id>
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from news_anchor_ai.config import (
    BRAND_NAME,
    INSTAGRAM_ACCOUNT,
    TEMP_DIR
)
from news_anchor_ai.database import (
    get_next_anchor,
    get_post_metadata,
    mark_post_status
)
from news_anchor_ai.extractor.instagram_fetcher import fetch_latest_posts
from news_anchor_ai.scriptwriter.script_generator import generate_news_script
from news_anchor_ai.voice.voice_generator import generate_anchor_voice
from news_anchor_ai.compositor.video_compositor import composite_news_reel
from news_anchor_ai.telegram_bot.candidate_notifier import notify_candidates_on_telegram
from news_anchor_ai.telegram_bot.approval_handler import (
    send_reel_for_approval,
    execute_publish_action
)

def run_generate_pipeline(media_id: str = None, dry_run: bool = False):
    print("=" * 60)
    print(f"🎬 AI NEWS ANCHOR PIPELINE — {BRAND_NAME}")
    print("=" * 60)

    # 1. Resolve Target Post Data
    target_post = None
    if media_id:
        cached = get_post_metadata(media_id)
        if cached and cached.get("image_path"):
            target_post = {
                "media_id": media_id,
                "headline": cached.get("headline", "Latest Student News"),
                "caption": cached.get("caption", ""),
                "image_path": cached.get("image_path"),
                "permalink": cached.get("permalink", "")
            }

    if not target_post:
        print("[Pipeline] Querying latest Instagram posts...")
        candidates = fetch_latest_posts(limit=15)
        if not candidates:
            print("[Pipeline] No eligible posts found to generate video.")
            return False
        # If media_id matches one of candidates, use that; else use newest candidate
        if media_id:
            for c in candidates:
                if c["media_id"] == media_id:
                    target_post = c
                    break
        if not target_post:
            target_post = candidates[0]

    post_id = target_post["media_id"]
    headline = target_post["headline"]
    caption = target_post["caption"]
    image_path = target_post["image_path"]

    print(f"\n[Target Post Identified]")
    print(f"  ID: {post_id}")
    print(f"  Headline: {headline}")
    print(f"  Image: {image_path}")

    # 2. Alternate Anchor Character
    anchor_type = get_next_anchor()
    print(f"\n👤 Selected Anchor for this video: Masked Anchor ({anchor_type.upper()})")

    # 3. Generate 30–45s Script with Gemini
    print(f"\n✍️ Generating 30–45s broadcast news script with Gemini...")
    script_data = generate_news_script(headline, caption)
    spoken_text = script_data.get("full_spoken_script", "")
    final_headline = script_data.get("headline", headline)
    category = script_data.get("category", "EXAM UPDATE")
    reel_caption = script_data.get("reel_caption", caption)

    print(f"  Headline: {final_headline}")
    print(f"  Category: {category}")
    print(f"  Script words: {len(spoken_text.split())}")

    # 4. Generate Indian English Male Voice
    print(f"\n🎙️ Synthesizing Indian English male voice (Prabhat)...")
    audio_path, duration, word_timestamps = generate_anchor_voice(spoken_text, post_id)
    print(f"  Audio rendered: {audio_path.name} ({duration:.1f}s)")

    # 5. Composite 1080x1920 (9:16) Vertical News Reel
    print(f"\n🎞️ Compositing vertical Reel with masked anchor & B-roll reading frame...")
    video_path = composite_news_reel(
        post_id=post_id,
        headline=final_headline,
        category=category,
        post_image_path=image_path,
        audio_path=audio_path,
        total_duration=duration,
        word_timestamps=word_timestamps,
        anchor_type=anchor_type
    )

    if dry_run:
        print(f"\n🔒 [DRY RUN ACTIVE] Video generated successfully at: {video_path}")
        return True

    # 6. Deliver to Telegram for Approval
    print(f"\n📲 Delivering video to Telegram for your review...")
    metadata = {
        "headline": final_headline,
        "duration": duration,
        "anchor_type": anchor_type,
        "reel_caption": reel_caption
    }
    sent = send_reel_for_approval(video_path, post_id, metadata)
    if sent:
        print(f"\n✅ SUCCESS! Video is ready in your Telegram chat. Tap Approve on your phone to publish!")
    return sent

def main():
    parser = argparse.ArgumentParser(description="AI News Anchor Pipeline")
    parser.add_argument("--check-candidates", action="store_true", help="Fetch fresh posts and send candidate menu to Telegram")
    parser.add_argument("--generate", type=str, nargs="?", const="latest", help="Generate video for specified post ID or latest")
    parser.add_argument("--publish", type=str, help="Publish approved video for specified post ID")
    parser.add_argument("--dry-run", action="store_true", help="Test run without sending to Telegram or Instagram")

    args = parser.parse_args()

    if args.check_candidates:
        notify_candidates_on_telegram()
    elif args.generate:
        target_id = None if args.generate == "latest" else args.generate
        run_generate_pipeline(media_id=target_id, dry_run=args.dry_run)
    elif args.publish:
        execute_publish_action(args.publish)
    else:
        # Default behavior: check candidates
        notify_candidates_on_telegram()

if __name__ == "__main__":
    main()
