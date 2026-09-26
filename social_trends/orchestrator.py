"""
social_trends/orchestrator.py
Main Pipeline Coordinator for India Social Trends Project (Reddit + Twitter -> Telegram)
Fetches top 3-4 trending news items twice daily and broadcasts text + source photos to Telegram.
"""

import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from social_trends.config import STORIES_PER_RUN, OUTPUT_DIR
from social_trends.fetcher import fetch_all_social_trends
from social_trends.analyzer import analyze_and_format_trend, is_student_career_relevant
from social_trends.telegram_notifier import broadcast_trend_to_telegram
from social_trends.database import init_db, insert_social_trend, is_post_processed


def run_social_trends_pipeline(run_type: str = "morning", dry_run: bool = False):
    print("=" * 60)
    print(f"🚀 INDIAN STUDENT & CAREER TRENDS PIPELINE — {run_type.upper()} RUN")
    print(f"📅 Timestamp (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔒 Mode: {'DRY RUN (Preview Only)' if dry_run else 'PRODUCTION'}")
    print("=" * 60)
    
    init_db()
    
    # 1. Fetch raw trending candidates from Reddit & Twitter/Social
    raw_candidates = fetch_all_social_trends()
    if not raw_candidates:
        print("  [Notice] No new candidate trends collected for this run window.")
        return
        
    print(f"\n📊 Filtered {len(raw_candidates)} candidate items. Selecting top {STORIES_PER_RUN} Student & Career stories...")
    
    # 2. Select top STORIES_PER_RUN (4 stories) with student/career relevance and image priority
    selected_stories = []
    seen_titles = set()
    
    # Prioritize candidates with attached source images
    image_candidates = [c for c in raw_candidates if c.get("image_path") or c.get("image_url")]
    no_image_candidates = [c for c in raw_candidates if not (c.get("image_path") or c.get("image_url"))]
    ordered_candidates = image_candidates + no_image_candidates
    
    # Separate ordered candidates into Reddit vs Social
    reddit_candidates = [c for c in ordered_candidates if c.get("platform", "").startswith("Reddit")]
    
    # Pick top 2 Reddit student/campus stories first
    for c in reddit_candidates:
        post_id = c.get("post_id")
        title = c.get("title", "")
        if is_post_processed(post_id, title):
            continue
        snippet = title[:40].lower()
        if snippet in seen_titles:
            continue
        if not is_student_career_relevant(c):
            print(f"  [Relevance Filter] Skipping non-student/career trend: '{title[:60]}...'")
            continue
        seen_titles.add(snippet)
        selected_stories.append(c)
        if len(selected_stories) >= 2:
            break
            
    # Fill remaining slots from top remaining candidates (Google Trends, Social, or additional Reddit)
    remaining_candidates = [c for c in ordered_candidates if c.get("post_id") not in {s["post_id"] for s in selected_stories}]
    for c in remaining_candidates:
        post_id = c.get("post_id")
        title = c.get("title", "")
        if is_post_processed(post_id, title):
            continue
        snippet = title[:40].lower()
        if snippet in seen_titles:
            continue
        if not is_student_career_relevant(c):
            print(f"  [Relevance Filter] Skipping non-student/career trend: '{title[:60]}...'")
            continue
        seen_titles.add(snippet)
        selected_stories.append(c)
        if len(selected_stories) >= STORIES_PER_RUN:
            break
            
    if not selected_stories:
        print("  [Notice] All fetched candidate posts have already been processed or filtered out as non-India news.")
        return
        
    print(f"\n🏆 [Selected {len(selected_stories)} Top Social Stories for Broadcast]:")
    for idx, story in enumerate(selected_stories):
        print(f"  [{idx+1}] ({story.get('platform')}) Score: {story.get('score')} | {story.get('title')[:70]}...")
        
    # 3. Process each story, format caption, broadcast to Telegram, and record in DB
    broadcast_count = 0
    for idx, story in enumerate(selected_stories):
        story_idx = idx + 1
        print(f"\n🧠 [Processing Story {story_idx}/{len(selected_stories)}] '{story.get('post_id')}'...")
        
        # Format AI text breakdown & caption
        analysis = analyze_and_format_trend(story)
        caption_text = analysis["caption"]
        
        # Broadcast to Telegram
        success = broadcast_trend_to_telegram(story, caption_text, dry_run=dry_run)
        
        # Record in SQLite Database
        db_item = {
            "platform": story.get("platform"),
            "post_id": story.get("post_id"),
            "title": analysis.get("headline", story.get("title")),
            "summary": analysis.get("summary"),
            "source_url": story.get("source_url"),
            "image_url": story.get("image_url"),
            "score": story.get("score", 0),
            "published_to_telegram": not dry_run if success else False
        }
        insert_social_trend(db_item)
        broadcast_count += 1
        
    print("\n" + "=" * 60)
    print(f"✨ INDIA SOCIAL TRENDS — {run_type.upper()} RUN COMPLETE")
    print(f"📡 Broadcasted {broadcast_count} stories to Telegram.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="India Social Trends Pipeline (Reddit + Twitter -> Telegram)")
    parser.add_argument("--type", choices=["morning", "evening"], default="morning", help="Run schedule type")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Execute dry run mode without live Telegram broadcasting")
    args = parser.parse_args()
    
    run_social_trends_pipeline(run_type=args.type, dry_run=args.dry_run)
