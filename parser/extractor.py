import re
from difflib import SequenceMatcher

def clean_title(title):
    if not title:
        return ""
    # Strip emojis, punctuation and convert to lowercase for comparison
    title = re.sub(r'[\W_]+', ' ', title.lower()).strip()
    return title

def calculate_similarity(a, b):
    return SequenceMatcher(None, clean_title(a), clean_title(b)).ratio()

def normalize_article(article):
    """Normalize a raw article dict to standard keys."""
    return {
        "title": (article.get("title") or "").strip(),
        "description": (article.get("description") or "").strip(),
        "url": (article.get("url") or "").strip(),
        "source": (article.get("source") or "Unknown").strip(),
        "published_at": (article.get("published_at") or "").strip(),
        "featured_image": (article.get("featured_image") or "").strip(),
        "category": (article.get("category") or "General").strip()
    }

def deduplicate_articles(articles):
    """Merges articles that are highly similar (> 0.65 similarity)."""
    normalized = [normalize_article(a) for a in articles if a.get("title")]
    unique = []
    
    for art in normalized:
        is_dup = False
        for u in unique:
            # Check title similarity
            sim = calculate_similarity(art["title"], u["title"])
            if sim > 0.65:
                # Merge sources
                if art["source"] not in u["source"]:
                    u["source"] = f"{u['source']}, {art['source']}"
                # Keep the longer description or newer published date
                if len(art["description"]) > len(u["description"]):
                    u["description"] = art["description"]
                if not u["featured_image"] and art["featured_image"]:
                    u["featured_image"] = art["featured_image"]
                is_dup = True
                break
        if not is_dup:
            unique.append(art)
            
    print(f"  [Deduplication] Merged {len(normalized)} articles down to {len(unique)} unique stories.")
    return unique
