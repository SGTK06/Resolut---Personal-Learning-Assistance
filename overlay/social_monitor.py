"""
Social Media Monitor Service

Monitors user activity and enforces intervention when prolonged
social media scrolling is detected.

States: IDLE -> WARNING -> NEGOTIATING -> LOCKDOWN
"""

import time
import requests
import psutil
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from activity_monitor import ActivityMonitor, BROWSER_APPS
from popup_window import PopupWindow

LOCAL_SERVICE_URL = "http://127.0.0.1:8000"


class SocialMonitorService:
    def __init__(self):
        self.monitor = ActivityMonitor()
        self.app = QApplication(sys.argv)
        self.popup = None

        # State tracking
        self.social_start_time = None
        self.non_social_start_time = None
        self.state = "IDLE"
        self.warning_shown = False
        self.negotiation_shown = False

        # Thresholds (seconds)
        self.warning_threshold = 180        # 3 min: show warning
        self.negotiation_threshold = 300    # 5 min: show negotiation
        self.lockdown_threshold = 360       # 6 min: enforce lockdown

        self.monitor.start()

    def get_settings(self):
        """Fetch intervention thresholds from backend."""
        try:
            resp = requests.get(f"{LOCAL_SERVICE_URL}/api/dev/lockdown_settings", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                self.warning_threshold = data.get("warning_interval_seconds", 180)
                negotiation_delta = data.get("negotiation_interval_seconds", 120)
                self.negotiation_threshold = self.warning_threshold + negotiation_delta
                self.lockdown_threshold = self.negotiation_threshold + 60
        except Exception:
            pass

    def check_lockdown_status(self) -> bool:
        """Check if server has lockdown enabled."""
        try:
            resp = requests.get(f"{LOCAL_SERVICE_URL}/api/lockdown/status", timeout=2)
            if resp.status_code == 200:
                return resp.json().get("is_locked_down", False)
        except Exception:
            pass
        return False

    def trigger_lockdown_on_server(self):
        """Tell server we entered lockdown."""
        try:
            requests.post(f"{LOCAL_SERVICE_URL}/api/lockdown/trigger", timeout=2)
        except Exception:
            pass

    def trigger_negotiation(self, app_name: str, duration_min: float) -> str:
        """Get a negotiation message from the AI."""
        try:
            prompt = f"User on {app_name} for {duration_min:.1f} min. Suggest they stop."
            resp = requests.post(
                f"{LOCAL_SERVICE_URL}/api/query",
                data={"topic": "wellbeing", "query": prompt},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get("response", "Time to learn something new!")
        except Exception:
            pass
        return "You've been scrolling for too long. Let's do a quick lesson?"

    def enforce_lockdown(self):
        """Kill browsers and bring Resolut window to foreground."""
        # Kill browser processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in BROWSER_APPS:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Focus Resolut window
        try:
            import win32gui
            import win32con

            def find_resolut_window(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "Resolut Learning Assistant" in title:
                        windows.append(hwnd)

            windows = []
            win32gui.EnumWindows(find_resolut_window, windows)

            if windows:
                hwnd = windows[0]
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Could not focus Resolut window: {e}")

    def show_popup(self, title: str, message: str):
        """Show a notification popup."""
        if self.popup:
            self.popup.close()
        self.popup = PopupWindow(title, message)
        self.popup.show()

    def reset_session(self):
        """Reset all state for a new monitoring session."""
        self.social_start_time = None
        self.state = "IDLE"
        self.warning_shown = False
        self.negotiation_shown = False
        print("Session reset")

    def update_loop(self):
        """Main monitoring loop, runs every second."""
        # Refresh settings periodically
        if int(time.time()) % 10 == 0:
            self.get_settings()

        # Check server lockdown status
        if self.check_lockdown_status():
            self.state = "LOCKDOWN"
            self.enforce_lockdown()
            return

        # Get current activity data
        data = self.monitor.current_data
        if not data:
            return

        is_social = data.get("is_social", False)
        now = time.time()

        if is_social:
            self.non_social_start_time = None

            # Start tracking if new session
            if self.social_start_time is None:
                self.social_start_time = now
                self.state = "MONITORING"

            duration = now - self.social_start_time

            # Check thresholds (highest first)
            if duration > self.lockdown_threshold:
                if self.state != "LOCKDOWN":
                    print("Entering LOCKDOWN")
                    self.state = "LOCKDOWN"
                    self.trigger_lockdown_on_server()
                self.enforce_lockdown()

            elif duration > self.negotiation_threshold:
                if not self.negotiation_shown:
                    print("Showing negotiation")
                    self.state = "NEGOTIATING"
                    msg = self.trigger_negotiation(data["app"], duration / 60)
                    self.show_popup("Taking a Break?", msg)
                    self.negotiation_shown = True

            elif duration > self.warning_threshold:
                if not self.warning_shown:
                    print("Showing warning")
                    self.state = "WARNING"
                    self.show_popup(
                        "Scroll Mindfully!",
                        "You've been scrolling for a while.\nTime to do something productive?"
                    )
                    self.warning_shown = True
        else:
            # Not on social media
            if self.non_social_start_time is None:
                self.non_social_start_time = now
            elif now - self.non_social_start_time > 30:
                # 30 seconds break = reset session (unless locked)
                if self.state != "LOCKDOWN":
                    self.reset_session()

    def run(self):
        """Start the monitor service."""
        timer = QTimer()
        timer.timeout.connect(self.update_loop)
        timer.start(1000)
        sys.exit(self.app.exec())


if __name__ == "__main__":
    service = SocialMonitorService()
    service.run()
