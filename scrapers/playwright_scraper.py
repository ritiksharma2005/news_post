import base64
import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from googlenewsdecoder import gnewsdecoder

def resolve_google_news_url(url):
    """
    Decodes the destination URL embedded inside a Google News link.
    First tries the offline base64 decoder, then falls back to googlenewsdecoder.
    """
    if "news.google.com/articles" not in url and "news.google.com/rss/articles" not in url and "news.google.com/read" not in url:
        return url
        
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
                return resolved
    except Exception:
        pass
        
    try:
        decoded_res = gnewsdecoder(url)
        if decoded_res.get("status"):
            return decoded_res["decoded_url"]
    except Exception as e:
        print(f"  [Resolver] Error calling googlenewsdecoder: {e}")
        
    return url

def extract_article_details(article_url):
    """
    Attempts to extract the featured image URL and the summary description
    directly from the target article's HTML meta tags.
    """
    img_url = ""
    summary = ""
    if not article_url or not article_url.startswith("http") or "google.com" in article_url:
        return img_url, summary
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(article_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Extract Image
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                img_url = og_img["content"].strip()
            else:
                tw_img = soup.find("meta", name="twitter:image")
                if tw_img and tw_img.get("content"):
                    img_url = tw_img["content"].strip()
                    
            # Extract Summary (og:description or standard description meta)
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                summary = og_desc["content"].strip()
            else:
                desc = soup.find("meta", name="description")
                if desc and desc.get("content"):
                    summary = desc["content"].strip()
                    
            # Clean HTML tags/escaped chars from summary
            if summary:
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = summary.replace("&nbsp;", " ").replace("&quot;", '"').strip()
    except Exception:
        pass
        
    return img_url, summary

def scrape_hindi_rss_feeds(limit=12):
    """
    Scrapes and merges news from multiple top Hindi RSS sources:
    Dainik Bhaskar, BBC Hindi, and Aaj Tak.
    """
    feeds = [
        {"name": "Dainik Bhaskar", "url": "https://www.bhaskar.com/rss-feed/1061/"},
        {"name": "BBC Hindi", "url": "https://feeds.bbci.co.uk/hindi/rss.xml"},
        {"name": "Aaj Tak", "url": "https://www.aajtak.in/rssfeeds/?id=home"}
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    stories = []
    
    # We want to round-robin or gather a balanced list of stories from the feeds
    per_feed_limit = max(3, limit // len(feeds) + 1)
    
    for f in feeds:
        try:
            print(f"  [Hindi RSS] Fetching {f['name']}...")
            res = requests.get(f["url"], headers=headers, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                items = soup.find_all("item")
                feed_stories = 0
                for item in items:
                    if feed_stories >= per_feed_limit:
                        break
                        
                    title_el = item.find("title")
                    link_el = item.find("link")
                    desc_el = item.find("description")
                    
                    title = title_el.text.strip() if title_el else ""
                    link = link_el.text.strip() if link_el else ""
                    description = desc_el.text.strip() if desc_el else ""
                    
                    # Clean CDATA/HTML tags
                    title = re.sub(r'<[^>]+>', '', title).replace("<![CDATA[", "").replace("]]>", "").strip()
                    description = re.sub(r'<[^>]+>', '', description).replace("<![CDATA[", "").replace("]]>", "").strip()
                    
                    # Extract image URL
                    image_url = ""
                    media = item.find("media:content") or item.find("content") or item.find("media:thumbnail") or item.find("thumbnail")
                    if media and media.get("url"):
                        image_url = media["url"].strip()
                    elif item.find("enclosure") and item.find("enclosure").get("url"):
                        image_url = item.find("enclosure")["url"].strip()
                        
                    if title:
                        stories.append({
                            "title": title,
                            "link": link,
                            "description": description,
                            "summary": description,
                            "image_url": image_url,
                            "featured_image": image_url,
                            "source": f["name"]
                        })
                        feed_stories += 1
        except Exception as e:
            print(f"  [Hindi RSS] Error parsing {f['name']}: {e}")
            
    return stories[:limit]

def scrape_bhaskar_rss(limit=8):
    """Alias for backward compatibility."""
    return scrape_hindi_rss_feeds(limit)

def scrape_google_news(query, lang="en", limit=10):
    """
    Uses Playwright to search Google News and extract headlines, target links,
    and featured images with zero external paid APIs.
    """
    lang_code = "hi" if lang == "hi" else "en"
    gl_code = "IN"
    url = f"https://news.google.com/search?q={query}&hl={lang_code}-IN&gl={gl_code}&ceid={gl_code}:{lang_code}"
    
    print(f"\n[Scraper] Launching Playwright browser for query: '{query}'...")
    results = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)  # Wait for dynamic lists to settle
            
            links = page.query_selector_all("a")
            seen_titles = set()
            
            for link in links:
                if len(results) >= limit:
                    break
                    
                href = link.get_attribute("href") or ""
                if "./read/" in href:
                    title = link.inner_text().strip()
                    if len(title) > 25 and title not in seen_titles:
                        seen_titles.add(title)
                        
                        # Find parent to search for story thumbnail fallback
                        parent = link
                        gnews_thumb = ""
                        for _ in range(5):
                            if parent:
                                parent = parent.query_selector("xpath=..")
                                if parent:
                                    img_els = parent.query_selector_all("img")
                                    found = False
                                    for img in img_els:
                                        src = img.get_attribute("src") or ""
                                        if src and not src.startswith("data:") and "favicon" not in src and "logo" not in src:
                                            if src.startswith("/"):
                                                gnews_thumb = "https://news.google.com" + src
                                            else:
                                                gnews_thumb = src
                                            found = True
                                            break
                                    if found:
                                        break
                        
                        gnews_link = "https://news.google.com" + href[1:]
                        results.append({
                            "title": title,
                            "gnews_link": gnews_link,
                            "gnews_thumb": gnews_thumb
                        })
                        
            browser.close()
    except Exception as e:
        print(f"[Scraper] Playwright browser error: {e}")
        
    # Post-process results to resolve final URLs, get summaries, and download images
    final_stories = []
    print(f"[Scraper] Resolving and post-processing {len(results)} raw items...")
    
    for item in results:
        gnews_link = item["gnews_link"]
        title = item["title"]
        
        # 1. Resolve redirect wrapper
        resolved_url = resolve_google_news_url(gnews_link)
        
        # 2. Extract details from target site
        img_url, summary = extract_article_details(resolved_url)
        
        # 3. Fallbacks
        if not img_url:
            img_url = item["gnews_thumb"]
        if not summary:
            summary = title # Fallback summary is the title itself
            
        # Clean source name from title (e.g. "Headline - ABP News" or "Headline | NDTV")
        clean_title = title
        source_name = "News Update"
        for sep in [" - ", " | "]:
            if sep in title:
                parts = title.rsplit(sep, 1)
                clean_title = parts[0].strip()
                source_name = parts[1].strip()
                break
                
        final_stories.append({
            "title": clean_title,
            "url": resolved_url,
            "featured_image": img_url,
            "summary": summary,
            "source": source_name
        })
        
    return final_stories
