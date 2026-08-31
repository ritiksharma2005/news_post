"""
trending_news/verifier.py
Verification Layer & Fact Checking Engine
"""

import requests
from typing import Dict, Any

# Trusted lead domains and official portals
HIGH_TRUST_SOURCES = ["forbesindia", "thebetterindia"]
SENSITIVE_CATEGORIES = ["Politics", "Government", "Crime", "Economy", "Health"]


def verify_news_lead(lead: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates verification status of a news lead item.
    Returns dictionary with verification_status ('verified', 'partially_verified', 'unverified')
    and verification_notes.
    """
    source_account = lead.get("source_account", "").lower()
    category = analysis.get("category", "General")
    headline = analysis.get("headline_extracted", "") or lead.get("caption", "")[:80]
    
    # 1. High trust established outlets automatically receive partially_verified / verified
    if source_account in HIGH_TRUST_SOURCES:
        if category not in SENSITIVE_CATEGORIES:
            return {
                "verification_status": "verified",
                "verification_notes": f"Published by trusted lead source @{source_account} in non-sensitive category."
            }
        else:
            return {
                "verification_status": "partially_verified",
                "verification_notes": f"Published by @{source_account}. High-stakes category ({category}) requires corroboration."
            }
            
    # 2. Check if lead headline can be cross-verified via news feed check
    try:
        # Search via RSS / Google News query parameter if keywords present
        keywords = "+".join(headline.split()[:5])
        search_url = f"https://news.google.com/rss/search?q={keywords}&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(search_url, timeout=5)
        if resp.status_code == 200 and "<item>" in resp.text:
            return {
                "verification_status": "verified",
                "verification_notes": "Corroborated by mainstream Indian news RSS reporting."
            }
    except Exception:
        pass
        
    # Default for standard student/social leads
    if category in SENSITIVE_CATEGORIES:
        return {
            "verification_status": "unverified",
            "verification_notes": f"Sensitive category '{category}' from social source; needs higher verification threshold."
        }
        
    return {
        "verification_status": "partially_verified",
        "verification_notes": "Standard social news lead."
    }
