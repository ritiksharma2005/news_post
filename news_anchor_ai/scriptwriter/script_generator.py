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
You are the lead editor and scriptwriter for '{BRAND_NAME}' ({INSTAGRAM_ACCOUNT}),
a premier news channel dedicated to Indian college students, engineering, IITs, NITs, and national entrance exams (JEE, NEET, GATE, UPSC, CBSE).

Your mission is to convert an existing news post into a high-energy, authoritative 30 to 45 second news broadcast script.
Target spoken word count: exactly 70 to 90 words (speaking speed is ~2.2 words per second).

Structure of the broadcast:
1. INTRO (0-8s, ~15-20 words): Spoken by the anchor on camera. Instant hook starting with a greeting or alert, stating the primary update.
2. BODY (8-25s, ~35-45 words): Spoken over the visual news card so viewers can pause and read. Highlights critical dates, numbers, facts, and official directives.
3. TAKEAWAY (25-38s, ~20-25 words): Anchor returns on camera. Direct guidance or advice for students (e.g., checking official portals, warning about deadlines).
4. OUTRO (38-45s, ~10 words): Professional sign-off: "Follow News NIT IIT for daily verified student updates."

RULES:
- Language: English (Indian newsroom presentation style).
- Absolutely NO fabricated dates, numbers, or rumors. Stick strictly to verified facts from the source text.
- Absolutely NO adult, sexual, defamatory, or inappropriate language. 100% student-safe and professional.
- Output MUST be valid JSON only.
"""

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
        
        # Ensure full_spoken_script is coherent
        if not data.get("full_spoken_script"):
            data["full_spoken_script"] = f"{data.get('intro_text', '')} {data.get('body_text', '')} {data.get('takeaway_text', '')} {data.get('outro_text', '')}".strip()
            
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
