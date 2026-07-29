"""
rewrite_news.py
Takes the top-ranked stories from rank_news.py and rewrites each one into
an original headline, summary, and a detailed visual prompt for AI image generation.
"""

import json
import os
import ai_client
import config

REWRITE_PROMPT = """You are a news editor writing for an Indian social media audience. Rewrite the following news story completely in your own original words — do not reuse phrasing from the description given to you.

Story details:
Title: {title}
Description: {description}

Write:
1. A detailed 2-line headline with emojis (Make it long enough to span exactly two lines, around 15-20 words, 60-80 characters total. E.g. 🚀 Union Budget 2026: Key Policy Decisions Announced for Student Loans)
2. A 2-3 line summary (max 50 words) explaining the key facts in plain, engaging language suitable for an Instagram/social media audience
3. A detailed, descriptive image generation prompt to generate a photorealistic news photo representing this story (E.g. "A professional news photograph of Indian college students working in a modern computer lab, natural lighting, high detail, editorial look" or "A professional news photograph of an Indian political leader speaking in the Rajya Sabha chamber, Delhi, photorealistic"). Avoid text, words, or logos.

Return ONLY a JSON object in this exact format, nothing else, no markdown fences:
{{
  "headline": "...",
  "summary": "...",
  "image_prompt": "..."
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


def rewrite_story(story):
    """Send one story to the AI (Gemini, falling back to Groq) and get back rewritten details."""
    prompt = REWRITE_PROMPT.format(
        title=story["title"],
        description=story.get("description", "")[:400],
    )

    try:
        response_text = ai_client.call_ai(prompt)
    except Exception as e:
        print(f"  AI call failed on both providers for '{story['title'][:50]}...': {e}")
        return None

    try:
        parsed = parse_gemini_json(response_text)
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        print(f"  Failed to parse rewrite for '{story['title'][:50]}...': {e}")
        return None

    return {
        "new_headline": parsed.get("headline", story["title"]),
        "new_summary": parsed.get("summary", ""),
        "image_prompt": parsed.get("image_prompt", ""),
    }


def rewrite_all():
    """Load ranked stories, rewrite each one, save the results."""
    with open(config.RANKED_ARTICLES_PATH, "r", encoding="utf-8") as f:
        stories = json.load(f)

    if not stories:
        print("No ranked stories found. Run rank_news.py first.")
        return []

    print(f"Rewriting {len(stories)} stories...")
    rewritten = []
    for story in stories:
        result = rewrite_story(story)
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
