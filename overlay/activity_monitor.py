# activity_monitor.py
"""
Activity Monitor - Enhanced with Duration Tracking

Monitors user activity and detects mindless social media scrolling.
Tracks continuous social media usage time and triggers callbacks when thresholds are exceeded.
"""

import time
import threading
import os
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
        self.off_social_start_time: Optional[float] = None # Grace period tracking
        self.was_on_social_media: bool = False
        
        # Self-identification to ignore self-focus
        import os
        self.self_pid = os.getpid()
        
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

    def _is_social_media_active(self, app: str, title: str) -> (bool, str):
        """Check if current activity is social media. Returns (bool, reason)."""
        app_lower = app.lower()
        title_lower = title.lower()
        
        # Explicit ignore for the agent's process OR IDE
        if "antigravity" in app_lower or "code.exe" in app_lower or "python.exe" in app_lower:
            return False, ""

        # 1. Check if the app itself is a known social media app
        from config import SOCIAL_MEDIA_APPS
        for sm_app in SOCIAL_MEDIA_APPS:
            if sm_app.lower() in app_lower:
                return True, f"app:{sm_app}"
        
        # 2. If it's a browser, check the title for keywords/patterns
        is_browser = False
        for browser in BROWSER_PROCESSES:
            if browser.lower() in app_lower:
                is_browser = True
                break
        
        if is_browser:
            # Check keywords in title
            for keyword in SOCIAL_MEDIA_KEYWORDS:
                if keyword.lower() in title_lower:
                    return True, f"keyword:{keyword}"
            
            # Check patterns in title
            patterns = ["reels", "shorts", "explore", "trending", "feed", "timeline"]
            for p in patterns:
                if p in title_lower:
                    return True, f"pattern:{p}"

        return False, ""

    def _loop(self):
        """Main monitoring loop."""
        last_app = None
        app_start = time.time()
        last_debug_time = 0

        while self.running:
            try:
                now = time.time()

                # Get foreground window info safely
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    time.sleep(0.5)
                    continue

                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                if pid <= 0:
                    time.sleep(0.5)
                    continue

                try:
                    app = psutil.Process(pid).name().lower()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
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

                # Check if on social media
                is_on_social, match_reason = self._is_social_media_active(app, title)
                is_self = (pid == self.self_pid)

                # Duration tracking with Grace Period (10s)
                with self.lock:
                    if is_on_social:
                        if not self.was_on_social_media:
                            self.social_media_start_time = now
                            self.was_on_social_media = True
                        
                        self.continuous_social_duration = now - (self.social_media_start_time or now)
                        self.off_social_start_time = None
                        self.last_state = f"ACTIVE ({match_reason})"
                    
                    elif is_self:
                        if self.was_on_social_media and self.social_media_start_time:
                            # Limit self-focus maintenance to 1 minute
                            if now - (self.off_social_start_time or now) < 60:
                                self.continuous_social_duration = now - self.social_media_start_time
                                self.last_state = "SELF-FOCUS (Persisted)"
                    
                    else:
                        if self.was_on_social_media:
                            if self.off_social_start_time is None:
                                self.off_social_start_time = now
                            
                            # Reduced grace period from 10s to 5s
                            if now - self.off_social_start_time > 5:
                                self.social_media_start_time = None
                                self.continuous_social_duration = 0
                                self.was_on_social_media = False
                                self.threshold_triggered = False
                                self.off_social_start_time = None
                                self.last_state = "FOCUSED"
                            else:
                                if self.social_media_start_time:
                                    self.continuous_social_duration = now - self.social_media_start_time
                                    self.last_state = "GRACE-PERIOD (Persisted)"
                        else:
                            self.last_state = "FOCUSED"

                    # Stable session state (Effective state)
                    is_effectively_on_social = self.was_on_social_media

                    self.current_data = {
                        "app": app,
                        "title": title,
                        "is_social": is_effectively_on_social,
                        "immediate_is_social": is_on_social,
                        "continuous_minutes": round(self.continuous_social_duration / 60, 2)
                    }

                # Trigger callbacks based on stable session state
                if is_effectively_on_social:
                    if not self.threshold_triggered:
                        minutes = self.continuous_social_duration / 60
                        if minutes >= SCROLL_DETECTION_THRESHOLD_MINUTES:
                            print(f"[Monitor] THRESHOLD HIT: {minutes:.2f} mins. Triggering nudge...")
                            self.threshold_triggered = True
                            if self.on_threshold_exceeded:
                                self.on_threshold_exceeded(minutes)
                    
                    if self.on_social_media_detected:
                        self.on_social_media_detected(self.current_data)

                # Debug output (Every 2 seconds)
                if now - last_debug_time > 2.0:
                    state_lbl = getattr(self, 'last_state', 'FOCUSED')
                    print(f"[Monitor] {state_lbl:25} | {app:15} | {title[:25]}... | {self.continuous_social_duration:.1f}s")
                    last_debug_time = now

            except Exception as e:
                print(f"[Monitor] Loop Error: {e}")
                time.sleep(1.0)
                continue

            time.sleep(0.5)

