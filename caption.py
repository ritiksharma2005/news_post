"""
caption.py
Generates an Instagram-style caption + hashtags for each rewritten story.

Run directly to test: python caption.py
(Requires output/rewritten_articles.json to already exist)
"""

import json
import time

from google import genai

import config


CAPTION_PROMPT = """You are writing an Instagram caption for an Indian news page called @news.nit_iit.

Story headline: {headline}
Story summary: {summary}

Write:
1. A short, punchy caption (2-4 lines) that makes people want to read more and engage (ask a question, invite opinions, or add a relevant reaction). Use 1-2 relevant emojis naturally, not excessively.
2. 8-10 relevant hashtags mixing broad reach tags (#India #news) with specific topic tags related to this story. No spaces within a hashtag.

Return ONLY a JSON object in this exact format, nothing else, no markdown fences:
{{
  "caption": "...",
  "hashtags": ["#tag1", "#tag2", "..."]
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


def generate_caption(client, story):
    """Generate a caption + hashtags for one story."""
    prompt = CAPTION_PROMPT.format(
        headline=story.get("new_headline", story.get("title", "")),
        summary=story.get("new_summary", ""),
    )

    try:
        response = call_gemini_with_retry(client, prompt)
    except Exception as e:
        print(f"  Gemini call failed after retries for '{story.get('new_headline', '')[:50]}...': {e}")
        return None

    try:
        parsed = parse_gemini_json(response.text)
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        print(f"  Failed to parse caption for '{story.get('new_headline', '')[:50]}...': {e}")
        return None

    return {
        "caption": parsed.get("caption", ""),
        "hashtags": parsed.get("hashtags", []),
    }


def caption_all():
    """Load rewritten stories, generate captions for each, save the results."""
    with open(config.REWRITTEN_ARTICLES_PATH, "r", encoding="utf-8") as f:
        stories = json.load(f)

    if not stories:
        print("No rewritten stories found. Run rewrite_news.py first.")
        return []

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    print(f"Generating captions for {len(stories)} stories...")
    captioned = []
    for story in stories:
        result = generate_caption(client, story)
        if result:
            combined = dict(story)
            combined.update(result)
            captioned.append(combined)
            print(f"  -> {combined['caption'][:60]}...")

    with open(config.CAPTIONED_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(captioned, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {config.CAPTIONED_ARTICLES_PATH}")
    return captioned


if __name__ == "__main__":
    caption_all()
