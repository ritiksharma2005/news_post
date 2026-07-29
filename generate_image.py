"""
generate_image.py
Entity-Based Image Decision Engine:
1. Check Local Asset Cache (Narendra Modi, Rahul Gandhi, Amit Shah, Parliament)
2. Check Whitelist for Web Search (ISRO, DRDO, IITs, NTA, NEET, JEE, etc.)
3. Fallback to Flux AI Generation for generic/tech concepts.
4. Final Fallback to assets/default_fallback.jpg if generation fails or times out.
Supports both English and Hindi keyword mapping.
"""

import os
import time
import urllib.parse
import json
import re
import requests
import shutil
from PIL import Image

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 480
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
RATE_LIMIT_SECONDS = 5

# Local asset mappings for famous people/places
LOCAL_ASSET_CACHE = {
    "narendra modi": "assets/narendra_modi.jpg",
    "rahul gandhi": "assets/rahul_gandhi.png",
    "amit shah": "assets/amit_shah.png",
    "parliament": "assets/indian_parliament.jpg",
    "lok sabha": "assets/indian_parliament.jpg",
    "rajya sabha": "assets/indian_parliament.jpg"
}

# Whitelist of leaders and organizations for which we want REAL web photos
REAL_IMAGE_KEYWORDS = [
    # Leaders / Historical Figures
    "narendra modi", "droupadi murmu", "amit shah", "rajnath singh", "nitin gadkari",
    "rahul gandhi", "mallikarjun kharge", "yogi adityanath", "arvind kejriwal",
    "mamata banerjee", "m. k. stalin", "devendra fadnavis", "piyush goyal",
    "nirmala sitharaman", "ashwini vaishnaw", "dr. a. p. j. abdul kalam",
    "swami vivekananda", "savitribai phule", "jyotirao phule", "vikram sarabhai",
    "c. v. raman", "homi j. bhabha", "verghese kurien",
    # Organizations / Exams / Logos
    "upsc", "ssc", "nta", "neet", "jee", "cbse", "gate", "ugc net", "cuet",
    "clat", "cat", "iit", "nit", "aiims", "isro", "drdo"
]

# Hindi equivalents mapped to English keywords
HINDI_KEYWORD_MAPPINGS = {
    "मोदी": "narendra modi", "नरेंद्र मोदी": "narendra modi",
    "अमित": "amit shah", "अमित शाह": "amit shah",
    "राहुल": "rahul gandhi", "राहुल गांधी": "rahul gandhi",
    "संसद": "parliament", "लोकसभा": "parliament", "राज्यसभा": "parliament",
    "इसरो": "isro", "आईआईटी": "iit", "एनआईटी": "nit",
    "नीट": "neet", "जेईई": "jee", "यूपीएससी": "upsc"
}


def fetch_search_image(query, output_path):
    """
    Queries Bing Images for a matching real photo, downloads it,
    and returns the local file path.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
    
    try:
        print(f"  Searching real photo for: '{query}'")
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code != 200:
            return None

        # Parse Bing's metadata class 'iusc' containing high-res image URLs ('murl')
        matches = re.findall(r'class="iusc"[^>]*m="([^"]+)"', res.text)
        image_urls = []
        for m_str in matches:
            try:
                # Clean HTML entity encodings if present
                clean_json = m_str.replace("&quot;", '"')
                m_data = json.loads(clean_json)
                murl = m_data.get("murl")
                if murl and murl.startswith("http"):
                    image_urls.append(murl)
            except Exception:
                continue

        # Try downloading the first 5 image results until one succeeds
        for img_url in image_urls[:5]:
            try:
                print(f"    Trying download: {img_url[:60]}")
                img_res = requests.get(img_url, headers=headers, timeout=10)
                if img_res.status_code == 200:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_res.content)
                    
                    # Validate that it is a readable image
                    with Image.open(output_path) as img:
                        img.verify()
                    
                    print(f"    🎉 Success! Downloaded real photo from web.")
                    return output_path
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"  Search query failed: {e}")

    return None


def generate_image(prompt, summary="", output_path="output/images/story.jpg", width=IMAGE_WIDTH, height=IMAGE_HEIGHT, model="flux", headline=""):
    """
    Routes the image selection conditionally:
    1. Local asset cache if it matches Modi, Rahul, Amit Shah, or Parliament.
    2. Web search if it matches whitelisted entities.
    3. Flux AI generation for everything else.
    4. Copies assets/default_fallback.jpg if all else fails.
    """
    is_quote = (width == 1080 and height == 1080)
    
    if not is_quote:
        # Combine prompt and headline to ensure robust matching across translations
        search_text = (prompt + " " + headline).lower()
        
        # Inject mapped English keywords if Hindi equivalent is present
        for hi_kw, en_kw in HINDI_KEYWORD_MAPPINGS.items():
            if hi_kw in search_text:
                search_text += " " + en_kw
        
        # 1. Check Local Asset Cache first!
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
        
        # 2. Check Whitelist for Web Search
        matched_kws = [kw for kw in REAL_IMAGE_KEYWORDS if kw in search_text]
        if matched_kws:
            matched_kws = list(set(matched_kws)) # Deduplicate
            search_query = " ".join([k.upper() if len(k) <= 5 else k.title() for k in matched_kws]) + " news photo"
            print(f"  Leader/Org detected: {matched_kws}. Redirecting to web search...")
            local_photo = fetch_search_image(search_query, output_path)
            if local_photo:
                return local_photo
            print("  ⚠️ Web search download failed. Falling back to AI generation...")

    # 3. Generate 100% via AI (Flux)
    if is_quote:
        print(f"  🎨 Generating Author portrait via Flux: '{prompt[:50]}...'")
    else:
        print(f"  📸 Generating news photo via Flux: '{prompt[:50]}...'")
        
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}{encoded_prompt}"
    params = {"width": width, "height": height, "nologo": "true", "model": model}

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    except Exception as e:
        print(f"  AI generation failed: {e}")
        # Final fallback to standard template image
        fallback_path = "assets/default_fallback.jpg"
        if os.path.exists(fallback_path):
            print(f"  🚨 All methods failed. Falling back to default image: {fallback_path}")
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy(fallback_path, output_path)
                return output_path
            except Exception as err:
                print(f"  Failed to copy default fallback: {err}")
        return None


def generate_images_for_stories(stories, output_dir="output/images"):
    """Batch generates images for a list of stories."""
    for i, story in enumerate(stories):
        image_prompt = story.get("image_prompt", story.get("new_headline", ""))
        headline = story.get("new_headline", "")
        output_path = os.path.join(output_dir, f"story_{i}.jpg")

        print(f"  Generating image {i + 1}/{len(stories)}: {image_prompt[:50]}...")
        result = generate_image(image_prompt, "", output_path=output_path, headline=headline)
        story["image_path"] = result

        if i < len(stories) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    return stories


if __name__ == "__main__":
    path = generate_image(
        prompt="A professional news photograph of Amit Shah speaking, natural lighting",
        output_path="output/images/test_web_image.jpg",
    )
    if path:
        print(f"Image saved: {path}")
    else:
        print("Failed to save image.")
