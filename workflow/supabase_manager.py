import os
import requests
import json
import config

SUPABASE_URL = os.getenv("SUPABASE_URL") or getattr(config, "SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or getattr(config, "SUPABASE_KEY", "")

def is_supabase_configured():
    return bool(SUPABASE_URL and SUPABASE_KEY)

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

def fetch_supabase_news_history():
    """
    Fetches the list of all published news titles and links from the Supabase database.
    """
    if not is_supabase_configured():
        return [], []

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/news_history?select=title,url"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            records = res.json()
            titles = [r.get("title") for r in records if r.get("title")]
            links = [r.get("url") for r in records if r.get("url")]
            print(f"  [Supabase] Successfully loaded {len(titles)} past news records from database.")
            return titles, links
        else:
            print(f"  [Supabase] Fetch failed: Status {res.status_code} ({res.text})")
    except Exception as e:
        print(f"  [Supabase] Error querying database: {e}")
    
    return [], []

def save_news_to_supabase(title, link=None):
    """
    Inserts a newly published news story into the Supabase database.
    """
    if not is_supabase_configured():
        return False

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/news_history"
    headers = get_supabase_headers()
    payload = {
        "title": title,
        "url": link
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code in [200, 201]:
            print(f"  [Supabase] Saved story to cloud: '{title[:40]}...'")
            return True
        else:
            print(f"  [Supabase] Save failed: Status {res.status_code} ({res.text})")
    except Exception as e:
        print(f"  [Supabase] Error saving news to database: {e}")
    
    return False
