"""
rank_news.py
Scores articles and guarantees a balanced 3-post selection:
1. Indian Politics & Government Bills/Protests
2. Student Education, Exams & Govt Jobs
3. Tech, AI & Innovation
"""

import json
import os
import time
import ai_client
import config

RANKING_PROMPT = """You are a news editor for an Indian student & Gen Z audience (@news.nit_iit).
Analyze the provided articles and assign a score (0-100) and a category bucket to each article.

CATEGORY BUCKETS:
1. "IndianPolitics": Indian national & state politics, BJP, Congress, party news, new Bills passed in Parliament, government policies, protests against government, Supreme Court verdicts, elections.
2. "StudentEducation": IIT/NIT updates, JEE/NEET/UPSC exam news, paper leak scandals, student protests, campus placements, Government job alerts (UPSC, SSC, Banking).
3. "TechInnovation": Artificial Intelligence, ISRO space launches, DRDO defense tech, Indian startup funding, tech updates.

SCORING RULES (0-100):
- Score > 80: High national importance, major political move, official job alert, or major exam update.
- Score < 40: Routine local crime, foreign news with no India connection.

OUTPUT FORMAT (Valid JSON Array of Objects only, no extra text):
[
  {
    "index": 0,
    "score": 92,
    "bucket": "IndianPolitics",
    "reason": "Major new bill passed in Parliament affecting citizens."
  },
  ...
]

Articles to evaluate:
"""


def rank_all():
    """Scores articles and selects 1 Indian Politics + 1 Student/Education + 1 Tech story."""
    raw_path = config.RAW_ARTICLES_PATH
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found. Run fetch_news.py first.")
        return []

    with open(raw_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    if not articles:
        print("No articles to rank.")
        return []

    print(f"Ranking {len(articles)} articles across Politics, Student & Tech buckets...")

    # Format articles for prompt
    formatted = []
    for i, a in enumerate(articles):
        title = a.get("title", "")
        desc = a.get("description", "")[:150]
        formatted.append(f"[{i}] {title}\nSummary: {desc}")

    prompt = RANKING_PROMPT + "\n\n".join(formatted[:30])

    try:
        response_text = ai_client.ask_ai(prompt)
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        scores_list = json.loads(clean_text)
    except Exception as e:
        print(f"AI ranking failed or returned invalid JSON: {e}")
        return articles[:3]

    # Map AI scores back to articles
    for item in scores_list:
        idx = item.get("index")
        if idx is not None and idx < len(articles):
            articles[idx]["score"] = item.get("score", 50)
            articles[idx]["bucket"] = item.get("bucket", "IndianPolitics")
            articles[idx]["reason"] = item.get("reason", "")

    # Group into Buckets
    buckets = {
        "IndianPolitics": [],
        "StudentEducation": [],
        "TechInnovation": [],
    }

    for a in articles:
        bucket = a.get("bucket", "StudentEducation")
        if bucket in buckets:
            buckets[bucket].append(a)
        else:
            buckets["StudentEducation"].append(a)

    # Sort each bucket by score
    for b in buckets:
        buckets[b].sort(key=lambda x: x.get("score", 0), reverse=True)

    # Select TOP 1 from each bucket for a balanced 3-post output
    selected_stories = []
    
    if buckets["IndianPolitics"]:
        selected_stories.append(buckets["IndianPolitics"][0])
    if buckets["StudentEducation"]:
        selected_stories.append(buckets["StudentEducation"][0])
    if buckets["TechInnovation"]:
        selected_stories.append(buckets["TechInnovation"][0])

    # Fallback if any bucket was missing
    if len(selected_stories) < 3:
        all_sorted = sorted(articles, key=lambda x: x.get("score", 0), reverse=True)
        for story in all_sorted:
            if story not in selected_stories:
                selected_stories.append(story)
            if len(selected_stories) == 3:
                break

    print(f"Selected {len(selected_stories)} stories (1 Politics + 1 Student + 1 Tech):")
    for s in selected_stories:
        print(f"  - [{s.get('bucket')}] Score: {s.get('score')} | {s.get('title')[:50]}")

    os.makedirs("output", exist_ok=True)
    with open(config.RANKED_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(selected_stories, f, indent=2, ensure_ascii=False)

    return selected_stories


if __name__ == "__main__":
    rank_all()
    