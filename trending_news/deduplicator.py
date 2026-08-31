"""
trending_news/deduplicator.py
Multi-Level Duplicate News Detection Engine
Level 1: Post ID Check (Database)
Level 2: Fuzzy String / Headline Similarity
Level 3: AI Semantic & Event Clustering
"""

import json
from difflib import SequenceMatcher
from typing import List, Dict, Any
from .database import get_recent_headlines
from .config import TRENDING_GEMINI_API_KEY, GEMINI_MODEL

try:
    from google import genai
    from google.genai import types
    GENAI_NEW_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    GENAI_NEW_SDK = False


def calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculates SequenceMatcher similarity ratio between two strings (0.0 to 1.0)."""
    if not str1 or not str2:
        return 0.0
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    return SequenceMatcher(None, s1, s2).ratio()


def filter_level2_string_duplicates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Level 2 Duplicate Detection:
    Checks candidates against recent DB headlines and each other using fuzzy string matching.
    """
    db_recent = get_recent_headlines(days=7)
    db_headlines = [item.get("headline", "").lower() for item in db_recent if item.get("headline")]
    
    unique_candidates = []
    seen_headlines = set(db_headlines)
    
    for c in candidates:
        headline = (c.get("headline_extracted") or c.get("caption")[:80]).strip()
        headline_lower = headline.lower()
        
        # Check against existing database headlines
        is_dup = False
        for db_h in seen_headlines:
            sim = calculate_string_similarity(headline_lower, db_h)
            if sim > 0.65:
                print(f"  [Deduplicator Level 2] Skipping duplicate headline '{headline[:40]}...' (Similarity {sim:.2f} with '{db_h[:40]}...')")
                is_dup = True
                break
                
        if not is_dup:
            seen_headlines.add(headline_lower)
            unique_candidates.append(c)
            
    return unique_candidates


def cluster_level3_semantic_duplicates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Level 3 Duplicate Detection (AI Semantic Event Clustering):
    Prompts Gemini to identify and group candidate posts that describe the same underlying
    real-world story/event from different source accounts.
    Merges them into 1 canonical story with combined source references.
    """
    if len(candidates) <= 1:
        return candidates
        
    api_key = TRENDING_GEMINI_API_KEY
    if not api_key:
        print("  [Deduplicator Level 3] Warning: API key missing. Skipping semantic clustering.")
        return candidates
        
    posts_summary = []
    for idx, c in enumerate(candidates):
        headline = c.get("headline_extracted") or c.get("caption")[:80]
        posts_summary.append(f"[{idx+1}] Account: @{c.get('source_account')}\nHeadline: {headline}\nCaption: {c.get('caption')[:150]}")
        
    prompt = (
        "Analyze these candidate news posts from different Instagram accounts:\n\n"
        + "\n\n".join(posts_summary) + "\n\n"
        "TASK:\n"
        "1. Identify posts that refer to the SAME underlying news story or event.\n"
        "2. Group duplicate posts together.\n"
        "3. For each group, select the single best index (1-based).\n\n"
        "OUTPUT FORMAT (Return a valid JSON array of integers representing the unique indices to keep, e.g. [1, 3]):\n"
        "[1, 2]"
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
            
        indices_to_keep = json.loads(clean_text)
        if isinstance(indices_to_keep, list):
            clustered = []
            for i in indices_to_keep:
                if isinstance(i, int) and 1 <= i <= len(candidates):
                    clustered.append(candidates[i-1])
            if clustered:
                print(f"  [Deduplicator Level 3] AI semantic clustering reduced {len(candidates)} candidates down to {len(clustered)} distinct stories.")
                return clustered
    except Exception as e:
        print(f"  [Deduplicator Level 3 Notice] AI clustering skipped: {e}")
        
    return candidates


def deduplicate_lead_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Master deduplication pipeline running Level 2 and Level 3 checks."""
    print(f"  [Deduplicator] Starting deduplication pipeline on {len(candidates)} candidates...")
    l2_filtered = filter_level2_string_duplicates(candidates)
    l3_clustered = cluster_level3_semantic_duplicates(l2_filtered)
    return l3_clustered
