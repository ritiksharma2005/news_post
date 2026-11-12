"""
news_anchor_ai/compositor/video_compositor.py
Composites the complete 30–45s 9:16 vertical Instagram Reel (1080x1920).
Integrates:
- Alternating Anchor character (Scarf vs Gaiter)
- Actual high-resolution post card for pause-and-read
- Breaking news lower-third banners
- Dynamic animated subtitles in the Instagram safe zone
- Broadcast audio mixing
"""

import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict

from news_anchor_ai.config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    TEMP_DIR,
    REELS_DIR,
    FONT_BOLD,
    FONT_REGULAR,
    BRAND_NAME,
    INSTAGRAM_ACCOUNT,
    ANCHOR_SCARF_IMAGE,
    ANCHOR_GAITER_IMAGE
)
from news_anchor_ai.backgrounds.studio_builder import (
    create_studio_background,
    create_post_reading_frame
)

def create_anchor_scene_frame(anchor_type: str, headline: str, category: str, subtitle: str = "") -> Path:
    """
    Renders a 1080x1920 frame featuring the masked anchor, news desk,
    top brand bar, and breaking news lower-third banner.
    """
    out_path = TEMP_DIR / f"anchor_scene_{anchor_type}.png"
    anchor_img_path = ANCHOR_SCARF_IMAGE if anchor_type == "scarf" else ANCHOR_GAITER_IMAGE

    # Base frame
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 14, 26, 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Load Anchor Image (crop/scale to fit 1080x1920 vertically)
    if anchor_img_path.exists():
        anchor = Image.open(anchor_img_path).convert("RGBA")
        # Resize maintaining aspect ratio to fill frame
        aspect = anchor.width / anchor.height
        target_h = int(VIDEO_WIDTH / aspect)
        anchor_resized = anchor.resize((VIDEO_WIDTH, target_h), Image.Resampling.LANCZOS)
        # Position anchor slightly lower so head and desk are framed naturally
        offset_y = (VIDEO_HEIGHT - target_h) // 2 + 80
        canvas.paste(anchor_resized, (0, offset_y), anchor_resized)

    # 2. Top Header Brand Bar
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 140)], fill=(15, 23, 42, 230))
    draw.rectangle([(0, 136), (VIDEO_WIDTH, 140)], fill=(225, 29, 72, 255))

    font_brand = ImageFont.truetype(str(FONT_BOLD), 36) if FONT_BOLD.exists() else ImageFont.load_default()
    font_live = ImageFont.truetype(str(FONT_BOLD), 22) if FONT_BOLD.exists() else ImageFont.load_default()
    font_cat = ImageFont.truetype(str(FONT_BOLD), 24) if FONT_BOLD.exists() else ImageFont.load_default()

    draw.text((40, 42), BRAND_NAME, fill=(255, 255, 255), font=font_brand)

    # Live Badge
    draw.rounded_rectangle([(VIDEO_WIDTH - 160, 42), (VIDEO_WIDTH - 40, 84)], radius=8, fill=(225, 29, 72))
    draw.text((VIDEO_WIDTH - 140, 49), "● LIVE", fill=(255, 255, 255), font=font_live)

    # 3. Lower-Third Breaking News Graphic Banner (at y=1420 to 1620)
    banner_y = 1420
    # Red category pill
    draw.rectangle([(50, banner_y - 36), (360, banner_y)], fill=(225, 29, 72))
    draw.text((65, banner_y - 30), f"⚡ {category.upper()[:18]}", fill=(255, 255, 255), font=font_cat)

    # Dark blue main headline container
    draw.rectangle([(50, banner_y), (VIDEO_WIDTH - 50, banner_y + 140)], fill=(15, 23, 42, 245), outline=(56, 189, 248, 200), width=2)

    font_headline = ImageFont.truetype(str(FONT_BOLD), 32) if FONT_BOLD.exists() else ImageFont.load_default()
    # Wrap headline text
    words = headline.split()
    line1, line2 = "", ""
    for w in words:
        if len(line1 + " " + w) <= 34:
            line1 += (" " if line1 else "") + w
        else:
            line2 += (" " if line2 else "") + w

    draw.text((75, banner_y + 25), line1, fill=(255, 255, 255), font=font_headline)
    if line2:
        draw.text((75, banner_y + 75), line2[:38], fill=(253, 224, 71), font=font_headline)

    canvas.convert("RGB").save(out_path, "PNG")
    return out_path


