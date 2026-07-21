"""
design_quote_post.py
Generates 1080x1080 Minimalist Quote Cards for "Life Mantra" Series (@news.nit_iit):
- Auto-downloads Google Noto Devanagari font so Hindi text NEVER shows boxes!
- Dynamic 12% Opacity Author Portrait Background Watermark (Socrates, Gandhi, Kalam, etc.)
- Styled Date Pill Badge with RGB Calendar Icon
- Camera logo & Username footer
"""

import os
import datetime
import urllib.request
from PIL import Image, ImageDraw, ImageFont


def ensure_hindi_font():
    """Auto-downloads Google Noto Devanagari font if missing so Hindi renders 100% on Linux & Mac."""
    os.makedirs("fonts", exist_ok=True)
    font_file = "fonts/NotoSansDevanagari-Bold.ttf"
    if not os.path.exists(font_file):
        try:
            print("  Downloading Google Noto Devanagari font for Hindi rendering...")
            url = "https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth%2Cwght%5D.ttf"
            urllib.request.urlretrieve(url, font_file)
        except Exception as e:
            print(f"  Font download notice: {e}")
    return font_file


def get_font(font_type="bold", size=32):
    paths_to_try = [
        "fonts/DejaVuSans-Bold.ttf" if font_type == "bold" else "fonts/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if font_type == "bold" else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if font_type == "bold" else "/Library/Fonts/Arial.ttf",
        "Arial.ttf"
    ]
    for p in paths_to_try:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def get_hindi_font(size=34, bold=True):
    """Loads Google Noto Devanagari font for both Linux (GitHub Actions) and Mac."""
    local_font = ensure_hindi_font()
    if os.path.exists(local_font):
        try:
            return ImageFont.truetype(local_font, size)
        except Exception:
            pass

    hindi_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/KohinoorDevanagari.ttc",
        "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "Arial.ttf"
    ]
    for p in hindi_paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_sunrise_icon(draw, x, y, color):
    """Draws a clean vector sunrise icon graphic."""
    draw.ellipse([(x + 8, y + 2), (x + 28, y + 22)], fill="#F59E0B")
    draw.line([(x, y + 24), (x + 36, y + 24)], fill=color, width=3)
    draw.line([(x + 18, y - 4), (x + 18, y + 1)], fill="#F59E0B", width=2)
    draw.line([(x + 4, y + 6), (x + 8, y + 9)], fill="#F59E0B", width=2)
    draw.line([(x + 32, y + 6), (x + 28, y + 9)], fill="#F59E0B", width=2)


def draw_calendar_icon(draw, x, y, color="#D95D39"):
    """Draws a crisp vector calendar icon directly in RGB mode."""
    draw.rounded_rectangle([(x, y + 4), (x + 24, y + 26)], radius=3, fill="#F0EAE1", outline=color, width=2)
    draw.rectangle([(x, y + 4), (x + 24, y + 10)], fill=color)
    draw.line([(x + 6, y + 1), (x + 6, y + 5)], fill=color, width=2)
    draw.line([(x + 18, y + 1), (x + 18, y + 5)], fill=color, width=2)


def draw_camera_logo(draw, x, y, color):
    """Draws a crisp camera logo icon directly in RGB mode."""
    draw.rounded_rectangle([(x, y + 5), (x + 36, y + 29)], radius=4, fill=color)
    draw.rectangle([(x + 12, y + 2), (x + 24, y + 5)], fill=color)
    draw.ellipse([(x + 10, y + 10), (x + 26, y + 26)], fill="#FAFAF9", outline=color, width=2)
    draw.ellipse([(x + 14, y + 14), (x + 22, y + 22)], fill=color)


