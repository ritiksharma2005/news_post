"""
news_anchor_ai/avatar/avatar_animator.py
AI Character Motion & Talking Avatar Engine (Option B: Hedra / Replicate / Fal).
Converts the still character portrait into an animated human-like news presenter
with natural lip movements, head tilts, and upper-body postures.
Includes automatic fallback if no external API key is provided.
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional

from news_anchor_ai.config import (
    TEMP_DIR,
    ANCHOR_SCARF_IMAGE,
    ANCHOR_GAITER_IMAGE
)

HEDRA_API_KEY = os.getenv("HEDRA_API_KEY", "").strip()
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "").strip()

def animate_character_with_hedra(image_path: Path, audio_path: Path, post_id: str) -> Optional[Path]:
    """
    Calls Hedra Character-2 API to generate talking anchor video
    with expressive facial animation, head motion, and body presence.
    """
    if not HEDRA_API_KEY:
        return None

    print(f"[Avatar Engine] Connecting to Hedra AI Character API...")
    headers = {"X-API-KEY": HEDRA_API_KEY}

    try:
        # 1. Upload Audio
        with open(audio_path, "rb") as f:
            audio_resp = requests.post(
                "https://mercury.dev.hedra.com/v1/audio",
                headers=headers,
                files={"file": f},
                timeout=60
            ).json()
        audio_id = audio_resp.get("url") or audio_resp.get("id")
        if not audio_id:
            print(f"[Avatar Engine] Hedra audio upload failed: {audio_resp}")
            return None

        # 2. Upload Character Image
        with open(image_path, "rb") as f:
            img_resp = requests.post(
                "https://mercury.dev.hedra.com/v1/portrait",
                headers=headers,
                files={"file": f},
                timeout=60
            ).json()
        image_id = img_resp.get("url") or img_resp.get("id")
        if not image_id:
            print(f"[Avatar Engine] Hedra image upload failed: {img_resp}")
            return None

        # 3. Create Video Project (9:16 vertical)
        gen_payload = {
            "avatarImageId": image_id,
            "audioSourceId": audio_id,
            "aspectRatio": "9:16"
        }
        proj_resp = requests.post(
            "https://mercury.dev.hedra.com/v1/characters",
            headers=headers,
            json=gen_payload,
            timeout=30
        ).json()
        job_id = proj_resp.get("jobId") or proj_resp.get("id")

        if not job_id:
            print(f"[Avatar Engine] Failed to start Hedra character job: {proj_resp}")
            return None

        print(f"[Avatar Engine] Hedra job started (ID: {job_id}). Polling generation...")

        # 4. Poll until complete
        out_video = TEMP_DIR / f"avatar_moving_{post_id}.mp4"
        poll_url = f"https://mercury.dev.hedra.com/v1/projects/{job_id}"

        for attempt in range(40):
            time.sleep(6)
            status_data = requests.get(poll_url, headers=headers, timeout=20).json()
            status = status_data.get("status")
            print(f"  Hedra poll {attempt+1}/40: {status} ({status_data.get('progress', 0)}%)")

            if status == "Complete" and status_data.get("videoUrl"):
                download_url = status_data["videoUrl"]
                vid_data = requests.get(download_url, timeout=60).content
                with open(out_video, "wb") as f:
                    f.write(vid_data)
                print(f"[Avatar Engine] 🚀 Successfully generated animated character video: {out_video.name}")
                return out_video
            elif status in ["Failed", "Error"]:
                print(f"[Avatar Engine] Hedra rendering failed: {status_data}")
                return None

    except Exception as e:
        print(f"[Avatar Engine] Hedra API error: {e}")
        return None

    return None


def get_animated_anchor_video(anchor_type: str, audio_path: Path, post_id: str) -> Optional[Path]:
    """
    Master entry point for Option B character animation:
    1. Checks Hedra API
    2. Falls back gracefully if no key is supplied
    """
    image_path = ANCHOR_SCARF_IMAGE if anchor_type == "scarf" else ANCHOR_GAITER_IMAGE
    
    # Try Hedra if key is configured
    if HEDRA_API_KEY:
        anim_video = animate_character_with_hedra(image_path, audio_path, post_id)
        if anim_video and anim_video.exists():
            return anim_video

    print("[Avatar Engine] Notice: No HEDRA_API_KEY set. To activate full human hand & body motion, add HEDRA_API_KEY to GitHub Secrets.")
    return None
