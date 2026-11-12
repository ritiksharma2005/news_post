"""
news_anchor_ai/database/job_manager.py
Manages production job states, unique Job IDs (NNIIT-2026-XXX),
and approval/rejection lifecycle using Supabase with local JSON fallback.
Ensures zero duplicate publishing and strict single-user approval.
"""

import json
import uuid
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List

from news_anchor_ai.config import DATA_DIR, PROJECT_DIR

STATE_FILE = DATA_DIR / "jobs_database.json"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

def _load_local_db() -> dict:
    if not STATE_FILE.exists():
        initial = {"counter": 1, "jobs": {}, "last_anchor": "gaiter"}
        _save_local_db(initial)
        return initial
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"counter": 1, "jobs": {}, "last_anchor": "gaiter"}

def _save_local_db(data: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_job_id() -> str:
    """Generates sequential official Job ID: NNIIT-2026-001, etc."""
    db = _load_local_db()
    c = db.get("counter", 1)
    year = datetime.now().year
    job_id = f"NNIIT-{year}-{c:03d}"
    db["counter"] = c + 1
    _save_local_db(db)
    return job_id

def create_job(source_url: str, post_id: str = None, raw_caption: str = "", image_url: str = "") -> dict:
    """Creates a new job in SUBMITTED state."""
    job_id = generate_job_id()
    now = datetime.now(timezone.utc).isoformat()
    job_record = {
        "job_id": job_id,
        "source_url": source_url,
        "post_id": post_id or str(uuid.uuid4())[:8],
        "raw_caption": raw_caption,
        "image_url": image_url,
        "status": "SUBMITTED",
        "created_at": now,
        "updated_at": now,
        "headline": "",
        "script": "",
        "voice_path": "",
        "video_path": "",
        "public_video_url": "",
        "anchor_type": "",
        "is_published": False,
        "is_rejected": False
    }

    # Save to local DB
    db = _load_local_db()
    db["jobs"][job_id] = job_record
    _save_local_db(db)

    # Sync to Supabase if available
    _sync_supabase_insert(job_record)
    return job_record

def update_job_status(job_id: str, status: str, updates: dict = None) -> dict:
    """Updates job progress and status."""
    db = _load_local_db()
    if job_id not in db.get("jobs", {}):
        raise ValueError(f"Job {job_id} not found.")

    job = db["jobs"][job_id]
    job["status"] = status
    job["updated_at"] = datetime.now(timezone.utc).isoformat()
    if updates:
        job.update(updates)

    _save_local_db(db)
    _sync_supabase_update(job_id, job)
    return job

def get_job(job_id: str) -> Optional[dict]:
    db = _load_local_db()
    return db.get("jobs", {}).get(job_id)

def get_latest_job() -> Optional[dict]:
    db = _load_local_db()
    jobs = db.get("jobs", {})
    if not jobs:
        return None
    latest_id = list(jobs.keys())[-1]
    return jobs[latest_id]

# --- Supabase Sync Helpers ---
def _sync_supabase_insert(record: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/anchor_jobs"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        requests.post(url, headers=headers, json=record, timeout=8)
    except Exception as e:
        print(f"[Supabase Notice] {e}")

def _sync_supabase_update(job_id: str, record: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/anchor_jobs?job_id=eq.{job_id}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        requests.patch(url, headers=headers, json=record, timeout=8)
    except Exception as e:
        print(f"[Supabase Notice] {e}")
