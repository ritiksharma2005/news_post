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


def is_student_career_relevant(story: Dict[str, Any]) -> bool:
    """
    Evaluates whether a candidate story is directly relevant to Indian Students, Campus Affairs,
    Exams (JEE, NEET, GATE, UPSC, CUET), Higher Education Institutions (IIT, NIT, IIIT), or Career/Corporate Trends
    (Placements, Internships, Layoffs, Hiring, Company Policies).
    """
    title = story.get("title", "")
    selftext = story.get("selftext", "")
    platform = story.get("platform", "")
    
    # Priority subreddits targeting students & career are automatically relevant
    student_subreddits = ["jeeneetards", "cuetards", "btechtards", "developersindia", "indian_academia", "indianengineers", "upsc", "studentsphile"]
    if any(f"r/{sub}" in platform.lower() for sub in student_subreddits):
        return True
        
    student_career_keywords = [
        "student", "protest", "ragging", "suicide", "murder", "crime", "safety", "discrimination",
        "jee", "neet", "gate", "upsc", "cuet", "cat", "iit", "nit", "iiit", "college", "campus",
        "university", "du", "bhu", "jnu", "exam", "cutoff", "result", "paper leak", "scam",
        "placement", "hiring", "layoff", "firing", "internship", "vacancy", "salary", "package",
        "company", "career", "svnit", "bits", "recruitment", "engineer", "medical", "hostel"
    ]
    combined_lower = f"{title} {selftext} {platform}".lower()
    if any(kw in combined_lower for kw in student_career_keywords):
        return True
        
    prompt = (
        "You are an AI editor filtering news for an Indian Student, Campus & Career Telegram channel.\n"
        f"Platform: {platform}\n"
        f"Title: {title}\n"
        f"Context: {selftext[:300]}\n\n"
        "QUESTION: Is this story directly related to Indian students, campus issues (protests, safety, ragging, administration), "
        "exams (JEE, NEET, GATE, UPSC, CUET), colleges (IIT, NIT, universities), or career/corporate trends (placements, hiring, layoffs, internships)?\n"
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


def is_india_relevant(story: Dict[str, Any]) -> bool:
    """Backward compatibility alias calling is_student_career_relevant."""
    return is_student_career_relevant(story)


def analyze_and_format_trend(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes raw social post data and generates a structured Telegram text breakdown for an Indian student & career audience.
    """
    title = story.get("title", "")
    selftext = story.get("selftext", "")
    platform = story.get("platform", "Social Media")
    source_url = story.get("source_url", "")
    
    prompt = (
        "You are an expert news editor formatting a Telegram update specifically for Indian students, campus youth, and job seekers.\n\n"
        f"Source Platform: {platform}\n"
        f"Post Title: {title}\n"
        f"Post Context/Body: {selftext}\n\n"
        "TASK:\n"
        "1. Write a punchy, engaging 1-line Headline summarizing the core student issue, exam update, campus event, protest, or placement/career trend.\n"
        "2. Write a clear, factual breakdown of 3 to 4 lines explaining 'What Happened' and 'Why It Matters to Students & Career Aspirants in India'.\n"
        "3. Highlight specific campus/college names (e.g. IIT, NIT, DU, BHU), exams (JEE, NEET, GATE, UPSC), or company names (Google, TCS, Infosys, startups).\n"
        "4. Keep text neutral, objective, easy to read, engaging, and relevant for student viewers. Do not invent unverified facts.\n\n"
        "OUTPUT FORMAT (Return a valid JSON object with fields 'headline' and 'summary'):\n"
        '{"headline": "DU College Students Protest Campus Safety Policies Following Incident", "summary": "Students at Delhi University staged a protest demanding enhanced campus safety measures and administration accountability. The student council submitted a formal petition to the Dean regarding hostel security protocols."}'
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
        
    # Generate dynamic mandatory & student/college hashtags
    base_hashtags = generate_news_hashtags(headline, summary)
    student_tags = ["#students", "#campus", "#jee", "#neet", "#gate", "#upsc", "#placements", "#career"]
    combined_words = base_hashtags.split()
    for st in student_tags:
        if st not in combined_words:
            combined_words.append(st)
    hashtags = " ".join(combined_words)
    
    author = story.get("author", "")
    author_line = f"👤 Voice / Source: {author}\n" if author else ""
    
    # Format Telegram caption text
    telegram_caption = (
        f"🔥 {headline}\n\n"
        f"📌 What Happened & Why It Matters to Students:\n"
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
