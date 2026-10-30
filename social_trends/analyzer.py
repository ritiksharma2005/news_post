"""
social_trends/analyzer.py
AI News Analyzer & Text Summary Formatter for Telegram
Rewrites raw Reddit/Twitter post data into high-impact Telegram captions.
"""

import sys
import os
import re
from typing import Dict, Any, List

# Add parent directory for ai_client import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import ai_client
from trending_news.hashtag_generator import generate_news_hashtags


def is_student_exam_relevant(story: Dict[str, Any]) -> bool:
    """
    Strictly evaluates whether a candidate story is directly relevant to Indian Students,
    Exams (JEE, NEET, GATE, UPSC, CUET, Boards, SSC, PSC), Higher Education (IIT, NIT, IIIT, AIIMS, Universities),
    Campus Issues (protests, ragging, safety, results, cutoffs), or Student Career/Placements.
    Strictly filters out non-student general politics, Bollywood, cricket, and unrelated crime/news.
    """
    title = story.get("title", "")
    selftext = story.get("selftext", "")
    platform = story.get("platform", "")
    combined_lower = f"{title} {selftext}".lower()

    # 1. Strict Negative Filters: Immediately reject purely unrelated topics (unless explicit student keywords present)
    negative_topics = [
        "bollywood", "box office", "cricket match", "bcci", "ipl", "t20", "actor", "actress",
        "movie review", "trailer release", "election rally", "assembly election", "lok sabha election",
        "modi rally", "rahul gandhi says", "parliament election", "sensex", "nifty", "crypto",
        "state polls", "exit polls"
    ]
    has_negative = any(neg in combined_lower for neg in negative_topics)

    core_student_indicators = [
        "student", "students", "exam", "exams", "jee", "neet", "gate", "upsc", "cuet", "iit", "nit",
        "iiit", "aiims", "campus", "ragging", "admit card", "answer key", "cutoff", "cut-off",
        "paper leak", "placement", "placements", "scholarship", "board exam", "cbse", "nta"
    ]
    has_core_student = any(bool(re.search(r'\b' + re.escape(ind) + r'\b', combined_lower)) for ind in core_student_indicators)

    # If it is clearly an unrelated topic with no core student connection, reject it immediately
    if has_negative and not has_core_student:
        return False

    # 2. Priority subreddits targeting students & exams
    student_subreddits = [
        "jeeneetards", "cuetards", "btechtards", "developersindia", "indian_academia",
        "indianengineers", "upsc", "studentsphile", "gatetards", "delhiuniversity", "medicoretards"
    ]
    if any(f"r/{sub}" in platform.lower() for sub in student_subreddits):
        return True

    # 3. Comprehensive Positive Keywords for Students, Exams, Campuses & Placements (Word-boundary matched)
    student_exam_keywords = [
        # Exams & Admissions
        "exam", "exams", "jee", "jee main", "jee advanced", "neet", "neet ug", "neet pg",
        "gate", "upsc", "cuet", "cat", "clat", "nda", "cds", "ssc", "ssc cgl", "ssc chsl",
        "ibps", "sbi po", "board exam", "cbse", "icse", "class 10", "class 12", "admit card",
        "answer key", "cutoff", "cut-off", "percentile", "result", "results", "rank", "ranks",
        "paper leak", "cheating", "nta", "ugc", "aicte", "counselling", "josaa", "csab",
        # Colleges, Campuses & Institutions
        "student", "students", "college", "colleges", "campus", "campuses", "university",
        "universities", "hostel", "hostels", "canteen", "mess", "faculty", "professor",
        "iit", "nit", "iiit", "aiims", "iim", "bits", "delhi university", "du", "jnu", "bhu",
        "jadavpur", "amu", "jamia", "anna university", "vtu", "svnit", "engineering college", "medical college",
        # Student Affairs, Issues & Safety
        "ragging", "anti-ragging", "student protest", "protests", "student union", "suicide",
        "harassment", "student safety", "fee hike", "scholarship", "fellowship", "stipend",
        "attendance", "reservation", "paper leak scam",
        # Career, Placements & Internships
        "placement", "placements", "campus placement", "job offer", "ppo", "internship",
        "internships", "fresher", "freshers", "hiring", "layoff", "layoffs", "package",
        "lpa", "salary", "campus drive", "off-campus", "recruitment"
    ]
    if any(bool(re.search(r'\b' + re.escape(kw) + r'\b', combined_lower)) for kw in student_exam_keywords):
        return True

    # 4. AI Verification Check (when Gemini is configured)
    prompt = (
        "You are an AI editor strictly filtering news for an Indian Student and Exam channel on Telegram.\n"
        f"Platform: {platform}\n"
        f"Title: {title}\n"
        f"Context: {selftext[:300]}\n\n"
        "QUESTION: Is this story DIRECTLY relevant to Indian students, competitive/entrance exams "
        "(such as JEE, NEET, GATE, UPSC, CUET, Boards), colleges/universities (IIT, NIT, campuses), "
        "student issues (protests, ragging, student safety, results), or campus placements/internships?\n"
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

    return False


def is_student_career_relevant(story: Dict[str, Any]) -> bool:
    """Alias for backward compatibility."""
    return is_student_exam_relevant(story)


def is_viral_trending_relevant(story: Dict[str, Any]) -> bool:
    """Deprecated: redirects to is_student_exam_relevant to prevent non-student viral posts."""
    return is_student_exam_relevant(story)


def is_india_relevant(story: Dict[str, Any]) -> bool:
    """Backward compatibility alias calling is_student_exam_relevant."""
    return is_student_exam_relevant(story)


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
        
    # Generate dynamic mandatory & student/college/exam hashtags
    base_hashtags = generate_news_hashtags(headline, summary)
    student_tags = ["#students", "#exams", "#campus", "#jee", "#neet", "#gate", "#upsc", "#placements", "#career", "#education"]
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
