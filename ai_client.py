"""
ai_client.py
Unified AI calling with automatic fallback: tries Gemini first, and if it
fails (rate limit, outage, missing library, key bug, etc.), falls back
to Groq automatically. Used by rank_news.py, rewrite_news.py, caption.py,
and generate_quote.py.

Run directly to test both providers: python ai_client.py
"""

import time
import requests
import config


def call_gemini(prompt, max_retries=2):
    """Try Gemini via the SDK, with fallback if google-genai package is missing locally."""
    key = getattr(config, "GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY is missing or empty.")

    # Try importing Google GenAI SDK dynamically
    client = None
    try:
        from google import genai
        client = genai.Client(api_key=key)
    except ImportError:
        try:
            import google.generativeai as genai_classic
            genai_classic.configure(api_key=key)
            model_name = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
            model = genai_classic.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            return res.text
        except Exception as e:
            raise Exception(f"Google SDK not installed or failed: {e}")

    delay = 5
    last_error = None
    model_name = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
    raise last_error


def call_groq(prompt):
    """Call Groq's OpenAI-compatible chat completions endpoint."""
    key = getattr(config, "GROQ_API_KEY", "")
    if not key:
        raise ValueError("GROQ_API_KEY is missing or empty.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": getattr(config, "GROQ_MODEL", "llama-3.1-8b-instant"),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def call_ai(prompt):
    """
    Call the AI with automatic fallback: try Gemini first, fall back to
    Groq if Gemini fails for any reason. Returns the raw text response.
    """
    try:
        return call_gemini(prompt)
    except Exception as e:
        print(f"    Gemini failed ({e}), falling back to Groq...")
        return call_groq(prompt)


# Alias function so ask_ai(prompt) works everywhere
def ask_ai(prompt):
    return call_ai(prompt)


if __name__ == "__main__":
    test_prompt = "Reply with exactly one word: hello"

    print("Testing Gemini...")
    try:
        result = call_gemini(test_prompt)
        print("  Gemini works:", result)
    except Exception as e:
        print("  Gemini failed:", e)

    print("\nTesting Groq...")
    try:
        result = call_groq(test_prompt)
        print("  Groq works:", result)
    except Exception as e:
        print("  Groq failed:", e)

    print("\nTesting call_ai (automatic fallback)...")
    result = call_ai(test_prompt)
    print("  Result:", result)
    