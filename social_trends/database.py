"""
social_trends/database.py
SQLite Database Manager for Social Trends (data/social_trends.db)
Enforces 100% uniqueness across runs.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .config import DB_PATH, DATA_DIR


def get_db_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite schema for social_trends table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        post_id TEXT UNIQUE NOT NULL,
        title TEXT,
        summary TEXT,
        source_url TEXT,
        image_url TEXT,
        score INTEGER DEFAULT 0,
        published_to_telegram INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()


import sys
import os

# Import history_manager for unified cross-run uniqueness across local JSON, SQLite & Supabase
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from workflow.history_manager import is_duplicate_news, add_published_news
    HISTORY_MANAGER_AVAILABLE = True
except Exception:
    HISTORY_MANAGER_AVAILABLE = False


def is_post_processed(post_id: str, title: str = "", source_url: str = "") -> bool:
    """Checks if a post ID, title similarity, or source URL has already been processed across runs."""
    if not post_id and not title:
        return False
        
    # 1. Check unified history_manager (fuzzy title similarity > 0.6, URL match, published_history.json & Supabase)
    if HISTORY_MANAGER_AVAILABLE and title and len(title.strip()) > 10:
        if is_duplicate_news(title, source_url):
            return True

    # 2. Check local SQLite DB
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if post_id:
        cursor.execute("SELECT 1 FROM social_trends WHERE post_id = ?", (str(post_id),))
        if cursor.fetchone() is not None:
            conn.close()
            return True
            
    if title and len(title.strip()) > 15:
        snippet = title.strip()[:40]
        cursor.execute("SELECT 1 FROM social_trends WHERE title LIKE ?", (f"%{snippet}%",))
        if cursor.fetchone() is not None:
            conn.close()
            return True
            
    conn.close()
    return False


def insert_social_trend(item: Dict[str, Any]) -> Optional[int]:
    """Inserts a new social trend item into SQLite DB and syncs with unified history_manager."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    title = item.get("title", "")
    source_url = item.get("source_url", "")
    
    # Sync with history_manager to record in published_history.json & Supabase
    if HISTORY_MANAGER_AVAILABLE and title:
        try:
            add_published_news(title, source_url)
        except Exception as he:
            print(f"  [History Manager Sync Notice] {he}")
    
    try:
        cursor.execute("""
        INSERT INTO social_trends (
            platform, post_id, title, summary, source_url, image_url, score, published_to_telegram, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            item.get("platform", "Reddit"),
            str(item.get("post_id", "")),
            title,
            item.get("summary", ""),
            source_url,
            item.get("image_url", ""),
            int(item.get("score", 0)),
            1 if item.get("published_to_telegram") else 0,
            now_iso
        ))
        conn.commit()
        inserted_id = cursor.lastrowid
        conn.close()
        return inserted_id
    except sqlite3.IntegrityError:
        conn.close()
        return None
    except Exception as e:
        print(f"  [DB Error] Insert failed: {e}")
        conn.close()
        return None
