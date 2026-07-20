"""
design_post.py
Generates 1080x1350 Instagram poster cards matching the exact News.nit_iit template:
- Top Coral Accent Bar + Header (News.nit_iit | 2026)
- Bold Headline with Accent Underline on top
- Full-width image in the middle
- Tinted Summary Box with left accent bar at bottom
- Watermark @news.nit_iit footer
"""

import os
from PIL import Image, ImageDraw, ImageFont


BUCKET_COLORS = {
    "IndianPolitics": {"accent": "#D95D39", "tint_bg": "#FDF0EB", "tint_border": "#F8C6B9", "text_dark": "#6E2A1A"},
    "StudentEducation": {"accent": "#2A9D8F", "tint_bg": "#EBF7F5", "tint_border": "#B2E2DD", "text_dark": "#16524A"},
    "TechInnovation": {"accent": "#7209B7", "tint_bg": "#F6EDFC", "tint_border": "#D8B4F3", "text_dark": "#3B0561"},
}

DEFAULT_COLOR = {"accent": "#D95D39", "tint_bg": "#FDF0EB", "tint_border": "#F8C6B9", "text_dark": "#6E2A1A"}


def get_font(font_type="bold", size=36):
    """Robust font loader working across macOS, Linux (GitHub Actions), and Windows."""
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

    # Fallback for newer Pillow versions with size parameter
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def create_card(headline, summary, image_path, bucket="StudentEducation", language="en", emoji="📩", output_path="output/card.png"):
    """
    Renders the exact News.nit_iit template layout (1080x1350).
    """
    theme = BUCKET_COLORS.get(bucket, DEFAULT_COLOR)
    accent_color = theme["accent"]

    width, height = 1080, 1350
    bg_color = "#F5EFEB"  # Off-white / Cream background
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)

    # Load High-Res Fonts
    font_header = get_font("bold", 38)
    font_headline = get_font("bold", 48)
    font_summary = get_font("regular", 32)
    font_footer = get_font("bold", 34)

    # 1. Top Accent Stripe
    draw.rectangle([(0, 0), (width, 22)], fill=accent_color)

    # 2. Header Bar (News.nit_iit ...... 2026)
    draw.text((40, 38), "News.nit_iit", fill="#1A1A1A", font=font_header)
    draw.text((930, 38), "2026", fill="#1A1A1A", font=font_header)
    draw.line([(40, 95), (1040, 95)], fill="#1A1A1A", width=3)

    # 3. Headline Text (Top Section)
    y_cursor = 125
    formatted_headline = f"{emoji} {headline}"

    # Wrap Headline
    words = formatted_headline.split()
    headline_lines = []
    cur_line = ""
    for w in words:
        if len(cur_line + " " + w) < 32:
            cur_line += " " + w if cur_line else w
        else:
            headline_lines.append(cur_line)
            cur_line = w
    if cur_line:
        headline_lines.append(cur_line)

    for line in headline_lines[:3]:
        draw.text((40, y_cursor), line, fill="#1A1A1A", font=font_headline)
        y_cursor += 62

    # Accent Underline
    y_cursor += 20
    draw.rectangle([(40, y_cursor), (280, y_cursor + 7)], fill=accent_color)
    draw.line([(280, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 4. Middle Image Section (Full Width 1080x490)
    image_top = y_cursor + 25
    image_height = 490
    if image_path and os.path.exists(image_path):
        try:
            main_img = Image.open(image_path).convert("RGB")
            main_img = main_img.resize((1080, image_height), Image.Resampling.LANCZOS)
            card.paste(main_img, (0, image_top))
        except Exception as e:
            print(f"Error placing image: {e}")
            draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
    else:
        # Placeholder background if no image
        draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")

    # 5. Summary Box Section (Bottom)
    box_top = image_top + image_height + 30
    box_bottom = 1240
    box_left, box_right = 40, 1040

    # Draw Tinted Summary Box
    draw.rounded_rectangle([(box_left, box_top), (box_right, box_bottom)], radius=16, fill=theme["tint_bg"], outline=theme["tint_border"], width=2)
    # Draw Left Vertical Accent Bar
    draw.rectangle([(box_left, box_top), (box_left + 14, box_bottom)], fill=accent_color)

    # Wrap Summary Text
    sum_words = summary.split()
    sum_lines = []
    cur_sum = ""
    for w in sum_words:
        if len(cur_sum + " " + w) < 46:
            cur_sum += " " + w if cur_sum else w
        else:
            sum_lines.append(cur_sum)
            cur_sum = w
    if cur_sum:
        sum_lines.append(cur_sum)

    sum_y = box_top + 28
    for line in sum_lines[:5]:
        draw.text((78, sum_y), line, fill=theme["text_dark"], font=font_summary)
        sum_y += 44

    # 6. Footer Watermark
    draw.text((430, 1285), "📸 @news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    print(f"  Poster card generated: {output_path}")
    return output_path
