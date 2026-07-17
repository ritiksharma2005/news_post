"""
design_post.py
Renders the final 1080x1080 news card:
  [ logo/username bar ]
  [ headline ]
  [ image ]
  [ 2-3 line summary ]

Supports both English and Hindi (Devanagari) text.

Run directly to test with sample data: python design_post.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

CARD_SIZE = (1080, 1080)
PAGE_USERNAME = "news_nit_iit"   # instagram user name 

FONT_EN_BOLD = "fonts/NotoSans-Bold.ttf"
FONT_EN_REGULAR = "fonts/NotoSans-Regular.ttf"
FONT_HI = "fonts/NotoSansDevanagari-Regular.ttf"

COLOR_BG = (247, 240, 220)          # light cream/yellow, newspaper-paper feel
COLOR_TEXT = (20, 20, 20)
COLOR_MUTED = (90, 90, 90)
COLOR_ACCENT = (216, 90, 48)        # warm coral accent
COLOR_ACCENT_DARK = (153, 60, 29)   # darker coral for text on tint
COLOR_ACCENT_TINT = (250, 236, 231) # pale coral tint for summary box
COLOR_BORDER = (230, 230, 230)
COLOR_PLACEHOLDER = (225, 225, 225)


def load_font(language, weight="regular", size=40):
    """Load the right font for the language/weight, with variable-font weight applied."""
    path = FONT_HI if language == "hi" else (FONT_EN_BOLD if weight == "bold" else FONT_EN_REGULAR)
    font = ImageFont.truetype(path, size)
    try:
        font.set_variation_by_axes([700 if weight == "bold" else 400])
    except Exception:
        pass  # not a variable font, ignore
    return font


def wrap_text(draw, text, font, max_width):
    """Wrap text to fit max_width, measuring actual rendered width per line."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_top_bar(draw, language):
    """Draw a colored accent strip, then a newspaper-style masthead below it."""
    accent_strip_height = 14
    draw.rectangle([0, 0, CARD_SIZE[0], accent_strip_height], fill=COLOR_ACCENT)

    bar_top = accent_strip_height
    bar_height = 70
    draw.rectangle([0, bar_top, CARD_SIZE[0], bar_top + bar_height], fill=COLOR_BG)

    padding_x = 40
    font_name = load_font("en", weight="bold", size=34)
    draw.text((padding_x, bar_top + bar_height // 2), "News.nit_iit",
               font=font_name, fill=COLOR_TEXT, anchor="lm")

    font_year = load_font("en", weight="bold", size=30)
    draw.text((CARD_SIZE[0] - padding_x, bar_top + bar_height // 2), "2026",      # year name 
               font=font_year, fill=COLOR_ACCENT_DARK, anchor="rm")

    line_y = bar_top + bar_height
    draw.line([0, line_y, CARD_SIZE[0], line_y], fill=COLOR_TEXT, width=6)
    draw.line([0, line_y + 10, CARD_SIZE[0], line_y + 10], fill=COLOR_TEXT, width=2)
    return line_y + 20


EMOJI_FONT_PATH = "fonts/NotoColorEmoji.ttf"
EMOJI_NATIVE_SIZE = 109  # Noto Color Emoji only renders at fixed sizes


def render_emoji_image(emoji_char, target_size):
    """
    Render a color emoji to its own small RGBA image, since color emoji
    fonts only support fixed native sizes and can't be drawn inline with
    regular text at arbitrary sizes.
    """
    font = ImageFont.truetype(EMOJI_FONT_PATH, EMOJI_NATIVE_SIZE)
    canvas = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 10), emoji_char, font=font, embedded_color=True)
    return canvas.resize((target_size, target_size), Image.LANCZOS)


def draw_headline(card, draw, headline, language, top_y, emoji=None):
    """Draw the headline block with an optional composited emoji prefix and accent underline."""
    padding_x = 40
    max_width = CARD_SIZE[0] - (padding_x * 2)
    font_size = 50
    font = load_font(language, weight="bold", size=font_size)

    y = top_y + 25
    text_start_x = padding_x

    if emoji:
        emoji_img = render_emoji_image(emoji, target_size=int(font_size * 1.1))
        card.paste(emoji_img, (padding_x, y - 4), emoji_img)
        text_start_x = padding_x + emoji_img.width + 12
        max_width -= (emoji_img.width + 12)

    lines = wrap_text(draw, headline, font, max_width)
    line_height = int(font_size * 1.22)
    for i, line in enumerate(lines[:4]):
        x = text_start_x if i == 0 else padding_x
        draw.text((x, y), line, font=font, fill=COLOR_TEXT)
        y += line_height

    y += 15
    draw.line([padding_x, y, padding_x + 140, y], fill=COLOR_ACCENT, width=6)
    draw.line([padding_x + 150, y, CARD_SIZE[0] - padding_x, y], fill=COLOR_TEXT, width=3)
    return y + 25


