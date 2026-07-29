"""
generate_image.py
Generates photorealistic news illustrations and quote portraits 100% from AI
using the Flux model on Pollinations.ai (no search engine lookup).
"""

import os
import time
import urllib.parse
import requests

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 480
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
RATE_LIMIT_SECONDS = 5


def generate_image(prompt, summary="", output_path="output/images/story.jpg", width=IMAGE_WIDTH, height=IMAGE_HEIGHT, model="flux"):
    """
    Generates a 1080x480 news banner or a 1080x1080 quote watermark using Flux.
    """
    is_quote = (width == 1080 and height == 1080)
    
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
        prompt="A professional news photograph of an Indian college classroom with students coding on laptops, natural lighting",
        output_path="output/images/test_web_image.jpg",
    )
    if path:
        print(f"Image saved: {path}")
    else:
        print("Failed to save image.")
