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
    TEMP_DIR,
    FONT_BOLD,
    FONT_REGULAR,
    BRAND_NAME,
    INSTAGRAM_ACCOUNT,
    ANCHOR_SCARF_IMAGE,
    ANCHOR_GAITER_IMAGE
)

def create_anchor_scene_frame(anchor_type: str, headline: str, category: str) -> Path:
    """
    Renders a 1080x1920 frame featuring the masked anchor, news desk,
    top brand bar, and breaking news lower-third banner.
    """
    out_path = TEMP_DIR / f"anchor_scene_{anchor_type}.png"
    anchor_img_path = ANCHOR_SCARF_IMAGE if anchor_type == "scarf" else ANCHOR_GAITER_IMAGE

    # Base frame
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (8, 12, 24, 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Load Anchor Image (crop/scale to fit 1080x1920 vertically)
    if anchor_img_path.exists():
        anchor = Image.open(anchor_img_path).convert("RGBA")
        aspect = anchor.width / anchor.height
        target_h = int(VIDEO_WIDTH / aspect)
        anchor_resized = anchor.resize((VIDEO_WIDTH, target_h), Image.Resampling.LANCZOS)
        offset_y = (VIDEO_HEIGHT - target_h) // 2 + 80
        canvas.paste(anchor_resized, (0, offset_y), anchor_resized)

    # 2. Top Header Brand Bar (Glassmorphism dark style)
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 140)], fill=(12, 18, 34, 235))
    draw.rectangle([(0, 136), (VIDEO_WIDTH, 140)], fill=(225, 29, 72, 255))

    font_brand = ImageFont.truetype(str(FONT_BOLD), 36) if FONT_BOLD.exists() else ImageFont.load_default()
    font_live = ImageFont.truetype(str(FONT_BOLD), 22) if FONT_BOLD.exists() else ImageFont.load_default()
    font_cat = ImageFont.truetype(str(FONT_BOLD), 24) if FONT_BOLD.exists() else ImageFont.load_default()

    draw.text((40, 42), BRAND_NAME, fill=(255, 255, 255), font=font_brand)

    # Pulsing Live Badge
    draw.rounded_rectangle([(VIDEO_WIDTH - 160, 42), (VIDEO_WIDTH - 40, 84)], radius=8, fill=(225, 29, 72))
    draw.text((VIDEO_WIDTH - 140, 49), "● LIVE", fill=(255, 255, 255), font=font_live)

    # 3. Lower-Third Breaking News Graphic Banner (at y=1400 to 1620)
    banner_y = 1400
    # Red category pill
    draw.rectangle([(50, banner_y - 36), (360, banner_y)], fill=(225, 29, 72))
    draw.text((65, banner_y - 30), f"⚡ {category.upper()[:18]}", fill=(255, 255, 255), font=font_cat)

    # Dark blue main headline container with glowing cyan border
    draw.rectangle([(50, banner_y), (VIDEO_WIDTH - 50, banner_y + 150)], fill=(12, 20, 38, 245), outline=(56, 189, 248, 220), width=2)

    font_headline = ImageFont.truetype(str(FONT_BOLD), 32) if FONT_BOLD.exists() else ImageFont.load_default()
    words = headline.split()
    line1, line2 = "", ""
    for w in words:
        if len(line1 + " " + w) <= 34:
            line1 += (" " if line1 else "") + w
        else:
            line2 += (" " if line2 else "") + w

    draw.text((75, banner_y + 25), line1, fill=(255, 255, 255), font=font_headline)
    if line2:
        draw.text((75, banner_y + 80), line2[:38], fill=(253, 224, 71), font=font_headline)

    canvas.convert("RGB").save(out_path, "PNG")
    return out_path


