"""
ai_client.py
Unified AI calling with automatic fallback: tries Gemini first, and if it
fails (rate limit, outage, missing library, key bug, etc.), falls back
to Groq automatically.
Added exponential backoff retries to handle 429 rate limit errors gracefully.
"""

import time
import requests
import config


def call_gemini(prompt, max_retries=3):
    """Try Gemini via the SDK, with fallback if google-genai package is missing locally."""
    key = getattr(config, "GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY is missing or empty.")

    # Try importing Google GenAI SDK dynamically
    client = None
    use_classic = False
    try:
        from google import genai
        from google.genai import types
        # Force stable v1 API version to bypass regional v1beta model limits
        client = genai.Client(api_key=key, http_options=types.HttpOptions(api_version='v1'))
    except ImportError:
        use_classic = True

    delay = 10
    last_error = None
    model_name = getattr(config, "GEMINI_MODEL", "gemini-3.6-flash")

    for attempt in range(1, max_retries + 1):
        try:
            if use_classic:
                import google.generativeai as genai_classic
                # Force stable v1 API version in classic SDK
                genai_classic.configure(api_key=key, client_options={'api_version': 'v1'})
                classic_model_name = getattr(config, "GEMINI_MODEL", "gemini-3.6-flash")
                model = genai_classic.GenerativeModel(classic_model_name)
                res = model.generate_content(prompt)
                return res.text
            else:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            if "429" in err_msg or "resource_exhausted" in err_msg:
                print(f"    [Gemini] Rate limited (429/Resource Exhausted). Attempt {attempt}/{max_retries}. Pausing {delay}s...")
            else:
                print(f"    [Gemini] Request failed: {e}. Attempt {attempt}/{max_retries}. Pausing {delay}s...")
            
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
    raise last_error


def call_ai(prompt):
    """
    Call the AI using Gemini. Returns the raw text response.
    """
    return call_gemini(prompt)


# Alias function so ask_ai(prompt) works everywhere
def ask_ai(prompt):
    return call_ai(prompt)


if __name__ == "__main__":
    test_prompt = "Reply with exactly one word: hello"

    print("Testing Gemini...")
    try:
        result = call_gemini(test_prompt)
        print(f"Gemini output: {result.strip()}")
    except Exception as e:
        print(f"Gemini failed: {e}")