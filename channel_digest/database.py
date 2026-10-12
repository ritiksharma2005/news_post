"""
channel_digest/database.py
Persistent storage and state management for Instagram Broadcast Channel daily digests.
Tracks processed media IDs and completed daily roundups using SQLite and published_history.json.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .config import DB_PATH, DATA_DIR, HISTORY_FILE


def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to the channel_digest SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables for post tracking and daily roundup history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table 1: Individual posts processed into roundups
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channel_digest_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_id TEXT UNIQUE NOT NULL,
        permalink TEXT NOT NULL,
        headline TEXT,
        caption TEXT,
        published_at_ist TEXT,
        roundup_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Table 2: Completed daily roundup summaries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channel_digest_roundups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roundup_date TEXT UNIQUE NOT NULL,
        post_count INTEGER NOT NULL,
        roundup_text TEXT,
        telegram_sent INTEGER DEFAULT 0,
        sent_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()


def _load_history_json() -> Dict[str, Any]:
    """Loads shared JSON history file with fallback defaults."""
    if not HISTORY_FILE.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return {"channel_digest_media_ids": [], "channel_digest_roundup_dates": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {}
            if "channel_digest_media_ids" not in data:
                data["channel_digest_media_ids"] = []
            if "channel_digest_roundup_dates" not in data:
                data["channel_digest_roundup_dates"] = []
            return data
    except Exception as e:
        print(f"  [Database Notice] Error reading history JSON: {e}")
        return {"channel_digest_media_ids": [], "channel_digest_roundup_dates": []}


def _save_history_json(data: Dict[str, Any]):
    """Saves updated state to shared JSON history file."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [Database Notice] Error writing history JSON: {e}")


def is_post_in_roundup(media_id: str) -> bool:
    """Checks whether an Instagram media ID has already been recorded in a roundup."""
    if not media_id:
        return False
        
    media_id_str = str(media_id).strip()
    
    # 1. Quick check against JSON history
    history = _load_history_json()
    if media_id_str in history.get("channel_digest_media_ids", []):
        return True
        
    # 2. Check SQLite database
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM channel_digest_posts WHERE media_id = ?", (media_id_str,))
    row = cursor.fetchone()
    conn.close()
    
    return row is not None


def is_roundup_completed(roundup_date: str) -> bool:
    """
    Checks whether a daily roundup for `roundup_date` (YYYY-MM-DD in IST) has already been completed.
    Returns True only if the roundup exists and was successfully delivered/generated.
    """
    if not roundup_date:
        return False
        
    # 1. Check JSON history
    history = _load_history_json()
    if roundup_date in history.get("channel_digest_roundup_dates", []):
        return True
        
    # 2. Check SQLite database
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_sent FROM channel_digest_roundups WHERE roundup_date = ?", (roundup_date,))
    row = cursor.fetchone()
    conn.close()
    
    if row is not None and row["telegram_sent"] == 1:
        return True
        
    return False


def get_roundup(roundup_date: str) -> Optional[Dict[str, Any]]:
    """Retrieves existing roundup record for a given date."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channel_digest_roundups WHERE roundup_date = ?", (roundup_date,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def record_roundup(
    roundup_date: str,
    posts: List[Dict[str, Any]],
    roundup_text: str,
    telegram_sent: bool = False
) -> bool:
    """
    Persistently records the completed daily roundup and all included post IDs in SQLite and JSON.
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    try:
        # Record each included post
        for post in posts:
            m_id = str(post.get("media_id") or post.get("id") or "").strip()
            if not m_id:
                continue
            cursor.execute("""
            INSERT OR IGNORE INTO channel_digest_posts (
                media_id, permalink, headline, caption, published_at_ist, roundup_date
            ) VALUES (?, ?, ?, ?, ?, ?);
            """, (
                m_id,
                post.get("permalink", ""),
                post.get("headline", ""),
                post.get("caption", "")[:500],
                post.get("published_at_ist", ""),
                roundup_date
            ))
            
        # Record or update roundup entry
        cursor.execute("""
        INSERT INTO channel_digest_roundups (
            roundup_date, post_count, roundup_text, telegram_sent, sent_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(roundup_date) DO UPDATE SET
            post_count=excluded.post_count,
            roundup_text=excluded.roundup_text,
            telegram_sent=excluded.telegram_sent,
            sent_at=excluded.sent_at;
        """, (
            roundup_date,
            len(posts),
            roundup_text,
            1 if telegram_sent else 0,
            now_iso if telegram_sent else None
        ))
        
        conn.commit()
    except Exception as e:
        print(f"  [Database Error] Failed to record roundup: {e}")
        conn.close()
        return False
    finally:
        conn.close()
        
    # Sync to JSON history
    try:
        history = _load_history_json()
        media_ids_set = set(history.get("channel_digest_media_ids", []))
        for post in posts:
            m_id = str(post.get("media_id") or post.get("id") or "").strip()
            if m_id:
                media_ids_set.add(m_id)
        history["channel_digest_media_ids"] = list(media_ids_set)
        
        dates_set = set(history.get("channel_digest_roundup_dates", []))
        if telegram_sent:
            dates_set.add(roundup_date)
        history["channel_digest_roundup_dates"] = list(dates_set)
        
        _save_history_json(history)
    except Exception as e:
        print(f"  [Database Notice] JSON history sync error: {e}")
        
    return True
