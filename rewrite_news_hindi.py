"""
rewrite_news_hindi.py
Rewrites the ranked Hindi stories into original Hindi headlines,
detailed 3-4 line Hindi summaries, and detailed English prompts for Flux.
"""

import json
import os
import ai_client
import config

REWRITE_PROMPT_HINDI = """You are a senior news editor rewriting stories for @news.nit_iit in Hindi.

Story details:
Title: {title}
Description: {description}

Write:
1. A detailed headline in HINDI with emojis spanning EXACTLY 2 lines (around 12-16 words, 60-70 characters total) so it occupies both lines and fills the template header space (E.g. 🚀 छात्र ऋण पर बड़ा फैसला: केंद्रीय बजट 2026 में महत्वपूर्ण बदलावों की घोषणा)
2. A detailed 3-4 line summary in HINDI (around 50-65 words) explaining the key facts in plain, engaging, young-audience Hindi.
3. A detailed, descriptive image generation prompt IN ENGLISH to generate a photorealistic news photo representing this story (E.g. "A professional news photograph of Indian college students working in a modern computer lab, natural lighting, high detail, editorial look"). Avoid text, words, or logos.

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
    """Send one story to the AI and get back rewritten Hindi details."""
    prompt = REWRITE_PROMPT_HINDI.format(
        title=story["title"],
        description=story.get("summary", story.get("title", ""))[:400],
    )

    try:
        response_text = ai_client.call_ai(prompt)
        parsed = parse_gemini_json(response_text)
        return {
            "new_headline": parsed.get("headline", story["title"]),
            "new_summary": parsed.get("summary", ""),
            "image_prompt": parsed.get("image_prompt", ""),
        }
    except Exception as e:
        print(f"  Failed to rewrite '{story['title'][:50]}...': {e}")
        return None


def rewrite_all():
    input_path = "data/ranked_hindi_news.json"
    if not os.path.exists(input_path):
        print("No ranked Hindi stories found. Run rank_news_hindi.py first.")
        return []

    with open(input_path, "r", encoding="utf-8") as f:
        stories = json.load(f)

    print(f"Rewriting {len(stories)} stories in Hindi...")
    rewritten = []
    for story in stories:
        result = rewrite_story(story)
        if result:
            combined = dict(story)
            combined.update(result)
            rewritten.append(combined)
            print(f"  -> {combined['new_headline']}")

    os.makedirs("data", exist_ok=True)
    output_path = "data/rewritten_hindi_news.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rewritten, f, indent=2, ensure_ascii=False)

    print(f"\nSaved rewritten Hindi news to {output_path}")
    return rewritten


if __name__ == "__main__":
    rewrite_all()
