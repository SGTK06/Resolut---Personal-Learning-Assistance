# activity_monitor.py
import time
import threading
import psutil
import win32gui
import win32process
from collections import deque
from pynput import mouse, keyboard

SOCIAL_KEYWORDS = {
    "instagram", "facebook", "tiktok", "whatsapp",
    "twitter", "x.com", "reddit", "snapchat",
    "youtube", "threads"
}

BROWSER_APPS = {
    "chrome.exe", "msedge.exe",
    "firefox.exe", "brave.exe"
}


class ActivityMonitor:
    def __init__(self, averaging_window=60):
        self.averaging_window = averaging_window

        self.scroll_events = deque()
        self.key_events = deque()

        self.current_data = {}
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        self.running = True

        mouse.Listener(on_scroll=self._on_scroll).start()
        keyboard.Listener(on_press=self._on_key).start()

        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _on_scroll(self, x, y, dx, dy):
        with self.lock:
            self.scroll_events.append((time.time(), abs(dy)))

    def _on_key(self, key):
        with self.lock:
            self.key_events.append(time.time())

    def _loop(self):
        last_app = None
        app_start = time.time()

        while self.running:
            now = time.time()

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

            # prune old events
            with self.lock:
                while self.scroll_events and self.scroll_events[0][0] < now - self.averaging_window:
                    self.scroll_events.popleft()
                while self.key_events and self.key_events[0] < now - self.averaging_window:
                    self.key_events.popleft()

                scrolls = sum(v for _, v in self.scroll_events)
                keys = len(self.key_events)

            scrolls_per_min = scrolls / (self.averaging_window / 60)
            keys_per_min = keys / (self.averaging_window / 60)

            # scoring
            score = 0.0
            if app in BROWSER_APPS:
                score += 0.2
            if any(k in title.lower() for k in SOCIAL_KEYWORDS):
                score += 0.45
            if scrolls_per_min > 60 and keys_per_min < 5:
                score += 0.25
            if now - app_start > self.averaging_window / 2:
                score += 0.1

            score = min(score, 1.0)

            with self.lock:
                self.current_data = {
                    "app": app,
                    "title": title,
                    "scrolls_per_min": round(scrolls_per_min, 1),
                    "keys_per_min": round(keys_per_min, 1),
                    "confidence": round(score, 2),
                    "is_social": score >= 0.6
                }

            time.sleep(0.25)  # monitor tick (4Hz)
