"""
rank_news_hindi.py
Classifies and ranks fetched raw Hindi news into 3 buckets:
- IndianPolitics
- StudentEducation
- TechInnovation
"""

import json
import os
import ai_client
import config

RANKING_PROMPT = """You are a senior news editor for @news.nit_iit (targeting Indian college students & Gen Z).

Below is a list of candidate Hindi news articles fetched from top Indian news outlets:

{articles_text}

TASK: Select EXACTLY 3 top articles—one for each of the following 3 distinct buckets:

1. "IndianPolitics": MUST be a major political news story focusing on Indian national politics, youth policies, political protests, parliament debates (BJP, Congress, leaders), or significant national political controversies.
2. "StudentEducation": MUST be a youth-centric or student controversy news item (e.g. paper leaks, student protests, college union clashes, campus placement controversies, viral student trends, or major policies affecting youth/teenagers). Avoid dry, official exam notices.
3. "TechInnovation": MUST be a viral technology, science, space (ISRO, DRDO), AI impact on jobs, or hot Indian startup funding news.

OUTPUT FORMAT (Return a valid JSON array of 3 objects only, no markdown formatting, no conversational text, no triple backticks):
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
    "source": "source name",
    "bucket": "TechInnovation"
  }}
]
"""


def extract_json_array(text):
    """Safely extracts JSON array from AI output."""
    import re
    clean_text = text.strip()
    
    # Remove markdown code blocks if present
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0].strip()

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
    p = "data/raw_hindi_news.json"
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def rank_all():
    articles = load_raw_articles()
    if not articles:
        print("No Hindi articles available to rank.")
        return []

    # Format articles for prompt
    formatted = []
    for i, a in enumerate(articles[:40]):  # Limit to top 40 to fit context windows
        formatted.append(f"[{i}] Source: {a['source']}\nTitle: {a['title']}\nURL: {a['url']}")
    
    articles_text = "\n\n".join(formatted)
    prompt = RANKING_PROMPT.format(articles_text=articles_text)

    print("AI Ranking Hindi articles...")
    try:
        response_text = ai_client.call_ai(prompt)
        selected = extract_json_array(response_text)
        
        # Validate that we got exactly 3 selections
        if not isinstance(selected, list) or len(selected) != 3:
            raise ValueError(f"AI returned {len(selected)} items instead of 3.")
            
        print("Successfully selected 3 top stories:")
        for s in selected:
            print(f"  [{s.get('bucket')}]: {s.get('title')[:60]}... ({s.get('source')})")
            
        # Save ranked stories
        os.makedirs("data", exist_ok=True)
        output_path = "data/ranked_hindi_news.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(selected, f, indent=2, ensure_ascii=False)
            
        print(f"Saved ranked Hindi stories to {output_path}")
        return selected
    except Exception as e:
        print(f"Ranking failed: {e}")
        return []


if __name__ == "__main__":
    rank_all()
