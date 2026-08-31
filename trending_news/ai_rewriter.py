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
Rewrite this lead into an ORIGINAL, high-impact news editorial for @news.nit_iit. Do NOT copy the original caption text verbatim.
Formulate a clear visual design concept and select the best poster layout type:
- LAYOUT_A: Breaking / National / Politics / Social Issue (High Contrast, Bold Header)
- LAYOUT_B: Achievement / Education / Student / Human Story (Clean, Modern)
- LAYOUT_C: Data / Economy / Salary / Statistics (Large Number / Metric Callout)
- LAYOUT_D: Sports / Culture / Entertainment (Full-Bleed Visual)

CRITICAL RULES:
1. Headline MUST be 5 to 14 words.
2. Headline MUST NOT contain any emojis.
3. Summary MUST be 1 to 2 concise sentences.
4. Language must be modern, fast, and easy for Indian students to understand.

OUTPUT FORMAT (Return a valid JSON object ONLY with no markdown formatting):
{{
  "headline": "Cabinet Clears Landmark Education Framework to Boost AI and Skill Training",
  "subheadline": "New National Initiative Opens Industry Internships for College Students Across India",
  "summary": "The Union Cabinet has approved a major national education update aimed at integrating artificial intelligence and practical skill modules into undergraduate curricula. This decision is expected to benefit millions of students across central and state universities.",
  "key_facts": [
    "Approved by the Union Cabinet for national implementation",
    "Focuses on AI, data science, and hands-on skill training",
    "Creates direct industry internship credits for B.Tech and degree students"
  ],
  "why_it_matters": "This reform significantly increases industry exposure and career readiness for Indian graduates.",
  "category": "Education",
  "layout_type": "LAYOUT_A",
  "metric_callout": "₹15,000 Cr",
  "visual_concept": "Editorial 3D style illustration of Indian university students holding digital laptops and AI certificates with modern geometry background."
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
            print(f"  ✨ AI Editorial Package compiled: '{editorial_data.get('headline', '')[:50]}...'")
            return editorial_data
        except Exception as pe:
            print(f"  [JSON Parse Error] {pe}. Raw: {response_text[:100]}")
            
    # Reliable fallback dictionary
    headline = story.get("analysis", {}).get("headline_extracted") or caption[:80].split("\n")[0]
    return {
        "headline": headline.replace("🚀", "").replace("🔥", "").strip(),
        "subheadline": "Major Update for Indian Students & Young Professionals",
        "summary": caption[:220].strip() + "...",
        "key_facts": [caption[:100]],
        "why_it_matters": "Important national news development.",
        "category": story.get("analysis", {}).get("category", "Education"),
        "layout_type": "LAYOUT_A",
        "metric_callout": "",
        "visual_concept": "Modern 3D digital education illustration"
    }
