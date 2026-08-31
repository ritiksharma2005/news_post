"""
trending_news/caption_generator.py
Instagram Caption & Hashtag Formatter
"""

from typing import Dict, Any, List
from .config import BRAND_HANDLE


def format_instagram_caption(editorial: Dict[str, Any], lead: Dict[str, Any]) -> str:
    """
    Generates a structured, highly engaging Instagram caption for @news.nit_iit.
    """
    headline = editorial.get("headline", "")
    summary = editorial.get("summary", "")
    why_it_matters = editorial.get("why_it_matters", "")
    category = editorial.get("category", "News")
    source_account = lead.get("source_account", "")
    
    # 1. Opening line
    opening = f"🔥 {headline}\n"
    
    # 2. Key Summary Explanation
    explanation = f"📝 What Happened:\n{summary}\n"
    
    # 3. Why It Matters
    context = ""
    if why_it_matters:
        context = f"💡 Why It Matters:\n{why_it_matters}\n"
        
    # 4. Community CTA
    cta = (
        "💬 What is your take on this update? Let us know in the comments below! 👇\n\n"
        f"📌 Tag a friend to keep them informed!\n\n"
        f"📲 Follow {BRAND_HANDLE} for daily verified news updates."
    )
    
    # 5. Source Attribution
    attribution = ""
    if source_account:
        attribution = f"\n\n(Source Lead: @{source_account})"
        
    # 6. Hashtags
    default_tags = ["#IndiaNews", "#StudentUpdates", "#UPSC", "#Education", "#Engineering", "#GenZNews", "#news_nit_iit"]
    category_tag = f"#{category.replace(' ', '')}" if category else ""
    if category_tag and category_tag not in default_tags:
        default_tags.insert(0, category_tag)
        
    hashtags_str = " ".join(default_tags[:8])
    
    caption_full = (
        f"{opening}\n"
        f"{explanation}\n"
        f"{context}\n"
        f"{cta}"
        f"{attribution}\n\n"
        f"{hashtags_str}"
    )
    
    return caption_full
