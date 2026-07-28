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
1. Identify the SINGLE MOST IMPORTANT student update (e.g. Hackathon, Internship, Exam alert, Placement record, Admission, or Event). Skip generic memes or ads.
2. Extract key facts: College Name, Event/Exam Title, Registration Deadline/Dates, Eligibility, and Why it matters for students.
3. Rewrite into @news.nit_iit's editorial style.

OUTPUT FORMAT (Return valid JSON object only, no markdown formatting):
{{
  "selected_index": 1,  // The [1-based index] of the selected post from the list below
  "headline": "A detailed 2-line headline with emojis (Make it long enough to span exactly two lines, around 60-80 characters. E.g. 🚀 IIT Bombay Opens National Innovation Hackathon: Registration Closes This Week)",
  "bullets": [
    "• Registration Deadline: 25 July 2026",
    "• Open for all B.Tech, M.Tech & Ph.D. students",
    "• Total prize pool of 5 Lakhs with mentorship",
    "• Direct internship interview slots for winners",
    "• Apply online via the official institute portal"
  ],  // MUST provide exactly 4 to 5 bullet points
  "why_it_matters": "A great opportunity for students interested in innovation and problem-solving.",
  "caption": "Full Instagram caption text with CTAs and hashtags"
}}
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

    # Format posts for AI
    posts_text = []
    for i, p in enumerate(posts[:10]):
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

        save_path = "output/processed_ig_digest.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(digest_data, f, indent=2, ensure_ascii=False)

        print(f"  Successfully rewritten Digest: {digest_data.get('headline')}")
        return digest_data
    except Exception as e:
        print(f"❌ Error rewriting digest: {e}")
        return None


if __name__ == "__main__":
    rewrite_latest_digest()