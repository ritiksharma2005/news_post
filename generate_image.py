"""
generate_image.py
Generates an AI illustration for each story using Pollinations.ai — a free,
no-API-key image generation service. This sidesteps copyright issues entirely
since we're never using a real news photo without a license.

Run directly to test: python generate_image.py
"""

import os
import time
import urllib.parse

import requests

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 480
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"

# Anonymous (no API key) requests are rate-limited to roughly 1 per 15 seconds.
# We wait this long between generations when producing multiple images in a row.
RATE_LIMIT_SECONDS = 16


def craft_image_prompt(headline, summary=""):
    """
    Turn a news headline into a safe, photorealistic illustration prompt.
    Uses a realistic news-photography style rather than cartoon/illustration.

    Safety note: this deliberately avoids generating specific real named
    individuals' likenesses (politicians, officials, celebrities) since a
    fabricated photorealistic image of a real person could be mistaken for
    an actual photo of them. Instead, for such stories, the prompt steers
    toward symbolic/contextual visuals (buildings, settings, generic crowds,
    objects) rather than a specific person's face.
    """
    base = headline
    style = (
        "photorealistic photography style, natural lighting, high detail, "
        "professional news photography aesthetic, documentary style, "
        "generic anonymous people only (no specific recognizable "
        "individuals, no celebrity or politician likenesses), "
        "focus on setting/scene/objects rather than close-up faces, "
        "no text, no words, no letters, no logos, no watermark"
    )
    return f"{base}, {style}"


def generate_image(headline, summary="", output_path="output/images/story.jpg", width=IMAGE_WIDTH, height=IMAGE_HEIGHT):
    """
    Request an illustration from Pollinations.ai for the given story and
    save it to disk. Returns the output_path on success, or None on failure
    (caller should fall back to the placeholder image block in that case).
    """
    prompt = craft_image_prompt(headline, summary)
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}{encoded_prompt}"
    params = {"width": width, "height": height, "nologo": "true"}

    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"  Image generation failed for '{headline[:50]}...': {e}")
        return None


def generate_images_for_stories(stories, output_dir="output/images"):
    """
    Generate an image for each story in a list, respecting the anonymous
    rate limit between requests. Adds an 'image_path' key to each story dict.
    """
    for i, story in enumerate(stories):
        headline = story.get("new_headline", story.get("title", ""))
        summary = story.get("new_summary", "")
        output_path = os.path.join(output_dir, f"story_{i}.jpg")

        print(f"  Generating image {i + 1}/{len(stories)}: {headline[:50]}...")
        result = generate_image(headline, summary, output_path=output_path)
        story["image_path"] = result

        if i < len(stories) - 1:
            time.sleep(RATE_LIMIT_SECONDS)

    return stories


if __name__ == "__main__":
    path = generate_image(
        headline="India Unveils Bold New Education Scheme for Colleges",
        summary="The government announced a fresh push to modernize higher education.",
        output_path="output/images/test_generated.jpg",
    )
    if path:
        print(f"Image saved: {path}")
    else:
        print("Image generation failed — check your internet connection.")
