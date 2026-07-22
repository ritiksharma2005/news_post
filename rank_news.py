"""
rank_news.py
Ranks all fetched news articles into 3 Buckets:
- Bucket 1: IndianPolitics (BJP, Congress, Parliament, Supreme Court, Govt Bills)
- Bucket 2: StudentEducation (JEE, NEET, UPSC, GATE, IIT/NIT alerts, Placements)
- Bucket 3: TechInnovation (AI, ISRO, Startups, Technology)
"""

import json
import os
import ai_client
import config


RANKING_PROMPT = """You are a senior news editor for @news.nit_iit (targeting Indian college students & Gen Z).

Below is a list of candidate news articles fetched from top Indian news outlets:

{articles_text}

TASK: Select EXACTLY 3 top articles—one for each of the following 3 distinct buckets:

1. "IndianPolitics": MUST be a major Indian political or party story involving Union Govt, Parliament, BJP, Congress, Opposition, Supreme Court verdicts, Election Commission, or key national bills/protests.
2. "StudentEducation": MUST be a student-centric story (JEE, NEET, UPSC, GATE, IIT/NIT updates, paper leaks, campus placements, or exam alerts).
3. "TechInnovation": MUST be a technology or science story (AI developments, ISRO rocket launches, DRDO, Tech news, or Indian startup funding).

OUTPUT FORMAT (Return valid JSON array of 3 objects only, no markdown or extra text):
[
  {{
    "title": "exact title of selected article",
    "url": "url of article",
    "summary": "brief description",
    "source": "source name",
    "bucket": "IndianPolitics"
  }},
  {{
    "title": "exact title of selected article",
    "url": "url of article",
    "summary": "brief description",
    "source": "source name",
    "bucket": "StudentEducation"
  }},
  {{
    "title": "exact title of selected article",
    "url": "url of article",
    "summary": "brief description",
    "source": "source name",
    "bucket": "TechInnovation"
  }}
]
"""


def extract_json_array(text):
    """Resilient parser that extracts and loads first JSON array [ ... ] inside conversational text."""
    import re
    clean_text = text.strip()
    
    # Remove markdown code blocks if present
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0].strip()

    # Try direct parse
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # Extract using regex search for array boundaries [ ... ]
    match = re.search(r'\[\s*\{.*\}\s*\]', clean_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Try bracket boundaries search
    start = clean_text.find('[')
    end = clean_text.rfind(']')
    if start != -1 and end != -1:
        try:
            return json.loads(clean_text[start:end+1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract a valid JSON array from AI output.")


def load_raw_articles():
    paths = [
        getattr(config, "RAW_ARTICLES_PATH", "output/raw_articles.json"),
        "output/raw_news.json"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data:
                        return data
            except Exception:
                continue
    return []


def rank_all():
    articles = load_raw_articles()
    if not articles:
        print("  No raw news found to rank.")
        return []

    print(f"  Ranking {len(articles)} articles into 3 Buckets (Politics, Student, Tech)...")

    # Format articles list for AI
    articles_summary = []
    for i, a in enumerate(articles[:40]):
        title = a.get("title", "")
        summary = a.get("summary", a.get("description", ""))[:150]
        source = a.get("source", "News")
        url = a.get("url", a.get("link", ""))
        articles_summary.append(f"[{i+1}] Title: {title}\n    Source: {source}\n    Summary: {summary}\n    URL: {url}\n")

    articles_text = "\n".join(articles_summary)
    prompt = RANKING_PROMPT.format(articles_text=articles_text)

    try:
        response_text = ai_client.ask_ai(prompt)
        ranked_stories = extract_json_array(response_text)

        os.makedirs("output", exist_ok=True)
        save_path = getattr(config, "RANKED_ARTICLES_PATH", "output/ranked_articles.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(ranked_stories, f, indent=2, ensure_ascii=False)

        # Dual save for full compatibility
        with open("output/ranked_news.json", "w", encoding="utf-8") as f:
            json.dump(ranked_stories, f, indent=2, ensure_ascii=False)

        print(f"  Successfully ranked 3 stories into 3 Buckets:")
        for s in ranked_stories:
            print(f"   • [{s.get('bucket')}] {s.get('title')[:60]}")

        return ranked_stories
    except Exception as e:
        print(f"❌ Error ranking news: {e}")
        return []


if __name__ == "__main__":
    rank_all()
    