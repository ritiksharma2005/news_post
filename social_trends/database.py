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


def is_post_processed(post_id: str, title: str = "") -> bool:
    """Checks if a post ID or matching title snippet has already been processed."""
    if not post_id:
        return False
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Exact match on post_id
    cursor.execute("SELECT 1 FROM social_trends WHERE post_id = ?", (str(post_id),))
    if cursor.fetchone() is not None:
        conn.close()
        return True
        
    # 2. Check title similarity snippet
    if title and len(title.strip()) > 15:
        snippet = title.strip()[:50]
        cursor.execute("SELECT 1 FROM social_trends WHERE title LIKE ?", (f"%{snippet}%",))
        if cursor.fetchone() is not None:
            conn.close()
            return True
            
    conn.close()
    return False


def insert_social_trend(item: Dict[str, Any]) -> Optional[int]:
    """Inserts a new social trend item into SQLite DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    try:
        cursor.execute("""
        INSERT INTO social_trends (
            platform, post_id, title, summary, source_url, image_url, score, published_to_telegram, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            item.get("platform", "Reddit"),
            str(item.get("post_id", "")),
            item.get("title", ""),
            item.get("summary", ""),
            item.get("source_url", ""),
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