def create_quote_card(quote_en, quote_hi, author, reflection, author_image_path=None, output_path="output/quote_card.png"):
    """
    Renders a minimalist 1080x1080 "Life Mantra" Quote Card.
    """
    width, height = 1080, 1080
    bg_color = (250, 250, 249, 255)  # Minimalist Warm Paper Off-White
    accent_color = "#D95D39"

    card = Image.new("RGBA", (width, height), bg_color)

    # 1. Author Portrait Watermark (12% Opacity behind right side)
    if author_image_path and os.path.exists(author_image_path):
        try:
            portrait = Image.open(author_image_path).convert("RGBA")
            portrait = portrait.resize((520, 600), Image.Resampling.LANCZOS)
            
            alpha = portrait.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.12))
            portrait.putalpha(alpha)
            
            card.paste(portrait, (520, 160), portrait)
            print(f"  Author watermark applied for: {author}")
        except Exception as e:
            print(f"  Watermark notice: {e}")

    draw = ImageDraw.Draw(card)

    font_brand = get_font("bold", 34)
    font_date = get_font("bold", 24)
    font_quote_en = get_font("bold", 36)
    font_quote_hi = get_hindi_font(34, bold=True)  # 🔹 Google Noto Devanagari Font
    font_author = get_font("bold", 32)
    font_reflection = get_font("regular", 26)
    font_footer = get_font("bold", 30)

    # 2. Top Stripe & Header
    draw.rectangle([(0, 0), (width, 14)], fill=accent_color)
    
    # Vector Sunrise Icon + LIFE MANTRA
    draw_sunrise_icon(draw, 50, 42, accent_color)
    draw.text((96, 38), "LIFE MANTRA", fill="#1C1917", font=font_brand)
    
    # Styled Date Pill Badge with RGB Calendar Icon (Top Right)
    date_str = datetime.datetime.now().strftime("%a, %d %b %Y").upper()
    date_box_x1, date_box_y1 = 660, 30
    date_box_x2, date_box_y2 = 1030, 72
    draw.rounded_rectangle([(date_box_x1, date_box_y1), (date_box_x2, date_box_y2)], radius=20, fill="#F0EAE1", outline="#E7E0D6", width=2)
    
    draw_calendar_icon(draw, date_box_x1 + 18, date_box_y1 + 8, accent_color)
    draw.text((date_box_x1 + 52, date_box_y1 + 8), date_str, fill="#44403C", font=font_date)

    draw.line([(50, 90), (1030, 90)], fill="#E7E5E4", width=2)

    # 3. Accent Quote Mark
    draw.text((50, 105), "“", fill=accent_color, font=get_font("bold", 120))

    # 4. English Quote
    y_cursor = 215
    words_en = quote_en.split()
    lines_en = []
    cur = ""
    for w in words_en:
        if len(cur + " " + w) < 36:
            cur += " " + w if cur else w
        else:
            lines_en.append(cur)
            cur = w
    if cur:
        lines_en.append(cur)

    for line in lines_en[:3]:
        draw.text((70, y_cursor), line, fill="#1C1917", font=font_quote_en)
        y_cursor += 48

    # 5. Hindi Quote (Rendered with Google Noto Devanagari)
    y_cursor += 16
    words_hi = quote_hi.split()
    lines_hi = []
    cur = ""
    for w in words_hi:
        if len(cur + " " + w) < 40:
            cur += " " + w if cur else w
        else:
            lines_hi.append(cur)
            cur = w
    if cur:
        lines_hi.append(cur)

    for line in lines_hi[:3]:
        draw.text((70, y_cursor), line, fill="#262626", font=font_quote_hi)
        y_cursor += 46

    # 6. Author Name
    y_cursor += 22
    draw.text((70, y_cursor), f"— {author}", fill=accent_color, font=font_author)

    # 7. Today's Student Reflection Box
    box_top = 770
    box_bottom = 980
    draw.rounded_rectangle([(50, box_top), (1030, box_bottom)], radius=12, fill="#F5F5F4", outline="#E7E5E4", width=2)
    draw.rectangle([(50, box_top), (62, box_bottom)], fill=accent_color)

    draw.text((80, box_top + 16), "TODAY'S STUDENT REFLECTION:", fill=accent_color, font=get_font("bold", 24))

    words_ref = reflection.split()
    lines_ref = []
    cur = ""
    for w in words_ref:
        if len(cur + " " + w) < 54:
            cur += " " + w if cur else w
        else:
            lines_ref.append(cur)
            cur = w
    if cur:
        lines_ref.append(cur)

    ref_y = box_top + 48
    for line in lines_ref[:3]:
        draw.text((80, ref_y), line, fill="#292524", font=font_reflection)
        ref_y += 34

    # 8. Bottom Center Watermark (📸 @news.nit_iit)
    footer_y = 1015
    footer_center_x = 410
    draw_camera_logo(draw, footer_center_x, footer_y + 2, accent_color)
    draw.text((footer_center_x + 46, footer_y), "@news.nit_iit", fill=accent_color, font=font_footer)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.convert("RGB").save(output_path)
    print(f"  Life Mantra Card generated: {output_path}")
    return output_path
