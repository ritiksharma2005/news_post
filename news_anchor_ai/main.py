"""
news_anchor_ai/main.py
Master Production Coordinator for NEWS NIT IIT — AI Anchor Studio.
Implements the complete 7-stage production lifecycle:
Input (URL / Upload) -> Analysis -> Gemini Multimodal Script -> Voice -> Motion -> 9:16 Render -> Telegram Review -> Instagram Reel
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
from news_anchor_ai.database.job_manager import (
    create_job,
    update_job_status,
    get_job,
    get_latest_job
)
from news_anchor_ai.database import get_next_anchor
from news_anchor_ai.ai.news_extractor import (
    extract_from_instagram_url,
    extract_from_direct_upload
)
from news_anchor_ai.extractor.instagram_fetcher import fetch_latest_posts
from news_anchor_ai.ai.script_generator import generate_multimodal_news_script
from news_anchor_ai.voice.voice_generator import generate_anchor_voice
from news_anchor_ai.video.renderer import render_master_news_reel
from news_anchor_ai.telegram.bot_controller import (
    send_job_status,
    deliver_reel_for_review,
    handle_approval_action,
    handle_reject_action,
    send_telegram_message
)
from news_anchor_ai.telegram_bot.candidate_notifier import notify_candidates_on_telegram

def run_production_pipeline(
    post_url: str = None,
    image_path: str = None,
    custom_caption: str = "",
    media_id: str = None,
    dry_run: bool = False
) -> bool:
    print("=" * 65)
    print(f"🎬 NEWS NIT IIT — AI ANCHOR STUDIO PIPELINE")
    print("=" * 65)

    # 1. Step 1: Ingest Content
    extracted = None
    if post_url:
        print(f"[Pipeline] Ingesting Instagram Post URL: {post_url}")
        extracted = extract_from_instagram_url(post_url)
    elif image_path and Path(image_path).exists():
        print(f"[Pipeline] Ingesting Direct Image Upload: {image_path}")
        extracted = extract_from_direct_upload(Path(image_path), custom_caption)
    else:
        print("[Pipeline] No direct URL or upload provided. Querying recent posts from @news.nit_iit...")
        candidates = fetch_latest_posts(limit=15)
        if candidates:
            if media_id and media_id != "latest":
                for c in candidates:
                    if c["media_id"] == media_id:
                        extracted = c
                        break
            if not extracted:
                extracted = candidates[0]

    if not extracted or not extracted.get("image_path"):
        print("[Pipeline] ⚠️ Error: Could not resolve eligible post content or image.")
        send_telegram_message(
            "⚠️ I couldn't automatically access that Instagram post media.\n\n"
            "Please upload the photo or screenshot directly here in Telegram, "
            "and I will generate the complete video immediately!"
        )
        return False

    # 2. Step 2: Initialize Official Job
    job = create_job(
        source_url=extracted.get("permalink", post_url or "Direct Upload"),
        post_id=extracted.get("media_id"),
        raw_caption=extracted.get("caption", ""),
        image_url=extracted.get("image_url", "")
    )
    job_id = job["job_id"]
    print(f"\n[Job Initialized] Official Job ID: {job_id}")

    send_job_status(job_id, "Link received. Analyzing post & extracting visual source elements…")

    # 3. Step 3: Multimodal Gemini 2.0 Scriptwriting
    anchor_type = get_next_anchor()
    print(f"👤 Assigned Anchor Persona: Masked Anchor ({anchor_type.upper()})")

    send_job_status(job_id, "Crafting 5-part storytelling script with Gemini 2.0 Vision…")
    script_data = generate_multimodal_news_script(
        post_headline=extracted.get("headline", ""),
        post_caption=extracted.get("caption", ""),
        post_image_path=extracted.get("image_path")
    )

    spoken_script = script_data.get("full_spoken_script", "")
    headline = script_data.get("headline", extracted.get("headline", ""))
    category = script_data.get("category", "Campus Update")
    reel_caption = script_data.get("reel_caption", extracted.get("caption", ""))

    update_job_status(job_id, "SCRIPT_READY", {
        "headline": headline,
        "script": spoken_script,
        "reel_caption": reel_caption,
        "anchor_type": anchor_type
    })

    # 4. Step 4: Signature Voice Generation
    send_job_status(job_id, "Synthesizing signature Indian English male voice (Prabhat)…")
    voice_path, duration, word_timestamps = generate_anchor_voice(spoken_script, job_id)

    update_job_status(job_id, "VOICE_READY", {"voice_path": str(voice_path)})

    # 5. Step 5: Render 9:16 Broadcast Sequence
    send_job_status(job_id, "Rendering 5-step broadcast sequence, HUD graphics & subtitles…")
    video_path = render_master_news_reel(
        job_id=job_id,
        headline=headline,
        category=category,
        post_image_path=extracted["image_path"],
        voice_path=voice_path,
        total_duration=duration,
        word_timestamps=word_timestamps,
        anchor_type=anchor_type
    )

    if dry_run:
        print(f"\n🔒 [DRY RUN ACTIVE] Render complete at: {video_path}")
        return True

    # 6. Step 6: Deliver to Telegram for Human Review
    metadata = {
        "headline": headline,
        "duration": duration,
        "anchor_type": anchor_type,
        "reel_caption": reel_caption
    }
    delivered = deliver_reel_for_review(job_id, video_path, metadata)
    if delivered:
        print(f"\n✅ Job {job_id} successfully delivered to Telegram for review!")
    return delivered


def main():
    parser = argparse.ArgumentParser(description="NEWS NIT IIT — AI Anchor Studio")
    parser.add_argument("--url", type=str, help="Instagram Post URL to process")
    parser.add_argument("--image", type=str, help="Path to direct image upload (Telegram fallback)")
    parser.add_argument("--caption", type=str, default="", help="Custom caption for direct image upload")
    parser.add_argument("--generate", type=str, nargs="?", const="latest", help="Generate from latest post or media ID")
    parser.add_argument("--check-candidates", action="store_true", help="Send candidate options to Telegram")
    parser.add_argument("--approve", type=str, help="Approve and publish Job ID")
    parser.add_argument("--reject", type=str, help="Reject Job ID")
    parser.add_argument("--dry-run", action="store_true", help="Test run without sending to Telegram/Instagram")

    args = parser.parse_args()

    if args.approve:
        handle_approval_action(args.approve)
    elif args.reject:
        handle_reject_action(args.reject)
    elif args.check_candidates:
        notify_candidates_on_telegram()
    elif args.url:
        run_production_pipeline(post_url=args.url, dry_run=args.dry_run)
    elif args.image:
        run_production_pipeline(image_path=args.image, custom_caption=args.caption, dry_run=args.dry_run)
    elif args.generate:
        target_id = None if args.generate == "latest" else args.generate
        run_production_pipeline(media_id=target_id, dry_run=args.dry_run)
    else:
        # Default: check candidates
        notify_candidates_on_telegram()

if __name__ == "__main__":
    main()
