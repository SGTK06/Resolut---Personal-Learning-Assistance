"""
Scroll Monitor Configuration

Developer-tweakable settings for the social media scrolling detection
and lockdown enforcement system.
"""

import json
from pathlib import Path

# =============================================================================
# Time Thresholds (in minutes)
# =============================================================================

# Trigger notification after X minutes of continuous social media scrolling
SCROLL_DETECTION_THRESHOLD_MINUTES = 1.5

# Wait Y minutes during negotiation before enforcing lockdown
NEGOTIATION_WAIT_MINUTES = 1.5

# How often to check for lesson completion during lockdown (seconds)
LESSON_COMPLETION_POLL_INTERVAL = 5


# =============================================================================
# UI Settings
# =============================================================================

# Notification popup position: "center", "top-right", "bottom-right"
NOTIFICATION_POSITION = "center"

# Popup dimensions
POPUP_WIDTH = 450
POPUP_HEIGHT = 280


# =============================================================================
# Social Media Detection
# =============================================================================

# Native app process names (lowercase)
SOCIAL_MEDIA_APPS = [
    "instagram",
    "facebook",
    "tiktok",
    "twitter",
    "reddit",
    "snapchat",
    "threads",
    "whatsapp",
]

# Keywords to detect in browser window titles
SOCIAL_MEDIA_KEYWORDS = [
    "instagram",
    "facebook",
    "tiktok",
    "twitter",
    "x.com",
    "reddit",
    "youtube",
    "snapchat",
    "threads",
    "whatsapp",
    "discord",
    "pinterest",
    "linkedin",
    "twitch",
    "tumblr",
    "netflix",
    "disney+",
    "hulu",
]

# Browser process names to monitor
BROWSER_PROCESSES = [
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "vivaldi.exe",
]


# =============================================================================
# Backend Integration
# =============================================================================

# Local service URL for checking lesson completion
BACKEND_URL = "http://127.0.0.1:8000"

# Lesson completion check endpoint
LESSON_PROGRESS_ENDPOINT = "/api/lessons/progress"


# =============================================================================
# Negotiation Messages
# =============================================================================

MESSAGES = {
    "stage1_title": "Hey there! 👋",
    "stage1_body": "You've been scrolling for {minutes} minutes. How about completing a quick lesson to meet your daily target?",
    "stage1_accept": "Open Resolut",
    "stage1_decline": "5 more minutes",
    
    "stage2_title": "Time's almost up! ⏰",
    "stage2_body": "You've used your extra time. Let's focus on learning for a bit!",
    "stage2_accept": "Start Lesson Now",
    "stage2_decline": "I'll do it later",
    
    "stage3_title": "Learning Time! 📚",
    "stage3_body": "Complete one lesson to unlock social media. You've got this!",
    "stage3_button": "Let's Learn",
}


# =============================================================================
# Config Persistence (Optional)
# =============================================================================

CONFIG_FILE = Path(__file__).parent / "scroll_monitor_settings.json"


def load_user_config() -> dict:
    """Load user-customized settings if they exist."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_user_config(settings: dict):
    """Save user-customized settings."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")


def get_config_value(key: str, default=None):
    """Get a config value, preferring user settings over defaults."""
    user_config = load_user_config()
    if key in user_config:
        return user_config[key]
    return globals().get(key, default)
