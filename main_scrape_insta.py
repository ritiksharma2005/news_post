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
from workflow.history_manager import is_duplicate_insta, add_published_insta

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

def process_instagram_post(post, username, lang="hi", dry_run=False, sequence_num=0):
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
        "category": None,
        "caption": final_caption
    }
    
    # 3. Download image and render card
    image_path = f"output/images/insta_{username}_{sequence_num}.jpg"
    card_path = f"output/cards/insta_{username}_{sequence_num}.png"
    
    final_image = image_handler.prepare_image(story, image_path)
    
    if lang == "hi":
        card = template_hi.create_hindi_card(
            headline=headline,
            summary=summary,
            image_path=final_image,
            bucket="StudentEducation",
            category=None,
            output_path=card_path
        )
    else:
        card = template_en.create_card(
            headline=headline,
            summary=summary,
            image_path=final_image,
            bucket="StudentEducation",
            category=None,
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
    
    # Save to global history
    post_code = post.get("code")
    if post_code:
        add_published_insta(post_code)
        
    print("\n🏁 INSTAGRAM SCRAPE-TO-NEWS WORKFLOW COMPLETE!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Instagram posts to news cards.")
    parser.add_argument("--username", type=str, default="iit__nit__iiit", help="Target Instagram username")
    parser.add_argument("--lang", type=str, default="hi", choices=["en", "hi"], help="Output card language")
    parser.add_argument("--dry-run", action="store_true", help="Generate card locally without posting")
    parser.add_argument("--date", type=str, help="Date to fetch posts for in YYYY-MM-DD format (default: yesterday)")
    
    args = parser.parse_args()
    
    # 1. Determine target date (yesterday by default)
    if args.date:
        target_date_str = args.date
    else:
        import datetime
        target_date = datetime.date.today() - datetime.timedelta(days=1)
        target_date_str = target_date.isoformat()
        
    print(f"[Workflow] Target date for Instagram posts: {target_date_str}")
    
    # 2. Fetch recent posts
    posts = fetch_instagram_posts(args.username, limit=12)
    
    if not posts:
        print(f"\n[Error] Could not fetch any posts for @{args.username}. Check your RapidAPI key or username.")
        sys.exit(1)
        
    # 3. Filter posts matching target date
    matching_posts = [p for p in posts if p.get("date") == target_date_str]
    
    if not matching_posts:
        print(f"\n[Warning] No posts found for @{args.username} on date: {target_date_str}")
        print("Available post dates in fetched batch:")
        for p in posts:
            print(f"  - Code: {p.get('code')} | Date: {p.get('date')}")
        sys.exit(0)
        
    print(f"[Workflow] Found {len(matching_posts)} posts from {target_date_str}.")
    
    # 4. Process all matching posts
    success_count = 0
    for idx, post in enumerate(matching_posts):
        post_code = post.get("code")
        if post_code and is_duplicate_insta(post_code):
            print(f"\n[Instagram Scraper] Notice: Post '{post_code}' is already published. Skipping duplicate.")
            continue
            
        success = process_instagram_post(post, args.username, lang=args.lang, dry_run=args.dry_run, sequence_num=idx)
        if success:
            success_count += 1
            
    print(f"\n🏁 Finished processing. Successfully converted {success_count} posts from {target_date_str}!")
