import os
import json
import sys
from difflib import SequenceMatcher

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from scrapers.playwright_scraper import scrape_google_news
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

def get_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def run_pipeline(language="en", run_type="morning", dry_run=False):
    """Executes the master pipeline using Playwright scraper and zero paid APIs."""
    print("=" * 60)
    print(f"🚀 RUNNING PLAYWRIGHT NEWS WORKFLOW: {language.upper()} | {run_type.upper()} RUN")
    print("=" * 60)
    
    # 1. Scrape News from Web using Playwright
    # Determine search queries based on language
    if language == "hi":
        general_query = "भारत समाचार"
        student_query = "परीक्षा परिणाम OR बोर्ड परीक्षा OR सरकारी नौकरी"
    else:
        general_query = "India news"
        student_query = "site:careers360.com OR site:shiksha.com OR site:nta.ac.in exam news"
        
    print(f"\n[Workflow] Scraping general/trending news...")
    general_stories = scrape_google_news(general_query, lang=language, limit=8)
    
    print(f"\n[Workflow] Scraping student/education news...")
    student_stories = scrape_google_news(student_query, lang=language, limit=5)
    
    # 2. Prevent duplication with morning run if this is the evening run
    morning_titles = []
    morning_log_file = f"data/morning_run_{language}.json"
    if run_type == "evening" and os.path.exists(morning_log_file):
        try:
            with open(morning_log_file, "r", encoding="utf-8") as f:
                morning_data = json.load(f)
                morning_titles = [s.get("title", "") for s in morning_data]
            print(f"Loaded {len(morning_titles)} morning stories to prevent duplication.")
        except Exception as e:
            print(f"Error loading morning log: {e}")

    # Helper to filter out similar/already published stories
    def filter_fresh_stories(stories):
        fresh = []
        for s in stories:
            # Check similarity with already selected in current run
            is_dup = False
            for f in fresh:
                if get_similarity(s["title"], f["title"]) > 0.6:
                    is_dup = True
                    break
            # Check similarity with morning stories
            for m_title in morning_titles:
                if get_similarity(s["title"], m_title) > 0.6:
                    is_dup = True
                    break
            if not is_dup:
                fresh.append(s)
        return fresh

    fresh_general = filter_fresh_stories(general_stories)
    fresh_student = filter_fresh_stories(student_stories)
    
    # 3. Apply Selection Rule (3 General + 1 Student = 4 stories)
    selected_stories = []
    
    # Take top 1 student story
    if fresh_student:
        selected_stories.append(fresh_student[0])
        # Mark as Student
        fresh_student[0]["bucket"] = "StudentEducation"
        fresh_student[0]["category"] = "छात्र समाचार" if language == "hi" else "Student"
    
    # Take top general stories to fill the remainder up to 4
    general_needed = 4 - len(selected_stories)
    for story in fresh_general[:general_needed]:
        # Simple dynamic categorization based on keywords
        title_lower = story["title"].lower()
        if any(kw in title_lower for kw in ["politics", "govt", "government", "policy", "minister", "modi", "kejriwal", "चुनाव", "सरकार", "मंत्री"]):
            story["bucket"] = "IndianPolitics"
            story["category"] = "राजनीति" if language == "hi" else "Politics"
        elif any(kw in title_lower for kw in ["market", "gdp", "golds", "rupee", "bank", "rbi", "sensex", "economy", "टैरिफ", "बैंक", "महंगाई"]):
            story["bucket"] = "Economy"
            story["category"] = "अर्थव्यवस्था" if language == "hi" else "Economy"
        elif any(kw in title_lower for kw in ["cricket", "olympics", "hockey", "sports", "match", "खेल", "क्रिकेट", "मैच"]):
            story["bucket"] = "Sports"
            story["category"] = "खेल" if language == "hi" else "Sports"
        else:
            story["bucket"] = "IndianPolitics"
            story["category"] = "राष्ट्रीय" if language == "hi" else "National"
            
        selected_stories.append(story)
        
    print(f"\n[Workflow] Selected {len(selected_stories)} final stories for the run.")
    if not selected_stories:
        print("No fresh stories selected. Stopping.")
        return
        
    # 4. Form Headlines, Summaries, and Captions (No LLM, direct formatting)
    final_posters = []
    for i, story in enumerate(selected_stories):
        # Truncate title and summary to fit card layout perfectly
        headline = clean_and_truncate(story["title"], 80)
        summary_limit = 210 if language == "hi" else 155
        summary = clean_and_truncate(story["summary"], summary_limit)
        
        story["new_headline"] = headline
        story["new_summary"] = summary
        
        # Build engagement caption
        if language == "hi":
            caption = (
                f"🔥 {headline}\n\n"
                f"{summary}\n\n"
                f"💬 इस घटनाक्रम पर आपकी क्या राय है? कमेंट में बताएं! 👇\n\n"
                f"📌 अपडेट रहने के लिए इसे अपने दोस्तों के साथ शेयर करें!\n\n"
                f"📲 रोज़ाना हिंदी अपडेट्स के लिए टेलीग्राम पर @news.nit_iit से जुड़ें!\n\n"
                f"#HindiNews #RashtriyaKhabar #SarkariFaisle #UPSC #CurrentAffairs #news_nit_iit"
            )
        else:
            caption = (
                f"🔥 {headline}\n\n"
                f"{summary}\n\n"
                f"💬 What is your opinion on this update? Let us know in the comments below! 👇\n\n"
                f"📌 Tag a friend to keep them informed! \n\n"
                f"📲 Join @news.nit_iit on Telegram for daily updates!\n\n"
                f"#IndiaNews #StudentAffairs #UPSC #CompetitiveExams #GenZNews #news_nit_iit"
            )
        story["caption"] = caption
        
        # Determine output paths
        image_path = f"output/images/story_{language}_{run_type}_{i}.jpg"
        card_path = f"output/cards/story_{language}_{run_type}_{i}.png"
        
        # Prepare image (download/search/fallback)
        final_image = image_handler.prepare_image(story, image_path)
        
        # Render poster card
        if language == "hi":
            card = template_hi.create_hindi_card(
                headline=headline,
                summary=summary,
                image_path=final_image,
                bucket=story["bucket"],
                category=story["category"],
                output_path=card_path
            )
        else:
            card = template_en.create_card(
                headline=headline,
                summary=summary,
                image_path=final_image,
                bucket=story["bucket"],
                category=story["category"],
                output_path=card_path
            )
        story["card_path"] = card
        print(f"  [Card Rendered] Story {i+1} poster saved to: {card}")
        final_posters.append(story)
        
    # Save selection log
    os.makedirs("data", exist_ok=True)
    log_file = f"data/{run_type}_run_{language}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(final_posters, f, indent=2, ensure_ascii=False)
    print(f"\nSaved run logs to: {log_file}")
    
    if dry_run:
        print("\n" + "=" * 60)
        print("🔒 [DRY RUN ACTIVE] Posters generated, skipping publishing.")
        print("=" * 60)
        for idx, s in enumerate(final_posters):
            print(f"\n--- Post {idx+1} ({s['bucket']}) ---")
            print(f"Headline: {s['new_headline']}")
            print(f"Summary: {s['new_summary']}")
            print(f"Caption:\n{s['caption']}")
        return
        
    # 5. Publish to Telegram
    print("\nSending stories to Telegram...")
    telegram.send_all_stories(final_posters)
    
    # 6. Publish to Instagram
    print("\nPublishing stories to Instagram...")
    instagram.publish_all_stories(final_posters)
    
    print("\n" + "=" * 60)
    print(f"🏁 {language.upper()} {run_type.upper()} RUN COMPLETE!")
    print("=" * 60)
