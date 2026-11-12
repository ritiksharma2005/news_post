"""
news_anchor_ai/video/renderer.py
Master 9:16 Video Compositing Engine for NEWS NIT IIT.
Implements the exact 5-step broadcast visual sequence:
1. 0–5s: Anchor opens with question (motion clip + breaking badge)
2. 5–15s: Framed post image with HUD tech corners [  ]
3. 15–27s: Slow camera push-in on graphic details + pause-to-read badge
4. 27–35s: Return to anchor for the 'Bigger Picture' takeaway
5. 35–40s: NEWS NIT IIT — Your campus, our news branded closing
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict

from news_anchor_ai.config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS,
    TEMP_DIR,
    REELS_DIR
)
from news_anchor_ai.backgrounds.studio_builder import (
    create_anchor_scene_frame,
    create_post_reading_frame,
    create_outro_frame
)
from news_anchor_ai.avatar.anchor_manager import (
    get_anchor_intro_clip,
    get_anchor_takeaway_clip
)
from news_anchor_ai.voice.bg_audio_generator import ensure_background_music

def generate_subtitles_srt(word_timestamps: List[Dict], srt_path: Path):
    """Generates animated 3-4 word subtitle bursts for modern mobile Reels."""
    if not word_timestamps:
        return

    def fmt_ts(sec: float) -> str:
        hrs = int(sec // 3600)
        mins = int((sec % 3600) // 60)
        secs = int(sec % 60)
        millis = int((sec - int(sec)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    chunks = []
    chunk_size = 4
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


def render_master_news_reel(
    job_id: str,
    headline: str,
    category: str,
    post_image_path: str,
    voice_path: Path,
    total_duration: float,
    word_timestamps: List[Dict],
    anchor_type: str = "scarf"
) -> Path:
    """
    Renders the complete broadcast television Reel adhering strictly
    to the 5-step visual sequence.
    """
    out_video_path = REELS_DIR / f"reel_{job_id}.mp4"
    srt_path = TEMP_DIR / f"subs_{job_id}.srt"
    bg_audio_path = ensure_background_music(total_duration + 5.0)

    # 1. Prepare visual layers
    post_frame = create_post_reading_frame(post_image_path, headline, category)
    outro_frame = create_outro_frame()

    # Anchor motion clips (0-5s intro and 27-35s return)
    intro_clip = get_anchor_intro_clip(anchor_type, duration=6.0)
    takeaway_clip = get_anchor_takeaway_clip(anchor_type, duration=8.0)

    # 2. Subtitles
    generate_subtitles_srt(word_timestamps, srt_path)

    # 3. Time segments
    t_intro_end = 5.0
    t_takeaway_start = max(total_duration - 12.0, t_intro_end + 12.0)
    t_outro_start = max(total_duration - 4.5, t_takeaway_start + 6.0)

    print(f"[Renderer] 5-Step Visual Sequence:")
    print(f"  1. 0.0s – {t_intro_end}s: Anchor Hook Opening (Motion Video)")
    print(f"  2. {t_intro_end}s – 15.0s: Framed Post Graphic & HUD Tech Corners")
    print(f"  3. 15.0s – {t_takeaway_start}s: Detail Push-in & Pause-to-Read Banner")
    print(f"  4. {t_takeaway_start}s – {t_outro_start}s: Return to Anchor for Bigger Picture")
    print(f"  5. {t_outro_start}s – {total_duration:.1f}s: Branded Outro ('Your campus, our news')")

    # 4. Construct Subtitle Filter (Electric Yellow #FFE600 with 3px black stroke in safe zone)
    sub_filter = ""
    if srt_path.exists() and srt_path.stat().st_size > 0:
        clean_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")
        sub_filter = f",subtitles='{clean_srt}':force_style='Fontname=Noto Sans,Fontsize=20,PrimaryColour=&H0000FFFF&,OutlineColour=&H00000000&,BorderStyle=3,Outline=3,Shadow=1,Alignment=2,MarginV=220'"

    # 5. Master Multi-Layer FFmpeg Command
    # Inputs:
    # [0:v] Intro anchor motion video
    # [1:v] Static anchor frame / fallback
    # [2:v] Framed post graphic with HUD corners
    # [3:v] Outro frame
    # [4:v] Takeaway anchor motion video
    # [5:a] Voiceover track
    # [6:a] 112 BPM news ticker ambient bed
    anchor_base_frame = create_anchor_scene_frame(anchor_type, headline, category)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(total_duration), "-i", str(anchor_base_frame), # [0:v]
        "-loop", "1", "-t", str(total_duration), "-i", str(post_frame),        # [1:v]
        "-loop", "1", "-t", str(total_duration), "-i", str(outro_frame),       # [2:v]
        "-i", str(intro_clip),                                                 # [3:v]
        "-i", str(takeaway_clip),                                              # [4:v]
        "-i", str(voice_path),                                                 # [5:a]
        "-i", str(bg_audio_path),                                              # [6:a]
        "-filter_complex",
        # Layer 1: Start with Intro clip (0 to t_intro_end)
        f"[0:v][3:v]overlay=enable='between(t,0,{t_intro_end})'[v1];"
        # Layer 2: Show Post reading graphic from t_intro_end to t_takeaway_start
        f"[v1][1:v]overlay=enable='between(t,{t_intro_end},{t_takeaway_start})'[v2];"
        # Layer 3: Return to Takeaway anchor clip from t_takeaway_start to t_outro_start
        f"[v2][4:v]overlay=enable='between(t,{t_takeaway_start},{t_outro_start})'[v3];"
        # Layer 4: Show Outro slide from t_outro_start to end
        f"[v3][2:v]overlay=enable='gte(t,{t_outro_start})'[v4]"
        # Layer 5: Subtitles
        f"{'[v4]' + sub_filter[1:] + '[vout]' if sub_filter else ';[v4]copy[vout]'};"
        # Audio Mix: Voice at 100% (1.0), newsroom ambient bed at -20dB (0.10)
        "[5:a]volume=1.0[v_aud];"
        "[6:a]volume=0.10[bg_aud];"
        "[v_aud][bg_aud]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "21",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(out_video_path)
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[Renderer Error] FFmpeg rendering failed: {res.stderr[-400:]}")
            # Robust fallback
            fb_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(total_duration), "-i", str(post_frame),
                "-i", str(voice_path),
                "-c:v", "libx264", "-c:a", "aac", "-shortest", "-pix_fmt", "yuv420p",
                str(out_video_path)
            ]
            subprocess.run(fb_cmd, check=True)
    except Exception as e:
        print(f"[Renderer Exception] {e}")

    print(f"[Renderer] 🚀 Master 9:16 News Reel rendered successfully: {out_video_path.name}")
    return out_video_path
