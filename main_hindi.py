"""
main_hindi.py
Master Orchestrator for @news.nit_iit (Hindi) - Playwright Scraping Version:
- Zero Paid API Dependencies (No NewsAPI, no LLM, no Flux Image generation)
- Scheduled 8:00 AM IST   -> Morning Hindi News Brief (4 posts: 1 Student + 3 Trending)
- Scheduled 6:00 PM IST   -> Evening Hindi News Brief (4 posts: 1 Student + 3 Trending)
- Dry Run mode supported  -> Test locally without posting: python main_hindi.py --dry-run
"""

import sys
import datetime
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow.orchestrator import run_pipeline

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    run_type = "morning"
    
    # Simple argument parsing for mode/run_type
    for arg in sys.argv[1:]:
        if arg.startswith("--type="):
            run_type = arg.split("=")[1]  # morning or evening
            
    # Check if run is scheduled or manual
    utc_hour = datetime.datetime.now(datetime.UTC).hour
    
    if run_type in ["morning", "evening"]:
        target_run = run_type
    elif utc_hour == 2:  # 7:30 AM / 8:00 AM IST approx
        target_run = "morning"
    elif utc_hour == 12: # 5:30 PM / 6:00 PM IST approx
        target_run = "evening"
    else:
        target_run = "morning"  # Default fallback for manual test runs
        
    run_pipeline(language="hi", run_type=target_run, dry_run=dry_run)
