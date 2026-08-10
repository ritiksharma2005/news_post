import os
import re
from PIL import Image, ImageDraw, ImageFont

BUCKET_COLORS = {
    "IndianPolitics": {"accent": "#DC2626", "tint_bg": "#FEF2F2", "tint_border": "#FEE2E2", "text_dark": "#991B1B"},
    "StudentEducation": {"accent": "#0D9488", "tint_bg": "#F0FDFA", "tint_border": "#CCFBF1", "text_dark": "#115E59"},
    "TechInnovation": {"accent": "#7C3AED", "tint_bg": "#F5F3FF", "tint_border": "#EDE9FE", "text_dark": "#5B21B6"}
}
DEFAULT_COLOR = {"accent": "#0284C7", "tint_bg": "#F0F9FF", "tint_border": "#E0F2FE", "text_dark": "#075985"}

CATEGORY_BADGES_HI = {
    "Student": "छात्र समाचार",
    "Education": "शिक्षा",
    "Jobs": "नौकरियां",
    "Placements": "करियर",
    "Scholarships": "छात्रवृत्ति",
    "Politics": "राजनीति",
    "Government": "सरकारी फैसले",
    "Science": "विज्ञान",
    "Technology": "टेक न्यूज़",
    "Economy": "अर्थव्यवस्था",
    "International": "विदेश",
    "National": "राष्ट्रीय",
    "Breaking": "ब्रेकिंग"
}

def get_font(style="regular", size=24):
    """Retrieves Devanagari or English font files."""
    if style == "english_bold":
        font_file = "NotoSans-Bold.ttf"
    elif style == "bold":
        font_file = "NotoSansDevanagari-Bold.ttf"
    else:
        font_file = "NotoSansDevanagari-Regular.ttf"
        
    paths_to_try = [
        os.path.join("fonts", font_file),
        os.path.join(os.path.dirname(__file__), "..", "fonts", font_file),
        font_file
    ]
    for p in paths_to_try:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def strip_emojis(text):
    """Removes all emojis to prevent box rendering bugs on standard TTFs."""
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2b50\u2b06\u2192]', '', text).strip()

def resize_and_crop(img, target_width, target_height):
    """Resizes and center-crops an image to cover the box cleanly."""
    width, height = img.size
    aspect_ratio = width / height
    target_ratio = target_width / target_height
    
    if aspect_ratio > target_ratio:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        img_cropped = img_resized.crop((left, 0, left + target_width, target_height))
    else:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        top = (new_height - target_height) // 2
        img_cropped = img_resized.crop((0, top, target_width, top + target_height))
        
    return img_cropped

def draw_camera_logo(draw, x, y, color):
    """Draws a crisp camera logo icon directly on the canvas."""
    draw.rounded_rectangle([(x, y + 5), (x + 36, y + 29)], radius=4, fill=color)
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 5)], fill=color)
    draw.ellipse([(x + 10, y + 10), (x + 26, y + 26)], fill="#F5EFEB", outline=color, width=2)
    draw.ellipse([(x + 14, y + 14), (x + 22, y + 22)], fill=color)

