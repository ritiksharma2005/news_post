"""
daily_channel_digest.py
Main CLI Entry Point for Daily Instagram Broadcast Channel News Digest.
Collects today's posts from @news.nit_iit, formats a clean roundup, and sends it to Telegram.
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Add project root directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from channel_digest.config import IST_TZ
from channel_digest.database import init_db, is_roundup_completed, record_roundup
from channel_digest.collector import collect_daily_posts
from channel_digest.formatter import build_roundup_messages
from channel_digest.telegram_sender import send_roundup_to_telegram


def run_daily_channel_digest(
    target_date_ist: str = None,
    run_type: str = "auto",
    dry_run: bool = False,
    force: bool = False
) -> bool:
    """
    Executes the daily channel digest workflow for morning (11 AM) or evening (9 PM).
    """
    if not target_date_ist or target_date_ist.strip().lower() in ["", "today", "now", "default", "current"]:
        target_date_ist = datetime.now(IST_TZ).strftime("%Y-%m-%d")
    else:
        target_date_ist = target_date_ist.strip()

    # Resolve automatic run_type based on current IST hour
    if not run_type or run_type.lower() == "auto":
        current_hour_ist = datetime.now(IST_TZ).hour
        run_type = "morning" if current_hour_ist < 15 else "evening"
    else:
        run_type = run_type.lower().strip()

    roundup_key = f"{target_date_ist}_{run_type}"

    print("=" * 65)
    print(f"🚀 DAILY INSTAGRAM BROADCAST DIGEST — @news.nit_iit ({run_type.upper()} RUN)")
    print(f"📅 Target Date (IST): {target_date_ist}")
    print(f"⏰ Run Slot: {run_type.capitalize()} (Key: {roundup_key})")
    print(f"🔒 Mode: {'DRY RUN (Preview Only)' if dry_run else 'PRODUCTION'}")
    if force:
        print("⚡ Force Flag: ACTIVE (bypassing duplicate run checks)")
    print("=" * 65)
    
    init_db()
    
    # 1. Duplicate Run Prevention (per run slot)
    if not force and is_roundup_completed(roundup_key):
        print(f"\n  [Notice] {run_type.capitalize()} roundup for {target_date_ist} has already been completed and sent.")
        print("  Pass '--force' if you explicitly wish to regenerate and resend this roundup.")
        return True
        
    # 2. Collect eligible Instagram posts published on target calendar day
    posts = collect_daily_posts(target_date_ist=target_date_ist, force=force)
    
    # 3. Format message(s)
    roundup_messages = build_roundup_messages(posts, target_date_ist, run_type=run_type)
    
    # 4. Deliver to Telegram
    display_date = f"{target_date_ist} ({run_type.capitalize()})"
    success = send_roundup_to_telegram(
        roundup_messages=roundup_messages,
        roundup_date=display_date,
        post_count=len(posts),
        dry_run=dry_run
    )
    
    # 5. Persist state in SQLite and JSON history
    if not dry_run and success:
        combined_text = "\n\n---\n\n".join(roundup_messages)
        record_roundup(
            roundup_date=roundup_key,
            posts=posts,
            roundup_text=combined_text,
            telegram_sent=True
        )
        print(f"  💾 Persisted {run_type} roundup state in SQLite and JSON history for {target_date_ist}.")
        
    print("\n" + "=" * 65)
    print(f"✨ DAILY CHANNEL DIGEST ({run_type.upper()}) FOR {target_date_ist} COMPLETED.")
    print(f"📊 Posts Included: {len(posts)} | Status: {'SUCCESS' if success else 'FAILED'}")
    print("=" * 65)
    
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Daily Instagram Broadcast Channel News Digest (@news.nit_iit -> Telegram)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target calendar date in YYYY-MM-DD (Asia/Kolkata timezone). Defaults to today."
    )
    parser.add_argument(
        "--run-type",
        type=str,
        choices=["auto", "morning", "evening"],
        default="auto",
        help="Roundup run type: 'auto' (default), 'morning' (11 AM), or 'evening' (9 PM)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run without sending messages to Telegram or committing DB changes."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Bypass 'already completed' check and force roundup regeneration."
    )
    
    args = parser.parse_args()
    ok = run_daily_channel_digest(
        target_date_ist=args.date,
        run_type=args.run_type,
        dry_run=args.dry_run,
        force=args.force
    )
    sys.exit(0 if ok else 1)
