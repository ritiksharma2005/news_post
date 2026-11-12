"""
news_anchor_ai/database.py
Local lightweight JSON-based state manager for News Anchor AI.
Tracks candidate posts, anchor rotation (Scarf vs Gaiter), and publishing status.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from news_anchor_ai.config import DATA_DIR

DB_FILE = DATA_DIR / "anchor_state.json"

DEFAULT_STATE = {
    "last_anchor": "gaiter",  # Will alternate to 'scarf' on next run
    "processed_posts": {},    # media_id -> metadata
    "candidate_queue": []     # list of current active candidate media_ids
}

def load_state() -> dict:
    if not DB_FILE.exists():
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE.copy()
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Database Error] Could not read state, reinitializing: {e}")
        return DEFAULT_STATE.copy()

def save_state(state: dict):
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_next_anchor() -> str:
    """Alternates between 'scarf' and 'gaiter' for brand variety."""
    state = load_state()
    last = state.get("last_anchor", "gaiter")
    next_anchor = "scarf" if last == "gaiter" else "gaiter"
    state["last_anchor"] = next_anchor
    save_state(state)
    return next_anchor

def is_post_processed(media_id: str) -> bool:
    """Returns True if the post has already been generated or published."""
    state = load_state()
    post = state.get("processed_posts", {}).get(media_id)
    if not post:
        return False
    # If it was generated, approved, or published, do not re-propose
    return post.get("status") in ["ready_for_approval", "approved", "published", "skipped"]

def mark_post_status(media_id: str, status: str, extra: dict = None):
    state = load_state()
    if "processed_posts" not in state:
        state["processed_posts"] = {}
    if media_id not in state["processed_posts"]:
        state["processed_posts"][media_id] = {}
    
    state["processed_posts"][media_id].update({
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    if extra:
        state["processed_posts"][media_id].update(extra)
    save_state(state)

def get_post_metadata(media_id: str) -> dict:
    state = load_state()
    return state.get("processed_posts", {}).get(media_id, {})
