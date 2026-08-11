"""
main_scrape_insta.py
Orchestrator to scrape public Instagram profile posts and convert them into news cards.
Usage:
  python main_scrape_insta.py --username iit_nit_iiit --lang hi --dry-run
"""

import os
import sys
import argparse
import json

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from scrapers.instagram_scraper import fetch_instagram_posts
from poster import image_handler, template_en, template_hi
from publisher import telegram, instagram

def clean_and_truncate(text, max_len):
    """Truncates text safely on word boundaries."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    trimmed = text[:max_len]
    if " " in trimmed:
        return trimmed.rsplit(" ", 1)[0] + "..."
    return trimmed + "..."

def process_instagram_post(post, username, lang="hi", dry_run=False):
    """Converts a raw Instagram post object into a formatted card and caption."""
    caption = post.get("caption", "").strip()
    image_url = post.get("image_url", "")
    
    if not caption:
        print("[Workflow] Warning: Post caption is empty. Skipping.")
        return False
        
    print(f"\n[Workflow] Processing scraped Instagram post from @{username}...")
    
    # 1. Split caption into Headline and Summary
    # Typically, the first line is the headline, remaining lines are the summary description.
    caption_lines = [line.strip() for line in caption.split("\n") if line.strip()]
    
    headline = caption_lines[0] if caption_lines else "Campus News Update"
    
    # Clean emojis from headline start/end
    headline = headline.replace("🔥", "").replace("📌", "").replace("📢", "").strip()
    
    if len(caption_lines) > 1:
        # Join subsequent paragraphs
        summary = " ".join(caption_lines[1:])
    else:
        summary = headline
        
    # Clean hashtags from summary to keep card text professional
    summary_words = []
    for word in summary.split():
        if not word.startswith("#"):
            summary_words.append(word)
    summary = " ".join(summary_words)
    
    # Truncate for templates (Hindi allows longer summaries now!)
    headline = clean_and_truncate(headline, 80)
    summary_limit = 210 if lang == "hi" else 155
    summary = clean_and_truncate(summary, summary_limit)
    
    print(f"  Parsed Headline: {headline}")
    print(f"  Parsed Summary: {summary}")
    
    # 2. Build engagement caption
    # Keep original hashtags or append standard ones
    hashtags = " ".join([word for word in caption.split() if word.startswith("#")])
    if not hashtags:
        hashtags = "#CampusLife #CollegeNews #EngineeringLife #iit_nit_iiit #news_nit_iit"
        
    if lang == "hi":
        final_caption = (
            f"🔥 {headline}\n\n"
            f"{summary}\n\n"
            f"📌 @{username} से साभार प्राप्त।\n\n"
            f"📲 रोज़ाना हिंदी अपडेट्स के लिए टेलीग्राम पर @news.nit_iit से जुड़ें!\n\n"
            f"{hashtags}"
        )
    else:
        final_caption = (
            f"🔥 {headline}\n\n"
            f"{summary}\n\n"
            f"📌 Scraped update courtesy of @{username}.\n\n"
            f"📲 Join @news.nit_iit on Telegram for daily updates!\n\n"
            f"{hashtags}"
        )
        
    story = {
        "title": headline,
        "new_headline": headline,
        "new_summary": summary,
        "featured_image": image_url,
        "bucket": "StudentEducation",
        "category": "Student",
        "caption": final_caption
    }
    
    # 3. Download image and render card
    image_path = f"output/images/insta_{username}.jpg"
    card_path = f"output/cards/insta_{username}.png"
    
    final_image = image_handler.prepare_image(story, image_path)
    
    if lang == "hi":
        card = template_hi.create_hindi_card(
            headline=headline,
            summary=summary,
            image_path=final_image,
            bucket="StudentEducation",
            category="Student",
            output_path=card_path
        )
    else:
        card = template_en.create_card(
            headline=headline,
            summary=summary,
            image_path=final_image,
            bucket="StudentEducation",
            category="Student",
            output_path=card_path
        )
        
    story["card_path"] = card
    print(f"  [Card Rendered] Poster card saved to: {card}")
    
    if dry_run:
        print("\n" + "=" * 60)
        print("🔒 [DRY RUN ACTIVE] Poster generated, skipping publishing.")
        print("=" * 60)
        print(f"Caption draft:\n{final_caption}")
        return True
        
    # 4. Publish
    print("\nSending story to Telegram...")
    telegram.send_all_stories([story])
    
    print("\nPublishing story to Instagram...")
    instagram.publish_all_stories([story])
    
    print("\n🏁 INSTAGRAM SCRAPE-TO-NEWS WORKFLOW COMPLETE!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Instagram posts to news cards.")
    parser.add_argument("--username", type=str, default="iit__nit__iiit", help="Target Instagram username")
    parser.add_argument("--lang", type=str, default="hi", choices=["en", "hi"], help="Output card language")
    parser.add_argument("--dry-run", action="store_true", help="Generate card locally without posting")
    
    args = parser.parse_args()
    
    # 1. Fetch latest post
    posts = fetch_instagram_posts(args.username, limit=1)
    
    if not posts:
        print(f"\n[Error] Could not fetch any posts for @{args.username}. Check your RapidAPI key or username.")
        sys.exit(1)
        
    # 2. Process the latest post
    success = process_instagram_post(posts[0], args.username, lang=args.lang, dry_run=args.dry_run)
    if not success:
        sys.exit(1)
