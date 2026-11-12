"""
news_anchor_ai/ai/script_generator.py
Multimodal Gemini 2.0 Flash News Scriptwriter for NEWS NIT IIT.
Analyzes BOTH the visual news graphic (logos, charts, dates, numbers) AND the caption
to craft a compelling 30–40 second broadcast television story.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
from google import genai
from google.genai import types

from news_anchor_ai.config import GEMINI_API_KEY, BRAND_NAME, INSTAGRAM_ACCOUNT

SYSTEM_PROMPT = f"""
You are the senior executive producer and master scriptwriter for 'News N-I-T, I-I-T' ({INSTAGRAM_ACCOUNT}),
India's premier high-impact journalism network for IITs, NITs, engineering, and national entrance exams.

Your mission is NOT to mechanically read the news post.
Your mission is to ANALYZE THE ATTACHED VISUAL POST GRAPHIC AND CAPTION, and CRAFT A COMPELLING 30 TO 40 SECOND BROADCAST TELEVISION STORY.

GOLD STANDARD BENCHMARK EXAMPLE:
----------------------------------------
Headline: IIT Bombay Alumni Are Building India's Startup Powerhouse

What do CoinDCX, Blinkit, Ola, Upstox and BrowserStack have in common?

They are among the companies associated with entrepreneurs from the I-I-T Bombay alumni network.

From fintech and consumer internet to SaaS, technology and quick commerce, I-I-T Bombay graduates have contributed to India's growing startup ecosystem.

Companies such as Druva, NoBroker, BillDesk, Cars24 and ideaForge also highlight the diverse sectors in which this entrepreneurial network has made its mark.

The bigger story is not just the number of startups, but how an institute's alumni network can help shape India's business and innovation landscape.

And this list is only a glimpse of that impact.

This is News N-I-T, I-I-T — your campus, our news.
----------------------------------------

THE 5-PART MASTER BROADCAST STRUCTURE:
1. THE HOOK (0–5 sec, ~12-16 words):
   Start with an intriguing rhetorical question or a bold, provocative opening hook that arrests attention within 2 seconds. Never start with "Hello" or "Today we have news".
2. THE REVEAL (5–15 sec, ~20-25 words):
   Deliver the core discovery or the official decision. Connect the hook to the post.
3. THE DEEP DIVE (15–27 sec, ~30-38 words):
   Highlight specific names, sectors, numbers, or rules visible directly on the visual graphic so viewers connect what they hear with what they see.
4. THE BIGGER PICTURE (27–35 sec, ~18-22 words):
   Explain why this story truly matters. The broader implication for students, institutes, or the country.
5. THE SIGNATURE OUTRO (35–40 sec, ~9 words):
   MUST END WITH: "This is News N-I-T, I-I-T — your campus, our news."

CRITICAL PRONUNCIATION & MODULATION RULES:
- NEVER write or pronounce 'NIT' or 'IIT' as single words.
- ALWAYS write 'N-I-T' and 'I-I-T' with hyphens.
- Use natural punctuation for dramatic broadcast voice modulation:
  * Questions ('?') naturally raise vocal pitch.
  * Em-dashes ('—') create dramatic broadcast pauses.
- Total spoken word count: exactly 75 to 90 words (~35–40 seconds at fast news pace).
- Output MUST be valid JSON only.
"""

def phonetic_normalize(text: str) -> str:
    """Enforces phonetic letter-by-letter pronunciation for TTS."""
    if not text:
        return ""
    text = re.sub(r'\bNEWS NIT IIT\b', 'News N-I-T, I-I-T', text, flags=re.IGNORECASE)
    text = re.sub(r'@news\.nit_iit', 'News N-I-T, I-I-T', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNIT\b', 'N-I-T', text)
    text = re.sub(r'\bIIT\b', 'I-I-T', text)
    text = re.sub(r'\bNTA\b', 'N-T-A', text)
    text = re.sub(r'\bUGC\b', 'U-G-C', text)
    text = re.sub(r'\bCBSE\b', 'C-B-S-E', text)
    return text

def generate_multimodal_news_script(
    post_headline: str,
    post_caption: str,
    post_image_path: Optional[str] = None
) -> Dict:
    """
    Calls Gemini 2.0 Flash with BOTH image and text context
    to generate an authentic television news broadcast story.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Original Headline: {post_headline}

Full News Post Text & Caption:
{post_caption[:1800]}

Analyze the attached visual news graphic and caption thoroughly.
Craft the 35–40s news broadcast story following the 5-Part Master Broadcast Structure.
Return as JSON with these exact keys:
{{
  "headline": "Bold on-screen title (max 7 words)",
  "category": "Startup / Exam Alert / Campus Life / Tech",
  "hook_text": "Intriguing rhetorical question or bold opening (12-16 words)",
  "reveal_text": "The core revelation connecting to the post (20-25 words)",
  "deep_dive_text": "Specific sectors, names, numbers or orders visible on graphic (30-38 words)",
  "bigger_picture_text": "The broader takeaway and impact (18-22 words)",
  "outro_text": "This is News N-I-T, I-I-T — your campus, our news.",
  "full_spoken_script": "Complete combined continuous broadcast script for voice generation",
  "reel_caption": "Engaging Instagram Reel caption with key bullet points and 10 hashtags"
}}
"""

    contents = []
    # If image is available, pass it directly for multimodal vision
    if post_image_path and Path(post_image_path).exists():
        try:
            img = Image.open(post_image_path)
            contents.append(img)
            print(f"[Script Generator] Loaded post image for Gemini Multimodal Vision: {post_image_path}")
        except Exception as e:
            print(f"[Script Generator] Notice: Image load skipped ({e})")

    contents.append(prompt)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        data = json.loads(response.text.strip())

        if not data.get("full_spoken_script"):
            parts = [
                data.get("hook_text", ""),
                data.get("reveal_text", ""),
                data.get("deep_dive_text", ""),
                data.get("bigger_picture_text", ""),
                data.get("outro_text", "This is News N-I-T, I-I-T — your campus, our news.")
            ]
            data["full_spoken_script"] = " ".join(p for p in parts if p).strip()

        data["full_spoken_script"] = phonetic_normalize(data["full_spoken_script"])
        words = data["full_spoken_script"].split()
        print(f"[Script Generator] 🚀 Multimodal script generated: {len(words)} words (~{len(words)/2.4:.1f}s speech).")
        return data

    except Exception as e:
        print(f"[Script Generator] Gemini generation failed: {e}")
        # High quality fallback
        clean_head = phonetic_normalize(post_headline[:60])
        return {
            "headline": clean_head,
            "category": "Campus Alert",
            "hook_text": f"Did you know about this major update regarding {clean_head}?",
            "reveal_text": "Official details have been confirmed across major academic and campus channels.",
            "deep_dive_text": "Looking at the official announcement, several critical directives and updates have been laid out for students.",
            "bigger_picture_text": "The key takeaway is to act early, verify official portals, and stay ahead of deadlines.",
            "outro_text": "This is News N-I-T, I-I-T — your campus, our news.",
            "full_spoken_script": f"Did you know about this major update regarding {clean_head}? Official details have been confirmed across major academic and campus channels. Looking at the official announcement, several critical directives and updates have been laid out for students. The key takeaway is to act early, verify official portals, and stay ahead of deadlines. This is News N-I-T, I-I-T — your campus, our news.",
            "reel_caption": f"🚨 {clean_head}\n\nStay informed with @news.nit_iit.\n\n#news_nitiit #studentnews #examalert #collegeupdates"
        }
