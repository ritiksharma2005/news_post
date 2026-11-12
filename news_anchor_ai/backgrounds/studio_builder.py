"""
news_anchor_ai/backgrounds/studio_builder.py
Generates high-resolution 1080x1920 (9:16) broadcast studio elements,
dynamic newsroom overlays, lower-third breaking news banners,
and reading frames for the news post images.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from news_anchor_ai.config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    BACKGROUNDS_DIR,
    FONT_BOLD,
    FONT_REGULAR,
    BRAND_NAME
)

def create_studio_background(style: str = "blue") -> Path:
    """
    Creates a sleek 1080x1920 broadcast studio backdrop.
    Styles: 'blue' (Tech/Academic), 'red' (Breaking News), 'dark' (Evening Studio)
    """
    output_path = BACKGROUNDS_DIR / f"studio_{style}.png"
    if output_path.exists():
        return output_path

    img = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 14, 26, 255))
    draw = ImageDraw.Draw(img)

    # 1. Background gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if style == "red":
            r = int(25 + ratio * 45)
            g = int(8 + ratio * 10)
            b = int(14 + ratio * 18)
        else:  # blue/tech
            r = int(8 + ratio * 15)
            g = int(15 + ratio * 28)
            b = int(35 + ratio * 55)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(r, g, b, 255))

    # 2. Studio glow circles (ambient studio spotlights)
    spotlight_color = (220, 30, 45, 60) if style == "red" else (20, 110, 240, 60)
    spotlight = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    spot_draw = ImageDraw.Draw(spotlight)
    spot_draw.ellipse([(-200, 100), (600, 900)], fill=spotlight_color)
    spot_draw.ellipse([(600, 300), (1300, 1100)], fill=spotlight_color)
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img, spotlight)

    # 3. Horizontal studio grid lines
    grid_draw = ImageDraw.Draw(img)
    line_color = (255, 60, 70, 40) if style == "red" else (70, 160, 255, 35)
    for y in range(200, 1200, 90):
        grid_draw.line([(0, y), (VIDEO_WIDTH, y)], fill=line_color, width=1)

    # Save
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[Studio Builder] Generated background: {output_path.name}")
    return output_path


def create_post_reading_frame(post_image_path: str, headline: str, category: str = "OFFICIAL UPDATE") -> Path:
    """
    Creates a framed 1080x1920 slide featuring the actual published Instagram post
    so viewers can clearly pause and read the full news announcement.
    """
    from news_anchor_ai.config import TEMP_DIR
    out_path = TEMP_DIR / "framed_post_slide.png"

    # Base canvas
    base = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (8, 12, 22, 255))
    draw = ImageDraw.Draw(base)

    # Header Bar
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 140)], fill=(15, 23, 42, 240))
    draw.rectangle([(0, 136), (VIDEO_WIDTH, 140)], fill=(225, 29, 72, 255))  # red accent line

    # Fonts
    font_bold_title = ImageFont.truetype(str(FONT_BOLD), 36) if FONT_BOLD.exists() else ImageFont.load_default()
    font_cat = ImageFont.truetype(str(FONT_BOLD), 24) if FONT_BOLD.exists() else ImageFont.load_default()
    font_hint = ImageFont.truetype(str(FONT_REGULAR), 24) if FONT_REGULAR.exists() else ImageFont.load_default()

    # Brand Title
    draw.text((40, 35), BRAND_NAME, fill=(255, 255, 255), font=font_bold_title)
    draw.rectangle([(300, 42), (480, 76)], fill=(225, 29, 72), outline=None)
    draw.text((315, 45), category.upper()[:16], fill=(255, 255, 255), font=font_cat)

    # Load original post image and scale cleanly
    try:
        post_img = Image.open(post_image_path).convert("RGBA")
        # Target area: max width 960, max height 1100
        max_w, max_h = 960, 1100
        post_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        # Center position
        x = (VIDEO_WIDTH - post_img.width) // 2
        y = 200 + (max_h - post_img.height) // 2

        # Card shadow / glowing border
        shadow_rect = [x - 8, y - 8, x + post_img.width + 8, y + post_img.height + 8]
        draw.rounded_rectangle(shadow_rect, radius=16, fill=(30, 41, 59, 255), outline=(56, 189, 248, 180), width=3)

        # Paste the post image
        base.paste(post_img, (x, y), post_img)

        # Pause hint badge below card
        badge_y = y + post_img.height + 25
        badge_rect = [(VIDEO_WIDTH - 420) // 2, badge_y, (VIDEO_WIDTH + 420) // 2, badge_y + 44]
        draw.rounded_rectangle(badge_rect, radius=12, fill=(15, 23, 42, 220), outline=(245, 158, 11, 200), width=2)
        draw.text(((VIDEO_WIDTH - 420) // 2 + 30, badge_y + 8), "⏸️ TAP & HOLD TO READ FULL NOTICE", fill=(253, 224, 71), font=font_hint)

    except Exception as e:
        print(f"[Studio Builder] Warning: Could not frame post image: {e}")

    base.convert("RGB").save(out_path, "PNG")
    return out_path
