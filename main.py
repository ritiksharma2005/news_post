"""
main.py
Runs the entire pipeline end to end:
  fetch -> rank -> rewrite -> caption -> generate images -> design cards -> Telegram -> Instagram

Run: python main.py
"""

import json

import config
import fetch_news
import rank_news
import rewrite_news
import caption as caption_module
import generate_image
import design_post
import telegram_bot
import instagram_publisher


def run_pipeline():
    print("=" * 50)
    print("STEP 1: Fetching news")
    print("=" * 50)
    fetch_news.fetch_all()

    print("\n" + "=" * 50)
    print("STEP 2: Ranking against your priorities")
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
    print("STEP 4: Writing captions & hashtags")
    print("=" * 50)
    captioned = caption_module.caption_all()

    if not captioned:
        print("\nCaptioning failed for all stories. Stopping here.")
        return

    print("\n" + "=" * 50)
    print("STEP 5: Generating images & building cards")
    print("=" * 50)
    for i, story in enumerate(captioned):
        headline = story.get("new_headline", story.get("title", ""))
        print(f"\n  Story {i + 1}/{len(captioned)}: {headline[:60]}")

        image_path = generate_image.generate_image(
            headline=headline,
            summary=story.get("new_summary", ""),
            output_path=f"output/images/story_{i}.jpg",
        )

        card_path = design_post.create_card(
            headline=headline,
            summary=story.get("new_summary", ""),
            image_path=image_path,
            language="en",
            emoji="📩",
            output_path=f"output/cards/story_{i}.png",
        )
        story["card_path"] = card_path
        print(f"    Card ready: {card_path}")

    print("\n" + "=" * 50)
    print("STEP 6: Sending to Telegram")
    print("=" * 50)
    telegram_bot.send_all(captioned)

    print("\n" + "=" * 50)
    print("STEP 7: Publishing to Instagram")
    print("=" * 50)
    instagram_publisher.publish_all(captioned)

    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    run_pipeline()
