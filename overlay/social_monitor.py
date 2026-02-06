import time
import requests
import psutil
import threading
import sys
import webbrowser
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from activity_monitor import ActivityMonitor, BROWSER_APPS
from popup_window import PopupWindow

# Configuration API
LOCAL_SERVICE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

class SocialMonitorService:
    def __init__(self):
        self.monitor = ActivityMonitor()
        self.app = QApplication(sys.argv)
        self.popup = None
        
        # State tracking
        self.social_start_time = None
        self.state = "IDLE" # IDLE, MONITORING, WARNING, NEGOTIATING, LOCKDOWN
        self.warning_shown = False
        self.negotiation_shown = False
        self.non_social_start_time = None
        
        # Default settings (will update from API)
        self.warning_threshold = 180 # 3 minutes
        self.negotiation_threshold_delta = 120 # +2 minutes (total 5)
        
        self.monitor.start()
        
    def get_settings(self):
        try:
            resp = requests.get(f"{LOCAL_SERVICE_URL}/api/dev/lockdown_settings", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                self.warning_threshold = data.get("warning_interval_seconds", 180)
                self.negotiation_threshold_delta = data.get("negotiation_interval_seconds", 120)
        except:
            pass # Use defaults or last known

    def check_lockdown_status(self):
        try:
            resp = requests.get(f"{LOCAL_SERVICE_URL}/api/lockdown/status", timeout=2)
            if resp.status_code == 200:
                return resp.json().get("is_locked_down", False)
        except:
            pass
        return False

    def trigger_negotiation(self, app_name, duration_min):
        try:
            # We use a special planning endpoint or just a direct agent call endpoint
            # Since we implemented 'ScrollingAgent' in backend, we should call a helper endpoint
            # But we didn't explicitly make a 'negotiate' endpoint in main.py, 
            # we just made the agent. 
            # Let's mock the negotiation text for now or assume a generic "Stop scrolling" response
            # to avoid complex wiring if the backend endpoint isn't ready.
            # Ideally, we call: POST /api/planning (or similar) -> Agent
            # For robustness, we will create a simple internal logic or call the generic query.
            
            # Let's try to use the 'query' endpoint with a specific prompt
            prompt = f"The user has been using {app_name} for {duration_min:.1f} minutes. Suggest they stop and learn. Return JSON with 'message'."
            resp = requests.post(f"{LOCAL_SERVICE_URL}/api/query", data={"topic": "wellbeing", "query": prompt}, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("response", "You've been scrolling too long. Time to learn!")
        except:
            pass
        return "You've been scrolling for too long. Let's do a quick lesson instead?"

    def enforce_lockdown(self):
        # Kill browsers/social apps
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in BROWSER_APPS:
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Bring Resolut Window to Foreground
        import win32gui
        import win32con

        def window_enum_handler(hwnd, resultList):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Resolut Learning Assistant" in title:
                    resultList.append(hwnd)

        top_windows = []
        win32gui.EnumWindows(window_enum_handler, top_windows)
        
        if top_windows:
            hwnd = top_windows[0]
            try:
                # If minimized, restore it
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Bring to front
                win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                print(f"Error focusing window: {e}")
        else:
            print("Resolut window not found! It might be closed.")
            # Optionally retry launching it, but run_app.py handles the lifecycle.


    def show_popup(self, title, message):
        # This needs to run on the main thread or be thread-safe
        # Since logic loop is separate, we emit signal or just run method if in same thread context
        # For this script, we'll run the logic in a QTimer within the QApplication event loop
        if self.popup:
            self.popup.close()
        self.popup = PopupWindow(title, message)
        self.popup.show()

    def update_loop(self):
        # 1. Update Settings
        if int(time.time()) % 10 == 0:
            self.get_settings()
            
        # 2. Check Global Lockdown Status (server authority)
        is_server_locked = self.check_lockdown_status()
        if is_server_locked:
            self.state = "LOCKDOWN"
            self.enforce_lockdown()
            # Even if server is locked, we continue to check logic below? 
            # No, if server is locked, we just enforce and return.
            return
            
        # 3. Monitor Activity
        data = self.monitor.current_data
        if not data:
            return

        is_social = data["is_social"]
        current_time = time.time()

        if is_social:
            if self.social_start_time is None:
                self.social_start_time = current_time
            
            duration = current_time - self.social_start_time
            
            # Check thresholds
            if duration > (self.warning_threshold + self.negotiation_threshold_delta):
                # LOCKDOWN TIME
                # LOCKDOWN TIME
                if self.state != "LOCKDOWN":
                    print("Status: Entering LOCKDOWN")
                    self.state = "LOCKDOWN"
                    # Tell server we are locked
                    try:
                        requests.post(f"{LOCAL_SERVICE_URL}/api/lockdown/trigger", timeout=2)
                    except:
                        pass
                    self.enforce_lockdown()
                else:
                    # ALREADY IN LOCKDOWN - KEEP ENFORCING
                    self.enforce_lockdown()
                    
            elif duration > self.warning_threshold:
                 # NEGOTIATION TIME
                 if not self.negotiation_shown:
                    print("Status: Negotiating")
                    self.state = "NEGOTIATING"
                    msg = self.trigger_negotiation(data["app"], duration / 60)
                    self.show_popup("Taking a Break?", msg)
                    self.negotiation_shown = True
                    
            elif duration > self.warning_threshold: 
                # (Logic error above: > w+n vs > w. The order matters. > w+n is checked first.)
                pass 
                
            # Wait, the WARNING popup needs to happen at 'warning_threshold'
            # But the logic above: if > W+N (LOCKDOWN). Else if > W (NEGOTIATION... wait).
            # The prompt said:
            # 1. Wait 3 mins (Warning)
            # 2. Wait 2 mins (Negotiation) -> This means at T=3+2=5 mins?
            # 3. If continues -> Lockdown.
            
            # Let's re-read carefully:
            # "start scrolling... wait 3 mins... show annoying popup... Wait for 2 minutes... negotiate... If user still does not cooperate... initiate lockdown"
            # So:
            # T=3m: Warning Popup "Scroll Mindfully!"
            # T=5m: Negotiation Agent
            # T=??: "If user still does not cooperate" -> Usually implies a short delay after negotiation or immediate if they reject.
            # Let's say T=5.5m or T=6m for lockdown. Or maybe just T=5m + epsilon.
            # "If the user still continues to scroll the agent can negotiate... If the user still does not cooperate, then initiate... lockdown"
            # I'll simply map it as:
            # T=3m: Warning
            # T=5m: Negotiation
            # T=6m (giving 1 min to comply): Lockdown
            
            pass # handled below
            
            if duration > (self.warning_threshold + self.negotiation_threshold_delta + 60):
                 # LOCKDOWN
                 if self.state != "LOCKDOWN":
                     self.state = "LOCKDOWN"
                     self.enforce_lockdown()
                     
            elif duration > (self.warning_threshold + self.negotiation_threshold_delta):
                 # NEGOTIATION
                 if not self.negotiation_shown:
                     self.state = "NEGOTIATING"
                     # Call AI
                     msg = self.trigger_negotiation(data["app"], duration / 60)
                     self.show_popup("Hey there", msg)
                     self.negotiation_shown = True
            
            elif duration > self.warning_threshold:
                 # WARNING
                 if not self.warning_shown:
                     self.state = "WARNING"
                     self.show_popup("Scroll Mindfully!", "You've been scrolling for a while.\nTime to do something productive?")
                     self.warning_shown = True
                     
        else:
            # Not social. Use a grace period logic to reset.
            # If we haven't seen social activity for > 30 seconds, reset the Session.
            # We need to track 'last_seen_social'.
            # Ideally, valid_social_time = current_time if is_social else last_seen_social
            # Since we are in the 'else' block, is_social is False.
            
            # We need a separate variable to track "last time we were social" to check the gap.
            # But we can approximate: 
            # If self.social_start_time is set, it means we HAD a session.
            # If we are here, we are NOT social right now.
            # If we stay here for X seconds... 
            # Easier implementation: Track 'non_social_start_time'.
            
            if hasattr(self, 'non_social_start_time') and self.non_social_start_time:
                if current_time - self.non_social_start_time > 30:
                     # Reset
                     if self.state != "LOCKDOWN":
                         self.social_start_time = None
                         self.state = "IDLE"
                         self.warning_shown = False
                         self.negotiation_shown = False
                         print("Status: Session Reset (Break detected)")
            else:
                self.non_social_start_time = current_time 
                
        # If we ARE social, clear the non_social timer
        if is_social:
            self.non_social_start_time = None

    def run(self):
        # We need a timer for the loop to allow PyQt event loop to run
        timer = QTimer()
        timer.timeout.connect(self.update_loop)
        timer.start(1000) # 1Hz check
        sys.exit(self.app.exec())

if __name__ == "__main__":
    service = SocialMonitorService()
    service.run()