def create_outro_frame() -> Path:
    """Renders the final closing slide for NEWS NIT IIT."""
    out_path = TEMP_DIR / "outro_slide.png"
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (10, 15, 30, 255))
    draw = ImageDraw.Draw(canvas)

    font_big = ImageFont.truetype(str(FONT_BOLD), 64) if FONT_BOLD.exists() else ImageFont.load_default()
    font_sub = ImageFont.truetype(str(FONT_REGULAR), 32) if FONT_REGULAR.exists() else ImageFont.load_default()
    font_handle = ImageFont.truetype(str(FONT_BOLD), 38) if FONT_BOLD.exists() else ImageFont.load_default()

    # Center Brand
    draw.text(((VIDEO_WIDTH - 520) // 2, 700), BRAND_NAME, fill=(255, 255, 255), font=font_big)
    draw.text(((VIDEO_WIDTH - 640) // 2, 800), "Daily Verified Student & Exam Updates", fill=(148, 163, 184), font=font_sub)

    # Follow Box
    box_rect = [(VIDEO_WIDTH - 600) // 2, 940, (VIDEO_WIDTH + 600) // 2, 1040]
    draw.rounded_rectangle(box_rect, radius=20, fill=(225, 29, 72))
    draw.text(((VIDEO_WIDTH - 460) // 2, 965), f"FOLLOW {INSTAGRAM_ACCOUNT}", fill=(255, 255, 255), font=font_handle)

    canvas.convert("RGB").save(out_path, "PNG")
    return out_path


def generate_srt_subtitles(word_timestamps: List[Dict], srt_path: Path):
    """
    Groups words into short, fast 3-5 word subtitle bursts
    so subtitles appear animated and dynamic on screen.
    """
    if not word_timestamps:
        return

    def fmt_ts(sec: float) -> str:
        hrs = int(sec // 3600)
        mins = int((sec % 3600) // 60)
        secs = int(sec % 60)
        millis = int((sec - int(sec)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    chunks = []
    chunk_size = 4  # 4 words per burst for mobile Reels
    for i in range(0, len(word_timestamps), chunk_size):
        group = word_timestamps[i:i + chunk_size]
        text = " ".join(w["word"] for w in group)
        start = group[0]["start"]
        end = group[-1]["end"]
        chunks.append((start, end, text))

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (start, end, text) in enumerate(chunks, 1):
            f.write(f"{idx}\n")
            f.write(f"{fmt_ts(start)} --> {fmt_ts(end)}\n")
            f.write(f"{text.upper()}\n\n")


def composite_news_reel(
    post_id: str,
    headline: str,
    category: str,
    post_image_path: str,
    audio_path: Path,
    total_duration: float,
    word_timestamps: List[Dict],
    anchor_type: str = "scarf"
) -> Path:
    """
    Renders the complete 9:16 vertical Reel using FFmpeg.
    Transitions:
    - 0 to 7.5s: Anchor Intro
    - 7.5s to (total_duration - 12s): Post Image Reading Frame (pause and read)
    - (total_duration - 12s) to (total_duration - 4.5s): Anchor Return
    - (total_duration - 4.5s) to End: Outro Branding
    """
    out_video_path = REELS_DIR / f"reel_{post_id}.mp4"
    srt_path = TEMP_DIR / f"subs_{post_id}.srt"

    # 1. Generate frames
    anchor_frame = create_anchor_scene_frame(anchor_type, headline, category)
    post_frame = create_post_reading_frame(post_image_path, headline, category)
    outro_frame = create_outro_frame()

    # 2. Generate subtitles
    generate_srt_subtitles(word_timestamps, srt_path)

    # 3. Calculate timing slices
    t_intro_end = 7.5
    t_outro_start = max(total_duration - 4.5, t_intro_end + 10)
    t_anchor_return = max(t_outro_start - 8.0, t_intro_end + 5)

    print(f"[Compositor] Timing: Intro: 0–{t_intro_end}s | B-Roll: {t_intro_end}–{t_anchor_return}s | Return: {t_anchor_return}–{t_outro_start}s | Outro: {t_outro_start}–{total_duration}s")

    # 4. Construct FFmpeg filtergraph
    # We load 3 image inputs + 1 audio input
    # Subtitle filter: yellow text, black border, centered at y=1680 (Instagram safe zone)
    sub_filter = ""
    if srt_path.exists() and srt_path.stat().st_size > 0:
        clean_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")
        sub_filter = f",subtitles='{clean_srt}':force_style='Fontname=Noto Sans,Fontsize=18,PrimaryColour=&H00EBFD&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Alignment=2,MarginV=180'"

    # FFmpeg multi-image overlay command
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(total_duration), "-i", str(anchor_frame),  # [0:v]
        "-loop", "1", "-t", str(total_duration), "-i", str(post_frame),    # [1:v]
        "-loop", "1", "-t", str(total_duration), "-i", str(outro_frame),   # [2:v]
        "-i", str(audio_path),                                             # [3:a]
        "-filter_complex",
        f"[0:v][1:v]overlay=enable='between(t,{t_intro_end},{t_anchor_return})'[v1];"
        f"[v1][2:v]overlay=enable='gte(t,{t_outro_start})'[v2]"
        f"{'[v2]' + sub_filter[1:] + '[vout]' if sub_filter else ';[v2]copy[vout]'}",
        "-map", "[vout]",
        "-map", "3:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(out_video_path)
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[Compositor Error] FFmpeg rendering failed: {res.stderr[-500:]}")
            # Try simpler fallback render
            fallback_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(total_duration), "-i", str(post_frame),
                "-i", str(audio_path),
                "-c:v", "libx264", "-c:a", "aac", "-shortest", "-pix_fmt", "yuv420p",
                str(out_video_path)
            ]
            subprocess.run(fallback_cmd, check=True)
    except Exception as e:
        print(f"[Compositor Exception] {e}")

    print(f"[Compositor] Rendered finished 9:16 Reel: {out_video_path}")
    return out_video_path
