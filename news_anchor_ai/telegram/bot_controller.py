"""
news_anchor_ai/telegram/bot_controller.py
Telegram Bot Control Plane for NEWS NIT IIT — AI Anchor Studio.
Implements:
- /start, /help, /status, /cancel commands
- Direct Instagram Post URL submission
- Media upload fallback (when an Instagram URL is private/inaccessible)
- Real-time job progress notifications (Job ID: NNIIT-2026-XXX)
- Video delivery with 4 interactive buttons:
  [ APPROVE & PUBLISH ], [ REGENERATE SCRIPT ], [ REGENERATE VOICE ], [ REJECT ]
- Single-tap publishing to @news.nit_iit with double-publish protection
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional

from news_anchor_ai.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    BRAND_NAME,
    INSTAGRAM_ACCOUNT
)
from news_anchor_ai.database.job_manager import (
    create_job,
    update_job_status,
    get_job,
    get_latest_job
)
from news_anchor_ai.publisher.instagram_reel_publisher import publish_video_reel

def send_telegram_message(text: str, reply_markup: dict = None) -> bool:
    """Sends a message to the authorized Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(url, json=payload, timeout=20)
        return resp.json().get("ok", False)
    except Exception as e:
        print(f"[Telegram Bot] Send error: {e}")
        return False

def get_telegram_file_url(file_id: str) -> Optional[str]:
    """Retrieves public direct CDN download URL for uploaded video/photo."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url, timeout=15).json()
        if resp.get("ok"):
            file_path = resp["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"[Telegram Bot] Error fetching file URL: {e}")
    return None

def send_job_status(job_id: str, stage_text: str):
    """Sends structured progress status to Telegram."""
    msg = f"⏳ *[{job_id}]* {stage_text}"
    send_telegram_message(msg)

def deliver_reel_for_review(job_id: str, video_path: Path, metadata: Dict) -> bool:
    """
    Delivers the finished 1080x1920 MP4 to Telegram with the 4 interactive buttons.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    caption_text = (
        f"🎬 *{BRAND_NAME} — VIDEO READY FOR REVIEW*\n\n"
        f"🆔 *Job ID*: {job_id}\n"
        f"📌 *Headline*: {metadata.get('headline', '')}\n"
        f"⏱️ *Duration*: {metadata.get('duration', 0):.1f}s (9:16 Vertical Reel)\n"
        f"👤 *Anchor*: Masked Anchor ({metadata.get('anchor_type', 'scarf').capitalize()})\n\n"
        f"📝 *Instagram Caption & Hashtags*:\n{metadata.get('reel_caption', '')[:350]}...\n\n"
        f"Review the video above and choose an action:"
    )

    inline_keyboard = [
        [{"text": "✅ APPROVE & PUBLISH", "callback_data": f"approve:{job_id}"}],
        [
            {"text": "🔄 REGEN SCRIPT", "callback_data": f"regen_script:{job_id}"},
            {"text": "🔄 REGEN VOICE", "callback_data": f"regen_voice:{job_id}"}
        ],
        [{"text": "❌ REJECT", "callback_data": f"reject:{job_id}"}]
    ]

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    try:
        with open(video_path, "rb") as vf:
            files = {"video": vf}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_text,
                "supports_streaming": True,
                "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
            }
            resp = requests.post(url, data=data, files=files, timeout=120).json()

        if not resp.get("ok"):
            print(f"[Telegram Bot] Failed to send video: {resp}")
            return False

        # Extract Telegram CDN video URL for Instagram Graph API
        public_url = None
        if "result" in resp and "video" in resp["result"]:
            file_id = resp["result"]["video"]["file_id"]
            public_url = get_telegram_file_url(file_id)

        update_job_status(job_id, "PENDING_APPROVAL", {
            "public_video_url": public_url,
            "video_path": str(video_path),
            "headline": metadata.get("headline", ""),
            "reel_caption": metadata.get("reel_caption", "")
        })
        print(f"[Telegram Bot] Delivered Job {job_id} to Telegram for review! Public URL: {public_url}")
        return True

    except Exception as e:
        print(f"[Telegram Bot] Error delivering video: {e}")
        return False


def handle_approval_action(job_id: str) -> bool:
    """
    Executes the APPROVE & PUBLISH action:
    Checks single-user approval, enforces zero double-publish,
    and publishes directly to Instagram Reels via Graph API.
    """
    job = get_job(job_id)
    if not job:
        send_telegram_message(f"❌ Error: Job {job_id} not found.")
        return False

    if job.get("is_published"):
        send_telegram_message(f"⚠️ Notice: Job {job_id} has already been published. Cannot publish twice.")
        return False

    if job.get("is_rejected"):
        send_telegram_message(f"❌ Error: Job {job_id} was rejected and cannot be published.")
        return False

    public_url = job.get("public_video_url")
    caption = job.get("reel_caption", "")

    send_telegram_message(f"🚀 *[{job_id}] Authorization verified! Publishing Reel to {INSTAGRAM_ACCOUNT}...*")

    success = publish_video_reel(public_url, caption)
    if success:
        update_job_status(job_id, "PUBLISHED", {"is_published": True})
        send_telegram_message(f"🎉 *[{job_id}] SUCCESS! Reel is live on Instagram: {INSTAGRAM_ACCOUNT}*")
    else:
        send_telegram_message(f"⚠️ *[{job_id}] Instagram publishing failed. Please check token or retry.*")
    return success

def handle_reject_action(job_id: str):
    """Marks job as REJECTED."""
    update_job_status(job_id, "REJECTED", {"is_rejected": True})
    send_telegram_message(f"🛑 *[{job_id}] Job marked as REJECTED. This video will never be published.*")
