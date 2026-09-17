"""
trending_news/caption_generator.py
Instagram Caption & Hashtag Formatter
"""

from typing import Dict, Any, List
from .config import BRAND_HANDLE
from .hashtag_generator import generate_news_hashtags


def format_instagram_caption(editorial: Dict[str, Any], lead: Dict[str, Any]) -> str:
    """
    Generates a structured, highly engaging Instagram caption for @news.nit_iit.
    """
    headline = editorial.get("headline", "")
    summary = editorial.get("summary", "")
    category = editorial.get("category", "News")
    source_account = lead.get("source_account", "")
    
    # 1. Opening line
    opening = f"🔥 {headline}\n"
    
    # 2. Key Summary Explanation
    explanation = f"📝 What Happened:\n{summary}\n"
        
    # 3. Community CTA
    cta = (
        "💬 What is your take on this update? Let us know in the comments below! 👇\n\n"
        "📌 Tag a friend to keep them informed!\n\n"
        "📲 Join our Instagram Community (Link in Bio): https://www.instagram.com/channel/AbYg9NWAeNaKS8gf/\n\n"
        f"📲 Follow {BRAND_HANDLE} for daily verified news updates."
    )
    
    # 4. Source Attribution
    attribution = ""
    if source_account:
        attribution = f"\n\n(Source Lead: @{source_account})"
        
    # 5. Mandatory + College-Specific + Topic Hashtags
    hashtags_str = generate_news_hashtags(headline, summary, category)
    
    caption_full = (
        f"{opening}\n"
        f"{explanation}\n"
        f"{cta}"
        f"{attribution}\n\n"
        f"{hashtags_str}"
    )
    
    return caption_full
