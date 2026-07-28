"""
generate_image.py
Fetches a real news photo matching the story headline using Bing Image Search.
Falls back to Pollinations.ai (AI illustration) if no real photo can be downloaded.
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
        print(f"  Searching real photo for: '{query[:50]}...'")
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
                # Print exception in debug or just try next URL
                continue
                
    except Exception as e:
        print(f"  Search query failed: {e}")

    return None


def craft_image_prompt(headline, summary=""):
    """Prompt generator for AI fallback illustration."""
    base = headline
    style = (
        "photorealistic photography style, natural lighting, high detail, "
        "professional news photography aesthetic, documentary style, "
        "generic anonymous people only, focus on setting/scene/objects rather than close-up faces, "
        "no text, no words, no letters, no logos, no watermark"
    )
    return f"{base}, {style}"


def generate_image(headline, summary="", output_path="output/images/story.jpg", width=IMAGE_WIDTH, height=IMAGE_HEIGHT):
    """
    Tries fetching a real photo from the web first.
    Falls back to Pollinations.ai if no web photo is found or successfully downloaded.
    """
    # 1. Try fetching a real photo matching the news title
    local_photo = fetch_search_image(headline, output_path)
    if local_photo:
        return local_photo

    # 2. Fallback to Pollinations AI Illustration
    print(f"  ⚠️ No real photo found. Falling back to AI Image generation...")
    prompt = craft_image_prompt(headline, summary)
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}{encoded_prompt}"
    params = {"width": width, "height": height, "nologo": "true"}

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
    """Batch generates/fetches images for a list of stories."""
    for i, story in enumerate(stories):
        headline = story.get("new_headline", story.get("title", ""))
        summary = story.get("new_summary", "")
        output_path = os.path.join(output_dir, f"story_{i}.jpg")

        print(f"  Fetching/Generating image {i + 1}/{len(stories)}: {headline[:50]}...")
        result = generate_image(headline, summary, output_path=output_path)
        story["image_path"] = result

        if i < len(stories) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    return stories


if __name__ == "__main__":
    path = generate_image(
        headline="IIT Bombay Placements 2026 record package",
        summary="A student bagged a record package at campus placements.",
        output_path="output/images/test_web_image.jpg",
    )
    if path:
        print(f"Image saved: {path}")
    else:
        print("Failed to save image.")
