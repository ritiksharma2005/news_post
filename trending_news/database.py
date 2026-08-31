"""
trending_news/database.py
SQLite Persistent Database Manager (data/trending_news.db)
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from .config import DB_PATH, DATA_DIR


def get_db_connection():
    """Returns a SQLite connection object with row_factory set to Row."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite schema for news_items and run_history tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Main news items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_account TEXT NOT NULL,
        source_post_id TEXT UNIQUE NOT NULL,
        source_url TEXT,
        caption TEXT,
        hashtags TEXT,
        posted_at TIMESTAMP,
        first_seen_at TIMESTAMP,
        image_url TEXT,
        image_path TEXT,
        category TEXT,
        headline TEXT,
        summary TEXT,
        story_hash TEXT,
        similarity_group TEXT,
        trend_score REAL DEFAULT 0.0,
        importance_score REAL DEFAULT 0.0,
        verification_status TEXT DEFAULT 'unverified',
        selected INTEGER DEFAULT 0,
        generated INTEGER DEFAULT 0,
        published INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Run history logging table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS run_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_type TEXT NOT NULL,
        processed_count INTEGER DEFAULT 0,
        selected_count INTEGER DEFAULT 0,
        run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()


def is_post_processed(source_post_id: str) -> bool:
    """Checks if a post ID has already been recorded in the database."""
    if not source_post_id:
        return False
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM news_items WHERE source_post_id = ?", (str(source_post_id),))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def insert_news_item(item: Dict[str, Any]) -> Optional[int]:
    """Inserts a new raw/processed news item into news_items table."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_iso = datetime.now(timezone.utc).isoformat()
    
    try:
        cursor.execute("""
        INSERT INTO news_items (
            source_account, source_post_id, source_url, caption, hashtags,
            posted_at, first_seen_at, image_url, image_path, category,
            headline, summary, story_hash, similarity_group, trend_score,
            importance_score, verification_status, selected, generated, published, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            item.get("source_account", ""),
            str(item.get("source_post_id", "")),
            item.get("source_url", ""),
            item.get("caption", ""),
            json.dumps(item.get("hashtags", [])) if isinstance(item.get("hashtags"), list) else str(item.get("hashtags", "")),
            str(item.get("posted_at", "")),
            now_iso,
            item.get("image_url", ""),
            item.get("image_path", ""),
            item.get("category", "General"),
            item.get("headline", ""),
            item.get("summary", ""),
            item.get("story_hash", ""),
            item.get("similarity_group", ""),
            float(item.get("trend_score", 0.0)),
            float(item.get("importance_score", 0.0)),
            item.get("verification_status", "unverified"),
            1 if item.get("selected") else 0,
            1 if item.get("generated") else 0,
            1 if item.get("published") else 0,
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


def update_news_item(item_id: int, updates: Dict[str, Any]):
    """Updates selected columns for a news item."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    for key, val in updates.items():
        set_clauses.append(f"{key} = ?")
        params.append(val)
        
    if not set_clauses:
        conn.close()
        return
        
    params.append(item_id)
    sql = f"UPDATE news_items SET {', '.join(set_clauses)} WHERE id = ?"
    cursor.execute(sql, tuple(params))
    conn.commit()
    conn.close()


def get_recent_headlines(days: int = 7) -> List[Dict[str, Any]]:
    """Retrieves recent stories from the database to assist string/semantic deduplication."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT id, source_account, source_post_id, headline, summary, story_hash, similarity_group, created_at
    FROM news_items
    ORDER BY id DESC LIMIT 100;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append(dict(r))
    return results


def record_run_history(run_type: str, processed_count: int, selected_count: int):
    """Logs the workflow run results into run_history table."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO run_history (run_type, processed_count, selected_count, run_timestamp)
    VALUES (?, ?, ?, ?);
    """, (run_type, processed_count, selected_count, now_iso))
    conn.commit()
    conn.close()


def get_last_run_timestamp(run_type: str) -> Optional[datetime]:
    """Retrieves the timestamp of the last successful run for a given run_type."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT run_timestamp FROM run_history
    WHERE run_type = ? ORDER BY id DESC LIMIT 1;
    """, (run_type,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row["run_timestamp"]:
        try:
            return datetime.fromisoformat(row["run_timestamp"].replace("Z", "+00:00"))
        except Exception:
            pass
    return None