def draw_image_block(card, image_path, top_y, block_height):
    """Paste the story image (or a placeholder) into the card."""
    if image_path and os.path.exists(image_path):
        img = Image.open(image_path).convert("RGB")
        target_w = CARD_SIZE[0]
        target_ratio = target_w / block_height
        img_ratio = img.width / img.height
        if img_ratio > target_ratio:
            new_height = img.height
            new_width = int(new_height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, new_height))
        else:
            new_width = img.width
            new_height = int(new_width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, new_width, top + new_height))
        img = img.resize((target_w, block_height))
        card.paste(img, (0, top_y))
    else:
        draw = ImageDraw.Draw(card)
        draw.rectangle([0, top_y, CARD_SIZE[0], top_y + block_height], fill=COLOR_PLACEHOLDER)
        font = load_font("en", weight="regular", size=28)
        draw.text((CARD_SIZE[0] // 2, top_y + block_height // 2), "image",
                   font=font, fill=COLOR_MUTED, anchor="mm")
    return top_y + block_height


def draw_summary(card, draw, summary, language, top_y):
    """Draw the 2-3 line summary in a pull-quote style box: accent left bar + border + icon."""
    padding_x = 40
    accent_bar_width = 10
    box_padding = 30
    text_left_offset = accent_bar_width + box_padding
    max_width = CARD_SIZE[0] - (padding_x * 2) - text_left_offset - box_padding
    font_size = 34
    font = load_font(language, weight="regular", size=font_size)

    lines = wrap_text(draw, summary, font, max_width)
    line_height = int(font_size * 1.5)
    text_height = line_height * min(len(lines), 4)
    box_top = top_y + 25
    box_height = text_height + (box_padding * 2)
    box_right = CARD_SIZE[0] - padding_x

    # Base tinted box with a visible border for definition
    draw.rounded_rectangle(
        [padding_x, box_top, box_right, box_top + box_height],
        radius=16, fill=COLOR_ACCENT_TINT, outline=COLOR_ACCENT, width=2,
    )

    # Solid accent bar along the left edge (pull-quote style), rounded to match the box
    draw.rounded_rectangle(
        [padding_x, box_top, padding_x + accent_bar_width + 16, box_top + box_height],
        radius=16, fill=COLOR_ACCENT,
    )
    # Square off the right side of the accent bar so it doesn't bulge into the text
    draw.rectangle(
        [padding_x + accent_bar_width, box_top, padding_x + accent_bar_width + 16, box_top + box_height],
        fill=COLOR_ACCENT_TINT,
    )
    draw.rectangle(
        [padding_x, box_top, padding_x + accent_bar_width, box_top + box_height],
        fill=COLOR_ACCENT,
    )

    y = box_top + box_padding
    for line in lines[:4]:
        draw.text((padding_x + text_left_offset, y), line, font=font, fill=COLOR_ACCENT_DARK)
        y += line_height
    return box_top + box_height


def draw_footer(card, draw, language, top_y, emoji="📸"):
    """Draw a centered '@news.nit_iit' signature with a media emoji, positioned
    with proper spacing below wherever the summary box actually ends."""
    separator_y = top_y + 45
    handle = "@news.nit_iit"
    font_size = 32
    font = load_font("en", weight="bold", size=font_size)

    draw.line([80, separator_y, CARD_SIZE[0] - 80, separator_y], fill=COLOR_BORDER, width=2)

    text_y = separator_y + 45
    emoji_size = int(font_size * 1.2)
    emoji_img = render_emoji_image(emoji, target_size=emoji_size)

    text_bbox = draw.textbbox((0, 0), handle, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    gap = 12
    total_width = emoji_img.width + gap + text_width
    start_x = (CARD_SIZE[0] - total_width) // 2

    card.paste(emoji_img, (start_x, text_y - emoji_img.height // 2), emoji_img)
    draw.text((start_x + emoji_img.width + gap, text_y), handle,
               font=font, fill=COLOR_ACCENT_DARK, anchor="lm")
    return text_y + 40


def create_card(headline, summary, image_path=None, language="en", emoji=None, output_path="output/card.png"):
    """
    Build the full card: masthead -> headline -> image -> summary -> footer.
    Canvas height grows automatically if content + footer need more room than
    the base 1080px, so the footer never ends up cramped or cut off.
    language: "en" or "hi"
    emoji: optional emoji string to prefix the headline (e.g. "📩")
    """
    # First pass on a tall scratch canvas to measure actual content height
    scratch = Image.new("RGB", (CARD_SIZE[0], 2000), COLOR_BG)
    draw = ImageDraw.Draw(scratch)
    y = draw_top_bar(draw, language)
    y = draw_headline(scratch, draw, headline, language, y, emoji=emoji)
    image_block_height = 480
    y += image_block_height
    draw = ImageDraw.Draw(scratch)
    summary_bottom = draw_summary(scratch, draw, summary, language, y)
    footer_bottom = summary_bottom + 45 + 45 + 40  # matches draw_footer's spacing

    final_height = max(CARD_SIZE[1], footer_bottom + 20)

    card = Image.new("RGB", (CARD_SIZE[0], final_height), COLOR_BG)
    draw = ImageDraw.Draw(card)

    y = draw_top_bar(draw, language)
    y = draw_headline(card, draw, headline, language, y, emoji=emoji)
    y = draw_image_block(card, image_path, y, image_block_height)

    draw = ImageDraw.Draw(card)
    y = draw_summary(card, draw, summary, language, y)

    draw_footer(card, draw, language, y)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    card.save(output_path)
    return output_path


if __name__ == "__main__":
    path_en = create_card(
        headline="India Unveils Bold New Education Scheme for Colleges",
        summary="The government announced a fresh push to modernize higher "
                "education, focusing on skill-based learning and better "
                "funding for state colleges across the country.",
        language="en",
        emoji="📚",
        output_path="output/test_card_en.png",
    )
    print(f"English card saved: {path_en}")

    path_hi = create_card(
        headline="भारत में कॉलेजों के लिए नई शिक्षा नीति की घोषणा",
        summary="सरकार ने उच्च शिक्षा में सुधार के लिए एक नई योजना की घोषणा की है, "
                "जिसमें कौशल आधारित शिक्षा पर विशेष ध्यान दिया गया है।",
        language="hi",
        emoji="📚",
        output_path="output/test_card_hi.png",
    )
    print(f"Hindi card saved: {path_hi}")
