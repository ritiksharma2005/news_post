"""
trending_news/parser.py
Raw Instagram Metadata Extractor & Sanitizer
"""

import re
from typing import Dict, Any, List


def extract_hashtags(caption: str) -> List[str]:
    """Extracts all #hashtag strings from caption text."""
    if not caption:
        return []
    return re.findall(r'#\w+', caption)


def clean_caption_text(caption: str) -> str:
    """Cleans Instagram caption text by removing excessive white spaces and promotion lines."""
    if not caption:
        return ""
    
    # Normalize line breaks
    text = re.sub(r'\n{3,}', '\n\n', caption).strip()
    return text


def parse_raw_post(raw_post: Dict[str, Any], source_username: str) -> Dict[str, Any]:
    """
    Transforms raw scraped Instagram data into standardized news lead object format.
    """
    caption_raw = raw_post.get("caption", "") or raw_post.get("text", "")
    caption_clean = clean_caption_text(caption_raw)
    hashtags = extract_hashtags(caption_raw)
    
    post_id = str(raw_post.get("id") or raw_post.get("code") or raw_post.get("shortcode") or "")
    post_url = raw_post.get("url") or raw_post.get("post_url")
    if not post_url and post_id:
        post_url = f"https://www.instagram.com/p/{post_id}/"
        
    image_url = raw_post.get("image_url") or raw_post.get("display_url") or raw_post.get("displayUrl") or ""
    
    return {
        "source_account": source_username,
        "source_post_id": post_id,
        "source_url": post_url,
        "caption": caption_clean,
        "hashtags": hashtags,
        "posted_at": raw_post.get("posted_at") or raw_post.get("taken_at") or raw_post.get("timestamp"),
        "image_url": image_url,
        "post_type": raw_post.get("post_type", "single_image"),
        "likes_count": raw_post.get("likes_count", 0),
        "comments_count": raw_post.get("comments_count", 0),
        "raw_data": raw_post
    }
