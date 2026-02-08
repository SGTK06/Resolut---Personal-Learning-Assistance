"""
Lockdown Enforcer

Enforces social media lockdown by:
1. Closing social media applications
2. Closing browser windows with social media sites
3. Launching the Resolut app
4. Monitoring for lesson completion to lift lockdown
"""

import os
import sys
import time
import threading
import subprocess
import requests
import psutil
import win32gui
import win32con
import win32process
from typing import Optional, Callable, List
from pathlib import Path

try:
    from .config import (
        SOCIAL_MEDIA_APPS, SOCIAL_MEDIA_KEYWORDS, BROWSER_PROCESSES,
        BACKEND_URL, LESSON_COMPLETION_POLL_INTERVAL
    )
except ImportError:
    from config import (
        SOCIAL_MEDIA_APPS, SOCIAL_MEDIA_KEYWORDS, BROWSER_PROCESSES,
        BACKEND_URL, LESSON_COMPLETION_POLL_INTERVAL
    )


class LockdownEnforcer:
    """
    Enforces social media lockdown until a lesson is completed.
    
    Features:
    - Closes social media applications
    - Closes browser windows/tabs with social media
    - Launches Resolut app
    - Polls backend for lesson completion
    - Lifts lockdown when lesson is done
    """
    
    def __init__(self):
        self.is_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.enforcement_thread: Optional[threading.Thread] = None
        self.on_lockdown_lifted: Optional[Callable[[], None]] = None
        self.initial_completed_lessons: int = 0
        self.current_topic: Optional[str] = None
        self._stop_event = threading.Event()
        
    def activate(self, topic: str = None):
        """
        Activate the lockdown.
        
        Args:
            topic: The topic being studied (for lesson completion check)
        """
        if self.is_active:
            return
            
        print("[Lockdown] Activating lockdown (non-blocking)...")
        self.is_active = True
        self.current_topic = topic
        self._stop_event.clear()
        
        # Start a background thread for the initial blocking tasks
        # to prevent freezing the UI thread that calls this.
        def _startup_routine():
            # 1. Get initial completion count (Network I/O)
            self.initial_completed_lessons = self._get_completed_lesson_count()
            
            # 2. Close social media immediately (Process I/O)
            self._close_social_media()
            
            # 3. Launch Resolut app (Process I/O)
            self._launch_resolut_app()
            
            # 4. Start enforcement loop (keeps closing social media)
            self.enforcement_thread = threading.Thread(
                target=self._enforcement_loop, daemon=True
            )
            self.enforcement_thread.start()
            
            # 5. Start monitoring for lesson completion
            self.monitor_thread = threading.Thread(
                target=self._monitor_lesson_completion, daemon=True
            )
            self.monitor_thread.start()

        startup_thread = threading.Thread(target=_startup_routine, daemon=True)
        startup_thread.start()
        
    def deactivate(self):
        """Lift the lockdown."""
        if not self.is_active:
            return
            
        print("[Lockdown] Deactivating lockdown...")
        self.is_active = False
        self._stop_event.set()
        
        if self.on_lockdown_lifted:
            self.on_lockdown_lifted()
            
    def _close_social_media(self):
        """Close all social media applications and browser tabs."""
        closed_apps = []
        
        # Find and terminate social media processes
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                
                # Check if it's a social media app
                for app in SOCIAL_MEDIA_APPS:
                    if app.lower() in proc_name:
                        print(f"[Lockdown] Closing social media app: {proc_name}")
                        proc.terminate()
                        closed_apps.append(proc_name)
                        break
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Find browser windows with social media
        self._close_social_media_browser_windows()
        
        return closed_apps
        
    def _close_social_media_browser_windows(self):
        """Close browser windows that have social media in the title."""
        windows_to_close = []
        
        def enum_windows_callback(hwnd, _):
            """Callback for EnumWindows."""
            if not win32gui.IsWindowVisible(hwnd):
                return True
                
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = psutil.Process(pid).name().lower()
                
                # Only check browsers
                if proc_name not in [p.lower() for p in BROWSER_PROCESSES]:
                    return True
                    
                title = win32gui.GetWindowText(hwnd).lower()
                
                # Check for social media keywords in title
                for keyword in SOCIAL_MEDIA_KEYWORDS:
                    if keyword.lower() in title:
                        windows_to_close.append((hwnd, title, pid))
                        break
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                pass
                
            return True
        
        win32gui.EnumWindows(enum_windows_callback, None)
        
        # Close the windows (terminate browser if it only has social media)
        for hwnd, title, pid in windows_to_close:
            try:
                print(f"[Lockdown] Closing browser window: {title[:50]}...")
                # Send close message to window
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception as e:
                print(f"[Lockdown] Failed to close window: {e}")
                
    def _launch_resolut_app(self):
        """Launch or focus the Resolut app."""
        try:
            # First, try to find and focus the window if it exists
            hwnd = win32gui.FindWindow(None, 'Resolut Learning Assistant')
            if hwnd:
                print("[Lockdown] Found existing Resolut window, focusing...")
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return

            # If not found, launch it
            current_dir = Path(__file__).parent
            app_dir = current_dir.parent / "app"
            run_app_path = app_dir / "desktop" / "run_app.py"
            
            if run_app_path.exists():
                print(f"[Lockdown] Launching Resolut app from: {run_app_path}")
                subprocess.Popen(
                    [sys.executable, str(run_app_path)],
                    cwd=str(app_dir),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                print(f"[Lockdown] Could not find run_app.py at {run_app_path}")
                # Try alternative: open the frontend URL directly
                subprocess.Popen(
                    ["cmd", "/c", "start", "http://localhost:5173"],
                    shell=True
                )
        except Exception as e:
            print(f"[Lockdown] Error launching app: {e}")
            
    def _enforcement_loop(self):
        """Continuously enforce lockdown by closing social media."""
        while self.is_active and not self._stop_event.is_set():
            self._close_social_media()
            # Check every 2 seconds
            self._stop_event.wait(2)
            
    def _monitor_lesson_completion(self):
        """Monitor backend for lesson completion."""
        while self.is_active and not self._stop_event.is_set():
            try:
                current_count = self._get_completed_lesson_count()
                
                if current_count > self.initial_completed_lessons:
                    print("[Lockdown] Lesson completed! Lifting lockdown.")
                    self.deactivate()
                    return
                    
            except Exception as e:
                print(f"[Lockdown] Error checking lesson completion: {e}")
                
            self._stop_event.wait(LESSON_COMPLETION_POLL_INTERVAL)
            
    def _get_completed_lesson_count(self) -> int:
        """Get the count of completed lessons from the backend."""
        try:
            # Get all topics first
            response = requests.get(f"{BACKEND_URL}/api/topics", timeout=5)
            if response.status_code != 200:
                return 0
                
            topics = response.json().get("topics", [])
            
            total_completed = 0
            for topic in topics:
                try:
                    prog_response = requests.get(
                        f"{BACKEND_URL}/api/lessons/progress/{topic}",
                        timeout=5
                    )
                    if prog_response.status_code == 200:
                        progress = prog_response.json()
                        completed = progress.get("completed_lessons", [])
                        total_completed += len(completed)
                except Exception:
                    continue
                    
            return total_completed
            
        except Exception as e:
            print(f"[Lockdown] Error fetching lesson count: {e}")
            return 0
            
    def get_blocked_apps(self) -> List[str]:
        """Get a list of currently blocked app names."""
        blocked = []
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                for app in SOCIAL_MEDIA_APPS:
                    if app.lower() in proc_name:
                        if proc_name not in blocked:
                            blocked.append(proc_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return blocked


# Test the enforcer if run directly
if __name__ == "__main__":
    print("Testing Lockdown Enforcer...")
    enforcer = LockdownEnforcer()
    
    def on_lifted():
        print("Lockdown has been lifted!")
        
    enforcer.on_lockdown_lifted = on_lifted
    
    # Just test closing (don't actually activate full lockdown in test)
    print(f"Would close: {enforcer._close_social_media()}")
    print(f"Currently blocked apps: {enforcer.get_blocked_apps()}")
