import os
import requests
import json
import config

SUPABASE_URL = os.getenv("SUPABASE_URL") or getattr(config, "SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or getattr(config, "SUPABASE_KEY", "")

def is_supabase_configured():
    return bool(SUPABASE_URL and SUPABASE_KEY)

print("=== Supabase Actions Runner Diagnostics ===")
print(f"Resolved SUPABASE_URL: '{SUPABASE_URL}'")
print(f"Resolved SUPABASE_KEY length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
print(f"Is configured: {is_supabase_configured()}")

if is_supabase_configured():
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/news_history?select=id,title"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=12)
        print(f"\nGET news_history Status: {res.status_code}")
        print(f"GET news_history Response: {res.text[:300]}")
        
        # Test insert
        post_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/news_history"
        headers_post = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        res_post = requests.post(post_url, headers=headers_post, json={"title": "Test run headline from GitHub Actions Diagnostics"}, timeout=12)
        print(f"\nPOST news_history Status: {res_post.status_code}")
        print(f"POST news_history Response: {res_post.text[:300]}")
    except Exception as e:
        print(f"\nError contacting Supabase REST endpoints: {e}")
