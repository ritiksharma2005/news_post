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
        client = genai.Client(api_key=key)
    except ImportError:
        use_classic = True

    delay = 10
    last_error = None
    model_name = getattr(config, "GEMINI_MODEL", "gemini-2.5-flash")

    for attempt in range(1, max_retries + 1):
        try:
            if use_classic:
                import google.generativeai as genai_classic
                genai_classic.configure(api_key=key)
                classic_model_name = getattr(config, "GEMINI_MODEL", "gemini-1.5-flash")
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


def call_groq(prompt, max_retries=3):
    """Call Groq's OpenAI-compatible chat completions endpoint with auto-retries on 429."""
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

    delay = 10
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            
            # Check if it is a 429 Rate Limit error
            is_429 = False
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                if e.response.status_code == 429:
                    is_429 = True
            
            if is_429:
                print(f"    [Groq] Rate limited (429). Attempt {attempt}/{max_retries}. Pausing {delay}s...")
            else:
                print(f"    [Groq] Request failed: {e}. Attempt {attempt}/{max_retries}. Pausing {delay}s...")
                
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
    raise last_error


def call_ai(prompt):
    """
    Call the AI with automatic fallback: try Gemini first, fall back to
    Groq if Gemini fails for any reason. Returns the raw text response.
    """
    try:
        return call_gemini(prompt)
    except Exception as e:
        print(f"    Gemini failed ({e}), falling back to Groq...")
        try:
            return call_groq(prompt)
        except Exception as ex:
            print(f"    Groq fallback failed: {ex}")
            raise ex


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

    print("\nTesting Groq...")
    try:
        result = call_groq(test_prompt)
        print(f"Groq output: {result.strip()}")
    except Exception as e:
        print(f"Groq failed: {e}")