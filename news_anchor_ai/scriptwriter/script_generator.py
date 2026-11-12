"""
news_anchor_ai/scriptwriter/script_generator.py
Uses Gemini API (google-genai SDK) to generate a concise 30–45 second
news broadcast script (70–90 words) tailored to Indian students & exams.
Strictly adheres to safety, factual accuracy, and high-impact journalism.
"""

import json
import re
from typing import Dict
from google import genai
from google.genai import types

from news_anchor_ai.config import GEMINI_API_KEY, BRAND_NAME, INSTAGRAM_ACCOUNT

SYSTEM_PROMPT = f"""
You are the lead prime-time news anchor and scriptwriter for 'News N. I. T., I. I. T.' (@news.nit_iit),
India's premier high-energy news network for engineering, college students, and national entrance exams (JEE, NEET, GATE, UPSC, CBSE).

Your mission is to convert an existing news post into a high-energy, fast-paced, interactive 30 to 45 second broadcast script.
Target spoken word count: exactly 75 to 90 words. Speaking speed is fast and engaging (~2.5 words per second).

CRITICAL PRONUNCIATION RULE:
- NEVER write or pronounce the channel name as 'Nit' or 'Iit'.
- ALWAYS spell it out letter-by-letter with hyphens: 'N-I-T, I-I-T' or 'N. I. T., I. I. T.'!
- When referring to institutes or the channel: write 'N-I-T' and 'I-I-T'.

BROADCAST STYLE & MODULATION:
- Do NOT sound like an automated robotic text-reader! Sound like a dynamic TV news presenter.
- Use vocal dynamics: high-energy opening hook, urgent alerts, and conversational clarity.
- Interactive delivery: Reference the visual document on screen directly ("Take a look right here on your screen...", "The official circular confirms...").

Structure:
1. INTRO (0-7s, ~15-20 words): Rapid-fire breaking news hook. High energy!
2. BODY (7-24s, ~35-45 words): Explains the key facts, dates, and official orders while referencing the visual document.
3. TAKEAWAY (24-34s, ~20-25 words): Direct, clear student advisory with urgency.
4. OUTRO (34-40s, ~10 words): "Follow News N-I-T, I-I-T for verified daily updates."

RULES:
- Zero fabricated facts. Use the real facts from the post.
- 100% student-safe, professional, and family-friendly.
- Output MUST be valid JSON only.
"""

def phonetic_normalize(text: str) -> str:
    """
    Enforces phonetic letter-by-letter pronunciation for TTS:
    NIT -> N-I-T
    IIT -> I-I-T
    """
    if not text:
        return ""
    # Replace common patterns case-insensitively
    text = re.sub(r'\bNEWS NIT IIT\b', 'News N-I-T, I-I-T', text, flags=re.IGNORECASE)
    text = re.sub(r'@news\.nit_iit', 'News N-I-T, I-I-T', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNIT\b', 'N-I-T', text)
    text = re.sub(r'\bIIT\b', 'I-I-T', text)
    text = re.sub(r'\bNTA\b', 'N-T-A', text)
    text = re.sub(r'\bUGC\b', 'U-G-C', text)
    text = re.sub(r'\bCBSE\b', 'C-B-S-E', text)
    return text

def generate_news_script(post_headline: str, post_caption: str) -> Dict:
    """
    Calls Gemini to generate a structured 30-45s news broadcast script.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment or config.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Original Headline: {post_headline}

Full News Post Text:
{post_caption[:1500]}

Generate the news broadcast script as a JSON object with these exact keys:
{{
  "headline": "Short bold on-screen headline (max 7 words)",
  "category": "Exam Alert / Admissions / Campus Update / Career",
  "intro_text": "Anchor intro lines (15-20 words)",
  "body_text": "News explanation over the visual card (35-45 words)",
  "takeaway_text": "Anchor return advice and key takeaway (20-25 words)",
  "outro_text": "Stay ahead with NEWS NIT IIT. Follow for verified daily updates.",
  "full_spoken_script": "Complete combined script (intro + body + takeaway + outro) for voice generation",
  "reel_caption": "Engaging Instagram Reel caption with summary bullet points and 10 relevant hashtags"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        text = response.text.strip()
        data = json.loads(text)
        
        # Ensure full_spoken_script is coherent and phonetically normalized
        if not data.get("full_spoken_script"):
            data["full_spoken_script"] = f"{data.get('intro_text', '')} {data.get('body_text', '')} {data.get('takeaway_text', '')} {data.get('outro_text', '')}".strip()
            
        data["full_spoken_script"] = phonetic_normalize(data["full_spoken_script"])
        words = data["full_spoken_script"].split()
        print(f"[Script Generator] Generated script with {len(words)} words (~{len(words)/2.2:.1f}s speech).")
        return data

    except Exception as e:
        print(f"[Script Generator] Gemini generation failed: {e}")
        # Robust fallback script
        clean_head = post_headline.strip()
        fallback_intro = f"Important news update from {BRAND_NAME}."
        fallback_body = f"Regarding {clean_head}, official notifications have confirmed key updates for candidates."
        fallback_takeaway = "Students are advised to review the details carefully and monitor official notification portals."
        fallback_outro = f"Follow {BRAND_NAME} for daily verified news."
        full = f"{fallback_intro} {fallback_body} {fallback_takeaway} {fallback_outro}"
        
        return {
            "headline": clean_head[:60],
            "category": "Student Alert",
            "intro_text": fallback_intro,
            "body_text": fallback_body,
            "takeaway_text": fallback_takeaway,
            "outro_text": fallback_outro,
            "full_spoken_script": full,
            "reel_caption": f"🚨 {clean_head}\n\nStay tuned with @news.nit_iit for verified student news.\n\n#news_nitiit #studentnews #examalert #collegeupdates"
        }
