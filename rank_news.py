"""
rank_news.py
Sends the articles fetched by fetch_news.py to Gemini for scoring against
your priority tiers, then keeps the top N highest-scoring stories.

Run directly to test: python rank_news.py
(Requires output/raw_articles.json to already exist — run fetch_news.py first)
"""

import json
import os
import time

from google import genai

import config


RANKING_PROMPT = """You are a news editor for an Indian audience. You will be given a list of news headlines with short descriptions, each with an index number.

CRITICAL GLOBAL RULE (applies before any tier scoring): every story must have an explicit, concrete connection to India — it is about India, affects India, or involves Indian people/teams/institutions. If a story has NO India connection at all (e.g. a UK-only school policy with no India mention, a UK cabinet reshuffle, a golf tournament with no Indian players, a UK-only crime story), score it below 15 regardless of how well it matches a tier's topic. Matching a tier's subject (education, sport, politics) is NOT enough by itself — the India connection is mandatory except where a tier explicitly says otherwise.

Score each one from 0-100 based on this priority system:

TIER 1 (85-100) — HIGHEST PRIORITY, TWO EQUAL CATEGORIES:
  (1A) Major India national news — top political, economic, or social developments directly about India (economy, government, national events).
  (1B) IIT/NIT/engineering/medical college and student news — exam paper leaks, JEE/NEET results or controversies, admission scandals, engineering/medical college announcements, campus issues at Indian technical/medical institutions. This category is EQUALLY important as national news, not secondary to it.

TIER 2 (45-60) — LOW PRIORITY: International news with a clear indirect impact on India (oil prices, currency, trade, global conflicts affecting Indian interests). IMPORTANT: this tier's score ceiling (60) is deliberately kept BELOW Tier 1's floor (85), so international news can never outrank India national or student/college news, no matter how large or fast-developing the international story is. International news only fills top-5 slots when there simply aren't enough Tier 1 stories available that day.
  - QUALIFIES (up to 60): Iran-Israel tensions affecting Strait of Hormuz oil shipments, a US Federal Reserve decision affecting the rupee.
  - DOES NOT QUALIFY (below 30): A country's internal cabinet reshuffle, leadership purge, or war with no explained effect on India's trade/energy/citizens/diplomacy.

TIER 3 (60-80): General education and social-issue news about India specifically (broader than Tier 1B — school policy, non-technical college news, social programs). Other countries' equivalent news does not qualify.

TIER 4 (55-75): Social issues and new government policy announcements about India specifically (central or state level). Other countries' social policy does not qualify.

TIER 5 (50-70): Sports involving Indian teams/athletes specifically. A global sporting event with no Indian participant or angle does not qualify — score below 20.

TIER 6 (40-60): Indian politics and national issues not already covered above — include but weight lowest among the core categories. Other countries' domestic politics does not qualify.

BONUS: Add +10 to any story's score (cap at 100) if it represents an "Indian pride" moment — an Indian individual, team, or achievement gaining recognition, winning, or excelling globally, regardless of which tier it falls in.

CRITICAL DEDUPLICATION RULE: group articles by the underlying real-world event or crisis they're about, not just by literal wording. If multiple articles are all about the same ongoing situation — even if each covers a different specific angle, fact, or development within it — treat them as ONE event cluster. Within each cluster, score only the single best/most comprehensive article normally; give every other article in that same cluster a score of 5 with reason "same event as index X" (replace X with the index of the one you kept).
  - EXAMPLE OF WHAT COUNTS AS ONE CLUSTER: "Iran stages military drills near Strait of Hormuz", "Tehran to impose new transit fees on ships crossing Hormuz", "Europe considers toll system for Hormuz shipping", "Tensions at Hormuz reach boiling point after US strike" — these are four different specific facts, but they are ALL part of the SAME ongoing Iran/Hormuz crisis. Only ONE of these should score highly; the other three get score 5.
  - Do NOT let a single ongoing crisis or story arc occupy more than one top-scoring slot, no matter how many distinct facts or angles different outlets publish about it. A fast-developing story generating many articles is exactly the case this rule exists for.
  - Articles about genuinely different events (even in the same broad region/topic) are NOT duplicates — e.g. an Iran/Hormuz story and a separate India-China border story are different clusters.

Also merge literal duplicates: if two or more articles clearly describe the same specific fact worded differently by different outlets, only score the best-written one and give the others a score of 5 with reason "duplicate".

Ignore or score below 15: celebrity gossip with no social relevance, international stories with no India angle, pure entertainment news, obituaries, and any story (regardless of topic) with no explicit India connection. Remember: international news (Tier 2) is your LAST priority — India national news and IIT/NIT/student/exam news (Tier 1) always come first.

Return ONLY a JSON object in this exact format, nothing else, no markdown fences:
{
  "results": [
    {"index": 0, "tier": "1", "score": 95, "reason": "short phrase"}
  ]
}

Here are the articles:
"""


def build_prompt(articles):
    """Build the full prompt text with numbered articles."""
    lines = [RANKING_PROMPT]
    for i, article in enumerate(articles):
        lines.append(
            f"\n[{i}] Title: {article['title']}\n"
            f"    Description: {article.get('description', '')[:200]}"
        )
    return "\n".join(lines)


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
    """
    Call Gemini with retries + exponential backoff for transient errors
    (like a 503 'high demand' response). Raises the last error if all
    retries are exhausted.
    """
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
            print(f"  Gemini call failed (attempt {attempt}/{max_retries}): {e}")
            print(f"  Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


def rank_articles(articles):
    """Send articles to Gemini for scoring, return them sorted with scores attached."""
    if not articles:
        print("No articles to rank.")
        return []

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    prompt = build_prompt(articles)

    try:
        response = call_gemini_with_retry(client, prompt)
    except Exception as e:
        print(f"Gemini call failed after retries: {e}")
        return []

    try:
        parsed = parse_gemini_json(response.text)
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        print(f"Failed to parse Gemini response as JSON: {e}")
        print(f"Raw response: {response.text[:500]}")
        return []

    scored = []
    for result in parsed.get("results", []):
        idx = result.get("index")
        if idx is None or idx >= len(articles):
            continue
        article = dict(articles[idx])
        article["score"] = result.get("score", 0)
        article["tier"] = result.get("tier", "")
        article["reason"] = result.get("reason", "")
        scored.append(article)

    scored.sort(key=lambda a: a["score"], reverse=True)
    return scored


def rank_all():
    """Load raw articles, rank them, save the top N to disk."""
    with open(config.RAW_ARTICLES_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Ranking {len(articles)} articles...")
    scored = rank_articles(articles)

    print(f"\nAll scored stories (for debugging):")
    for story in scored:
        print(f"  [{story['score']}] ({story['tier']}) {story['title'][:70]}")

    top_stories = [a for a in scored if a["score"] > 0][:config.TOP_STORIES_COUNT]

    print(f"\nTop {len(top_stories)} stories:")
    for story in top_stories:
        print(f"  [{story['score']}] ({story['tier']}) {story['title']} — {story['reason']}")

    os.makedirs(os.path.dirname(config.RANKED_ARTICLES_PATH), exist_ok=True)
    with open(config.RANKED_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(top_stories, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {config.RANKED_ARTICLES_PATH}")
    return top_stories


if __name__ == "__main__":
    rank_all()
