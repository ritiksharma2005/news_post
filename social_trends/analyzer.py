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


def is_india_relevant(story: Dict[str, Any]) -> bool:
    """
    Evaluates whether a candidate story is directly relevant to an Indian audience
    (Indian politics, student exams/issues, state/national events, Indian sports,
    entertainment, economy, or viral Indian social media trends).
    """
    title = story.get("title", "")
    selftext = story.get("selftext", "")
    platform = story.get("platform", "")
    
    # Fast heuristic checks for obvious India markers
    india_keywords = [
        "india", "indian", "delhi", "mumbai", "bihar", "upsc", "neet", "jee",
        "iit", "nit", "modi", "rahul", "parliament", "supreme court", "bjp",
        "congress", "rupee", "isro", "cricket", "bcci", "bollywood", "bengaluru",
        "hyderabad", "chennai", "kolkata", "punjab", "kerala", "gujarat", "maharashtra",
        "cabinet", "lok sabha", "rajya sabha", "high court", "rbi", "sebi", "svnit"
    ]
    combined_lower = f"{title} {selftext} {platform}".lower()
    if any(kw in combined_lower for kw in india_keywords):
        return True
        
    prompt = (
        "You are an AI editor filtering news for an Indian Telegram channel.\n"
        f"Platform: {platform}\n"
        f"Title: {title}\n"
        f"Context: {selftext[:300]}\n\n"
        "QUESTION: Is this story directly related to India or relevant to Indian viewers "
        "(e.g. Indian news, politics, students/exams, state events, Indian culture, sports, or viral Indian topics)?\n"
        "Respond ONLY with 'YES' or 'NO'."
    )
    
    try:
        ans = ai_client.ask_ai(prompt).strip().upper()
        if "YES" in ans:
            return True
        elif "NO" in ans:
            return False
    except Exception as e:
        print(f"  [Relevance Filter Notice] AI check fallback: {e}")
        
    return True


def analyze_and_format_trend(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes raw social post data and generates a structured Telegram text breakdown for an Indian audience.
    """
    title = story.get("title", "")
    selftext = story.get("selftext", "")
    platform = story.get("platform", "Social Media")
    source_url = story.get("source_url", "")
    
    prompt = (
        "You are an expert news editor formatting a Telegram news update specifically for an Indian audience.\n\n"
        f"Source Platform: {platform}\n"
        f"Post Title: {title}\n"
        f"Post Context/Body: {selftext}\n\n"
        "TASK:\n"
        "1. Write a punchy, engaging 1-line Headline summarizing the core Indian event, policy, student issue, or viral trend.\n"
        "2. Write a clear, factual breakdown of 2 to 3 sentences explaining 'What Happened' and 'Why It's Trending in India'.\n"
        "3. Highlight Indian context (e.g. relevant state, ministry, exam, city, or public impact).\n"
        "4. Keep language neutral, objective, highly readable, and engaging for Indian viewers. Do not invent unverified facts.\n\n"
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
    
    author = story.get("author", "")
    author_line = f"👤 Voice / Source: {author}\n" if author else ""
    
    # Format Telegram caption text
    telegram_caption = (
        f"🔥 {headline}\n\n"
        f"📌 What Happened & Why It's Trending in India:\n"
        f"{summary}\n\n"
        f"🌐 Platform: {platform}\n"
        f"{author_line}"
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
