"""
generate_image.py
Generates illustrations for news posts and quote posters.
If a news story mentions a specific leader or organization from the whitelist,
it downloads a real photo from the web. Otherwise, it generates the image 100% via AI (Flux).
"""

import os
import time
import urllib.parse
import json
import re
import requests
from PIL import Image

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 480
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
RATE_LIMIT_SECONDS = 5

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


def generate_image(prompt, summary="", output_path="output/images/story.jpg", width=IMAGE_WIDTH, height=IMAGE_HEIGHT, model="flux"):
    """
    Generates a photo for a story.
    If the prompt/headline mentions a whitelisted leader or organization, it searches and downloads a real photo.
    Otherwise, it uses Flux to generate the illustration directly.
    """
    is_quote = (width == 1080 and height == 1080)
    
    # 1. For non-quotes, check if the prompt mentions any of the whitelisted entities
    if not is_quote:
        lower_prompt = prompt.lower()
        matched_kws = [kw for kw in REAL_IMAGE_KEYWORDS if kw in lower_prompt]
        
        if matched_kws:
            # Construct a clean entity-based search query (e.g. "Rahul Gandhi news photo")
            search_query = " ".join([k.upper() if len(k) <= 5 else k.title() for k in matched_kws]) + " news photo"
            print(f"  Leader/Org detected: {matched_kws}. Redirecting to web search...")
            local_photo = fetch_search_image(search_query, output_path)
            if local_photo:
                return local_photo
            print("  ⚠️ Web search download failed. Falling back to AI generation...")

    # 2. Generate 100% via AI (Flux)
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
        return None


def generate_images_for_stories(stories, output_dir="output/images"):
    """Batch generates images for a list of stories."""
    for i, story in enumerate(stories):
        image_prompt = story.get("image_prompt", story.get("new_headline", ""))
        output_path = os.path.join(output_dir, f"story_{i}.jpg")

        print(f"  Generating image {i + 1}/{len(stories)}: {image_prompt[:50]}...")
        result = generate_image(image_prompt, "", output_path=output_path)
        story["image_path"] = result

        if i < len(stories) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    return stories


if __name__ == "__main__":
    path = generate_image(
        prompt="A professional news photograph of Rahul Gandhi speaking, natural lighting",
        output_path="output/images/test_web_image.jpg",
    )
    if path:
        print(f"Image saved: {path}")
    else:
        print("Failed to save image.")
