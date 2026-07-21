"""
main.py
Master Orchestrator for @news.nit_iit:
- Mode "quote": Generates 7:00 AM "Life Mantra" Quote & Reflection
- Mode "news": Generates 3-Bucket Student News Briefs
- Mode "auto": Detects current time to choose quote vs news automatically
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

# 🛑 Toggle True when ready to post live on Instagram!
ENABLE_INSTAGRAM_POSTING = True


def run_quote_pipeline():
    """Runs the 7:00 AM Life Mantra Quote Pipeline."""
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


def run_news_pipeline():
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
        bucket = story.get("bucket", "StudentEducation")
        print(f"\n  Story {i + 1}/{len(captioned)} [{bucket}]: {headline[:60]}")

        image_path = generate_image.generate_image(
            headline=headline,
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
    for arg in sys.argv[1:]:
        if arg.startswith("--mode="):
            mode = arg.split("=")[1]
        elif arg in ["quote", "news", "auto"]:
            mode = arg

    if mode == "auto":
        # Check current UTC hour to determine run mode
        utc_hour = datetime.datetime.utcnow().hour
        if utc_hour in [1, 2]:  # Around 7am-8am IST -> Run quote first, then news
            print("Auto-detected morning run mode: Running Life Mantra...")
            run_quote_pipeline()
        else:
            run_news_pipeline()
    elif mode == "quote":
        run_quote_pipeline()
    else:
        run_news_pipeline()
        