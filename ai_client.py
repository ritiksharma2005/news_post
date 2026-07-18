"""
ai_client.py
Unified AI calling with automatic fallback: tries Gemini first, and if it
fails (rate limit, outage, the ongoing AQ.-prefix key bug, etc.), falls back
to Groq automatically. Used by rank_news.py, rewrite_news.py, and caption.py
so all three benefit from the same fallback behavior.

Run directly to test both providers: python ai_client.py
"""

import time

import requests
from google import genai

import config


def call_gemini(prompt, max_retries=2):
    """Try Gemini via the SDK, with a couple of quick retries for transient errors."""
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    delay = 5
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
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
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.GROQ_MODEL,
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
    Raises the Groq error if both fail (Gemini's error is printed but not
    raised, so we know the fallback path was actually taken).
    """
    try:
        return call_gemini(prompt)
    except Exception as e:
        print(f"    Gemini failed ({e}), falling back to Groq...")
        return call_groq(prompt)


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
