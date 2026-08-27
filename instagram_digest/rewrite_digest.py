"""
instagram_digest/rewrite_digest.py
Filters raw scraped IG posts, extracts key facts, and rewrites them into
@news.nit_iit's unique editorial student format.
"""

import sys
import os

# 🔹 PATH RESOLVER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import ai_client

DIGEST_REWRITE_PROMPT = """You are an editor for @news.nit_iit. Below are raw Instagram post captions scraped from trusted IIT/NIT update pages:

{posts_text}

TASK:
1. Identify the TWO MOST IMPORTANT distinct student updates (e.g. Hackathon, Internship, Exam alert, Placement record, Admission, or Event). Skip generic memes or ads.
2. For each, extract key facts: College Name, Event/Exam Title, Registration Deadline/Dates, Eligibility, and why it matters.
3. Rewrite them into a cohesive paragraph of exactly 5 to 7 lines of sentence-based text. Do not use bullet points or lists.

OUTPUT FORMAT (Return a valid JSON array containing up to 2 distinct objects, no markdown formatting):
[
  {{
    "selected_index": 1,  // The [1-based index] of the selected post from the list below
    "headline": "A detailed 2-line headline with emojis (Make it long enough to span exactly two lines, E.g. 🚀 IIT Bombay Opens National Innovation Hackathon: Registration Closes This Week)",
    "summary": "A cohesive, detailed paragraph of 5 to 7 sentences detailing the college, event/exam, dates, eligibility, and key details. No bullets, list symbols, or dashes.",
    "caption": "Full Instagram caption text with CTAs and hashtags"
  }},
  ...
]
"""


def rewrite_latest_digest():
    raw_path = "output/raw_ig_digest.json"
    if not os.path.exists(raw_path):
        print("  No raw IG digest data found.")
        return None

    with open(raw_path, "r", encoding="utf-8") as f:
        posts = json.load(f)

    if not posts:
        print("  No posts available to digest.")
        return None

    # Format posts for AI, filtering out duplicate shortcodes
    from workflow.history_manager import is_duplicate_insta
    filtered_posts = []
    for p in posts:
        shortcode = p.get("shortcode")
        if shortcode and is_duplicate_insta(shortcode):
            print(f"  [Deduplication] Skipping already processed source post: {shortcode}")
            continue
        filtered_posts.append(p)

    if not filtered_posts:
        print("  No new/unprocessed posts available to digest.")
        return None

    posts_text = []
    for i, p in enumerate(filtered_posts[:5]):
        posts_text.append(f"[{i+1}] Account: {p.get('source_account')}\nCaption: {p.get('caption')[:300]}\n")

    prompt = DIGEST_REWRITE_PROMPT.format(posts_text="\n".join(posts_text))

    print("🧠 Filtering & Rewriting Instagram News Digest with AI...")
    try:
        response_text = ai_client.ask_ai(prompt)
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        digest_data = json.loads(clean_text)
        
        # Ensure digest_data is a list
        if not isinstance(digest_data, list):
            digest_data = [digest_data]

        # Add the selected post's shortcode to each item in the list for history tracking
        for item in digest_data:
            selected_idx = item.get("selected_index", 1) - 1
            if 0 <= selected_idx < len(filtered_posts):
                item["selected_shortcode"] = filtered_posts[selected_idx].get("shortcode")

        # Limit to at most 2 updates
        digest_data = digest_data[:2]

        save_path = "output/processed_ig_digest.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(digest_data, f, indent=2, ensure_ascii=False)

        print(f"  Successfully compiled {len(digest_data)} rewritten updates.")
        return digest_data
    except Exception as e:
        print(f"❌ Error rewriting digest: {e}")
        return None


if __name__ == "__main__":
    rewrite_latest_digest()