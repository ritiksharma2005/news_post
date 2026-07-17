"""
rewrite_news.py
Takes the top-ranked stories from rank_news.py and rewrites each one into
an original headline + 2-3 line summary, in your own words (never copying
the source article's exact phrasing).

Run directly to test: python rewrite_news.py
(Requires output/ranked_articles.json to already exist — run rank_news.py first)
"""

import json
import os
import time

from google import genai

import config


REWRITE_PROMPT = """You are a news editor writing for an Indian social media audience. Rewrite the following news story completely in your own original words — do not reuse phrasing from the description given to you.

Story details:
Title: {title}
Description: {description}

Write:
1. A short, punchy headline (under 15 words) that captures the story
2. A 2-3 line summary (max 50 words) explaining the key facts in plain, engaging language suitable for an Instagram/social media audience

Return ONLY a JSON object in this exact format, nothing else, no markdown fences:
{{
  "headline": "...",
  "summary": "..."
}}
"""


def parse_gemini_json(text):
    """Strip markdown fences if present and parse JSON safely."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


def call_gemini_with_retry(client, prompt, max_retries=3):
    """Call Gemini with retries + exponential backoff for transient errors (like 503 high-demand)."""
    delay = 5
    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
        except Exception as e:
            if attempt == max_retries:
                raise
            print(f"    Gemini call failed (attempt {attempt}/{max_retries}): {e}")
            print(f"    Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


def rewrite_story(client, story):
    """Send one story to Gemini and get back an original headline + summary."""
    prompt = REWRITE_PROMPT.format(
        title=story["title"],
        description=story.get("description", "")[:400],
    )

    try:
        response = call_gemini_with_retry(client, prompt)
    except Exception as e:
        print(f"  Gemini call failed after retries for '{story['title'][:50]}...': {e}")
        return None

    try:
        parsed = parse_gemini_json(response.text)
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        print(f"  Failed to parse rewrite for '{story['title'][:50]}...': {e}")
        return None

    return {
        "new_headline": parsed.get("headline", story["title"]),
        "new_summary": parsed.get("summary", ""),
    }


def rewrite_all():
    """Load ranked stories, rewrite each one, save the results."""
    with open(config.RANKED_ARTICLES_PATH, "r", encoding="utf-8") as f:
        stories = json.load(f)

    if not stories:
        print("No ranked stories found. Run rank_news.py first.")
        return []

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    print(f"Rewriting {len(stories)} stories...")
    rewritten = []
    for story in stories:
        result = rewrite_story(client, story)
        if result:
            combined = dict(story)
            combined.update(result)
            rewritten.append(combined)
            print(f"  -> {combined['new_headline']}")

    os.makedirs(os.path.dirname(config.REWRITTEN_ARTICLES_PATH), exist_ok=True)
    with open(config.REWRITTEN_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(rewritten, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {config.REWRITTEN_ARTICLES_PATH}")
    return rewritten


if __name__ == "__main__":
    rewrite_all()
