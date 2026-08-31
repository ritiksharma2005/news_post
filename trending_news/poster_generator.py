"""
trending_news/poster_generator.py
4:5 Portrait Poster Engine (1080 x 1350 px) for @news.nit_iit
Implements Layout A (Breaking), Layout B (Achievement), Layout C (Data), Layout D (Sports/Culture)
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Any, List, Optional
from .config import CANVAS_WIDTH, CANVAS_HEIGHT, BRAND_HANDLE, BRAND_NAME, FONTS_DIR


def strip_emojis(text: str) -> str:
    """Strips emoji characters from headline to ensure clean typography rendering."""
    if not text:
        return ""
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2b50\u2b06\u2192]', '', text).strip()


def load_font(font_name: str = "bold", size: int = 42) -> ImageFont.FreeTypeFont:
    """Loads display fonts with system fallbacks."""
    paths_to_try = [
        str(FONTS_DIR / "Montserrat-Bold.ttf"),
        str(FONTS_DIR / "Inter-Bold.ttf"),
        str(FONTS_DIR / "DejaVuSans-Bold.ttf"),
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if font_name == "bold" else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Arial.ttf"
    ]
    for p in paths_to_try:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text_pixels(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Wraps text so no line exceeds max_width in pixels."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test = current_line + " " + word if current_line else word
        if draw.textlength(test, font=font) <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def fit_headline_font(headline: str, max_width: int, max_lines: int, start_size: int, draw: ImageDraw.ImageDraw) -> tuple[ImageFont.FreeTypeFont, List[str]]:
    """Dynamically scales down headline font size until it fits within max_lines."""
    font_size = start_size
    while font_size >= 28:
        font = load_font("bold", font_size)
        wrapped = wrap_text_pixels(headline, font, max_width, draw)
        if len(wrapped) <= max_lines:
            return font, wrapped
        font_size -= 4
    font = load_font("bold", 28)
    return font, wrap_text_pixels(headline, font, max_width, draw)[:max_lines]


def draw_header_brand(draw: ImageDraw.ImageDraw, accent_color: str = "#0284C7", bg_is_dark: bool = False):
    """Renders a top solid white strip border (banner) with NEWS.NIT_IIT and DAILY EDITORIAL."""
    font_brand = load_font("bold", 32)
    font_tag = load_font("bold", 24)
    
    # 1. Top White Strip Border Banner (Height: 90px)
    draw.rectangle([(0, 0), (CANVAS_WIDTH, 90)], fill="#FFFFFF")
    # Top accent stripe
    draw.rectangle([(0, 0), (CANVAS_WIDTH, 10)], fill=accent_color)
    
    # Left: NEWS.NIT_IIT
    draw.text((50, 32), BRAND_NAME, fill="#0F172A", font=font_brand)
    
    # Right: DAILY EDITORIAL
    tag_w = draw.textlength("DAILY EDITORIAL", font=font_tag)
    draw.text((CANVAS_WIDTH - 50 - tag_w, 36), "DAILY EDITORIAL", fill=accent_color, font=font_tag)
    
    # Bottom separator line of the white border
    draw.line([(0, 90), (CANVAS_WIDTH, 90)], fill=accent_color, width=3)


def draw_footer_brand(draw: ImageDraw.ImageDraw, y_pos: int = 1270, bg_is_dark: bool = False):
    """Renders a bottom solid white strip border (banner) with @news.nit_iit."""
    font_footer = load_font("bold", 32)
    accent_color = "#0284C7"
    
    # 1. Bottom White Strip Border Banner (Height: 80px)
    draw.rectangle([(0, 1270), (CANVAS_WIDTH, CANVAS_HEIGHT)], fill="#FFFFFF")
    draw.line([(0, 1270), (CANVAS_WIDTH, 1270)], fill=accent_color, width=3)
    
    # Centered: @news.nit_iit
    w = draw.textlength(BRAND_HANDLE, font=font_footer)
    x = int((CANVAS_WIDTH - w) // 2)
    draw.text((x, 1292), BRAND_HANDLE, fill=accent_color, font=font_footer)


# ==================================================
# LAYOUT A — BREAKING / TRENDING (Dark Theme)
# ==================================================
def render_layout_a(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    card = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#0F172A")
    draw = ImageDraw.Draw(card)
    
    draw_header_brand(draw, accent_color="#38BDF8", bg_is_dark=True)
    
    # Category Badge
    category = editorial.get("category", "BREAKING").upper()
    font_badge = load_font("bold", 22)
    draw.rounded_rectangle([(50, 110), (220, 148)], radius=8, fill="#0284C7")
    draw.text((66, 118), category, fill="#FFFFFF", font=font_badge)
    
    # Headline (Max 3 lines)
    headline = strip_emojis(editorial.get("headline", ""))
    font_hl, hl_lines = fit_headline_font(headline, max_width=980, max_lines=3, start_size=52, draw=draw)
    
    y = 175
    for line in hl_lines:
        draw.text((50, y), line, fill="#FFFFFF", font=font_hl, stroke_width=1, stroke_fill="#FFFFFF")
        y += font_hl.size + 10
        
    # Visual Image Box
    image_top = y + 20
    image_height = 540
    
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            iw, ih = img.size
            ratio = 980 / iw
            nh = int(ih * ratio)
            resized = img.resize((980, nh), Image.Resampling.LANCZOS)
            
            if nh > image_height:
                cropped = resized.crop((0, (nh - image_height) // 2, 980, (nh - image_height) // 2 + image_height))
            else:
                cropped = Image.new("RGB", (980, image_height), "#1E293B")
                cropped.paste(resized, (0, (image_height - nh) // 2))
                
            card.paste(cropped, (50, image_top))
        except Exception:
            draw.rectangle([(50, image_top), (1030, image_top + image_height)], fill="#1E293B")
    else:
        draw.rectangle([(50, image_top), (1030, image_top + image_height)], fill="#1E293B")
        
    # Summary Highlight Box
    sum_top = image_top + image_height + 25
    sum_height = 180
    draw.rounded_rectangle([(50, sum_top), (1030, sum_top + sum_height)], radius=12, fill="#1E293B", outline="#38BDF8", width=2)
    draw.rectangle([(50, sum_top), (62, sum_top + sum_height)], fill="#38BDF8")
    
    font_sum = load_font("regular", 26)
    summary = strip_emojis(editorial.get("summary", ""))
    sum_lines = wrap_text_pixels(summary, font_sum, 920, draw)
    
    sy = sum_top + 20
    for line in sum_lines[:3]:
        draw.text((80, sy), line, fill="#E2E8F0", font=font_sum)
        sy += 36
        
    draw_footer_brand(draw, y_pos=1275, bg_is_dark=True)
    card.save(output_path)
    return output_path


# ==================================================
# LAYOUT B — ACHIEVEMENT / EDUCATION (Light Theme)
# ==================================================
def render_layout_b(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    card = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#F8FAFC")
    draw = ImageDraw.Draw(card)
    
    draw_header_brand(draw, accent_color="#0284C7", bg_is_dark=False)
    
    # Headline
    headline = strip_emojis(editorial.get("headline", ""))
    font_hl, hl_lines = fit_headline_font(headline, max_width=980, max_lines=3, start_size=50, draw=draw)
    
    y = 120
    for line in hl_lines:
        draw.text((50, y), line, fill="#0F172A", font=font_hl, stroke_width=1, stroke_fill="#0F172A")
        y += font_hl.size + 10
        
    # Centered Visual Image
    image_top = y + 20
    image_height = 560
    
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            iw, ih = img.size
            ratio = 980 / iw
            nh = int(ih * ratio)
            resized = img.resize((980, nh), Image.Resampling.LANCZOS)
            
            if nh > image_height:
                cropped = resized.crop((0, (nh - image_height) // 2, 980, (nh - image_height) // 2 + image_height))
            else:
                cropped = Image.new("RGB", (980, image_height), "#E2E8F0")
                cropped.paste(resized, (0, (image_height - nh) // 2))
                
            card.paste(cropped, (50, image_top))
        except Exception:
            draw.rectangle([(50, image_top), (1030, image_top + image_height)], fill="#E2E8F0")
    else:
        draw.rectangle([(50, image_top), (1030, image_top + image_height)], fill="#E2E8F0")
        
    # Key Facts Box
    sum_top = image_top + image_height + 25
    sum_height = 200
    draw.rounded_rectangle([(50, sum_top), (1030, sum_top + sum_height)], radius=12, fill="#E0F2FE", outline="#BAE6FD", width=2)
    draw.rectangle([(50, sum_top), (62, sum_top + sum_height)], fill="#0284C7")
    
    font_sum = load_font("regular", 26)
    summary = strip_emojis(editorial.get("summary", ""))
    sum_lines = wrap_text_pixels(summary, font_sum, 920, draw)
    
    sy = sum_top + 22
    for line in sum_lines[:4]:
        draw.text((80, sy), line, fill="#0369A1", font=font_sum)
        sy += 36
        
    draw_footer_brand(draw, y_pos=1275, bg_is_dark=False)
    card.save(output_path)
    return output_path


# ==================================================
# LAYOUT C — DATA / ECONOMY / SALARY (Metric Callout)
# ==================================================
def render_layout_c(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    card = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#042F2E")  # Deep Emerald
    draw = ImageDraw.Draw(card)
    
    draw_header_brand(draw, accent_color="#34D399", bg_is_dark=True)
    
    # Large Metric Callout Text
    metric = editorial.get("metric_callout") or "FINANCE & ECONOMY"
    font_metric = load_font("bold", 72)
    draw.text((50, 110), metric, fill="#34D399", font=font_metric)
    
    # Headline
    headline = strip_emojis(editorial.get("headline", ""))
    font_hl, hl_lines = fit_headline_font(headline, max_width=980, max_lines=3, start_size=46, draw=draw)
    
    y = 210
    for line in hl_lines:
        draw.text((50, y), line, fill="#FFFFFF", font=font_hl)
        y += font_hl.size + 10
        
    # Visual Box
    image_top = y + 20
    image_height = 500
    
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            iw, ih = img.size
            ratio = 980 / iw
            nh = int(ih * ratio)
            resized = img.resize((980, nh), Image.Resampling.LANCZOS)
            
            if nh > image_height:
                cropped = resized.crop((0, (nh - image_height) // 2, 980, (nh - image_height) // 2 + image_height))
            else:
                cropped = Image.new("RGB", (980, image_height), "#064E3B")
                cropped.paste(resized, (0, (image_height - nh) // 2))
                
            card.paste(cropped, (50, image_top))
        except Exception:
            draw.rectangle([(50, image_top), (1030, image_top + image_height)], fill="#064E3B")
    else:
        draw.rectangle([(50, image_top), (1030, image_top + image_height)], fill="#064E3B")
        
    # Explanation Box
    sum_top = image_top + image_height + 25
    sum_height = 180
    draw.rounded_rectangle([(50, sum_top), (1030, sum_top + sum_height)], radius=12, fill="#065F46", outline="#34D399", width=2)
    
    font_sum = load_font("regular", 26)
    summary = strip_emojis(editorial.get("summary", ""))
    sum_lines = wrap_text_pixels(summary, font_sum, 920, draw)
    
    sy = sum_top + 22
    for line in sum_lines[:3]:
        draw.text((80, sy), line, fill="#ECFDF5", font=font_sum)
        sy += 36
        
    draw_footer_brand(draw, y_pos=1275, bg_is_dark=True)
    card.save(output_path)
    return output_path


# ==================================================
# LAYOUT D — SPORTS / CULTURE (Full-Bleed Image)
# ==================================================
def render_layout_d(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    card = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#0F172A")
    draw = ImageDraw.Draw(card)
    
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            iw, ih = img.size
            ratio = 1350 / ih
            nw = int(iw * ratio)
            resized = img.resize((nw, 1350), Image.Resampling.LANCZOS)
            if nw > 1080:
                cropped = resized.crop(((nw - 1080) // 2, 0, (nw - 1080) // 2 + 1080, 1350))
            else:
                cropped = Image.new("RGB", (1080, 1350), "#0F172A")
                cropped.paste(resized, ((1080 - nw) // 2, 0))
            card.paste(cropped, (0, 0))
        except Exception:
            pass
            
    # Dark gradient overlay at bottom
    overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for gy in range(400, 1350):
        alpha = int(240 * ((gy - 400) / 950))
        odraw.line([(0, gy), (1080, gy)], fill=(15, 23, 42, alpha))
        
    card = Image.alpha_composite(card.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)
    
    draw_header_brand(draw, accent_color="#F59E0B", bg_is_dark=True)
    
    # Big Headline at bottom
    headline = strip_emojis(editorial.get("headline", ""))
    font_hl, hl_lines = fit_headline_font(headline, max_width=980, max_lines=3, start_size=54, draw=draw)
    
    y = 850
    for line in hl_lines:
        draw.text((50, y), line, fill="#FFFFFF", font=font_hl, stroke_width=2, stroke_fill="#000000")
        y += font_hl.size + 12
        
    # Summary
    font_sum = load_font("regular", 26)
    summary = strip_emojis(editorial.get("summary", ""))
    sum_lines = wrap_text_pixels(summary, font_sum, 980, draw)
    
    for line in sum_lines[:3]:
        draw.text((50, y), line, fill="#F1F5F9", font=font_sum)
        y += 36
        
    draw_footer_brand(draw, y_pos=1275, bg_is_dark=True)
    card.save(output_path)
    return output_path


# ==================================================
# MASTER POSTER RENDERER ROUTER
# ==================================================
def create_trending_poster(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    """
    Renders a 4:5 Instagram Portrait Poster (1080 x 1350 px) by selecting the designated
    layout type (LAYOUT_A, LAYOUT_B, LAYOUT_C, LAYOUT_D).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    layout = editorial.get("layout_type", "LAYOUT_A").upper()
    
    print(f"  🎨 [PosterGenerator] Rendering 4:5 Portrait Poster (1080x1350) using {layout}...")
    
    if layout == "LAYOUT_B":
        return render_layout_b(editorial, image_path, output_path)
    elif layout == "LAYOUT_C":
        return render_layout_c(editorial, image_path, output_path)
    elif layout == "LAYOUT_D":
        return render_layout_d(editorial, image_path, output_path)
    else:
        return render_layout_a(editorial, image_path, output_path)
