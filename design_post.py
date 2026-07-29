"""
design_post.py
Master 1080x1080 Square Poster Generator for @news.nit_iit:
- Fixed 1080 x 1080 Square Instagram Post Ratio (1:1)
- Fully Dynamic Headline (1 to 4 lines adjustable)
- Fully Dynamic Summary Box (2 to 5 lines adjustable)
- Smart Image Resizing (fills exact middle space with ZERO gaps)
- Camera Logo & Username footer anchored at bottom
"""

import os
from PIL import Image, ImageDraw, ImageFont


BUCKET_COLORS = {
    "IndianPolitics": {
        "accent": "#D95D39", 
        "tint_bg": "#FDF0EB", 
        "tint_border": "#F8C6B9", 
        "text_dark": "#6E2A1A",
    },
    "StudentEducation": {
        "accent": "#2A9D8F", 
        "tint_bg": "#EBF7F5", 
        "tint_border": "#B2E2DD", 
        "text_dark": "#16524A",
    },
    "TechInnovation": {
        "accent": "#7209B7", 
        "tint_bg": "#F6EDFC", 
        "tint_border": "#D8B4F3", 
        "text_dark": "#3B0561",
    },
}

DEFAULT_COLOR = {
    "accent": "#D95D39", 
    "tint_bg": "#FDF0EB", 
    "tint_border": "#F8C6B9", 
    "text_dark": "#6E2A1A",
}


def get_font(font_type="bold", size=32):
    """Loads text font for macOS, Linux, or Windows."""
    paths_to_try = []
    if font_type == "bold":
        paths_to_try = [
            "fonts/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
            "Arial Bold.ttf",
        ]
    else:
        paths_to_try = [
            "fonts/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "Arial.ttf",
        ]

    for p in paths_to_try:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_camera_logo(draw, x, y, color):
    """Draws a crisp camera logo icon directly on the canvas."""
    draw.rounded_rectangle([(x, y + 5), (x + 36, y + 29)], radius=4, fill=color)
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 5)], fill=color)
    draw.ellipse([(x + 10, y + 10), (x + 26, y + 26)], fill="#F5EFEB", outline=color, width=2)
    draw.ellipse([(x + 14, y + 14), (x + 22, y + 22)], fill=color)


def strip_emojis(text):
    """Removes all emojis and special dingbat symbols to prevent box rendering bugs."""
    import re
    # Match standard emoji Unicode ranges, CJK symbols, and dingbats
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2b50\u2b06\u2192]', '', text).strip()


def create_card(headline, summary, image_path, bucket="StudentEducation", language="en", emoji=None, output_path="output/card.png"):
    """
    Renders a 1080x1080 Square Poster with fully dynamic headline, summary, and auto-filling image.
    """
    theme = BUCKET_COLORS.get(bucket, DEFAULT_COLOR)
    accent_color = theme["accent"]

    # 🔹 1:1 SQUARE INSTAGRAM POST RATIO (1080 x 1080)
    width, height = 1080, 1080
    bg_color = "#F5EFEB"  # Off-white / Cream background
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)

    # Load Fonts
    font_header = get_font("bold", 34)
    font_headline = get_font("bold", 40)
    font_summary = get_font("regular", 28)
    font_footer = get_font("bold", 30)

    # 1. Top Accent Stripe
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)

    # 2. Header Bar (News.nit_iit ...... 2026)
    draw.text((40, 30), "News.nit_iit", fill="#1A1A1A", font=font_header)
    draw.text((930, 30), "2026", fill="#1A1A1A", font=font_header)
    draw.line([(40, 78), (1040, 78)], fill="#1A1A1A", width=3)

    # 3. FULLY DYNAMIC Headline Section (Fits 1, 2, 3, or 4 lines naturally!)
    y_cursor = 94
    clean_headline = strip_emojis(headline)

    words = clean_headline.split()
    headline_lines = []
    cur_line = ""
    for w in words:
        if len(cur_line + " " + w) < 38:
            cur_line += " " + w if cur_line else w
        else:
            headline_lines.append(cur_line)
            cur_line = w
    if cur_line:
        headline_lines.append(cur_line)

    for line in headline_lines:
        draw.text((40, y_cursor), line, fill="#1A1A1A", font=font_headline)
        y_cursor += 48

    # Accent Underline
    y_cursor += 10
    draw.rectangle([(40, y_cursor), (260, y_cursor + 6)], fill=accent_color)
    draw.line([(260, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 4. FULLY DYNAMIC Summary Box Calculation
    clean_summary = strip_emojis(summary)
    sum_words = clean_summary.split()
    sum_lines = []
    cur_sum = ""
    for w in sum_words:
        if len(cur_sum + " " + w) < 52:
            cur_sum += " " + w if cur_sum else w
        else:
            sum_lines.append(cur_sum)
            cur_sum = w
    if cur_sum:
        sum_lines.append(cur_sum)

    display_summary_lines = sum_lines[:5]
    line_height = 36
    box_padding_vertical = 16
    content_height = (len(display_summary_lines) * line_height) + (box_padding_vertical * 2)

    # Anchor Footer at bottom of Square Card
    footer_y = 1022
    footer_center_x = 420
    box_bottom = footer_y - 20
    box_top = box_bottom - content_height
    box_left, box_right = 40, 1040

    # 5. SMART MIDDLE IMAGE RESIZING (Fills exact middle space between headline & summary!)
    image_top = y_cursor + 16
    image_bottom = box_top - 16
    image_height = max(260, image_bottom - image_top)

    if image_path and os.path.exists(image_path):
        try:
            main_img = Image.open(image_path).convert("RGB")
            main_img = main_img.resize((1000, image_height), Image.Resampling.LANCZOS)
            card.paste(main_img, (40, image_top))
            # Draw a crisp, thin border around the photo to match the editorial template
            draw.rectangle([(40, image_top), (1040, image_top + image_height)], outline="#1A1A1A", width=2)
        except Exception as e:
            print(f"Error placing image: {e}")
            draw.rectangle([(40, image_top), (1040, image_top + image_height)], fill="#CBD5E1", outline="#1A1A1A", width=2)
    else:
        draw.rectangle([(40, image_top), (1040, image_top + image_height)], fill="#CBD5E1", outline="#1A1A1A", width=2)
        draw.text((460, image_top + (image_height // 2) - 15), "news.nit_iit", fill="#64748B", font=font_header)

    # Draw Dynamic Summary Box
    draw.rounded_rectangle([(box_left, box_top), (box_right, box_bottom)], radius=12, fill=theme["tint_bg"], outline=theme["tint_border"], width=2)
    draw.rectangle([(box_left, box_top), (box_left + 12, box_bottom)], fill=accent_color)

    # Draw Summary Lines inside box
    sum_y = box_top + box_padding_vertical
    for line in display_summary_lines:
        draw.text((68, sum_y), line, fill=theme["text_dark"], font=font_summary)
        sum_y += line_height

    # 6. Footer Watermark (📸 @news.nit_iit)
    draw_camera_logo(draw, footer_center_x, footer_y + 2, accent_color)
    draw.text((footer_center_x + 46, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    print(f"  Square Poster Generated: {output_path} (Headline: {len(headline_lines)} lines, Summary: {len(display_summary_lines)} lines)")
    return output_path
