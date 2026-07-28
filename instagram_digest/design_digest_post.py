"""
instagram_digest/design_digest_post.py
Generates 1080x1080 Branded Posters for "Campus Digest" Series (@news.nit_iit)
with the original post image in the center.
"""

import os
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
    """Draws a camera logo icon directly in RGB mode."""
    draw.rounded_rectangle([(x, y + 5), (x + 36, y + 29)], radius=4, fill=color)
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 5)], fill=color)
    draw.ellipse([(x + 10, y + 10), (x + 26, y + 26)], fill="#F5EFEB", outline=color, width=2)
    draw.ellipse([(x + 14, y + 14), (x + 22, y + 22)], fill=color)


def create_digest_card(headline, bullets, why_it_matters, image_path=None, output_path="output/digest_card.png"):
    """
    Renders a 1080x1080 Square Campus Digest Poster with centered image.
    """
    width, height = 1080, 1080
    bg_color = "#F5EFEB"
    accent_color = "#0284C7"  # Deep Sky Blue Theme
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)

    font_brand = get_font("bold", 34)
    font_headline = get_font("bold", 40)
    font_bullet = get_font("regular", 28)
    font_footer = get_font("bold", 30)

    # 1. Top Stripe & Header
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    draw.text((40, 30), "🎓 CAMPUS DIGEST", fill="#1A1A1A", font=font_brand)
    draw.text((930, 30), "2026", fill="#1A1A1A", font=font_brand)
    draw.line([(40, 78), (1040, 78)], fill="#1A1A1A", width=3)

    # 2. Headline (Fits 1 or 2 lines)
    y_cursor = 94
    words = headline.strip().split()
    lines = []
    cur = ""
    for w in words:
        if len(cur + " " + w) < 38:
            cur += " " + w if cur else w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    for line in lines[:2]:
        draw.text((40, y_cursor), line, fill="#1A1A1A", font=font_headline)
        y_cursor += 46

    # Underline
    y_cursor += 10
    draw.rectangle([(40, y_cursor), (260, y_cursor + 6)], fill=accent_color)
    draw.line([(260, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 3. Dynamic Summary Box Details first (anchored at bottom)
    display_bullets = bullets[:3]
    line_height = 36
    box_padding_vertical = 16
    content_height = (len(display_bullets) * line_height) + (box_padding_vertical * 2) + 40 # extra space for "why it matters"

    footer_y = 1022
    box_bottom = footer_y - 20
    box_top = box_bottom - content_height
    box_left, box_right = 40, 1040

    # 4. Center Image Section (Fills exact remaining middle space!)
    image_top = y_cursor + 16
    image_bottom = box_top - 16
    image_height = max(260, image_bottom - image_top)

    if image_path and os.path.exists(image_path):
        try:
            main_img = Image.open(image_path).convert("RGB")
            main_img = main_img.resize((1080, image_height), Image.Resampling.LANCZOS)
            card.paste(main_img, (0, image_top))
        except Exception as e:
            print(f"Error placing image: {e}")
            draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
    else:
        draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
        draw.text((460, image_top + (image_height // 2) - 15), "news.nit_iit", fill="#64748B", font=font_brand)

    # 5. Draw Summary Box
    draw.rounded_rectangle([(box_left, box_top), (box_right, box_bottom)], radius=12, fill="#E0F2FE", outline="#BAE6FD", width=2)
    draw.rectangle([(box_left, box_top), (box_left + 12, box_bottom)], fill=accent_color)

    # Draw Bullets inside box
    sum_y = box_top + box_padding_vertical
    for b in display_bullets:
        draw.text((68, sum_y), b, fill="#0369A1", font=font_bullet)
        sum_y += line_height

    # Draw Why It Matters inside box
    sum_y += 10
    draw.text((68, sum_y), f"💡 Why it matters: {why_it_matters[:90]}...", fill="#075985", font=get_font("bold", 24))

    # 6. Footer Watermark (📸 @news.nit_iit)
    footer_center_x = 420
    draw_camera_logo(draw, footer_center_x, footer_y + 2, accent_color)
    draw.text((footer_center_x + 46, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    print(f"  Campus Digest Card generated: {output_path}")
    return output_path
