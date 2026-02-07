# activity_monitor.py
"""
Activity Monitor - Enhanced with Duration Tracking

Monitors user activity and detects mindless social media scrolling.
Tracks continuous social media usage time and triggers callbacks when thresholds are exceeded.
"""

import time
import threading
import psutil
import win32gui
import win32process
from collections import deque
from pynput import mouse, keyboard
from typing import Callable, Optional

try:
    from .config import (
        SOCIAL_MEDIA_KEYWORDS, BROWSER_PROCESSES,
        SCROLL_DETECTION_THRESHOLD_MINUTES
    )
except ImportError:
    from config import (
        SOCIAL_MEDIA_KEYWORDS, BROWSER_PROCESSES,
        SCROLL_DETECTION_THRESHOLD_MINUTES
    )


class ActivityMonitor:
    """
    Monitors user activity to detect social media scrolling behavior.
    
    Features:
    - Tracks scroll events and keyboard activity
    - Detects social media apps and browser tabs
    - Calculates confidence score for "mindless scrolling"
    - Tracks continuous social media usage duration
    - Triggers callbacks when thresholds are exceeded
    """
    
    def __init__(self, averaging_window: int = 60):
        """
        Initialize the activity monitor.
        
        Args:
            averaging_window: Window in seconds for calculating scroll/key rates
        """
        self.averaging_window = averaging_window

        self.scroll_events = deque()
        self.key_events = deque()

        self.current_data = {}
        self.lock = threading.Lock()
        self.running = False
        
        # Duration tracking
        self.social_media_start_time: Optional[float] = None
        self.continuous_social_duration: float = 0  # in seconds
        self.was_on_social_media: bool = False
        
        # Callbacks
        self.on_threshold_exceeded: Optional[Callable[[float], None]] = None
        self.on_social_media_detected: Optional[Callable[[dict], None]] = None
        self.threshold_triggered: bool = False

    def start(self):
        """Start monitoring user activity."""
        self.running = True
        self.threshold_triggered = False

        mouse.Listener(on_scroll=self._on_scroll).start()
        keyboard.Listener(on_press=self._on_key).start()

        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        """Stop monitoring."""
        self.running = False

    def reset_duration(self):
        """Reset the continuous social media duration counter."""
        with self.lock:
            self.social_media_start_time = None
            self.continuous_social_duration = 0
            self.was_on_social_media = False
            self.threshold_triggered = False

    def get_continuous_social_duration_minutes(self) -> float:
        """Returns minutes of continuous social media usage."""
        with self.lock:
            return self.continuous_social_duration / 60

    def _on_scroll(self, x, y, dx, dy):
        with self.lock:
            self.scroll_events.append((time.time(), abs(dy)))

    def _on_key(self, key):
        with self.lock:
            self.key_events.append(time.time())

    def _is_social_media_active(self, app: str, title: str) -> bool:
        """Check if current activity is social media."""
        app_lower = app.lower()
        title_lower = title.lower()
        
        # Check if it's a browser with social media content
        is_browser = any(browser.lower() in app_lower for browser in BROWSER_PROCESSES)
        
        if is_browser:
            # Check window title for social media keywords
            for keyword in SOCIAL_MEDIA_KEYWORDS:
                kw_lower = keyword.lower()
                if kw_lower in title_lower:
                    return True
            
            # Also check for common URL patterns in browser titles
            # Browsers often show "Site Name - Browser" or "Page Title - Site - Browser"
            social_url_patterns = [
                "youtube.com", "instagram.com", "facebook.com", "twitter.com",
                "tiktok.com", "reddit.com", "x.com", "snapchat.com", "threads.net",
                "whatsapp", "- youtube", "- instagram", "- facebook", "- twitter",
                "- tiktok", "- reddit", "- x -", "| youtube", "| instagram"
            ]
            for pattern in social_url_patterns:
                if pattern in title_lower:
                    return True
        
        # Check if it's a social media app process directly
        for keyword in SOCIAL_MEDIA_KEYWORDS:
            kw_lower = keyword.lower()
            if kw_lower in app_lower:
                return True
                
        return False

    def _loop(self):
        """Main monitoring loop."""
        last_app = None
        app_start = time.time()

        while self.running:
            now = time.time()

            # Get foreground window info
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid > 0:
                try:
                    app = psutil.Process(pid).name().lower()
                except psutil.NoSuchProcess:
                    app = "unknown"
            else:
                app = "unknown"

            if app != last_app:
                last_app = app
                app_start = now

            # Prune old events
            with self.lock:
                while self.scroll_events and self.scroll_events[0][0] < now - self.averaging_window:
                    self.scroll_events.popleft()
                while self.key_events and self.key_events[0] < now - self.averaging_window:
                    self.key_events.popleft()

                scrolls = sum(v for _, v in self.scroll_events)
                keys = len(self.key_events)

            scrolls_per_min = scrolls / (self.averaging_window / 60)
            keys_per_min = keys / (self.averaging_window / 60)

            # Check if on social media
            is_on_social = self._is_social_media_active(app, title)

            # Scoring for confidence
            score = 0.0
            if app.lower() in [p.lower() for p in BROWSER_PROCESSES]:
                score += 0.2
            if is_on_social:
                score += 0.45
            if scrolls_per_min > 60 and keys_per_min < 5:
                score += 0.25
            if now - app_start > self.averaging_window / 2:
                score += 0.1

            score = min(score, 1.0)

            # Duration tracking
            with self.lock:
                if is_on_social:
                    if not self.was_on_social_media:
                        # Just started using social media
                        self.social_media_start_time = now
                        self.was_on_social_media = True
                    else:
                        # Continue tracking
                        if self.social_media_start_time:
                            self.continuous_social_duration = now - self.social_media_start_time
                else:
                    # Left social media - reset
                    if self.was_on_social_media:
                        self.social_media_start_time = None
                        self.continuous_social_duration = 0
                        self.was_on_social_media = False
                        self.threshold_triggered = False

                self.current_data = {
                    "app": app,
                    "title": title,
                    "scrolls_per_min": round(scrolls_per_min, 1),
                    "keys_per_min": round(keys_per_min, 1),
                    "confidence": round(score, 2),
                    "is_social": is_on_social,
                    "continuous_minutes": round(self.continuous_social_duration / 60, 1)
                }

            # Check threshold and trigger callback
            if is_on_social and not self.threshold_triggered:
                minutes = self.continuous_social_duration / 60
                if minutes >= SCROLL_DETECTION_THRESHOLD_MINUTES:
                    self.threshold_triggered = True
                    if self.on_threshold_exceeded:
                        self.on_threshold_exceeded(minutes)
            
            # Trigger social media detection callback
            if is_on_social and self.on_social_media_detected:
                self.on_social_media_detected(self.current_data)

            time.sleep(0.25)  # Monitor tick (4Hz)

