"""
caption.py
Generates Instagram captions with high-converting Call-To-Action (CTA) prompts,
relevant category hashtags, and Telegram channel invites.
"""

import json
import os
import ai_client
import config

CALL_TO_ACTIONS = {
    "IndianPolitics": "\n\n💬 What is your opinion on this political development? Drop your thoughts in the comments below! 👇\n\n📌 Share this with a friend to keep them updated!",
    "StudentEducation": "\n\n📌 Share this with a classmate or friend preparing for JEE / NEET / UPSC / Jobs!\n\n💬 Have questions or thoughts? Let us know in the comments below! 👇",
    "TechInnovation": "\n\n🚀 How do you think this tech update will impact our future? Comment below! 👇\n\n📌 Tag a fellow tech enthusiast!",
}

HASHTAGS = {
    "IndianPolitics": ["#IndianPolitics", "#NationalNews", "#GovtPolicy", "#Parliament", "#India", "#news_nit_iit"],
    "StudentEducation": ["#IIT", "#NIT", "#JEE2026", "#NEET2026", "#UPSC", "#GovtJobs", "#CampusPlacements", "#news_nit_iit"],
    "TechInnovation": ["#AI", "#ArtificialIntelligence", "#ISRO", "#Technology", "#StartupIndia", "#TechNews", "#news_nit_iit"],
}


def generate_caption_for_story(story):
    """
    Generates an engaging Instagram caption with CTA, hashtags, and Telegram link.
    """
    headline = story.get("new_headline", story.get("title", ""))
    summary = story.get("new_summary", story.get("description", ""))
    bucket = story.get("bucket", "StudentEducation")

    # Construct clean, readable caption text
    caption_text = f"🔥 {headline}\n\n{summary}"

    # Append Category CTA
    cta = CALL_TO_ACTIONS.get(bucket, CALL_TO_ACTIONS["StudentEducation"])
    caption_text += cta

    # Append Telegram Invite
    caption_text += "\n\n📲 Join @news.nit_iit on Telegram for instant alerts!"

    # Append Bucket Hashtags
    bucket_tags = HASHTAGS.get(bucket, HASHTAGS["StudentEducation"])
    story["caption"] = caption_text
    story["hashtags"] = bucket_tags

    return story


def caption_all():
    """Reads rewritten articles and applies engagement captions."""
    rw_path = config.REWRITTEN_ARTICLES_PATH
    if not os.path.exists(rw_path):
        print(f"Error: {rw_path} not found. Run rewrite_news.py first.")
        return []

    with open(rw_path, "r", encoding="utf-8") as f:
        stories = json.load(f)

    print(f"Generating engagement captions for {len(stories)} stories...")
    captioned = [generate_caption_for_story(s) for s in stories]

    os.makedirs("output", exist_ok=True)
    with open(config.CAPTIONED_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(captioned, f, indent=2, ensure_ascii=False)

    return captioned


if __name__ == "__main__":
    caption_all()
    