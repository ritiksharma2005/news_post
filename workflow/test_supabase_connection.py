import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    return bool(SUPABASE_URL and SUPABASE_KEY)

print("=== Supabase Actions Runner Diagnostics ===")
print(f"Resolved SUPABASE_URL: '{SUPABASE_URL}'")
print(f"Resolved SUPABASE_KEY length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
print(f"Is configured: {is_supabase_configured()}")

def _get_endpoint_url(table, params=""):
    base = SUPABASE_URL.rstrip('/')
    if "/rest/v1" in base:
        url = f"{base}/{table}"
    else:
        url = f"{base}/rest/v1/{table}"
    if params:
        url = f"{url}?{params}"
    return url

if is_supabase_configured():
    url = _get_endpoint_url("news_history", "select=id,title")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=12)
        print(f"\nGET news_history Status: {res.status_code}")
        print(f"GET news_history Response: {res.text[:300]}")
        
        # Test insert
        post_url = _get_endpoint_url("news_history")
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

# --- Generative AI Diagnostics ---
print("\n=== Generative AI Diagnostics ===")
import ai_client

gemini_key = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY configured: {bool(gemini_key)} (Length: {len(gemini_key) if gemini_key else 0})")
if gemini_key:
    clean_gemini = _clean_val(gemini_key)
    preview = f"{clean_gemini[:6]}...{clean_gemini[-4:]}" if len(clean_gemini) > 10 else clean_gemini
    print(f"Sanitized GEMINI_API_KEY length: {len(clean_gemini)} (Preview: '{preview}')")
    print(f"Testing Gemini client directly...")
    try:
        config.GEMINI_API_KEY = clean_gemini
        res = ai_client.call_gemini("Reply with the word SUCCESS.")
        print(f"Gemini Call: SUCCESS (Response: '{res.strip()}')")
    except Exception as e:
        print(f"Gemini Call failed: {e}")



