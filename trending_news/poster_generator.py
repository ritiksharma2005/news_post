"""
trending_news/poster_generator.py
4:5 Portrait Poster Engine (1080 x 1350 px) for @news.nit_iit
Implements Refined Warm Cream Header, Dynamic Category Label, Keyword Highlighted Headlines,
Natural Gradient Overlay, and 📸 @news.nit_iit Footer Branding.
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional
from .config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, BRAND_HANDLE, BRAND_HANDLE_WITH_ICON, BRAND_NAME,
    BRAND_HEADER_BG, BRAND_HEADER_TEXT, BRAND_COLOR_ACCENT, BRAND_BORDER_LINE,
    DEFAULT_HEADER_LABEL, FONTS_DIR
)


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


def draw_header_brand(draw: ImageDraw.ImageDraw, header_label: str = DEFAULT_HEADER_LABEL):
    """
    Renders top header banner with warm cream background (#FDFBF7),
    top orange accent line, NEWS.NIT_IIT on left, and dynamic label on right.
    """
    font_brand = load_font("bold", 30)
    font_tag = load_font("bold", 22)
    
    label_text = (header_label or DEFAULT_HEADER_LABEL).upper()
    
    # 1. Warm Cream Header Banner (Height: 90px)
    draw.rectangle([(0, 0), (CANVAS_WIDTH, 90)], fill=BRAND_HEADER_BG)
    # Top Orange Accent Stripe (Height: 10px)
    draw.rectangle([(0, 0), (CANVAS_WIDTH, 10)], fill=BRAND_COLOR_ACCENT)
    
    # Left: NEWS.NIT_IIT
    draw.text((50, 32), BRAND_NAME, fill=BRAND_HEADER_TEXT, font=font_brand)
    
    # Right: Dynamic Header Label (e.g., THE LATEST, INDIA, SPORTS)
    tag_w = draw.textlength(label_text, font=font_tag)
    draw.text((CANVAS_WIDTH - 50 - tag_w, 36), label_text, fill=BRAND_COLOR_ACCENT, font=font_tag)
    
    # Thin 1.5px Separator Line
    draw.line([(0, 90), (CANVAS_WIDTH, 90)], fill=BRAND_BORDER_LINE, width=2)


def draw_vector_camera_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 28, fill_color: str = "#0F172A", accent_color: str = "#F97316"):
    """
    Renders a crisp vector camera icon directly using PIL geometric shapes (RGB filled).
    """
    # 1. Main camera body (rounded rectangle)
    body_box = [(x, y + 5), (x + size, y + size + 1)]
    draw.rounded_rectangle(body_box, radius=5, fill=fill_color)
    
    # 2. Camera top flash bump
    bump_box = [(x + int(size * 0.3), y), (x + int(size * 0.7), y + 5)]
    draw.rectangle(bump_box, fill=fill_color)
    
    # 3. Lens outer ring
    lens_box = [(x + int(size * 0.22), y + 5 + int(size * 0.14)), (x + int(size * 0.78), y + 5 + int(size * 0.70))]
    draw.ellipse(lens_box, fill="#FFFFFF")
    
    # 4. Lens inner aperture
    aperture_box = [(x + int(size * 0.36), y + 5 + int(size * 0.28)), (x + int(size * 0.64), y + 5 + int(size * 0.56))]
    draw.ellipse(aperture_box, fill=accent_color)


def draw_footer_brand(draw: ImageDraw.ImageDraw):
    """
    Renders bottom header banner with warm cream background (#FDFBF7)
    and RGB vector camera icon + @news.nit_iit branding centered.
    """
    font_footer = load_font("bold", 30)
    
    # 1. Bottom Warm Cream Banner (Height: 80px)
    draw.rectangle([(0, 1270), (CANVAS_WIDTH, CANVAS_HEIGHT)], fill=BRAND_HEADER_BG)
    draw.line([(0, 1270), (CANVAS_WIDTH, 1270)], fill=BRAND_BORDER_LINE, width=2)
    
    # Centered: Vector Camera Icon + @news.nit_iit
    handle_text = BRAND_HANDLE
    handle_w = draw.textlength(handle_text, font=font_footer)
    
    icon_size = 28
    gap = 12
    total_w = icon_size + gap + handle_w
    
    start_x = int((CANVAS_WIDTH - total_w) // 2)
    y_pos = 1294
    
    # Draw vector camera icon (RGB)
    draw_vector_camera_icon(draw, x=start_x, y=y_pos - 2, size=icon_size, fill_color="#0F172A", accent_color=BRAND_COLOR_ACCENT)
    
    # Draw handle text
    draw.text((start_x + icon_size + gap, y_pos - 5), handle_text, fill=BRAND_HEADER_TEXT, font=font_footer)


def draw_highlighted_headline(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
    lines: List[str],
    highlight_text: str,
    x: int,
    start_y: int,
    line_gap: int = 12
) -> int:
    """
    Renders headline lines word-by-word. Words matching highlight_text are drawn
    in Brand Accent Orange (#F97316), while other words are drawn in White (#FFFFFF).
    """
    h_tokens = set(w.lower().strip(".,!?:;\"'") for w in (highlight_text or "").split())
    y = start_y
    
    for line in lines:
        words = line.split()
        cur_x = x
        for word in words:
            clean_w = word.lower().strip(".,!?:;\"'")
            is_highlighted = clean_w in h_tokens and len(clean_w) > 1
            color = BRAND_COLOR_ACCENT if is_highlighted else "#FFFFFF"
            
            draw.text((cur_x, y), word, fill=color, font=font, stroke_width=1, stroke_fill="#000000")
            cur_x += int(draw.textlength(word + " ", font=font))
        y += font.size + line_gap
        
    return y


def apply_bottom_gradient(card: Image.Image, start_y: int = 450, end_y: int = 1270) -> Image.Image:
    """Applies a smooth dark gradient overlay at the lower photographic area for maximum text readability."""
    overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    
    grad_height = end_y - start_y
    for gy in range(start_y, end_y):
        alpha = int(230 * ((gy - start_y) / grad_height))
        odraw.line([(0, gy), (CANVAS_WIDTH, gy)], fill=(15, 23, 42, alpha))
        
    return Image.alpha_composite(card.convert("RGBA"), overlay).convert("RGB")


def prepare_clean_source_photo(image_path: str, target_w: int = 1080, target_h: int = 680) -> Optional[Image.Image]:
    """
    Extracts the clean photographic subject from a source news card by cropping out
    the lower 42% portion where original source headlines, text overlays, and logos are baked in.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        img = Image.open(image_path).convert("RGB")
        iw, ih = img.size
        
        # 1. Crop top 58% of original image (where actual faces/photo subject are located)
        clean_top = img.crop((0, 0, iw, int(ih * 0.58)))
        
        # 2. Resize to fit target width & height cleanly
        ct_w, ct_h = clean_top.size
        ratio = target_w / ct_w
        nh = int(ct_h * ratio)
        resized = clean_top.resize((target_w, nh), Image.Resampling.LANCZOS)
        
        if nh >= target_h:
            final_crop = resized.crop((0, 0, target_w, target_h))
        else:
            final_crop = Image.new("RGB", (target_w, target_h), "#0F172A")
            final_crop.paste(resized, (0, 0))
            
        return final_crop
    except Exception as e:
        print(f"  [Photo Clean Error] {e}")
        return None


# ==================================================
# LAYOUT A — BREAKING / TRENDING (Refined Layout)
# ==================================================
def render_layout_a(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    card = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#0F172A")
    
    # 1. Main Clean Photographic Subject (Top 58% Crop, removing baked-in source text & logos)
    clean_photo = prepare_clean_source_photo(image_path, target_w=CANVAS_WIDTH, target_h=680)
    if clean_photo:
        card.paste(clean_photo, (0, 90))
            
    # 2. Dark Gradient Transition
    card = apply_bottom_gradient(card, start_y=450, end_y=1270)
    draw = ImageDraw.Draw(card)
    
    # 3. Warm Cream Top Header Banner
    header_label = editorial.get("header_label") or DEFAULT_HEADER_LABEL
    draw_header_brand(draw, header_label=header_label)
    
    # 4. Category Tag Pill
    category = editorial.get("category", "TRENDING").upper()
    font_badge = load_font("bold", 20)
    badge_w = draw.textlength(category, font=font_badge)
    draw.rounded_rectangle([(50, 780), (70 + badge_w, 816)], radius=6, fill=BRAND_COLOR_ACCENT)
    draw.text((60, 787), category, fill="#FFFFFF", font=font_badge)
    
    # 5. Headline (5-12 words) with Keyword Highlighting
    headline = strip_emojis(editorial.get("headline", ""))
    highlight = editorial.get("highlight_text", "")
    font_hl, hl_lines = fit_headline_font(headline, max_width=980, max_lines=3, start_size=50, draw=draw)
    
    y = draw_highlighted_headline(draw, font_hl, hl_lines, highlight, x=50, start_y=835)
    
    # 6. Concise Summary (1-2 sentences)
    font_sum = load_font("regular", 25)
    summary = strip_emojis(editorial.get("summary", ""))
    sum_lines = wrap_text_pixels(summary, font_sum, 980, draw)
    
    sy = y + 10
    for line in sum_lines[:2]:
        draw.text((50, sy), line, fill="#E2E8F0", font=font_sum)
        sy += 34
        
    # 7. Warm Cream Bottom Footer Banner
    draw_footer_brand(draw)
    
    card.save(output_path)
    return output_path


# ==================================================
# LAYOUT B — ACHIEVEMENT / EDUCATION (Refined Layout)
# ==================================================
def render_layout_b(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    return render_layout_a(editorial, image_path, output_path)


# ==================================================
# LAYOUT C — DATA / ECONOMY / SALARY (Metric Callout)
# ==================================================
def render_layout_c(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    card = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#0F172A")
    
    clean_photo = prepare_clean_source_photo(image_path, target_w=CANVAS_WIDTH, target_h=680)
    if clean_photo:
        card.paste(clean_photo, (0, 90))
            
    card = apply_bottom_gradient(card, start_y=450, end_y=1270)
    draw = ImageDraw.Draw(card)
    
    header_label = editorial.get("header_label") or "DATA & ECONOMY"
    draw_header_brand(draw, header_label=header_label)
    
    # Metric Callout Text
    metric = editorial.get("metric_callout") or "BIG NUMBERS"
    font_metric = load_font("bold", 68)
    draw.text((50, 720), metric, fill=BRAND_COLOR_ACCENT, font=font_metric, stroke_width=2, stroke_fill="#000000")
    
    # Headline
    headline = strip_emojis(editorial.get("headline", ""))
    highlight = editorial.get("highlight_text", "")
    font_hl, hl_lines = fit_headline_font(headline, max_width=980, max_lines=3, start_size=46, draw=draw)
    
    y = draw_highlighted_headline(draw, font_hl, hl_lines, highlight, x=50, start_y=810)
    
    # Summary
    font_sum = load_font("regular", 25)
    summary = strip_emojis(editorial.get("summary", ""))
    sum_lines = wrap_text_pixels(summary, font_sum, 980, draw)
    
    sy = y + 10
    for line in sum_lines[:2]:
        draw.text((50, sy), line, fill="#E2E8F0", font=font_sum)
        sy += 34
        
    draw_footer_brand(draw)
    card.save(output_path)
    return output_path


# ==================================================
# LAYOUT D — SPORTS / CULTURE (Full-Bleed Visual)
# ==================================================
def render_layout_d(editorial: Dict[str, Any], image_path: Optional[str], output_path: str) -> str:
    return render_layout_a(editorial, image_path, output_path)


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
    
    print(f"  🎨 [PosterGenerator] Rendering Refined 4:5 Portrait Poster (1080x1350) using {layout}...")
    
    if layout == "LAYOUT_C":
        return render_layout_c(editorial, image_path, output_path)
    else:
        return render_layout_a(editorial, image_path, output_path)
