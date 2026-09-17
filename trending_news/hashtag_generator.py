"""
trending_news/hashtag_generator.py
Dynamic Hashtag Generator for @news.nit_iit
Enforces mandatory hashtags: #news.nit_iit #news #nit #iit
Extracts college-specific hashtags (e.g., #svnit #nitsurat, #iitbombay #iitb, #vnit #vnitnagpur)
And appends topic & general student hashtags.
"""

import re
from typing import List

MANDATORY_HASHTAGS = ["#news.nit_iit", "#news", "#nit", "#iit"]

COLLEGE_HASHTAG_MAP = {
    # NITs
    "svnit": ["#svnit", "#nitsurat"],
    "surat": ["#svnit", "#nitsurat"],
    "manit": ["#manit", "#nitbhopal"],
    "bhopal": ["#manit", "#nitbhopal"],
    "vnit": ["#vnit", "#vnitnagpur"],
    "nagpur": ["#vnit", "#vnitnagpur"],
    "mnit": ["#mnit", "#nitjaipur"],
    "jaipur": ["#mnit", "#nitjaipur"],
    "mnnit": ["#mnnit", "#nitallahabad"],
    "allahabad": ["#mnnit", "#nitallahabad"],
    "prayagraj": ["#mnnit", "#nitallahabad"],
    "nitk": ["#nitk", "#nitsurathkal"],
    "surathkal": ["#nitk", "#nitsurathkal"],
    "nitt": ["#nitt", "#nittrichy"],
    "trichy": ["#nitt", "#nittrichy"],
    "tiruchirappalli": ["#nitt", "#nittrichy"],
    "nitr": ["#nitr", "#nitrourkela"],
    "rourkela": ["#nitrourkela", "#nitr"],
    "nitc": ["#nitc", "#nitcalicut"],
    "calicut": ["#nitcalicut", "#nitc"],
    "nitw": ["#nitw", "#nitwarangal"],
    "warangal": ["#nitwarangal", "#nitw"],
    "kurukshetra": ["#nitkurukshetra"],
    "silchar": ["#nitsilchar"],
    "hamirpur": ["#nithamirpur"],
    "jalandhar": ["#nitjalandhar"],
    "patna": ["#nitpatna"],
    "raipur": ["#nitraipur"],
    "agartala": ["#nitagartala"],
    "durgapur": ["#nitdurgapur"],
    "jamshedpur": ["#nitjamshedpur"],

    # IITs
    "iitb": ["#iitbombay", "#iitb"],
    "bombay": ["#iitbombay", "#iitb"],
    "mumbai": ["#iitbombay", "#iitb"],
    "iitd": ["#iitdelhi", "#iitd"],
    "delhi": ["#iitdelhi", "#iitd"],
    "iitm": ["#iitmadras", "#iitm"],
    "madras": ["#iitmadras", "#iitm"],
    "chennai": ["#iitmadras", "#iitm"],
    "iitk": ["#iitkanpur", "#iitk"],
    "kanpur": ["#iitkanpur", "#iitk"],
    "iitkgp": ["#iitkharagpur", "#iitkgp"],
    "kharagpur": ["#iitkharagpur", "#iitkgp"],
    "iitr": ["#iitroorkee"],
    "roorkee": ["#iitroorkee"],
    "iitg": ["#iitguwahati"],
    "guwahati": ["#iitguwahati"],
    "iith": ["#iithyderabad", "#iith"],
    "hyderabad": ["#iithyderabad", "#iith"],
    "iitbhu": ["#iitbhu"],
    "varanasi": ["#iitbhu"],
    "iitism": ["#iitismdhanbad", "#iitism"],
    "dhanbad": ["#iitismdhanbad", "#iitism"],
    "indore": ["#iitindore"],
    "bhubaneswar": ["#iitbhubaneswar"],
    "gandhinagar": ["#iitgandhinagar"],
    "jodhpur": ["#iitjodhpur"],
    "ropar": ["#iitropar"],
    "mandi": ["#iitmandi"],
}


def extract_college_hashtags(text: str) -> List[str]:
    """Extracts college-specific hashtags from news headline and summary text."""
    if not text:
        return []
        
    text_lower = text.lower()
    tags = []
    
    # 1. Check known acronyms/cities
    for key, val_tags in COLLEGE_HASHTAG_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
            for t in val_tags:
                if t not in tags:
                    tags.append(t)
                    
    # 2. Check regex patterns for "IIT <City>" or "NIT <City>" or "IIIT <City>"
    matches = re.findall(r'\b(iit|nit|iiit)\s+([a-zA-Z]+)\b', text_lower)
    for inst, city in matches:
        city_clean = city.lower()
        if city_clean in ["is", "the", "and", "in", "to", "for", "of", "on", "at", "by", "has", "had", "have", "will", "opens", "launches", "closes", "sets", "gets"]:
            continue
        clean_tag = f"#{inst}{city_clean}"
        if clean_tag not in tags:
            tags.append(clean_tag)
            
    return tags


def generate_news_hashtags(headline: str = "", summary: str = "", category: str = "") -> str:
    """
    Generates structured Instagram hashtags for @news.nit_iit:
    1. Mandatory Fixed Hashtags: #news.nit_iit #news #nit #iit
    2. College-Specific Hashtags: e.g. #svnit #nitsurat or #iitbombay #iitb
    3. Topic / Category Hashtags: e.g. #engineering #placements #education #studentupdates
    """
    combined_text = f"{headline} {summary}"
    
    # 1. Mandatory Fixed Hashtags (Always first!)
    ordered_tags = list(MANDATORY_HASHTAGS)
    
    # 2. College-Specific Hashtags
    college_tags = extract_college_hashtags(combined_text)
    for ct in college_tags:
        if ct.lower() not in [t.lower() for t in ordered_tags]:
            ordered_tags.append(ct)
            
    # 3. Category Hashtag
    if category and category.lower() not in ["general", "news"]:
        cat_tag = f"#{category.replace(' ', '')}"
        if cat_tag.lower() not in [t.lower() for t in ordered_tags]:
            ordered_tags.append(cat_tag)
            
    # 4. Topic Hashtags based on keywords in headline/summary
    text_lower = combined_text.lower()
    topic_map = {
        "placement": "#placements",
        "package": "#packages",
        "internship": "#internships",
        "exam": "#examalerts",
        "jee": "#jee2026",
        "neet": "#neet",
        "upsc": "#upsc",
        "hackathon": "#hackathon",
        "admission": "#admissions",
        "scholarship": "#scholarship",
        "salary": "#packages",
        "research": "#research",
        "tech": "#technology"
    }
    for kw, tag in topic_map.items():
        if kw in text_lower and tag.lower() not in [t.lower() for t in ordered_tags]:
            ordered_tags.append(tag)
            
    # 5. General Fallback Hashtags
    general_fallbacks = ["#engineering", "#education", "#studentupdates", "#campusnews"]
    for gt in general_fallbacks:
        if gt.lower() not in [t.lower() for t in ordered_tags]:
            ordered_tags.append(gt)
            
    return " ".join(ordered_tags[:12])
