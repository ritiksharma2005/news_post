import os
import json
from difflib import SequenceMatcher

HISTORY_FILE = "data/published_history.json"

def get_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def load_history():
    if not os.path.exists(HISTORY_FILE):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        return {"news_links": [], "news_titles": [], "quotes": [], "insta_ids": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for key in ["news_links", "news_titles", "quotes", "insta_ids"]:
                if key not in data:
                    data[key] = []
            return data
    except Exception:
        return {"news_links": [], "news_titles": [], "quotes": [], "insta_ids": []}

def save_history(history):
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [History Manager] Error saving history file: {e}")

# Cache Supabase lookups to avoid sequential HTTP requests in a loop
_supabase_news_cache = None
_supabase_insta_cache = None

def is_duplicate_news(title, url=None):
    global _supabase_news_cache
    from workflow.supabase_manager import fetch_supabase_news_history, is_supabase_configured
    
    # Check Supabase first if configured
    if is_supabase_configured():
        if _supabase_news_cache is None:
            _supabase_news_cache = fetch_supabase_news_history()
        supabase_titles, supabase_links = _supabase_news_cache
        norm_title = title.lower().strip()
        
        # 1. Match by URL
        if url and url.strip() in supabase_links:
            print(f"  [Supabase History Match] URL matched: {url}")
            return True
            
        # 2. Match by exact title
        if norm_title in [t.lower().strip() for t in supabase_titles]:
            print(f"  [Supabase History Match] Exact Title matched: '{title}'")
            return True
            
        # 3. Match by similarity ratio (> 0.6)
        for past_title in supabase_titles:
            if get_similarity(title, past_title) > 0.6:
                print(f"  [Supabase History Match] Similar Title matched: '{title}' ~ '{past_title}'")
                return True

    # Fallback to local history
    history = load_history()
    norm_title = title.lower().strip()
    
    # 1. Match by URL
    if url and url.strip() in history.get("news_links", []):
        print(f"  [History Match] URL matched: {url}")
        return True
        
    # 2. Match by exact title
    if norm_title in [t.lower().strip() for t in history.get("news_titles", [])]:
        print(f"  [History Match] Exact Title matched: '{title}'")
        return True
        
    # 3. Match by similarity ratio (> 0.6)
    for past_title in history.get("news_titles", []):
        if get_similarity(title, past_title) > 0.6:
            print(f"  [History Match] Similar Title matched: '{title}' ~ '{past_title}'")
            return True
            
    return False

def add_published_news(title, url=None):
    history = load_history()
    if title not in history["news_titles"]:
        history["news_titles"].append(title)
    if url and url not in history["news_links"]:
        history["news_links"].append(url)
    save_history(history)

    from workflow.supabase_manager import save_news_to_supabase, is_supabase_configured
    if is_supabase_configured():
        save_news_to_supabase(title, url)

def is_duplicate_quote(quote_text):
    history = load_history()
    norm_quote = quote_text.lower().strip()
    for q in history.get("quotes", []):
        if get_similarity(norm_quote, q) > 0.7:
            print(f"  [History Match] Similar Quote matched: '{quote_text[:40]}...'")
            return True
    return False

def add_published_quote(quote_text):
    history = load_history()
    if quote_text not in history["quotes"]:
        history["quotes"].append(quote_text)
        save_history(history)

def is_duplicate_insta(post_code):
    global _supabase_insta_cache
    from workflow.supabase_manager import fetch_supabase_insta_history, is_supabase_configured
    if is_supabase_configured():
        if _supabase_insta_cache is None:
            _supabase_insta_cache = fetch_supabase_insta_history()
        if post_code in _supabase_insta_cache:
            print(f"  [Supabase History Match] Instagram post code matched: {post_code}")
            return True

    history = load_history()
    return post_code in history.get("insta_ids", [])

def add_published_insta(post_code):
    history = load_history()
    if post_code not in history["insta_ids"]:
        history["insta_ids"].append(post_code)
        save_history(history)

    from workflow.supabase_manager import save_insta_to_supabase, is_supabase_configured
    if is_supabase_configured():
        save_insta_to_supabase(post_code)
