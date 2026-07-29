"""
main.py
Master Orchestrator for @news.nit_iit:
- Scheduled 7:00 AM IST   -> Life Mantra Quote (1 post)
- Scheduled 8:00 AM IST   -> Morning News Brief (3 posts)
- Scheduled 6:00 PM IST   -> Evening News Brief (3 posts)
- Manual "Run workflow"   -> BOTH Life Mantra Quote + 3 News Briefs (4 posts total!)
- Dry Run mode supported  -> Test locally without posting: python main.py --mode news --dry-run
"""

import sys
import datetime
import config
import fetch_news
import rank_news
import rewrite_news
import caption as caption_module
import generate_image
import design_post
import telegram_bot
import instagram_publisher

# Quote Modules
import generate_quote
import design_quote_post

ENABLE_INSTAGRAM_POSTING = True


def run_quote_pipeline(dry_run=False):
    """Runs the Life Mantra Quote Pipeline."""
    print("=" * 50)
    print("🌅 STEP 1: Fetching today's Life Mantra Quote")
    print("=" * 50)
    quote_data = generate_quote.fetch_daily_quote()

    author_name = quote_data.get("author", "Wise Leader")
    print(f"\n🎨 STEP 2: Fetching background portrait for {author_name}...")
    portrait_path = generate_image.generate_image(
        headline=f"Minimalist black and white sketch portrait illustration of {author_name}, high quality line art",
        summary="pencil sketch line art background",
        output_path=f"output/images/portrait_{author_name.replace(' ', '_')}.jpg"
    )

    print("\n🎨 STEP 3: Rendering Life Mantra Poster...")
    card_path = design_quote_post.create_quote_card(
        quote_en=quote_data["quote_en"],
        quote_hi=quote_data["quote_hi"],
        author=author_name,
        reflection=quote_data["reflection"],
        author_image_path=portrait_path,
        output_path="output/cards/quote_today.png"
    )

    caption_text = (
        f"🌅 Today's Life Mantra: \"{quote_data['quote_en']}\"\n\n"
        f"🇮🇳 {quote_data['quote_hi']}\n\n"
        f"— {author_name}\n\n"
        f"💭 Today's Reflection for Students:\n{quote_data['reflection']}\n\n"
        f"💬 How are you applying this in your prep today? Comment below! 👇\n\n"
        f"📲 Join @news.nit_iit on Telegram for daily alerts!\n\n"
        f"#LifeMantra #Motivation #UPSC #JEE #NEET #GATE #StudentLife #news_nit_iit"
    )

    story_obj = {
        "card_path": card_path,
        "caption": caption_text,
        "hashtags": []
    }

    if dry_run:
        print("\n" + "=" * 50)
        print("🔒 [DRY RUN ACTIVE] Quote card generated at output/cards/quote_today.png")
        print("=" * 50)
        print(f"Caption draft:\n{caption_text}")
        return

    print("\n" + "=" * 50)
    print("STEP 4: Sending Life Mantra to Telegram")
    print("=" * 50)
    telegram_bot.send_story(story_obj)

    print("\n" + "=" * 50)
    print("STEP 5: Publishing Life Mantra to Instagram")
    print("=" * 50)
    if ENABLE_INSTAGRAM_POSTING:
        instagram_publisher.publish_story(story_obj)
    else:
        print("🔒 [DRY RUN ACTIVE] Instagram publishing paused.")

    print("\n" + "=" * 50)
    print("🌅 LIFE MANTRA PIPELINE COMPLETE")
    print("=" * 50)


def run_news_pipeline(dry_run=False):
    """Runs the 3-Bucket Student News Pipeline."""
    print("=" * 50)
    print("STEP 1: Fetching news & RSS feeds")
    print("=" * 50)
    fetch_news.fetch_all()

    print("\n" + "=" * 50)
    print("STEP 2: Ranking into 3 Buckets (Politics, Student, Tech)")
    print("=" * 50)
    ranked = rank_news.rank_all()

    if not ranked:
        print("\nNo stories made it through ranking. Stopping here.")
        return

    print("\n" + "=" * 50)
    print("STEP 3: Rewriting headlines & summaries")
    print("=" * 50)
    rewritten = rewrite_news.rewrite_all()

    if not rewritten:
        print("\nRewriting failed for all stories. Stopping here.")
        return

    print("\n" + "=" * 50)
    print("STEP 4: Writing captions, CTAs & hashtags")
    print("=" * 50)
    captioned = caption_module.caption_all()

    if not captioned:
        print("\nCaptioning failed for all stories. Stopping here.")
        return

    print("\n" + "=" * 50)
    print("STEP 5: Generating images & building cards")
    print("=" * 50)
    captioned = captioned[:3]

    for i, story in enumerate(captioned):
        headline = story.get("new_headline", story.get("title", ""))
        image_query = story.get("image_query") or headline
        bucket = story.get("bucket", "StudentEducation")
        print(f"\n  Story {i + 1}/{len(captioned)} [{bucket}]: {headline[:60]}")

        image_path = generate_image.generate_image(
            headline=image_query,
            summary=story.get("new_summary", ""),
            output_path=f"output/images/story_{i}.jpg",
        )

        card_path = design_post.create_card(
            headline=headline,
            summary=story.get("new_summary", ""),
            image_path=image_path,
            bucket=bucket,
            language="en",
            emoji="📩",
            output_path=f"output/cards/story_{i}.png",
        )
        story["card_path"] = card_path
        print(f"    Card Ready: {card_path}")

    if dry_run:
        print("\n" + "=" * 50)
        print("🔒 [DRY RUN ACTIVE] 3 News cards generated at output/cards/")
        print("=" * 50)
        for i, s in enumerate(captioned):
            print(f"\n--- Story {i+1} Caption draft: ---\n{s.get('caption')}")
        return

    print("\n" + "=" * 50)
    print("STEP 6: Sending to Telegram")
    print("=" * 50)
    telegram_bot.send_all(captioned)

    print("\n" + "=" * 50)
    print("STEP 7: Publishing to Instagram")
    print("=" * 50)
    if ENABLE_INSTAGRAM_POSTING:
        instagram_publisher.publish_all(captioned)
    else:
        print("🔒 [DRY RUN ACTIVE] Instagram publishing paused.")

    print("\n" + "=" * 50)
    print("NEWS PIPELINE COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    mode = "auto"
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv

    for arg in sys.argv[1:]:
        if arg.startswith("--mode="):
            mode = arg.split("=")[1]
        elif arg in ["quote", "news", "auto", "manual"]:
            mode = arg

    if mode == "quote":
        run_quote_pipeline(dry_run)
    elif mode == "news":
        run_news_pipeline(dry_run)
    elif mode == "manual":
        print("🚀 Manual Trigger: Testing Quote + 3 News Briefs...")
        run_quote_pipeline(dry_run)
        run_news_pipeline(dry_run)
    else:  # mode == "auto"
        utc_hour = datetime.datetime.utcnow().hour
        if utc_hour == 1:
            print("🌅 Scheduled 7:00 AM IST Run...")
            run_quote_pipeline(dry_run)
        elif utc_hour == 2:
            print("📰 Scheduled 8:00 AM IST Run...")
            run_news_pipeline(dry_run)
        elif utc_hour == 12:
            print("🌆 Scheduled 6:00 PM IST Run...")
            run_news_pipeline(dry_run)
        else:
            print("🚀 Manual Run Detected...")
            run_quote_pipeline(dry_run)
            run_news_pipeline(dry_run)