import requests
import base64
import re
from bs4 import BeautifulSoup

def resolve_google_news_url(url):
    """
    Decodes the destination URL embedded inside a Google News link.
    First tries the offline base64 decoder, then falls back to googlenewsdecoder.
    """
    if "news.google.com/articles" not in url and "news.google.com/rss/articles" not in url:
        return url
        
    # 1. Try fast base64 offline decode first (zero network call)
    try:
        part = url.split("/")[-1].split("?")[0]
        if part.endswith("/"):
            part = part[:-1]
            
        padding = len(part) % 4
        if padding:
            part += "=" * (4 - padding)
            
        decoded_bytes = base64.b64decode(part)
        decoded = decoded_bytes.decode('utf-8', errors='ignore')
        
        url_match = re.search(r'(https?://[^\s\x00-\x1f\x7f-\xff]+)', decoded)
        if url_match:
            resolved = url_match.group(1)
            if "google.com" not in resolved:
                print(f"  [Resolver] Decoded base64 Google News URL to: {resolved[:65]}...")
                return resolved
    except Exception:
        pass
        
    # 2. Fall back to googlenewsdecoder package
    try:
        from googlenewsdecoder import gnewsdecoder
        decoded_res = gnewsdecoder(url)
        if decoded_res.get("status"):
            resolved = decoded_res["decoded_url"]
            print(f"  [Resolver] Library resolved Google News URL to: {resolved[:65]}...")
            return resolved
    except Exception as e:
        print(f"  [Resolver] Error calling googlenewsdecoder: {e}")
        
    return url

def extract_featured_image(article_url):
    """
    Attempts to extract the featured image URL from the article's meta tags.
    Looks for og:image, twitter:image, and standard image fallbacks.
    """
    if not article_url or not article_url.startswith("http"):
        return ""
        
    # Decode Google News wrapper links to their true destination website
    resolved_url = resolve_google_news_url(article_url)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(resolved_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return ""
            
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 1. Try OpenGraph image meta tag (widely supported)
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            return og_img["content"].strip()
            
        # 2. Try Twitter image meta tag
        tw_img = soup.find("meta", name="twitter:image")
        if tw_img and tw_img.get("content"):
            return tw_img["content"].strip()
            
        # 3. Try standard image link tag
        link_img = soup.find("link", rel="image_src")
        if link_img and link_img.get("href"):
            return link_img["href"].strip()
            
    except Exception as e:
        pass
        
    return ""
