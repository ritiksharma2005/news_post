import os
import requests
import json
import config

def _clean_val(value):
    if not value:
        return ""
    val = value.strip()
    if val.startswith('"') and val.endswith('"'):
        val = val[1:-1].strip()
    elif val.startswith("'") and val.endswith("'"):
        val = val[1:-1].strip()
    return val

SUPABASE_URL = _clean_val(os.getenv("SUPABASE_URL") or getattr(config, "SUPABASE_URL", ""))
SUPABASE_KEY = _clean_val(os.getenv("SUPABASE_KEY") or getattr(config, "SUPABASE_KEY", ""))

def is_supabase_configured():
    # Debug print to trace credentials loading
    print(f"  [DEBUG] SUPABASE_URL: {SUPABASE_URL}, Key Length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
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

def fetch_supabase_insta_history():
    """
    Fetches the list of all published Instagram post shortcodes from the Supabase database.
    """
    if not is_supabase_configured():
        return []

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/insta_history?select=post_code"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            records = res.json()
            codes = [r.get("post_code") for r in records if r.get("post_code")]
            print(f"  [Supabase] Successfully loaded {len(codes)} past Instagram post codes from database.")
            return codes
        else:
            print(f"  [Supabase] Fetch failed: Status {res.status_code} ({res.text})")
    except Exception as e:
        print(f"  [Supabase] Error querying database: {e}")
    
    return []

def save_insta_to_supabase(post_code):
    """
    Inserts a newly published Instagram post shortcode into the Supabase database.
    """
    if not is_supabase_configured():
        return False

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/insta_history"
    headers = get_supabase_headers()
    payload = {
        "post_code": post_code
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        if res.status_code in [200, 201]:
            print(f"  [Supabase] Saved Instagram post code to cloud: {post_code}")
            return True
        else:
            print(f"  [Supabase] Save failed: Status {res.status_code} ({res.text})")
    except Exception as e:
        print(f"  [Supabase] Error saving Instagram post code: {e}")
    
    return False
