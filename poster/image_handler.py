import os
import urllib.parse
import json
import re
import requests
import shutil
from PIL import Image

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 480

LOCAL_ASSET_CACHE = {
    "narendra modi": "assets/narendra_modi.jpg",
    "rahul gandhi": "assets/rahul_gandhi.png",
    "amit shah": "assets/amit_shah.png",
    "parliament": "assets/indian_parliament.jpg",
    "lok sabha": "assets/indian_parliament.jpg",
    "rajya sabha": "assets/indian_parliament.jpg"
}

REAL_IMAGE_KEYWORDS = [
    "narendra modi", "droupadi murmu", "amit shah", "rajnath singh", "nitin gadkari",
    "rahul gandhi", "mallikarjun kharge", "yogi adityanath", "arvind kejriwal",
    "mamata banerjee", "m. k. stalin", "devendra fadnavis", "piyush goyal",
    "nirmala sitharaman", "ashwini vaishnaw", "dr. a. p. j. abdul kalam",
    "swami vivekananda", "savitribai phule", "jyotirao phule", "vikram sarabhai",
    "c. v. raman", "homi j. bhabha", "verghese kurien",
    "upsc", "ssc", "nta", "neet", "jee", "cbse", "gate", "ugc net", "cuet",
    "clat", "cat", "iit", "nit", "aiims", "isro", "drdo"
]

HINDI_KEYWORD_MAPPINGS = {
    "मोदी": "narendra modi", "नरेंद्र मोदी": "narendra modi",
    "अमित": "amit shah", "अमित शाह": "amit shah",
    "राहुल": "rahul gandhi", "राहुल गांधी": "rahul gandhi",
    "संसद": "parliament", "लोकसभा": "parliament", "राज्यसभा": "parliament",
    "इसरो": "isro", "आईआईटी": "iit", "एनआईटी": "nit",
    "नीट": "neet", "जेईई": "jee", "यूपीएससी": "upsc"
}

def download_image(url, output_path):
    """Attempts to download an image from a direct URL and validates it."""
    if not url or not url.startswith("http"):
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.content)
            with Image.open(output_path) as img:
                img.verify()
            print(f"  🎉 Successfully downloaded image: {url[:60]}...")
            return output_path
    except Exception as e:
        print(f"  ⚠️ Image download failed: {e}")
    return None

def fetch_search_image(query, output_path):
    """Queries Bing Images for a matching real photo and downloads it."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
    try:
        res = requests.get(search_url, headers=headers, timeout=12)
        if res.status_code != 200:
            return None

        matches = re.findall(r'class="iusc"[^>]*m="([^"]+)"', res.text)
        image_urls = []
        for m_str in matches:
            try:
                clean_json = m_str.replace("&quot;", '"')
                m_data = json.loads(clean_json)
                murl = m_data.get("murl")
                if murl and murl.startswith("http"):
                    image_urls.append(murl)
            except Exception:
                continue

        for img_url in image_urls[:5]:
            try:
                img_res = requests.get(img_url, headers=headers, timeout=8)
                if img_res.status_code == 200:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_res.content)
                    with Image.open(output_path) as img:
                        img.verify()
                    print(f"    🎉 Success! Downloaded real photo from web search.")
                    return output_path
            except Exception:
                continue
    except Exception as e:
        print(f"  Search query failed: {e}")
    return None

def prepare_image(story, output_path, width=IMAGE_WIDTH, height=IMAGE_HEIGHT):
    """
    Coordinates image pipeline:
    1. Try featured image crawled from the website.
    2. Try local whitelisted cache.
    3. Try Bing web search if keywords matched.
    4. Fall back directly to default fallback image.
    """
    is_quote = (width == 1080 and height == 1080)
    headline = story.get("new_headline", story.get("title", ""))
    featured_url = story.get("featured_image", "")
    
    # 1. Try Featured Image first
    if not is_quote and featured_url:
        # Ignore generic publisher placeholder images (logos, fallbacks, headers, etc.)
        blacklist = ["logo", "fallback", "default", "header", "banner", "favicon", "background"]
        featured_url_lower = featured_url.lower()
        is_generic = any(term in featured_url_lower for term in blacklist)
        
        if is_generic:
            print(f"  Ignoring generic publisher image URL: {featured_url[:60]}...")
        else:
            print(f"  Trying featured image download: {featured_url[:60]}...")
            path = download_image(featured_url, output_path)
            if path:
                return path

    if not is_quote:
        search_text = headline.lower()
        for hi_kw, en_kw in HINDI_KEYWORD_MAPPINGS.items():
            if hi_kw in search_text:
                search_text += " " + en_kw

        # 2. Check Local Whitelist Cache
        for key, asset_path in LOCAL_ASSET_CACHE.items():
            if key in search_text:
                if os.path.exists(asset_path):
                    print(f"  🎯 Local Asset matched for '{key}' -> {asset_path}. Copying to output...")
                    try:
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        shutil.copy(asset_path, output_path)
                        return output_path
                    except Exception as e:
                        print(f"  Error loading local asset: {e}")

        # 3. Check Whitelist for Web Search
        matched_kws = [kw for kw in REAL_IMAGE_KEYWORDS if kw in search_text]
        if matched_kws:
            matched_kws = list(set(matched_kws))
            search_query = " ".join([k.upper() if len(k) <= 5 else k.title() for k in matched_kws]) + " news photo"
            print(f"  Leader/Org detected: {matched_kws}. Redirecting to web search...")
            local_photo = fetch_search_image(search_query, output_path)
            if local_photo:
                return local_photo
        else:
            # Relevancy fallback: Search web using the first 7 words of the headline
            headline_words = headline.split()
            clean_query = " ".join(headline_words[:7])
            print(f"  No whitelist matched. Searching web using headline: '{clean_query}'...")
            local_photo = fetch_search_image(clean_query, output_path)
            if local_photo:
                return local_photo

    # 4. Final fallback to default template image (No AI generation)
    fallback_path = "assets/default_fallback.jpg"
    if os.path.exists(fallback_path):
        print(f"  🚨 Image retrieval failed. Falling back to default image: {fallback_path}")
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(fallback_path, output_path)
            return output_path
        except Exception as err:
            print(f"  Failed to copy default fallback: {err}")
            
    return None
