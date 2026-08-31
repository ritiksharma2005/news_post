"""
trending_news/time_filter.py
Time Window & Timestamp Filtering Utility (IST / UTC)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

# IST is UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc


def get_current_ist_time() -> datetime:
    """Returns the current datetime in IST timezone."""
    return datetime.now(IST)


def get_run_time_window(run_type: str = "morning", last_run_timestamp: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Calculates the (start_time_utc, end_time_utc) window for the requested run type.
    
    Morning Run (9:00 AM IST):
        Default window: Prev Day 8:00 PM IST to Current Day 9:00 AM IST (13 hours)
    Evening Run (8:00 PM IST):
        Default window: Current Day 9:00 AM IST to Current Day 8:00 PM IST (11 hours)
        
    If last_run_timestamp is provided and earlier than default start_time, start_time is set to last_run_timestamp
    to prevent content loss if workflow runs late.
    """
    now_ist = get_current_ist_time()
    
    if run_type.lower() == "morning":
        # Current day 9:00 AM IST end target
        end_ist = now_ist.replace(hour=9, minute=0, second=0, microsecond=0)
        # Previous day 8:00 PM IST start target (13h before end)
        start_ist = end_ist - timedelta(hours=13)
        
        # If running earlier/later than 9 AM, align end to now_ist
        if now_ist > end_ist:
            end_ist = now_ist
            start_ist = end_ist - timedelta(hours=13)
    else:
        # Evening run target 8:00 PM IST
        end_ist = now_ist.replace(hour=20, minute=0, second=0, microsecond=0)
        start_ist = end_ist - timedelta(hours=11)
        
        if now_ist > end_ist:
            end_ist = now_ist
            start_ist = end_ist - timedelta(hours=11)
            
    # Adjust start_time to last successful run if available and earlier
    if last_run_timestamp:
        if last_run_timestamp.tzinfo is None:
            last_run_timestamp = last_run_timestamp.replace(tzinfo=UTC)
        last_run_ist = last_run_timestamp.astimezone(IST)
        if last_run_ist < start_ist:
            print(f"  [TimeFilter] Adjusting window start from {start_ist.strftime('%Y-%m-%d %H:%M %Z')} to last run: {last_run_ist.strftime('%Y-%m-%d %H:%M %Z')}")
            start_ist = last_run_ist

    start_utc = start_ist.astimezone(UTC)
    end_utc = end_ist.astimezone(UTC)
    
    return start_utc, end_utc


def parse_post_timestamp(posted_at_raw: Any) -> Optional[datetime]:
    """
    Parses various raw timestamp inputs (ISO string, UNIX epoch integer, float, etc.)
    into a timezone-aware UTC datetime.
    """
    if not posted_at_raw:
        return None
        
    try:
        # UNIX Epoch integer/float
        if isinstance(posted_at_raw, (int, float)):
            return datetime.fromtimestamp(posted_at_raw, tz=UTC)
            
        if isinstance(posted_at_raw, str):
            posted_at_str = posted_at_raw.strip()
            if posted_at_str.isdigit():
                return datetime.fromtimestamp(int(posted_at_str), tz=UTC)
                
            # ISO 8601 parsing
            # Replace 'Z' with '+00:00'
            posted_at_str = posted_at_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(posted_at_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
            
        if isinstance(posted_at_raw, datetime):
            if posted_at_raw.tzinfo is None:
                return posted_at_raw.replace(tzinfo=UTC)
            return posted_at_raw.astimezone(UTC)
    except Exception as e:
        print(f"  [TimeFilter] Error parsing timestamp '{posted_at_raw}': {e}")
        
    return None


def is_within_time_window(posted_at_raw: Any, start_utc: datetime, end_utc: datetime) -> bool:
    """
    Checks whether a post's creation timestamp falls strictly within [start_utc, end_utc].
    """
    post_dt = parse_post_timestamp(posted_at_raw)
    if not post_dt:
        # If timestamp is missing/unparseable, include with warning
        return True
        
    return start_utc <= post_dt <= end_utc
