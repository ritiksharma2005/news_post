"""
social_trends/analyzer.py
AI News Analyzer & Text Summary Formatter for Telegram
Rewrites raw Reddit/Twitter post data into high-impact Telegram captions.
"""

import sys
import os
from typing import Dict, Any, List

# Add parent directory for ai_client import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import ai_client
from trending_news.hashtag_generator import generate_news_hashtags


def analyze_and_format_trend(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes raw social post data and generates a structured Telegram text breakdown.
    """
    title = story.get("title", "")
    selftext = story.get("selftext", "")
    platform = story.get("platform", "Social Media")
    source_url = story.get("source_url", "")
    
    prompt = (
        "You are an expert news editor formatting a Telegram news update for an Indian audience.\n\n"
        f"Source Platform: {platform}\n"
        f"Post Title: {title}\n"
        f"Post Context/Body: {selftext}\n\n"
        "TASK:\n"
        "1. Write a punchy, engaging 1-line Headline summarizing the core event or trend.\n"
        "2. Write a clear, factual breakdown of 2 to 3 sentences explaining 'What Happened' and 'Why It's Trending'.\n"
        "3. Keep language neutral, objective, highly readable, and engaging. Do not invent unverified facts.\n\n"
        "OUTPUT FORMAT (Return a valid JSON object with fields 'headline' and 'summary'):\n"
        '{"headline": "Bihar Cabinet Approves Major Infrastructure Package", "summary": "The Bihar State Cabinet approved a ₹4,500 Crore package for highway expansion and flood control infrastructure. The decision aims to improve interstate connectivity and mitigate seasonal river surges across northern districts."}'
    )
    
    try:
        response_text = ai_client.ask_ai(prompt)
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        import json
        parsed = json.loads(clean_text)
        headline = parsed.get("headline", title)
        summary = parsed.get("summary", selftext or title)
    except Exception as e:
        print(f"  [Analyzer Notice] AI rewrite fallback: {e}")
        headline = title
        summary = selftext or title
        
    # Generate dynamic mandatory & college/topic hashtags
    hashtags = generate_news_hashtags(headline, summary)
    
    # Format Telegram caption text
    telegram_caption = (
        f"🔥 {headline}\n\n"
        f"📌 What Happened & Why It's Trending:\n"
        f"{summary}\n\n"
        f"🌐 Platform: {platform}\n"
        f"🔗 Source Post: {source_url}\n\n"
        f"💬 Share your thoughts in the comments below! 👇\n\n"
        f"{hashtags}"
    )
    
    return {
        "headline": headline,
        "summary": summary,
        "caption": telegram_caption,
        "hashtags": hashtags
    }
