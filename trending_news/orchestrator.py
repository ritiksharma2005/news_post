"""
trending_news/orchestrator.py
Main Pipeline Coordinator for Trend India Project (@news.nit_iit)
"""

import sys
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from trending_news.config import OUTPUT_DIR, MAX_POSTERS_PER_RUN
from trending_news.collector import collect_leads_for_run
from trending_news.image_analyzer import analyze_lead_multimodal
from trending_news.verifier import verify_news_lead
from trending_news.deduplicator import deduplicate_lead_candidates
from trending_news.ranker import rank_and_select_top_stories
from trending_news.ai_rewriter import rewrite_story_editorial
from trending_news.visual_generator import generate_editorial_visual
from trending_news.poster_generator import create_trending_poster
from trending_news.caption_generator import format_instagram_caption
from trending_news.database import insert_news_item, record_run_history, init_db
import telegram_bot


def run_trending_news_pipeline(run_type: str = "morning", dry_run: bool = True):
    print("=" * 60)
    print(f"🔥 TREND INDIA PROJECT — {run_type.upper()} RUN")
    print(f"📅 Timestamp (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔒 Mode: {'DRY RUN (Preview Only)' if dry_run else 'PRODUCTION'}")
    print("=" * 60)
    
    init_db()
    
    # 1. Collect candidate news leads within time window
    raw_leads = collect_leads_for_run(run_type)
    if not raw_leads:
        print("  [Notice] No new candidate leads collected for this run window.")
        record_run_history(run_type, processed_count=0, selected_count=0)
        return
        
    # 2. Multimodal Analysis & Verification
    print(f"\n🧠 [Multimodal Analysis & Fact Check] Processing {len(raw_leads)} leads...")
    analyzed_leads = []
    for lead in raw_leads:
        analysis = analyze_lead_multimodal(lead.get("caption", ""), lead.get("image_path"))
        verification = verify_news_lead(lead, analysis)
        
        lead["analysis"] = analysis
        lead["verification"] = verification
        analyzed_leads.append(lead)
        
    # 3. Deduplication (Level 2 String + Level 3 Semantic Event Clustering)
    unique_leads = deduplicate_lead_candidates(analyzed_leads)
    
    # 4. News Ranking (Select Top 2)
    selected_stories = rank_and_select_top_stories(unique_leads, max_select=MAX_POSTERS_PER_RUN)
    if not selected_stories:
        print("  [Notice] No stories met minimum qualifying threshold.")
        record_run_history(run_type, processed_count=len(raw_leads), selected_count=0)
        return
        
    # Prepare date-based output folder: output/trending/YYYY-MM-DD/{morning|evening}/
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_output_dir = OUTPUT_DIR / today_str / run_type.lower()
    run_output_dir.mkdir(parents=True, exist_ok=True)
    
    published_count = 0
    
    for idx, story in enumerate(selected_stories):
        story_idx = idx + 1
        post_id = story.get("source_post_id") or f"story_{story_idx}"
        print(f"\n🎨 [Generating Story {story_idx}/{len(selected_stories)}] Lead: '{post_id}' (@{story.get('source_account')})...")
        
        # 5. AI Editorial Rewrite
        editorial = rewrite_story_editorial(story)
        
        # 6. Select Visual (Prioritize original Instagram source photo)
        visual_path = generate_editorial_visual(
            visual_concept=editorial.get("visual_concept", ""),
            category=editorial.get("category", "News"),
            post_id=post_id,
            source_image_path=story.get("image_path")
        )
        
        # 7. Render 4:5 Portrait Poster (1080 x 1350 px)
        card_file_path = str(run_output_dir / f"story_{story_idx:02d}.png")
        card_path = create_trending_poster(editorial, visual_path, card_file_path)
        
        # 8. Generate Caption
        caption_text = format_instagram_caption(editorial, story)
        caption_file_path = run_output_dir / f"story_{story_idx:02d}_caption.txt"
        with open(caption_file_path, "w", encoding="utf-8") as f:
            f.write(caption_text)
            
        # 9. Save Metadata JSON
        meta_data = {
            "headline": editorial.get("headline"),
            "subheadline": editorial.get("subheadline"),
            "summary": editorial.get("summary"),
            "category": editorial.get("category"),
            "trend_score": story.get("trend_score", 0.0),
            "importance_score": story.get("importance_score", 0.0),
            "verification_status": story.get("verification", {}).get("verification_status", "unverified"),
            "source_accounts": [story.get("source_account")],
            "source_urls": [story.get("source_url")],
            "visual_type": "editorial_ai",
            "template": editorial.get("layout_type", "LAYOUT_A"),
            "caption": caption_text,
            "hashtags": story.get("hashtags", [])
        }
        json_file_path = run_output_dir / f"story_{story_idx:02d}.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)
            
        # 10. Record in SQLite Database
        db_item = {
            "source_account": story.get("source_account"),
            "source_post_id": post_id,
            "source_url": story.get("source_url"),
            "caption": story.get("caption"),
            "hashtags": story.get("hashtags"),
            "posted_at": story.get("posted_at"),
            "image_url": story.get("image_url"),
            "image_path": card_path,
            "category": editorial.get("category"),
            "headline": editorial.get("headline"),
            "summary": editorial.get("summary"),
            "trend_score": story.get("trend_score"),
            "importance_score": story.get("importance_score"),
            "verification_status": story.get("verification", {}).get("verification_status"),
            "selected": True,
            "generated": True,
            "published": not dry_run
        }
        insert_news_item(db_item)
        
        # 11. Telegram Preview Broadcast
        story_obj = {
            "card_path": card_path,
            "caption": caption_text,
            "hashtags": []
        }
        print(f"  📤 Sending story {story_idx} preview to Telegram...")
        telegram_bot.send_story(story_obj)
        
        # 12. Instagram Graph API Publishing (if not in dry run mode)
        if not dry_run:
            try:
                import instagram_publisher
                print(f"  🎓 Publishing story {story_idx} to Instagram (@news.nit_iit)...")
                instagram_publisher.publish_story(story_obj)
            except Exception as ie:
                print(f"  [Instagram Publisher Notice] {ie}")
        else:
            print("  🔒 [DRY RUN ACTIVE] Instagram publishing paused for preview.")
            
        published_count += 1
        
    record_run_history(run_type, processed_count=len(raw_leads), selected_count=published_count)
    
    print("\n" + "=" * 60)
    print(f"✨ TREND INDIA PROJECT — {run_type.upper()} RUN COMPLETE")
    print(f"📁 Output saved to: {run_output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trend India Project Pipeline")
    parser.add_argument("--type", choices=["morning", "evening"], default="morning", help="Run schedule type")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Execute dry run mode without Instagram publishing")
    args = parser.parse_args()
    
    run_trending_news_pipeline(run_type=args.type, dry_run=args.dry_run)
