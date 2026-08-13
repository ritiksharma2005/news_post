"""
instagram_digest/design_digest_post.py
Generates 1080x1080 Branded Posters for "Campus Digest" Series (@news.nit_iit)
with the original post image in the center and space for a 2-line headline & 4-5 bullets.
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


def strip_emojis(text):
    """Removes all emojis and special dingbat symbols to prevent box rendering bugs."""
    import re
    return re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2b50\u2b06\u2192]', '', text).strip()


def draw_camera_logo(draw, x, y, color):
    """Draws a camera logo icon directly in RGB mode."""
    draw.rounded_rectangle([(x, y + 5), (x + 36, y + 29)], radius=4, fill=color)
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 5)], fill=color)
    draw.ellipse([(x + 10, y + 10), (x + 26, y + 26)], fill="#F5EFEB", outline=color, width=2)
    draw.ellipse([(x + 14, y + 14), (x + 22, y + 22)], fill=color)


def wrap_text_by_pixels(text, font, max_width, draw):
    """Wraps text into multiple lines such that no line exceeds max_width in pixels."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def create_digest_card(headline, bullets, why_it_matters, image_path=None, output_path="output/digest_card.png"):
    """
    Renders a 1080x1080 Square Campus Digest Poster with centered image (increased height)
    and space for a 2-line headline and 4-5 bullet points.
    """
    width, height = 1080, 1080
    bg_color = "#F5EFEB"
    accent_color = "#0284C7"  # Deep Sky Blue Theme
    card = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(card)

    font_brand = get_font("bold", 34)
    font_headline = get_font("bold", 48)
    font_bullet = get_font("regular", 22)  # Highly readable size for bullets
    font_insight = get_font("bold", 22)
    font_footer = get_font("bold", 30)

    # 1. Top Stripe & Header
    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    
    # news.nit_iit on left, 2026 on right
    draw.text((40, 30), "2026", fill="#1A1A1A", font=font_brand)
    logo_w = draw.textlength("news.nit_iit", font=font_brand)
    draw.text((1040 - logo_w, 30), "news.nit_iit", fill="#1A1A1A", font=font_brand)
    draw.line([(40, 78), (1040, 78)], fill="#1A1A1A", width=3)

    # 2. Headline (Wraps into exactly 2 lines using pixel width limits)
    y_cursor = 94
    clean_headline = strip_emojis(headline)
    lines = wrap_text_by_pixels(clean_headline, font_headline, 1000, draw)

    # Draw exactly 2 lines (pad with empty line if only 1 line was generated)
    while len(lines) < 2:
        lines.append("")
        
    for line in lines[:2]:
        # Centered headline with a stroke for maximum crispness
        line_w = draw.textlength(line, font=font_headline)
        line_x = max(40, int((width - line_w) // 2))
        draw.text((line_x, y_cursor), line, fill="#1A1A1A", font=font_headline, stroke_width=1, stroke_fill="#1A1A1A")
        y_cursor += 54

    # Underline
    y_cursor += 12
    draw.rectangle([(40, y_cursor), (260, y_cursor + 6)], fill=accent_color)
    draw.line([(260, y_cursor + 3), (1040, y_cursor + 3)], fill="#1A1A1A", width=2)

    # 3. Compact Summary Box Proportions (anchored at bottom)
    footer_y = 1022
    box_bottom = footer_y - 20
    box_height = 340  # Made more compact to allow larger centered image
    box_top = box_bottom - box_height
    box_left, box_right = 40, 1040

    # 4. Center Image Section (Fills remaining middle space)
    image_top = y_cursor + 16
    image_bottom = box_top - 16
    image_height = image_bottom - image_top

    if image_path and os.path.exists(image_path):
        try:
            main_img = Image.open(image_path).convert("RGB")
            # Aspect ratio resize
            img_w, img_h = main_img.size
            ratio = 1080 / img_w
            new_h = int(img_h * ratio)
            resized_img = main_img.resize((1080, new_h), Image.Resampling.LANCZOS)
            
            # Crop to fit the image box
            if new_h > image_height:
                crop_y = (new_h - image_height) // 2
                cropped_img = resized_img.crop((0, crop_y, 1080, crop_y + image_height))
            else:
                # Pad with background color if too small
                cropped_img = Image.new("RGB", (1080, image_height), bg_color)
                pad_y = (image_height - new_h) // 2
                cropped_img.paste(resized_img, (0, pad_y))
                
            card.paste(cropped_img, (0, image_top))
        except Exception as e:
            print(f"Error placing image: {e}")
            draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
    else:
        draw.rectangle([(0, image_top), (1080, image_top + image_height)], fill="#CBD5E1")
        draw.text((460, image_top + (image_height // 2) - 15), "news.nit_iit", fill="#64748B", font=font_brand)

    # 5. Draw Summary Box
    draw.rounded_rectangle([(box_left, box_top), (box_right, box_bottom)], radius=12, fill="#E0F2FE", outline="#BAE6FD", width=2)
    draw.rectangle([(box_left, box_top), (box_left + 14, box_bottom)], fill=accent_color)

    # Draw up to 5 Bullets inside box with pixel-based auto-wrap
    sum_y = box_top + 20
    max_text_width = box_right - box_left - 72 - 32  # margins: left=72, right=32
    line_spacing = 30
    
    for b in bullets[:5]:
        wrapped = wrap_text_by_pixels(strip_emojis(b), font_bullet, max_text_width, draw)
        for line in wrapped:
            draw.text((72, sum_y), line, fill="#0369A1", font=font_bullet)
            sum_y += line_spacing
        sum_y += 4  # gap between bullets

    # Draw Why It Matters inside box
    sum_y += 6
    insight_text = f"Insight: {strip_emojis(why_it_matters)}"
    wrapped_insight = wrap_text_by_pixels(insight_text, font_insight, max_text_width, draw)
    for line in wrapped_insight[:2]:  # Limit to 2 lines
        draw.text((72, sum_y), line, fill="#075985", font=font_insight)
        sum_y += line_spacing

    # 6. Footer Watermark (📸 @news.nit_iit)
    footer_center_x = 420
    draw_camera_logo(draw, footer_center_x, footer_y + 2, accent_color)
    draw.text((footer_center_x + 46, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    print(f"  Campus Digest Card generated: {output_path}")
    return output_path
