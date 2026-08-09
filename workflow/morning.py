import sys
import os

# Add parent path to import orchestrator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from workflow.orchestrator import run_pipeline

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    print("🌅 Triggering Scheduled 8:00 AM IST Morning Run...")
    
    # Run English morning
    run_pipeline(language="en", run_type="morning", dry_run=dry_run)
    
    # Run Hindi morning
    run_pipeline(language="hi", run_type="morning", dry_run=dry_run)