def create_outro_frame() -> Path:
    """Renders the final closing slide for NEWS NIT IIT."""
    out_path = TEMP_DIR / "outro_slide.png"
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 15, 30, 255))
    draw = ImageDraw.Draw(canvas)

    font_big = ImageFont.truetype(str(FONT_BOLD), 64) if FONT_BOLD.exists() else ImageFont.load_default()
    font_sub = ImageFont.truetype(str(FONT_REGULAR), 32) if FONT_REGULAR.exists() else ImageFont.load_default()
    font_handle = ImageFont.truetype(str(FONT_BOLD), 38) if FONT_BOLD.exists() else ImageFont.load_default()

    draw.text(((VIDEO_WIDTH - 520) // 2, 700), BRAND_NAME, fill=(255, 255, 255), font=font_big)
    draw.text(((VIDEO_WIDTH - 520) // 2 + 50, 800), "Your Campus, Our News", fill=(253, 224, 71), font=font_sub)

    box_rect = [(VIDEO_WIDTH - 600) // 2, 940, (VIDEO_WIDTH + 600) // 2, 1040]
    draw.rounded_rectangle(box_rect, radius=20, fill=(225, 29, 72))
    draw.text(((VIDEO_WIDTH - 460) // 2, 965), f"FOLLOW {INSTAGRAM_ACCOUNT}", fill=(255, 255, 255), font=font_handle)

    canvas.convert("RGB").save(out_path, "PNG")
    return out_path

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
    Creates an advanced, broadcast-grade 1080x1920 reading frame for the published
    Instagram post with HUD tech corners, glowing borders, stat badges,
    and a pause-to-read banner.
    """
    from news_anchor_ai.config import TEMP_DIR
    out_path = TEMP_DIR / "framed_post_slide.png"

    # Base canvas (dark broadcast newsroom palette)
    base = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (6, 10, 20, 255))
    draw = ImageDraw.Draw(base)

    # 1. Subtle background grid
    for y in range(160, VIDEO_HEIGHT - 200, 100):
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(15, 23, 42, 100), width=1)
    for x in range(100, VIDEO_WIDTH, 120):
        draw.line([(x, 160), (x, VIDEO_HEIGHT - 200)], fill=(15, 23, 42, 60), width=1)

    # 2. Header Bar with Red & Cyan Accents
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 140)], fill=(12, 18, 32, 245))
    draw.rectangle([(0, 136), (VIDEO_WIDTH, 140)], fill=(225, 29, 72, 255))  # red accent line

    # Fonts
    font_bold_title = ImageFont.truetype(str(FONT_BOLD), 36) if FONT_BOLD.exists() else ImageFont.load_default()
    font_cat = ImageFont.truetype(str(FONT_BOLD), 22) if FONT_BOLD.exists() else ImageFont.load_default()
    font_hint = ImageFont.truetype(str(FONT_BOLD), 26) if FONT_BOLD.exists() else ImageFont.load_default()
    font_badge = ImageFont.truetype(str(FONT_BOLD), 20) if FONT_BOLD.exists() else ImageFont.load_default()

    # Brand Title
    draw.text((40, 38), BRAND_NAME, fill=(255, 255, 255), font=font_bold_title)
    draw.rectangle([(320, 42), (520, 78)], fill=(225, 29, 72))
    draw.text((335, 46), f"● {category.upper()[:16]}", fill=(255, 255, 255), font=font_cat)

    # 3. Load & Frame the Post Image
    try:
        post_img = Image.open(post_image_path).convert("RGBA")
        max_w, max_h = 920, 1060
        post_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        x = (VIDEO_WIDTH - post_img.width) // 2
        y = 200 + (max_h - post_img.height) // 2

        # Glowing cyan outer border
        outer_box = [x - 8, y - 8, x + post_img.width + 8, y + post_img.height + 8]
        draw.rounded_rectangle(outer_box, radius=16, fill=(15, 23, 42, 255), outline=(56, 189, 248, 220), width=3)

        # Paste the post image
        base.paste(post_img, (x, y), post_img)

        # 4. HUD Viewfinder Tech Corners (Professional Graphic Accents)
        c_len = 35
        # Top-Left corner
        draw.line([(x - 16, y - 16), (x - 16 + c_len, y - 16)], fill=(253, 224, 71), width=4)
        draw.line([(x - 16, y - 16), (x - 16, y - 16 + c_len)], fill=(253, 224, 71), width=4)
        # Top-Right corner
        draw.line([(x + post_img.width + 16, y - 16), (x + post_img.width + 16 - c_len, y - 16)], fill=(253, 224, 71), width=4)
        draw.line([(x + post_img.width + 16, y - 16), (x + post_img.width + 16, y - 16 + c_len)], fill=(253, 224, 71), width=4)
        # Bottom-Left corner
        draw.line([(x - 16, y + post_img.height + 16), (x - 16 + c_len, y + post_img.height + 16)], fill=(253, 224, 71), width=4)
        draw.line([(x - 16, y + post_img.height + 16), (x - 16, y + post_img.height + 16 - c_len)], fill=(253, 224, 71), width=4)
        # Bottom-Right corner
        draw.line([(x + post_img.width + 16, y + post_img.height + 16), (x + post_img.width + 16 - c_len, y + post_img.height + 16)], fill=(253, 224, 71), width=4)
        draw.line([(x + post_img.width + 16, y + post_img.height + 16), (x + post_img.width + 16, y + post_img.height + 16 - c_len)], fill=(253, 224, 71), width=4)

        # 5. Floating Status Badges (Left & Right)
        draw.rounded_rectangle([(x, y - 48), (x + 220, y - 14)], radius=8, fill=(225, 29, 72))
        draw.text((x + 18, y - 43), "OFFICIAL DOCUMENT", fill=(255, 255, 255), font=font_badge)

        draw.rounded_rectangle([(x + post_img.width - 180, y - 48), (x + post_img.width, y - 14)], radius=8, fill=(30, 41, 59), outline=(56, 189, 248), width=1)
        draw.text((x + post_img.width - 160, y - 43), "VERIFIED SOURCE", fill=(56, 189, 248), font=font_badge)

        # 6. High-Contrast Interactive Pause Banner
        badge_y = y + post_img.height + 30
        badge_rect = [(VIDEO_WIDTH - 480) // 2, badge_y, (VIDEO_WIDTH + 480) // 2, badge_y + 52]
        draw.rounded_rectangle(badge_rect, radius=14, fill=(15, 23, 42, 240), outline=(245, 158, 11, 240), width=3)
        draw.text(((VIDEO_WIDTH - 480) // 2 + 25, badge_y + 11), "⏸️ TAP & HOLD TO READ FULL NOTICE", fill=(253, 224, 71), font=font_hint)

    except Exception as e:
        print(f"[Studio Builder] Warning: Could not frame post image: {e}")

    base.convert("RGB").save(out_path, "PNG")
    return out_path
