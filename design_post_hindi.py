"""
design_post_hindi.py
Renders a 1080x1080 Square Hindi News Poster.
Uses Noto Sans Devanagari fonts to display clean Hindi headlines and summaries.
"""

import os
import re
from PIL import Image, ImageDraw, ImageFont

# Define Theme Colors (Matching English)
BUCKET_COLORS = {
    "IndianPolitics": {"accent": "#DC2626", "tint_bg": "#FEF2F2", "tint_border": "#FEE2E2", "text_dark": "#991B1B"},
    "StudentEducation": {"accent": "#059669", "tint_bg": "#ECFDF5", "tint_border": "#D1FAE5", "text_dark": "#065F46"},
    "TechInnovation": {"accent": "#7C3AED", "tint_bg": "#F5F3FF", "tint_border": "#EDE9FE", "text_dark": "#5B21B6"}
}
DEFAULT_COLOR = {"accent": "#0284C7", "tint_bg": "#F0F9FF", "tint_border": "#E0F2FE", "text_dark": "#075985"}


def get_font(style="regular", size=24):
    """Retrieves Noto Sans Devanagari font for high-quality Hindi rendering."""
    font_file = "NotoSansDevanagari-Regular.ttf" if style == "regular" else "NotoSansDevanagari-Bold.ttf"
    
    # Try multiple path resolutions
    paths_to_try = [
        os.path.join(os.path.dirname(__file__), "fonts", font_file),
        os.path.join("fonts", font_file),
        font_file
    ]
    for p in paths_to_try:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
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


def create_hindi_card(headline, summary, image_path, bucket="StudentEducation", output_path="output/cards/hindi_card.png"):
    """Renders a square poster card in Hindi."""
    theme = BUCKET_COLORS.get(bucket, DEFAULT_COLOR)
    accent_color = theme["accent"]

    width, height = 1080, 1080
    bg_color = "#F5EFEB"  # Off-white / Cream background
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)

    # Load Devanagari Fonts
    font_header = get_font("bold", 34)
    font_headline = get_font("bold", 38)
    font_summary = get_font("regular", 28)
    font_footer = get_font("bold", 30)

    # 1. Top Accent Stripe
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)

    # 2. Header Bar (Date top-left, Brand logo top-right)
    draw.text((40, 30), "2026", fill="#1A1A1A", font=font_header)
    draw.text((850, 30), "समाचार.nit_iit", fill="#1A1A1A", font=font_header)
    draw.line([(40, 78), (1040, 78)], fill="#1A1A1A", width=3)

    # 3. DYNAMIC Hindi Headline Section (Centered horizontally!)
    y_cursor = 94
    clean_headline = strip_emojis(headline)

    words = clean_headline.split()
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

    for line in headline_lines[:3]:  # Max 3 lines
        # Calculate line width to center it horizontally
        line_w = draw.textlength(line, font=font_headline)
        line_x = max(40, int((width - line_w) // 2))
        draw.text((line_x, y_cursor), line, fill="#1A1A1A", font=font_headline)
        y_cursor += 48

    # Accent Underline
    y_cursor += 10
    draw.rectangle([(40, y_cursor), (260, y_cursor + 6)], fill=accent_color)
    draw.line([(260, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 4. DYNAMIC Hindi Summary Box
    clean_summary = strip_emojis(summary)
    sum_words = clean_summary.split()
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

    display_summary_lines = sum_lines[:5]  # Cap at 5 lines
    line_height = 36
    box_padding_vertical = 16
    content_height = (len(display_summary_lines) * line_height) + (box_padding_vertical * 2)

    # Anchor Footer at bottom
    footer_y = 1022
    footer_center_x = 420
    box_bottom = footer_y - 20
    box_top = box_bottom - content_height
    box_left, box_right = 40, 1040

    # 5. SMART MIDDLE IMAGE RESIZING (Fits exactly between headline and summary box)
    image_top = y_cursor + 16
    image_bottom = box_top - 16
    image_height = max(260, image_bottom - image_top)

    if image_path and os.path.exists(image_path):
        try:
            main_img = Image.open(image_path).convert("RGB")
            main_img = main_img.resize((1000, image_height), Image.Resampling.LANCZOS)
            card.paste(main_img, (40, image_top))
            draw.rectangle([(40, image_top), (1040, image_top + image_height)], outline="#1A1A1A", width=2)
        except Exception as e:
            print(f"Error placing image: {e}")
            draw.rectangle([(40, image_top), (1040, image_top + image_height)], fill="#CBD5E1", outline="#1A1A1A", width=2)
    else:
        draw.rectangle([(40, image_top), (1040, image_top + image_height)], fill="#CBD5E1", outline="#1A1A1A", width=2)
        draw.text((440, image_top + (image_height // 2) - 15), "समाचार.nit_iit", fill="#64748B", font=font_header)

    # Draw Summary Box
    draw.rounded_rectangle([(box_left, box_top), (box_right, box_bottom)], radius=12, fill=theme["tint_bg"], outline=theme["tint_border"], width=2)
    draw.rectangle([(box_left, box_top), (box_left + 12, box_bottom)], fill=accent_color)

    # Draw Summary Lines inside box (Centered horizontally inside the summary box!)
    sum_y = box_top + box_padding_vertical
    for line in display_summary_lines:
        line_w = draw.textlength(line, font=font_summary)
        line_x = max(68, int(box_left + (box_right - box_left - line_w) // 2))
        draw.text((line_x, sum_y), line, fill=theme["text_dark"], font=font_summary)
        sum_y += line_height

    # 6. Footer (📸 @news.nit_iit)
    draw_camera_logo(draw, footer_center_x, footer_y, accent_color)
    draw.text((footer_center_x + 46, footer_y + 4), "@news.nit_iit", fill="#1A1A1A", font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path, "PNG")
    return output_path
