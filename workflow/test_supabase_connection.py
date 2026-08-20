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

# --- Generative AI Diagnostics ---
print("\n=== Generative AI Diagnostics ===")
import ai_client

gemini_key = os.getenv("GEMINI_API_KEY")
print(f"GEMINI_API_KEY configured: {bool(gemini_key)} (Length: {len(gemini_key) if gemini_key else 0})")
if gemini_key:
    clean_gemini = _clean_val(gemini_key)
    print(f"Sanitized GEMINI_API_KEY length: {len(clean_gemini)}")
    print(f"Testing Gemini client directly...")
    try:
        config.GEMINI_API_KEY = clean_gemini
        res = ai_client.call_gemini("Reply with the word SUCCESS.")
        print(f"Gemini Call: SUCCESS (Response: '{res.strip()}')")
    except Exception as e:
        print(f"Gemini Call failed: {e}")

groq_key = os.getenv("GROQ_API_KEY")
print(f"GROQ_API_KEY configured: {bool(groq_key)} (Length: {len(groq_key) if groq_key else 0})")
if groq_key:
    clean_groq = _clean_val(groq_key)
    print(f"Sanitized GROQ_API_KEY length: {len(clean_groq)}")
    print(f"Testing Groq client directly...")
    try:
        config.GROQ_API_KEY = clean_groq
        res = ai_client.call_groq("Reply with the word SUCCESS.")
        print(f"Groq Call: SUCCESS (Response: '{res.strip()}')")
    except Exception as e:
        print(f"Groq Call failed: {e}")
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {clean_groq}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Reply with the word SUCCESS."}],
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            print(f"Direct Groq POST status: {resp.status_code}")
            print(f"Direct Groq POST body: {resp.text}")
        except Exception as ex:
            print(f"Direct Groq POST failed: {ex}")

