"""
trending_news/image_analyzer.py
Gemini Multimodal Analysis Engine (Image OCR + Caption Fact Extraction)
"""

import os
from PIL import Image
from typing import Dict, Any, Optional
from .config import TRENDING_GEMINI_API_KEY, GEMINI_MODEL

# Try google.genai or google.generativeai wrapper
try:
    from google import genai
    from google.genai import types
    GENAI_NEW_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    GENAI_NEW_SDK = False


def analyze_lead_multimodal(caption: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs multimodal analysis on both caption text and local image file.
    Extracts embedded image OCR text, event title, category, statistics, dates, key entities,
    and verification claims.
    """
    api_key = TRENDING_GEMINI_API_KEY
    if not api_key:
        print("  [ImageAnalyzer] Warning: TRENDING_GEMINI_API_KEY missing. Returning text fallback analysis.")
        return {
            "headline_extracted": caption[:80] if caption else "News Update",
            "ocr_text": "",
            "category": "General",
            "key_facts": [caption[:200]] if caption else [],
            "verification_claims": []
        }
        
    prompt = (
        "Analyze this Instagram news post caption and image. Extract:\n"
        "1. Main Headline / Core Event Title\n"
        "2. Any text/numbers/tables embedded inside the image (OCR text)\n"
        "3. News Category (choose one: Politics, Education, Jobs, Economy, Technology, Science, Achievement, SocialIssue, Sports, HumanInterest)\n"
        "4. Key Facts (list of specific numbers, names, locations, dates)\n"
        "5. Specific claims that require verification\n\n"
        f"Caption:\n{caption}"
    )
    
    try:
        if GENAI_NEW_SDK:
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1"))
            contents = [prompt]
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                contents.append(img)
                
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents
            )
            raw_result = response.text
        else:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(GEMINI_MODEL)
            contents = [prompt]
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                contents.append(img)
                
            response = model.generate_content(contents)
            raw_result = response.text
            
        return parse_analysis_result(raw_result, caption)
    except Exception as e:
        print(f"  [ImageAnalyzer Error] Multimodal analysis failed: {e}")
        return {
            "headline_extracted": caption[:80] if caption else "News Lead",
            "ocr_text": "",
            "category": "General",
            "key_facts": [caption[:200]] if caption else [],
            "verification_claims": []
        }


def parse_analysis_result(analysis_text: str, original_caption: str) -> Dict[str, Any]:
    """Parses raw text response into structured dictionary."""
    lines = [l.strip() for l in analysis_text.split("\n") if l.strip()]
    
    headline = ""
    category = "General"
    key_facts = []
    claims = []
    ocr_text = ""
    
    for line in lines:
        if "headline" in line.lower() or "title" in line.lower():
            headline = line.split(":", 1)[-1].strip() if ":" in line else line
        elif "category" in line.lower():
            cat = line.split(":", 1)[-1].strip() if ":" in line else line
            if any(c in cat for c in ["Politics", "Education", "Jobs", "Economy", "Tech", "Science", "Achievement", "Social"]):
                category = cat
        elif line.startswith("-") or line.startswith("*"):
            key_facts.append(line.lstrip("-* ").strip())
            
    if not headline:
        headline = original_caption[:80].split("\n")[0]
        
    return {
        "headline_extracted": headline,
        "ocr_text": ocr_text,
        "category": category,
        "key_facts": key_facts[:5],
        "verification_claims": claims,
        "full_analysis": analysis_text
    }
