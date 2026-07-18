"""
caption.py
Generates an Instagram-style caption + hashtags for each rewritten story.
Uses Gemini, falling back to Groq automatically if Gemini is unavailable.

Run directly to test: python caption.py
(Requires output/rewritten_articles.json to already exist)
"""

import json

import ai_client
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


def generate_caption(story):
    """Generate a caption + hashtags for one story using the AI (Gemini, falling back to Groq)."""
    prompt = CAPTION_PROMPT.format(
        headline=story.get("new_headline", story.get("title", "")),
        summary=story.get("new_summary", ""),
    )

    try:
        response_text = ai_client.call_ai(prompt)
    except Exception as e:
        print(f"  AI call failed on both providers for '{story.get('new_headline', '')[:50]}...': {e}")
        return None

    try:
        parsed = parse_gemini_json(response_text)
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

    print(f"Generating captions for {len(stories)} stories...")
    captioned = []
    for story in stories:
        result = generate_caption(story)
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
