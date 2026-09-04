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


import re
import json

def sanitize_extracted_title(text: str) -> str:
    """Strips markdown headers (###), bullet numbers, and prompt template titles."""
    if not text:
        return ""
    clean = re.sub(r'^#+\s*', '', text)
    clean = re.sub(r'^\d+[\.\)]\s*', '', clean)
    clean = clean.replace("**", "").replace("*", "").strip()
    
    # Reject generic prompt template placeholders
    low = clean.lower()
    if "main headline" in low or "core event title" in low or "news update" in low or "news lead" in low:
        return ""
    return clean


def analyze_lead_multimodal(caption: str, image_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs multimodal analysis on both caption text and local image file.
    Extracts embedded image OCR text, event title, category, statistics, dates, key entities,
    and classifies whether the post is genuine news vs meme/joke/satire.
    """
    api_key = TRENDING_GEMINI_API_KEY
    if not api_key:
        print("  [ImageAnalyzer] Warning: TRENDING_GEMINI_API_KEY missing. Returning text fallback analysis.")
        first_line = sanitize_extracted_title(caption.split("\n")[0]) if caption else "National News Update"
        return {
            "is_real_news": True,
            "headline_extracted": first_line or "National News Update",
            "ocr_text": "",
            "category": "General",
            "key_facts": [caption[:200]] if caption else [],
            "verification_claims": []
        }
        
    prompt = (
        "You are a strict news editor analyzing an Instagram post for a student news platform (@news.nit_iit).\n"
        "Examine the post caption and image and evaluate:\n"
        "1. Is this post GENUINE, REAL NEWS (National, Politics, Education, Jobs, Economy, Technology, Science, Sports, Policy)?\n"
        "   Set is_real_news: false if this post is a meme, joke, relationship advice, fictional satire, comedy reel, or promotional ad.\n"
        "2. Extract a concise, factual headline title (no markdown headers '###', no emojis, no template text).\n"
        "3. Determine category (Politics, Education, Jobs, Economy, Tech, Science, Achievement, SocialIssue, Sports, HumanInterest).\n"
        "4. Extract key factual numbers, dates, locations, names.\n\n"
        "RETURN VALID JSON ONLY:\n"
        '{\n'
        '  "is_real_news": true,\n'
        '  "headline_extracted": "Union Cabinet Approves Landmark National Policy",\n'
        '  "category": "Politics",\n'
        '  "key_facts": ["Approved by Union Cabinet", "Focuses on AI and skill training"],\n'
        '  "verification_claims": []\n'
        '}\n\n'
        f"Caption:\n{caption}"
    )
    
    try:
        raw_result = ""
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
        first_line = sanitize_extracted_title(caption.split("\n")[0]) if caption else "National News Update"
        return {
            "is_real_news": True,
            "headline_extracted": first_line or "National News Update",
            "ocr_text": "",
            "category": "General",
            "key_facts": [caption[:200]] if caption else [],
            "verification_claims": []
        }


def parse_analysis_result(analysis_text: str, original_caption: str) -> Dict[str, Any]:
    """Parses raw JSON text response into structured dictionary."""
    clean_text = analysis_text.strip()
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_text:
        clean_text = clean_text.split("```")[1].split("```")[0].strip()
        
    try:
        data = json.loads(clean_text)
        headline = sanitize_extracted_title(data.get("headline_extracted", ""))
        if not headline:
            headline = sanitize_extracted_title(original_caption.split("\n")[0])
            
        return {
            "is_real_news": bool(data.get("is_real_news", True)),
            "headline_extracted": headline or "National News Update",
            "ocr_text": data.get("ocr_text", ""),
            "category": data.get("category", "General"),
            "key_facts": data.get("key_facts", [])[:5],
            "verification_claims": data.get("verification_claims", []),
            "full_analysis": analysis_text
        }
    except Exception:
        pass
        
    # Text fallback parsing
    headline = ""
    for line in analysis_text.split("\n"):
        line_s = line.strip()
        if any(k in line_s.lower() for k in ["headline", "title"]):
            extracted = line_s.split(":", 1)[-1].strip() if ":" in line_s else line_s
            headline = sanitize_extracted_title(extracted)
            if headline:
                break
                
    if not headline:
        headline = sanitize_extracted_title(original_caption.split("\n")[0])
        
    return {
        "is_real_news": True,
        "headline_extracted": headline or "National News Update",
        "ocr_text": "",
        "category": "General",
        "key_facts": [],
        "verification_claims": [],
        "full_analysis": analysis_text
    }
