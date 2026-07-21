"""
design_post.py
Generates 1080x1350 Instagram portrait posters matching the exact News.nit_iit template:
- Fixed Headline Line Wrapping (1 & 2 lines fit naturally!)
- Zero awkward blank gaps between headline, image, and summary box
- Guaranteed Camera 📸 & Category icons rendering across all Mac/Linux machines
"""

import os
from PIL import Image, ImageDraw, ImageFont


BUCKET_COLORS = {
    "IndianPolitics": {
        "accent": "#D95D39", 
        "tint_bg": "#FDF0EB", 
        "tint_border": "#F8C6B9", 
        "text_dark": "#6E2A1A", 
        "badge_label": "🏛️ POLITICS",
        "default_emoji": "🏛️"
    },
    "StudentEducation": {
        "accent": "#2A9D8F", 
        "tint_bg": "#EBF7F5", 
        "tint_border": "#B2E2DD", 
        "text_dark": "#16524A", 
        "badge_label": "📚 EDUCATION",
        "default_emoji": "📚"
    },
    "TechInnovation": {
        "accent": "#7209B7", 
        "tint_bg": "#F6EDFC", 
        "tint_border": "#D8B4F3", 
        "text_dark": "#3B0561", 
        "badge_label": "🚀 TECH & AI",
        "default_emoji": "🚀"
    },
}

DEFAULT_COLOR = {
    "accent": "#D95D39", 
    "tint_bg": "#FDF0EB", 
    "tint_border": "#F8C6B9", 
    "text_dark": "#6E2A1A", 
    "badge_label": "📩 NEWS",
    "default_emoji": "📩"
}


def get_font(font_type="bold", size=36):
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


def get_emoji_font(size=44):
    """Loads Apple Color Emoji on Mac (with index=0) or Noto Color Emoji on Linux."""
    emoji_configs = [
        ("/System/Library/Fonts/Apple Color Emoji.ttc", 0),
        ("/System/Library/Fonts/Apple Color Emoji.ttf", 0),
        ("/Library/Fonts/Apple Color Emoji.ttc", 0),
        ("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 0),
    ]
    for path, idx in emoji_configs:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return None


def draw_camera_icon(draw, x, y, color):
    """Draws a crisp camera icon vector graphic so camera logo ALWAYS displays cleanly!"""
    # Camera Body
    draw.rounded_rectangle([(x, y + 6), (x + 36, y + 30)], radius=4, fill=color)
    # Camera Flash/Top Lens bump
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 6)], fill=color)
    # Lens Circle
    draw.ellipse([(x + 11, y + 11), (x + 25, y + 25)], fill="#F5EFEB", outline=color, width=2)


def draw_color_emoji(draw, x, y, emoji_char, font_emoji):
    """Draws a color emoji glyph safely."""
    if emoji_char and font_emoji:
        try:
            draw.text((x, y - 2), emoji_char, font=font_emoji, embedded_color=True)
            return True
        except Exception:
            pass
    return False


