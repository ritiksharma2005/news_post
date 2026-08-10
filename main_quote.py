"""
main_quote.py
Master Orchestrator for Life Mantra Quote Workflow:
- Fetches daily quote (using generate_quote.fetch_daily_quote())
- Generates B&W sketch portrait (using generate_image.generate_image())
- Renders quote card (using design_quote_post.create_quote_card())
- Publishes to Telegram & Instagram
- Dry Run mode supported: python main_quote.py --dry-run
"""

import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import generate_image
import design_quote_post
import telegram_bot
import instagram_publisher
import generate_quote

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
        prompt=f"Minimalist black and white sketch portrait illustration of {author_name}, high quality line art",
        summary="pencil sketch line art background",
        output_path=f"output/images/portrait_{author_name.replace(' ', '_')}.jpg",
        width=1080,
        height=1080
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

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    run_quote_pipeline(dry_run)
