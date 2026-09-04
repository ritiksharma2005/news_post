"""
trending_news/ai_rewriter.py
AI News Rewriter Engine (Gemini 3.6 Flash Primary, Groq Fallback)
"""

import json
import requests
from typing import Dict, Any, Optional
from .config import TRENDING_GEMINI_API_KEY, TRENDING_GROQ_API_KEY, GEMINI_MODEL

try:
    from google import genai
    from google.genai import types
    GENAI_NEW_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    GENAI_NEW_SDK = False


REWRITE_PROMPT_TEMPLATE = """You are the Senior Editor for @news.nit_iit, a modern digital news brand for Indian students and young adults.
Below is a raw news lead scraped from Instagram:

Source Account: @{source_account}
Raw Caption:
{caption}

Multimodal Analysis:
{analysis_summary}

TASK:
Rewrite this lead into an ORIGINAL, high-impact news editorial for @news.nit_iit.

CRITICAL RULES:
1. Headline MUST be a SHORT, PUNCHY BOLD TITLE (strictly 5 to 10 words max!).
   Example: "Grand Mufti Remarks Spark Major National Controversy"
   Do NOT output long multi-clause sentences as headlines!
2. Identify 2 to 4 key visual words from the headline to set as "highlight_text" (e.g. "National Controversy" or "Grand Mufti").
3. Headline MUST NOT contain emojis, markdown symbols ('###', '**'), or numbered prefixes.
4. Summary MUST be 1 to 2 short sentences providing distinct background context. Do NOT repeat the headline text verbatim!

OUTPUT FORMAT (Return a valid JSON object ONLY with no markdown formatting):
{{
  "headline": "Grand Mufti Remarks Spark Major National Controversy",
  "highlight_text": "National Controversy",
  "header_label": "THE LATEST",
  "subheadline": "Controversial Statement Triggers Widespread Public Debate",
  "summary": "Prominent religious figure Sheikh Abubakr Ahmad faced intense backlash following public remarks regarding social roles.",
  "category": "NATIONAL",
  "layout_type": "LAYOUT_A",
  "metric_callout": "",
  "visual_concept": "Modern news illustration"
}}
"""


def rewrite_with_groq(prompt: str) -> Optional[str]:
    """Fallback rewriter engine using Groq API."""
    api_key = TRENDING_GROQ_API_KEY
    if not api_key:
        return None
        
    print("  [Groq Fallback] Attempting AI rewriting via Groq API...")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [Groq Error] {e}")
        
    return None


import re

def sanitize_headline(text: str) -> str:
    """Strips markdown headers (###), asterisks, bullet numbers, and prompt placeholders from headlines."""
    if not text:
        return ""
    clean = re.sub(r'^#+\s*', '', text)
    clean = re.sub(r'^\d+[\.\)]\s*', '', clean)
    clean = clean.replace("**", "").replace("*", "").replace("`", "").strip()
    
    # Reject generic prompt template placeholders
    low = clean.lower()
    if "main headline" in low or "core event title" in low or "news update" in low or "news lead" in low:
        return ""
    return clean


def rewrite_story_editorial(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invokes Gemini (or Groq fallback) to rewrite a lead story into structured editorial JSON.
    """
    caption = story.get("caption", "")
    source_account = story.get("source_account", "news_lead")
    analysis = story.get("analysis", {})
    
    analysis_str = f"Category: {analysis.get('category')}\nHeadline: {analysis.get('headline_extracted')}\nKey Facts: {', '.join(analysis.get('key_facts', []))}"
    prompt = REWRITE_PROMPT_TEMPLATE.format(source_account=source_account, caption=caption, analysis_summary=analysis_str)
    
    api_key = TRENDING_GEMINI_API_KEY
    response_text = ""
    
    if api_key:
        try:
            if GENAI_NEW_SDK:
                client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1"))
                res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
                response_text = res.text
            else:
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel(GEMINI_MODEL)
                res = model.generate_content(prompt)
                response_text = res.text
        except Exception as e:
            print(f"  [Gemini Rewrite Notice] Primary engine failed: {e}. Trying Groq fallback...")
            response_text = rewrite_with_groq(prompt) or ""
    else:
        response_text = rewrite_with_groq(prompt) or ""
        
    if response_text:
        try:
            clean_json = response_text.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
                
            editorial_data = json.loads(clean_json)
            
            # Sanitize headline to ensure zero markdown symbols ('###', '**') or placeholders
            raw_hl = editorial_data.get("headline", "")
            clean_hl = sanitize_headline(raw_hl)
            if not clean_hl:
                clean_hl = sanitize_headline(story.get("analysis", {}).get("headline_extracted", ""))
            if not clean_hl:
                clean_hl = sanitize_headline(caption.split("\n")[0]) or "National News Update"
                
            editorial_data["headline"] = clean_hl
            print(f"  ✨ AI Editorial Package compiled: '{clean_hl[:50]}...'")
            return editorial_data
        except Exception as pe:
            print(f"  [JSON Parse Error] {pe}. Raw: {response_text[:100]}")
            
    # Reliable fallback dictionary
    headline = sanitize_headline(story.get("analysis", {}).get("headline_extracted", "")) or sanitize_headline(caption.split("\n")[0]) or "National News Update"
    words = headline.split()
    highlight = " ".join(words[:2]) if len(words) >= 2 else headline
    return {
        "headline": headline,
        "highlight_text": highlight,
        "header_label": "THE LATEST",
        "subheadline": "Major Update for Indian Students & Young Professionals",
        "summary": re.sub(r'[\U00010000-\U0010ffff]', '', caption[:160]).strip() + "...",
        "key_facts": [caption[:100]],
        "why_it_matters": "Important national news development.",
        "category": story.get("analysis", {}).get("category", "EDUCATION").upper(),
        "layout_type": "LAYOUT_A",
        "metric_callout": "",
        "visual_concept": "Modern 3D digital education illustration"
    }