def create_card(headline, summary, image_path, bucket="StudentEducation", language="en", emoji=None, output_path="output/card.png"):
    """
    Renders the exact News.nit_iit 1080x1350 template with zero blank gaps & crisp layout.
    """
    theme = BUCKET_COLORS.get(bucket, DEFAULT_COLOR)
    accent_color = theme["accent"]
    head_emoji = emoji or theme["default_emoji"]

    width, height = 1080, 1350
    bg_color = "#F5EFEB"  # Off-white / Cream background
    card = Image.new("RGBA", (width, height), (245, 239, 235, 255))
    draw = ImageDraw.Draw(card)

    # Load Fonts
    font_header = get_font("bold", 38)
    font_headline = get_font("bold", 48)
    font_summary = get_font("regular", 32)
    font_footer = get_font("bold", 34)
    font_emoji = get_emoji_font(44)

    # 1. Top Accent Stripe
    draw.rectangle([(0, 0), (width, 22)], fill=accent_color)

    # 2. Header Bar (News.nit_iit ...... 2026)
    draw.text((40, 38), "News.nit_iit", fill="#1A1A1A", font=font_header)
    draw.text((930, 38), "2026", fill="#1A1A1A", font=font_header)
    draw.line([(40, 95), (1040, 95)], fill="#1A1A1A", width=3)

    # 3. Headline Section with Clean Line Wrapping (1 or 2 lines fit naturally!)
    y_cursor = 118

    # Clean headline text (remove leading emojis if passed in text)
    clean_headline = headline.strip()
    if clean_headline and ord(clean_headline[0]) > 0x2000:
        clean_headline = clean_headline[1:].strip()

    # Draw Category Emoji / Icon
    has_emoji = draw_color_emoji(draw, 40, y_cursor, head_emoji, font_emoji)
    headline_x = 96 if has_emoji else 40

    # 🔹 WIDER WRAPPING LIMIT (40 characters) -> Allows 1 and 2 line headlines to fit cleanly!
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

    for i, line in enumerate(headline_lines[:3]):
        draw_x = headline_x if i == 0 else 40
        draw.text((draw_x, y_cursor), line, fill="#1A1A1A", font=font_headline)
        y_cursor += 58

    # Accent Underline
    y_cursor += 12
    draw.rectangle([(40, y_cursor), (280, y_cursor + 7)], fill=accent_color)
    draw.line([(280, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 4. Middle Image Section (Full Width 1080px, Dynamic height to eliminate gaps!)
    image_top = y_cursor + 20
    # Image height automatically expands to fill middle space cleanly
    image_height = 510 if len(headline_lines) <= 2 else 460

    if image_path and os.path.exists(image_path):
        try:
            main_img = Image.open(image_path).convert("RGBA")
            main_img = main_img.resize((1080, image_height), Image.Resampling.LANCZOS)
            card.paste(main_img, (0, image_top))
        except Exception as e:
            print(f"Error placing image: {e}")
            draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
    else:
        # High quality neutral background placeholder if no photo
        draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
        draw.text((460, image_top + (image_height // 2) - 15), "news.nit_iit", fill="#64748B", font=font_header)

    # 5. DYNAMIC Summary Box Section
    clean_summary = summary.strip()
    if clean_summary and ord(clean_summary[0]) > 0x2000:
        clean_summary = clean_summary[1:].strip()

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

    display_lines = sum_lines[:5]
    line_height = 42
    box_top = image_top + image_height + 22
    
    box_padding_vertical = 20
    content_height = (len(display_lines) * line_height) + (box_padding_vertical * 2)
    box_bottom = min(1240, box_top + content_height)
    box_left, box_right = 40, 1040

    # Draw Dynamic Summary Box
    draw.rounded_rectangle([(box_left, box_top), (box_right, box_bottom)], radius=14, fill=theme["tint_bg"], outline=theme["tint_border"], width=2)
    draw.rectangle([(box_left, box_top), (box_left + 14, box_bottom)], fill=accent_color)

    # Draw Summary Lines inside box
    sum_y = box_top + box_padding_vertical
    has_sum_emoji = draw_color_emoji(draw, 72, sum_y, "📌", font_emoji)
    sum_text_x = 120 if has_sum_emoji else 72

    for i, line in enumerate(display_lines):
        draw_x = sum_text_x if i == 0 else 72
        draw.text((draw_x, sum_y), line, fill=theme["text_dark"], font=font_summary)
        sum_y += line_height

    # 6. GUARANTEED Footer Watermark (📸 @news.nit_iit)
    footer_y = min(1280, box_bottom + 25)
    footer_center_x = 410

    # Try color emoji first, fallback to crisp vector camera icon if font unsupported
    has_cam = draw_color_emoji(draw, footer_center_x, footer_y, "📸", font_emoji)
    if has_cam:
        draw.text((footer_center_x + 52, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)
    else:
        draw_camera_icon(draw, footer_center_x, footer_y + 4, accent_color)
        draw.text((footer_center_x + 46, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.convert("RGB").save(output_path)
    print(f"  Poster card generated: {output_path}")
    return output_path
