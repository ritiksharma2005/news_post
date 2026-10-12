"""
channel_digest/config.py
Configuration and environment management for Daily Instagram Broadcast Channel Digest.
Reuses existing project environment settings and defines channel-specific constants.
"""

import os
import sys
from pathlib import Path
from datetime import timezone, timedelta

# Ensure parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import config as root_config
except ImportError:
    root_config = None

from dotenv import load_dotenv

load_dotenv()


def clean_env(name: str) -> str:
    """Retrieve environment variable and strip extraneous quotes/spaces."""
    val = os.getenv(name)
    if not val and root_config and hasattr(root_config, name):
        val = getattr(root_config, name)
    if not val:
        return ""
    val = str(val).strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    return val


def clean_bot_token(name: str) -> str:
    """Clean Telegram bot token (stripping 'bot' prefix if present)."""
    token = clean_env(name)
    if token.lower().startswith("bot") and ":" in token:
        token = token[3:].strip()
    return token


# Credentials & IDs
INSTAGRAM_ACCESS_TOKEN = clean_env("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = clean_env("INSTAGRAM_USER_ID")
TELEGRAM_BOT_TOKEN = clean_bot_token("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = clean_env("TELEGRAM_CHAT_ID")
RAPIDAPI_KEY = clean_env("RAPIDAPI_KEY")
APIFY_TOKEN = clean_env("APIFY_TOKEN")

# Instagram Channel Metadata
INSTAGRAM_USERNAME = "news.nit_iit"
BROADCAST_CHANNEL_URL = "https://www.instagram.com/channel/AbYg9NWAeNaKS8gf/"

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "channel_digest.db"
HISTORY_FILE = DATA_DIR / "published_history.json"

# Timezone (Asia/Kolkata = UTC + 5:30)
TIMEZONE_NAME = "Asia/Kolkata"

def get_ist_timezone():
    """Returns Asia/Kolkata timezone object, falling back to fixed +05:30 offset if zoneinfo unavailable."""
    try:
        import zoneinfo
        return zoneinfo.ZoneInfo(TIMEZONE_NAME)
    except Exception:
        return timezone(timedelta(hours=5, minutes=30), name="IST")

IST_TZ = get_ist_timezone()

# Telegram Message Limit (Safe limit below 4096)
MAX_TELEGRAM_MESSAGE_CHARS = 3800