def wrap_text_by_pixels(text, font, max_width, draw):
    """Wraps text into lines based on rendered pixel width."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        width = draw.textlength(test_line, font=font)
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def create_hindi_card(headline, summary, image_path, bucket="StudentEducation", category="Student", output_path="output/card_hindi.png"):
    """Renders a 1080x1080 Devanagari Square Poster matching the user's ideal template."""
    theme = BUCKET_COLORS.get(bucket, DEFAULT_COLOR)
    accent_color = theme["accent"]
    
    width, height = 1080, 1080
    bg_color = "#F5EFEB"
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)
    
    # Load fonts
    font_header_eng = get_font("english_bold", 34)
    font_footer = get_font("english_bold", 30)
    font_summary = get_font("regular", 28)
    
    # 1. Top Accent Stripe
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    
    # 2. Header Bar (News.nit_iit on left, 2026 on right)
    draw.text((60, 30), "News.nit_iit", fill="#1A1A1A", font=font_header_eng)
    logo_w = draw.textlength("2026", font=font_header_eng)
    draw.text((1020 - logo_w, 30), "2026", fill="#1A1A1A", font=font_header_eng)
    draw.line([(60, 78), (1020, 78)], fill="#1A1A1A", width=3)
    
    # 3. Centered Headline Section (Standard NotoSansDevanagari-Bold, 2 lines max)
    y_cursor = 94
    clean_headline = strip_emojis(headline)
    
    headline_size = 38
    headline_lines = []
    font_headline = get_font("bold", headline_size)
    
    while headline_size >= 28:
        font_headline = get_font("bold", headline_size)
        headline_lines = wrap_text_by_pixels(clean_headline, font_headline, 960, draw)
        if len(headline_lines) <= 2:
            break
        headline_size -= 2
        
    for line in headline_lines[:2]:
        # Center-aligned drawing with bold outline stroke (stroke_width=1)
        text_w = draw.textlength(line, font=font_headline)
        line_x = (width - text_w) // 2
        draw.text((line_x, y_cursor), line, fill="#1A1A1A", font=font_headline, stroke_width=1, stroke_fill="#1A1A1A")
        y_cursor += (headline_size + 14)
        
    y_cursor += 10
    # Centered stripe and line below headline
    draw.line([(60, y_cursor + 3), (1020, y_cursor + 3)], fill="#1A1A1A", width=2)
    draw.rectangle([(460, y_cursor), (620, y_cursor + 6)], fill=accent_color)
    
    # 4. Image Section (Height: 480px, crop-to-fill)
    y_image_start = y_cursor + 20
    image_h = 480
    image_w = 960
    
    if image_path and os.path.exists(image_path):
        try:
            with Image.open(image_path) as img:
                cropped_img = resize_and_crop(img, image_w, image_h)
                card.paste(cropped_img, (60, y_image_start))
        except Exception as e:
            print(f"  Error loading image onto Hindi card: {e}")
            draw.rectangle([(60, y_image_start), (1020, y_image_start + image_h)], fill="#EAE5E1")
    else:
        draw.rectangle([(60, y_image_start), (1020, y_image_start + image_h)], fill="#EAE5E1")
        
    # 5. Draw Devanagari Category Badge Banner overlaying the image top-left
    badge_text = CATEGORY_BADGES_HI.get(category, "राष्ट्रीय")
    font_badge = get_font("bold", 22)
    badge_w = draw.textlength(badge_text, font=font_badge)
    
    bx, by = 80, y_image_start + 20
    draw.rounded_rectangle([(bx, by), (bx + badge_w + 30, by + 40)], radius=6, fill=accent_color)
    draw.text((bx + 15, by + 8), badge_text, fill="#FFFFFF", font=font_badge)
    
    # 6. Left-Aligned Summary Section (with light tint background)
    y_summary_start = y_image_start + image_h + 16
    summary_h = 230
    
    draw.rounded_rectangle(
        [(60, y_summary_start), (1020, y_summary_start + summary_h)],
        radius=8,
        fill=theme["tint_bg"],
        outline=theme["tint_border"],
        width=2
    )
    # Vertical accent bar
    draw.rectangle([(60, y_summary_start + 2), (76, y_summary_start + summary_h - 2)], fill=accent_color)
    
    # Draw summary lines
    words_sum = summary.split()
    summary_lines = []
    cur_line = ""
    for w in words_sum:
        if len(cur_line + " " + w) < 52:
            cur_line += " " + w if cur_line else w
        else:
            summary_lines.append(cur_line)
            cur_line = w
    if cur_line:
        summary_lines.append(cur_line)
        
    y_sum_text = y_summary_start + 24
    box_center_x = (60 + 1020) // 2
    for line in summary_lines[:5]:  # Max 5 lines
        # Center-aligned summary text
        text_w = draw.textlength(line, font=font_summary)
        line_x = box_center_x - (text_w // 2)
        if line_x < 96:
            line_x = 96
        draw.text((line_x, y_sum_text), line, fill="#2D3748", font=font_summary)
        y_sum_text += 38
        
    # 7. Footer Separator Line
    draw.line([(100, 1000), (980, 1000)], fill="#E2E8F0", width=1)
    
    # Footer Centering
    draw_camera_logo(draw, 388, 1018, "#1A1A1A")
    draw.text((436, 1016), "@news.nit_iit", fill="#1A1A1A", font=font_footer)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    return output_path
