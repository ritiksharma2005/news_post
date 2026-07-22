"""
instagram_digest/design_digest_post.py
Generates 1080x1080 Branded Posters for "Campus Digest" Series (@news.nit_iit).
"""

import os
import datetime
from PIL import Image, ImageDraw, ImageFont


def get_font(font_type="bold", size=32):
    paths_to_try = [
        "fonts/DejaVuSans-Bold.ttf" if font_type == "bold" else "fonts/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if font_type == "bold" else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "Arial.ttf"
    ]
    for p in paths_to_try:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_camera_logo(draw, x, y, color):
    """Draws a camera logo icon in RGB mode."""
    draw.rounded_rectangle([(x, y + 5), (x + 36, y + 29)], radius=4, fill=color)
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 5)], fill=color)
    draw.ellipse([(x + 10, y + 10), (x + 26, y + 26)], fill="#F5EFEB", outline=color, width=2)
    draw.ellipse([(x + 14, y + 14), (x + 22, y + 22)], fill=color)


def create_digest_card(headline, bullets, why_it_matters, output_path="output/digest_card.png"):
    """
    Renders a 1080x1080 Campus Digest Poster.
    """
    width, height = 1080, 1080
    bg_color = "#F5EFEB"
    accent_color = "#0284C7"  # Deep Sky Blue Theme for Campus Digest
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)

    font_brand = get_font("bold", 34)
    font_headline = get_font("bold", 42)
    font_bullet = get_font("bold", 30)
    font_why = get_font("regular", 28)
    font_footer = get_font("bold", 30)

    # 1. Top Stripe & Header
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    draw.text((40, 32), "🎓 CAMPUS DIGEST", fill="#1A1A1A", font=font_brand)
    draw.text((930, 32), "2026", fill="#1A1A1A", font=font_brand)
    draw.line([(40, 80), (1040, 80)], fill="#1A1A1A", width=3)

    # 2. Headline
    y_cursor = 98
    words = headline.strip().split()
    lines = []
    cur = ""
    for w in words:
        if len(cur + " " + w) < 36:
            cur += " " + w if cur else w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    for line in lines[:2]:
        draw.text((40, y_cursor), line, fill="#1A1A1A", font=font_headline)
        y_cursor += 50

    y_cursor += 10
    draw.rectangle([(40, y_cursor), (260, y_cursor + 6)], fill=accent_color)
    draw.line([(260, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 3. Key Bullet Points Box
    y_cursor += 25
    box_top = y_cursor
    box_bottom = box_top + (len(bullets[:3]) * 48) + 30
    draw.rounded_rectangle([(40, box_top), (1040, box_bottom)], radius=12, fill="#E0F2FE", outline="#BAE6FD", width=2)
    draw.rectangle([(40, box_top), (52, box_bottom)], fill=accent_color)

    b_y = box_top + 18
    for b in bullets[:3]:
        draw.text((72, b_y), b, fill="#0369A1", font=font_bullet)
        b_y += 48

    # 4. "Why It Matters" Box (Bottom)
    box2_top = box_bottom + 25
    box2_bottom = 990
    draw.rounded_rectangle([(40, box2_top), (1040, box2_bottom)], radius=12, fill="#FFFFFF", outline="#E2E8F0", width=2)
    draw.rectangle([(40, box2_top), (52, box2_bottom)], fill="#0284C7")

    draw.text((72, box2_top + 16), "WHY IT MATTERS FOR STUDENTS:", fill=accent_color, font=get_font("bold", 24))

    words_why = why_it_matters.strip().split()
    lines_why = []
    cur = ""
    for w in words_why:
        if len(cur + " " + w) < 54:
            cur += " " + w if cur else w
        else:
            lines_why.append(cur)
            cur = w
    if cur:
        lines_why.append(cur)

    w_y = box2_top + 48
    for line in lines_why[:3]:
        draw.text((72, w_y), line, fill="#334155", font=font_why)
        w_y += 34

    # 5. Footer Watermark (📸 @news.nit_iit)
    footer_y = 1020
    footer_center_x = 410
    draw_camera_logo(draw, footer_center_x, footer_y + 2, accent_color)
    draw.text((footer_center_x + 46, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    print(f"  Campus Digest Card generated: {output_path}")
    return output_path
