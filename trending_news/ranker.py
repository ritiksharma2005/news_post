"""
trending_news/ranker.py
6-Factor News Ranking Engine (0-100 Score)
Public Interest: 25% | Trending Potential: 20% | News Importance: 20%
Freshness: 15% | Indian Relevance: 10% | Student Relevance: 10%
"""

import json
from typing import List, Dict, Any
from .config import RANKING_WEIGHTS, MIN_QUALIFYING_SCORE, MAX_POSTERS_PER_RUN, TRENDING_GEMINI_API_KEY, GEMINI_MODEL

try:
    from google import genai
    from google.genai import types
    GENAI_NEW_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    GENAI_NEW_SDK = False


def calculate_algorithmic_score(lead: Dict[str, Any], analysis: Dict[str, Any]) -> float:
    """Calculates baseline heuristic score (0-100) based on categories and keywords."""
    category = (analysis.get("category") or lead.get("category") or "General").lower()
    caption = (lead.get("caption") or "").lower()
    
    # Priority sub-scores
    public_interest = 70.0
    trending_potential = 65.0
    news_importance = 70.0
    freshness = 90.0  # Freshly scraped lead
    indian_relevance = 95.0  # From Indian news sources
    student_relevance = 70.0
    
    # High student/youth interest boosters
    student_keywords = ["exam", "jee", "neet", "upsc", "iit", "nit", "scholarship", "job", "recruitment", "salary", "admission", "college", "university", "tech", "ai"]
    if any(k in caption for k in student_keywords) or any(k in category for k in ["education", "jobs", "tech"]):
        student_relevance += 20.0
        news_importance += 10.0
        
    # High national interest boosters
    national_keywords = ["government", "policy", "cabinet", "isro", "india", "supreme court", "economy", "gdp", "bill", "law"]
    if any(k in caption for k in national_keywords) or any(k in category for k in ["politics", "economy", "achievement"]):
        public_interest += 15.0
        news_importance += 15.0
        
    # Penalize low-value memes/gossip
    trash_keywords = ["meme", "gossip", "unverified", "sponsor", "ad ", "sale ", "discount", "follow for more"]
    if any(k in caption for k in trash_keywords):
        public_interest -= 40.0
        news_importance -= 40.0
        student_relevance -= 30.0
        
    # Weighted composite score calculation
    score = (
        (min(100.0, public_interest) * RANKING_WEIGHTS["public_interest"]) +
        (min(100.0, trending_potential) * RANKING_WEIGHTS["trending_potential"]) +
        (min(100.0, news_importance) * RANKING_WEIGHTS["news_importance"]) +
        (min(100.0, freshness) * RANKING_WEIGHTS["freshness"]) +
        (min(100.0, indian_relevance) * RANKING_WEIGHTS["indian_relevance"]) +
        (min(100.0, student_relevance) * RANKING_WEIGHTS["student_relevance"])
    )
    
    return round(max(0.0, min(100.0, score)), 2)


def evaluate_score_with_ai(lead: Dict[str, Any], analysis: Dict[str, Any]) -> float:
    """Invokes Gemini to evaluate an accurate news importance & relevance score (0-100)."""
    api_key = TRENDING_GEMINI_API_KEY
    if not api_key:
        return calculate_algorithmic_score(lead, analysis)
        
    headline = analysis.get("headline_extracted") or lead.get("caption", "")[:80]
    caption = lead.get("caption", "")[:300]
    
    prompt = (
        "Rate the overall news value and student relevance of this news story for an audience of Indian college students and young adults (@news.nit_iit).\n\n"
        f"Headline: {headline}\n"
        f"Caption Summary: {caption}\n\n"
        "Criteria:\n"
        "- Public Interest (25%)\n"
        "- Trending Potential (20%)\n"
        "- News Importance (20%)\n"
        "- Freshness (15%)\n"
        "- Indian Relevance (10%)\n"
        "- Student Relevance (10%)\n\n"
        "OUTPUT FORMAT (Return a JSON object with a single float field 'score' between 0 and 100):\n"
        '{"score": 88.5}'
    )
    
    try:
        if GENAI_NEW_SDK:
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1"))
            res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            clean_text = res.text.strip()
        else:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(GEMINI_MODEL)
            res = model.generate_content(prompt)
            clean_text = res.text.strip()
            
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(clean_text)
        if isinstance(data, dict) and "score" in data:
            return round(float(data["score"]), 2)
    except Exception:
        pass
        
    return calculate_algorithmic_score(lead, analysis)


def rank_and_select_top_stories(candidates: List[Dict[str, Any]], max_select: int = MAX_POSTERS_PER_RUN) -> List[Dict[str, Any]]:
    """
    Ranks candidate leads by news importance score (0-100) and selects up to max_select (Top 2) stories.
    """
    print(f"\n📊 [Ranker] Evaluating news importance scores for {len(candidates)} candidates...")
    
    scored_candidates = []
    for c in candidates:
        analysis = c.get("analysis", {})
        
        # Exclude unverified sensitive claims
        verification = c.get("verification", {})
        if verification.get("verification_status") == "unverified":
            print(f"  [Ranker Skip] Skipping unverified lead: '{c.get('source_post_id')}' ({verification.get('verification_notes')})")
            continue
            
        score = evaluate_score_with_ai(c, analysis)
        c["trend_score"] = score
        c["importance_score"] = score
        scored_candidates.append(c)
        print(f"  ⭐ Candidate '{c.get('source_post_id')}' (@{c.get('source_account')}) | Score: {score}/100")
        
    # Sort descending by score
    scored_candidates.sort(key=lambda x: x.get("trend_score", 0.0), reverse=True)
    
    selected_stories = scored_candidates[:max_select]
    print(f"\n🏆 [Ranker Selection Complete] Selected TOP {len(selected_stories)} stories for poster generation.")
    for i, story in enumerate(selected_stories):
        headline = story.get("analysis", {}).get("headline_extracted") or story.get("caption", "")[:60]
        print(f"  [{i+1}] Score {story.get('trend_score')}: {headline}")
        
    return selected_stories
