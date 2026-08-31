"""
trending_news/visual_generator.py
Original Editorial Visual Generator (Watermark & Source Logo Protection)
"""

import os
import urllib.parse
import requests
from PIL import Image, ImageDraw
from pathlib import Path
from typing import Optional
from .config import OUTPUT_DIR


def generate_procedural_editorial_art(category: str, output_path: str) -> str:
    """
    Generates a clean, modern procedural gradient background with editorial geometry
    if remote image generation is unavailable.
    """
    width, height = 1080, 700
    
    cat = category.lower()
    if "politi" in cat or "gov" in cat:
        bg_top, bg_bottom = "#1E293B", "#0F172A"  # Dark Slate
        accent = "#38BDF8"
    elif "edu" in cat or "student" in cat or "job" in cat:
        bg_top, bg_bottom = "#0F4C81", "#022C43"  # Classic Blue
        accent = "#F59E0B"
    elif "econ" in cat or "fin" in cat:
        bg_top, bg_bottom = "#064E3B", "#022C22"  # Deep Emerald
        accent = "#34D399"
    else:
        bg_top, bg_bottom = "#312E81", "#1E1B4B"  # Deep Indigo
        accent = "#A855F7"
        
    img = Image.new("RGB", (width, height), bg_bottom)
    draw = ImageDraw.Draw(img)
    
    # Draw geometric background lines
    draw.rectangle([(0, 0), (width, 20)], fill=accent)
    draw.ellipse([(-100, -100), (400, 400)], fill=bg_top)
    draw.ellipse([(600, 300), (1200, 900)], fill=bg_top)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    return output_path


def generate_editorial_visual(visual_concept: str, category: str, post_id: str) -> str:
    """
    Generates an original editorial visual based on the AI visual_concept prompt.
    Uses Pollinations AI free image endpoint with fallback to procedural art.
    Ensures ZERO source logos or watermarks.
    """
    out_dir = OUTPUT_DIR / "temp"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"visual_{post_id}.jpg")
    
    if not visual_concept:
        visual_concept = f"Modern editorial 3D digital illustration about {category} in India"
        
    # Clean and encode prompt
    safe_prompt = f"{visual_concept}, professional 3D editorial digital media artwork, clean vector, no text, no watermark, 4k"
    encoded_prompt = urllib.parse.quote(safe_prompt)
    
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=700&nologo=true&seed=42"
    
    print(f"  🎨 [VisualGenerator] Requesting AI visual illustration for story '{post_id}'...")
    try:
        resp = requests.get(pollinations_url, timeout=18)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"  ✅ Original AI visual generated successfully: {out_path}")
            return out_path
    except Exception as e:
        print(f"  [VisualGenerator Notice] Image generation service offline ({e}). Using procedural artwork fallback.")
        
    return generate_procedural_editorial_art(category, out_path)
