"""
main_hindi.py
Master Orchestrator for Hindi News Workflow:
- Fetches news from AajTak, Jagran, Newspinch, and NewsAPI
- Selects top 3 stories for Politics, Student, and Tech
- Rewrites and translates them to Hindi
- Generates conditional images (searches for whitelisted keywords, otherwise uses Flux)
- Compiles the posters in Hindi using Noto Sans Devanagari fonts
- Posts to Telegram & Instagram (supports --dry-run for local testing)
"""

import sys
import os
import datetime
import requests
import json
import config
import fetch_news_hindi
import rank_news_hindi
import rewrite_news_hindi
import generate_image
import design_post_hindi
import telegram_bot
import instagram_publisher
import ai_client

ENABLE_INSTAGRAM_POSTING = True

CAPTION_PROMPT = """Write an engaging social media post caption in HINDI for the following news story:
Headline: {headline}
Summary: {summary}

Include:
- 1 relevant emoji at the start
- A 1-2 sentence description in Hindi
- A Call-to-action (CTA) question in Hindi asking users to comment below (E.g. "इस बारे में आपकी क्या राय है? कमेंट में बताएं! 👇")
- The standard footer:
📌 इसे अपने दोस्तों के साथ शेयर करें!
📲 रोजाना अपडेट्स के लिए टेलीग्राम पर @news.nit_iit से जुड़ें!

- HashTags at the bottom: #NewsHindi #StudentLife #UPSC #JEE #NEET #news_nit_iit

Return ONLY the caption text.
"""


def generate_hindi_caption(headline, summary):
    """Calls AI to generate an engaging Hindi caption."""
    prompt = CAPTION_PROMPT.format(headline=headline, summary=summary)
    try:
        caption = ai_client.call_ai(prompt)
        return caption.strip()
    except Exception as e:
        print(f"  Caption generation failed: {e}")
        # Simple fallback template
        return (
            f"🔥 {headline}\n\n"
            f"{summary}\n\n"
            f"💬 इस बारे में आपकी क्या राय है? कमेंट में बताएं! 👇\n\n"
            f"📌 इसे अपने दोस्तों के साथ शेयर करें!\n"
            f"📲 रोजाना अपडेट्स के लिए टेलीग्राम पर @news.nit_iit से जुड़ें!\n\n"
            f"#NewsHindi #StudentLife #UPSC #JEE #NEET #news_nit_iit"
        )


def run_hindi_pipeline(dry_run=False):
    print("=" * 50)
    print("🌅 STEP 1: Fetching Hindi News Stories...")
    print("=" * 50)
    fetch_news_hindi.fetch_all()

    print("\n" + "=" * 50)
    print("🌅 STEP 2: Ranking into 3 Buckets (Politics, Student, Tech)...")
    print("=" * 50)
    ranked = rank_news_hindi.rank_all()

    if not ranked:
        print("No stories ranked successfully. Stopping.")
        return

    print("\n" + "=" * 50)
    print("🌅 STEP 3: Rewriting Headlines, Summaries & Visual Prompts...")
    print("=" * 50)
    rewritten = rewrite_news_hindi.rewrite_all()

    if not rewritten:
        print("Rewriting failed. Stopping.")
        return

    # Process up to 3 stories
    rewritten = rewritten[:3]

    print("\n" + "=" * 50)
    print("🌅 STEP 4: Generating Captions, Images & rendering Hindi cards...")
    print("=" * 50)
    
    captioned_stories = []

    for i, story in enumerate(rewritten):
        headline = story.get("new_headline", story.get("title", ""))
        summary = story.get("new_summary", "")
        image_prompt = story.get("image_prompt") or headline
        bucket = story.get("bucket", "StudentEducation")
        
        print(f"\nProcessing Story {i+1}/{len(rewritten)} [{bucket}]: {headline[:50]}...")
        
        # 1. Generate Hindi Caption
        caption = generate_hindi_caption(headline, summary)
        
        # 2. Fetch/Generate Image (Uses whitelisted conditional search or Flux)
        image_path = generate_image.generate_image(
            prompt=image_prompt,
            summary="",
            output_path=f"output/images/story_hindi_{i}.jpg",
        )
        
        # 3. Render Hindi Card Poster
        card_path = design_post_hindi.create_hindi_card(
            headline=headline,
            summary=summary,
            image_path=image_path,
            bucket=bucket,
            output_path=f"output/cards/story_hindi_{i}.png"
        )
        
        story["card_path"] = card_path
        story["caption"] = caption
        captioned_stories.append(story)
        print(f"    Card compiled successfully: {card_path}")

    if dry_run:
        print("\n" + "=" * 50)
        print("🔒 [DRY RUN ACTIVE] Hindi posters compiled successfully at output/cards/")
        print("=" * 50)
        for i, s in enumerate(captioned_stories):
            print(f"\n--- Story {i+1} Caption draft: ---\n{s.get('caption')}")
        return

    print("\n" + "=" * 50)
    print("🌅 STEP 5: Publishing Hindi Stories to Telegram...")
    print("=" * 50)
    telegram_bot.send_all(captioned_stories)

    print("\n" + "=" * 50)
    print("🌅 STEP 6: Publishing Hindi Stories to Instagram...")
    print("=" * 50)
    if ENABLE_INSTAGRAM_POSTING:
        instagram_publisher.publish_all(captioned_stories)
    else:
        print("🔒 [DRY RUN ACTIVE] Instagram publishing paused.")

    print("\n" + "=" * 50)
    print("HINDI NEWS PIPELINE COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    run_hindi_pipeline(dry_run)
