import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BUCKET_COLORS = {
    "IndianPolitics": {"accent": "#DC2626", "tint_bg": "#FEF2F2", "tint_border": "#FEE2E2", "text_dark": "#991B1B"},
    "StudentEducation": {"accent": "#0D9488", "tint_bg": "#F0FDFA", "tint_border": "#CCFBF1", "text_dark": "#115E59"},
    "TechInnovation": {"accent": "#7C3AED", "tint_bg": "#F5F3FF", "tint_border": "#EDE9FE", "text_dark": "#5B21B6"}
}
DEFAULT_COLOR = {"accent": "#0284C7", "tint_bg": "#F0F9FF", "tint_border": "#E0F2FE", "text_dark": "#075985"}

CATEGORY_BADGES = {
    "Student": "STUDENT",
    "Education": "EDUCATION",
    "Jobs": "JOBS",
    "Placements": "CAREERS",
    "Scholarships": "SCHOLARSHIPS",
    "Politics": "POLITICS",
    "Government": "GOVERNMENT",
    "Science": "SCIENCE",
    "Technology": "TECHNOLOGY",
    "Economy": "ECONOMY",
    "International": "WORLD",
    "National": "NATIONAL",
    "Breaking": "BREAKING"
}

def get_font(style="regular", size=24):
    """Retrieves system Arial fonts or falls back cleanly to NotoSans."""
    if style == "bold":
        font_file = "Arial Bold.ttf"
        fallback_file = "NotoSans-Bold.ttf"
    else:
        font_file = "Arial.ttf"
        fallback_file = "NotoSans-Regular.ttf"
        
    paths_to_try = [
        f"/System/Library/Fonts/Supplemental/{font_file}",
        f"/Library/Fonts/{font_file}",
        os.path.join("fonts", font_file),
        os.path.join(os.path.dirname(__file__), "..", "fonts", font_file),
        os.path.join("fonts", fallback_file),
        os.path.join(os.path.dirname(__file__), "..", "fonts", fallback_file),
        font_file,
        fallback_file
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
        # Image is wider -> scale by height
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        img_cropped = img_resized.crop((left, 0, left + target_width, target_height))
    else:
        # Image is taller -> scale by width
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

def create_card(headline, summary, image_path, bucket="StudentEducation", category="Student", output_path="output/card.png"):
    """Renders a 1080x1080 Square Poster with Category Badges and professional layouts."""
    theme = BUCKET_COLORS.get(bucket, DEFAULT_COLOR)
    accent_color = theme["accent"]
    
    width, height = 1080, 1080
    bg_color = "#F5EFEB"  # Premium Off-white background
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)
    
    # Load fonts
    font_header = get_font("bold", 34)
    font_footer = get_font("bold", 30)
    font_summary = get_font("regular", 28)
    
    # 1. Top Accent Stripe
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    
    draw.text((40, 30), "2026", fill="#1A1A1A", font=font_header)
    logo_w = draw.textlength("news.nit_iit", font=font_header)
    draw.text((1040 - logo_w, 30), "news.nit_iit", fill="#1A1A1A", font=font_header)
    draw.line([(40, 78), (1040, 78)], fill="#1A1A1A", width=3)
    
    # 3. Dynamic Headline Section (Centered horizontally, exactly 2 lines max)
    y_cursor = 94
    clean_headline = strip_emojis(headline)
    
    headline_size = 40
    headline_lines = []
    font_headline = get_font("bold", headline_size)
    
    while headline_size >= 28:
        font_headline = get_font("bold", headline_size)
        headline_lines = wrap_text_by_pixels(clean_headline, font_headline, 1000, draw)
        if len(headline_lines) <= 2:
            break
        headline_size -= 2
        
    for line in headline_lines[:2]:
        line_w = draw.textlength(line, font=font_headline)
        line_x = max(40, int((width - line_w) // 2))
        draw.text((line_x, y_cursor), line, fill="#1A1A1A", font=font_headline, stroke_width=1, stroke_fill="#1A1A1A")
        y_cursor += (headline_size + 14)
        
    y_cursor += 12
    draw.rectangle([(40, y_cursor), (260, y_cursor + 6)], fill=accent_color)
    
    # 4. Image Section (Height: 480px, crop-to-fill cover scaling)
    y_image_start = y_cursor + 20
    image_h = 480
    image_w = 1000
    
    if image_path and os.path.exists(image_path):
        try:
            with Image.open(image_path) as img:
                cropped_img = resize_and_crop(img, image_w, image_h)
                card.paste(cropped_img, (40, y_image_start))
        except Exception as e:
            print(f"  Error loading image onto card: {e}")
            draw.rectangle([(40, y_image_start), (1040, y_image_start + image_h)], fill="#EAE5E1")
    else:
        draw.rectangle([(40, y_image_start), (1040, y_image_start + image_h)], fill="#EAE5E1")
        
    # 5. Draw Category Badge Banner overlaying the image top-left
    if category:
        badge_text = CATEGORY_BADGES.get(category, str(category).upper())
        font_badge = get_font("bold", 22)
        badge_w = draw.textlength(badge_text, font=font_badge)
        
        # Draw nice rounded tag banner
        bx, by = 60, y_image_start + 20
        draw.rounded_rectangle([(bx, by), (bx + badge_w + 30, by + 40)], radius=6, fill=accent_color)
        draw.text((bx + 15, by + 8), badge_text, fill="#FFFFFF", font=font_badge)
    
    # 6. Summary Section (with light tint background)
    y_summary_start = y_image_start + image_h + 16
    summary_h = 190
    
    draw.rounded_rectangle(
        [(40, y_summary_start), (1040, y_summary_start + summary_h)],
        radius=8,
        fill=theme["tint_bg"],
        outline=theme["tint_border"],
        width=2
    )
    # Vertical accent bar
    draw.rectangle([(40, y_summary_start + 2), (54, y_summary_start + summary_h - 2)], fill=accent_color)
    
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
    for line in summary_lines[:4]:  # Max 4 lines
        line_w = draw.textlength(line, font=font_summary)
        line_x = max(68, int((width - line_w) // 2))
        draw.text((line_x, y_sum_text), line, fill="#2D3748", font=font_summary)
        y_sum_text += 38
        
    # 7. Footer
    draw_camera_logo(draw, 388, 1020, "#1A1A1A")
    draw.text((436, 1018), "@news.nit_iit", fill="#1A1A1A", font=font_footer)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    return output_path
