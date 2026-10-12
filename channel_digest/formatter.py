"""
channel_digest/formatter.py
Prepares clean, readable daily news roundups formatted for the News NIT IIT Instagram Broadcast Channel.
Handles headline extraction, item numbering, link formatting, and multi-part message splitting.
"""

import re
from typing import List, Dict, Any
from .config import MAX_TELEGRAM_MESSAGE_CHARS


def extract_concise_headline(caption: str, fallback_title: str = "") -> str:
    """
    Extracts a concise, readable news headline from an Instagram post caption.
    Removes hashtags, excessive tags, and extracts the primary lead statement.
    """
    if not caption and fallback_title:
        return fallback_title.strip()
    if not caption:
        return "Latest Campus & Student Update"
        
    text = caption.strip()
    
    # Remove leading common fire/alert emojis while keeping the core headline
    text = re.sub(r'^[🔥🚨⚡📢📌💡👉]+\s*', '', text).strip()
    
    # Split by double newline or known section markers
    parts = re.split(r'\n\s*\n|📌|\n(?=[A-Z0-9#])', text)
    first_line = parts[0].strip() if parts else text
    
    # Strip trailing hashtags from first line
    first_line = re.sub(r'#\w+', '', first_line).strip()
    
    # Strip trailing source links or handles from headline
    first_line = re.sub(r'https?://\S+', '', first_line).strip()
    first_line = re.sub(r'Tap the link in bio.*', '', first_line, flags=re.I).strip()
    
    # Clean redundant spaces and quotes
    first_line = re.sub(r'\s+', ' ', first_line).strip()
    if first_line.startswith('"') and first_line.endswith('"'):
        first_line = first_line[1:-1].strip()
        
    if not first_line:
        first_line = "Latest Campus & Student Update"
        
    # Truncate if excessively long (e.g. over 110 chars)
    if len(first_line) > 110:
        truncated = first_line[:107]
        # Trim at last word boundary
        last_space = truncated.rfind(' ')
        if last_space > 60:
            truncated = truncated[:last_space]
        first_line = truncated.rstrip(",.;- ") + "..."
        
    return first_line


def format_single_entry(idx: int, post: Dict[str, Any]) -> str:
    """Formats one news item entry with headline and Instagram post link."""
    caption = post.get("caption", "")
    headline = post.get("headline") or extract_concise_headline(caption, post.get("title", ""))
    permalink = post.get("permalink", "").strip()
    
    return f"{idx}. {headline}\n   Read here: {permalink}"


def build_roundup_messages(
    posts: List[Dict[str, Any]],
    roundup_date: str,
    run_type: str = "evening"
) -> List[str]:
    """
    Constructs the complete daily roundup text matching the requested format.
    Splits into multiple numbered parts if the message exceeds Telegram character limits.
    """
    title_label = "MORNING NEWS ROUNDUP" if run_type == "morning" else "DAILY NEWS ROUNDUP"
    time_label = "this morning" if run_type == "morning" else "today"

    # Case: No posts published on this date
    if not posts:
        empty_msg = (
            f"NEWS NIT IIT — {title_label}\n\n"
            f"No new posts were published {time_label} on @news.nit_iit.\n\n"
            f"📅 Date: {roundup_date}\n"
            "Follow @news.nit_iit for more updates!"
        )
        return [empty_msg]
        
    # Format all individual items
    entries = []
    for idx, post in enumerate(posts, 1):
        # Cache extracted headline onto post dict for database logging
        post["headline"] = post.get("headline") or extract_concise_headline(post.get("caption", ""), post.get("title", ""))
        entries.append(format_single_entry(idx, post))
        
    intro_header = (
        f"NEWS NIT IIT — {title_label}\n\n"
        "Here are today's latest updates from @news.nit_iit. Tap the links to read the complete posts.\n\n"
    )
    footer = "\n\nFollow @news.nit_iit for more updates!"
    
    # Try fitting into a single message
    full_body = "\n\n".join(entries)
    full_text = intro_header + full_body + footer
    
    if len(full_text) <= MAX_TELEGRAM_MESSAGE_CHARS:
        return [full_text]
        
    # Message too long: Split entries across multiple parts
    parts = []
    current_entries = []
    current_len = len(intro_header) + len(footer) + 50
    
    for entry in entries:
        entry_len = len(entry) + 2  # account for \n\n
        if current_entries and (current_len + entry_len > MAX_TELEGRAM_MESSAGE_CHARS):
            parts.append(current_entries)
            current_entries = [entry]
            current_len = len(intro_header) + len(footer) + entry_len + 50
        else:
            current_entries.append(entry)
            current_len += entry_len
            
    if current_entries:
        parts.append(current_entries)
        
    total_parts = len(parts)
    messages = []
    
    for p_idx, p_entries in enumerate(parts, 1):
        p_header = f"NEWS NIT IIT — DAILY NEWS ROUNDUP (Part {p_idx}/{total_parts})\n\n"
        if p_idx == 1:
            p_header += "Here are today's latest updates from @news.nit_iit. Tap the links to read the complete posts.\n\n"
            
        p_body = "\n\n".join(p_entries)
        p_footer = footer if p_idx == total_parts else f"\n\n(Continued in Part {p_idx+1}...)"
        messages.append(p_header + p_body + p_footer)
        
    return messages
