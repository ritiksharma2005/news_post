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


def calculate_word_jaccard(str1: str, str2: str) -> float:
    """Calculates Jaccard similarity of significant words (length >= 4) between two texts."""
    if not str1 or not str2:
        return 0.0
    w1 = set(w.lower().strip(".,!?:;\"'()[]") for w in str1.split() if len(w.strip(".,!?:;\"'()[]")) >= 4)
    w2 = set(w.lower().strip(".,!?:;\"'()[]") for w in str2.split() if len(w.strip(".,!?:;\"'()[]")) >= 4)
    if not w1 or not w2:
        return 0.0
    return len(w1.intersection(w2)) / len(w1.union(w2))


def filter_level2_string_duplicates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Level 2 Duplicate Detection:
    Checks candidates against recent DB headlines/summaries/captions and each other using fuzzy string matching & Jaccard overlap.
    """
    db_recent = get_recent_headlines(days=30)
    db_texts = []
    for item in db_recent:
        if item.get("headline"):
            db_texts.append(item["headline"].lower())
        if item.get("summary"):
            db_texts.append(item["summary"].lower())
        if item.get("caption"):
            db_texts.append(item["caption"].lower())
            
    unique_candidates = []
    seen_candidate_texts = list(db_texts)
    
    for c in candidates:
        headline = (c.get("headline_extracted") or c.get("caption")[:120]).strip()
        caption = (c.get("caption") or "").strip()
        combined_text = f"{headline} {caption}".lower()
        
        is_dup = False
        for ref_text in seen_candidate_texts:
            seq_sim = calculate_string_similarity(combined_text[:150], ref_text[:150])
            jaccard_sim = calculate_word_jaccard(combined_text, ref_text)
            
            if seq_sim > 0.50 or jaccard_sim > 0.35:
                print(f"  [Deduplicator Level 2] Skipping duplicate candidate '{headline[:40]}...' (SeqSim {seq_sim:.2f}, Jaccard {jaccard_sim:.2f})")
                is_dup = True
                break
                
        if not is_dup:
            seen_candidate_texts.append(combined_text)
            unique_candidates.append(c)
            
    return unique_candidates


def cluster_level3_semantic_duplicates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Level 3 Duplicate Detection (AI Semantic Event Clustering):
    Prompts Gemini to identify and group candidate posts that describe the same underlying
    real-world story/event from different source accounts or against recent database history.
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
        posts_summary.append(f"[{idx+1}] Account: @{c.get('source_account')}\nHeadline: {headline}\nCaption: {c.get('caption')[:200]}")
        
    db_recent = get_recent_headlines(days=7)
    db_history_snippets = [f"- {item.get('headline') or item.get('caption')[:80]}" for item in db_recent[:20] if item.get("headline") or item.get("caption")]
    db_context = "\n".join(db_history_snippets)
    
    prompt = (
        "You are an expert news editor enforcing strict 100% uniqueness for Instagram news stories.\n\n"
        "RECENTLY PUBLISHED STORIES (Do NOT repeat any event matching these):\n"
        f"{db_context}\n\n"
        "CANDIDATE NEWS POSTS TO EVALUATE:\n"
        + "\n\n".join(posts_summary) + "\n\n"
        "TASK:\n"
        "1. Identify any candidates that describe the SAME event as recently published stories or each other.\n"
        "2. Keep only unique, distinct stories that represent brand new news events.\n"
        "3. Return a valid JSON array of 1-based indices for the unique candidate posts to keep.\n\n"
        "OUTPUT FORMAT (JSON array of integers, e.g. [1, 2]):\n"
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
                print(f"  [Deduplicator Level 3] AI semantic clustering filtered candidate list down to {len(clustered)} 100% unique stories.")
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
