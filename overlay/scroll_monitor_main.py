"""
Scroll Monitor Main - Unified Entry Point

Combines all scroll monitoring components:
- ActivityMonitor: Detects social media scrolling
- NegotiationOverlay: User interaction popup
- LockdownEnforcer: Blocks social media until lesson done

Can be run standalone or integrated with the Resolut app.
"""

import sys
import os
import signal
from pathlib import Path

# Add overlay directory to path for imports
overlay_dir = Path(__file__).parent
if str(overlay_dir) not in sys.path:
    sys.path.insert(0, str(overlay_dir))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QAction

from activity_monitor import ActivityMonitor
from negotiation_overlay import NegotiationOverlay, ToastNotification
from floating_indicator import FloatingIndicator
from lockdown_enforcer import LockdownEnforcer
from config import (
    SCROLL_DETECTION_THRESHOLD_MINUTES, NEGOTIATION_WAIT_MINUTES,
    SOCIAL_MEDIA_KEYWORDS, BROWSER_PROCESSES
)

class MonitorSignals(QObject):
    """Bridge for cross-thread communication from ActivityMonitor to PyQt UI."""
    socialDetected = pyqtSignal(dict)
    thresholdExceeded = pyqtSignal(float)

class ScrollMonitor:
    """
    Main orchestrator for the scroll monitoring system.
    """
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Signal bridge for thread-safety
        self.signals = MonitorSignals()
        
        # Initialize components
        self.monitor = ActivityMonitor()
        self.overlay = NegotiationOverlay()
        self.enforcer = LockdownEnforcer()
        self.indicator = FloatingIndicator()
        
        # Show indicator by default
        self.indicator.show()
        
        # Wire up callbacks
        self._setup_callbacks()
        
        # Setup system tray
        self._setup_tray()
        
        # Status
        self.is_paused = False
        self.toast_shown = False
        self.active_toasts = [] # Prevent garbage collection
        
        # Diagnostic heartbeat
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._print_heartbeat)
        self.heartbeat_timer.start(60000) # every 60s
        
    def _print_heartbeat(self):
        print(f"[Main] Heartbeat - {self.monitor.get_continuous_social_duration_minutes():.1f} mins social")
        
    def _setup_callbacks(self):
        """Connect all component signals and callbacks."""
        
        # 1. Redirect monitor callbacks to emit signals (thread-safe bridge)
        self.monitor.on_social_media_detected = self.signals.socialDetected.emit
        self.monitor.on_threshold_exceeded = self.signals.thresholdExceeded.emit
        
        # 2. Connect signals to main-thread handlers
        self.signals.socialDetected.connect(self._handle_social_detected)
        self.signals.thresholdExceeded.connect(self._handle_threshold_exceeded)
        
        # 3. Handle lockdown lifting
        self.enforcer.on_lockdown_lifted = self.monitor.reset_duration
        
        # 4. Handle indicator click (Open App)
        self.indicator.clicked.connect(self._handle_indicator_clicked)
        
        # When user accepts (clicks Open Resolut)
        def on_accepted():
            print("[ScrollMonitor] User accepted - opening Resolut")
            self.monitor.reset_duration()
            self.toast_shown = False # Reset for next cycle
            
            # If at stage 3, activate lockdown
            if self.overlay.current_stage == 3:
                self.enforcer.activate()
            else:
                # Just open the app without lockdown
                self.enforcer._launch_resolut_app()
                
        self.overlay.accepted.connect(on_accepted)
        
        def on_declined():
            print(f"[ScrollMonitor] User declined stage {self.overlay.current_stage}")
            
        self.overlay.declined.connect(on_declined)

    def _handle_indicator_clicked(self):
        """Handle click on the floating R icon."""
        print("[ScrollMonitor] Indicator clicked - launching app")
        self.enforcer._launch_resolut_app()

    def _handle_social_detected(self, data: dict):
        """Handle signal from monitor thread about active social media (Main Thread)."""
        # Update the floating R indicator
        self.indicator.update_data(data)
        
        mins = data.get("continuous_minutes", 0)
        
        # Trigger toast at 0.5 minutes (30s)
        if mins >= 0.5 and not self.toast_shown:
            if mins < SCROLL_DETECTION_THRESHOLD_MINUTES:
                print(f"[Main] Triggering nudge at {mins:.2f} minutes")
                toast = ToastNotification(
                    f"You've been on {data.get('app', 'social media')} for 30 seconds. Ready to learn? 📚"
                )
                self.active_toasts.append(toast)
                toast.show_toast()
                self.toast_shown = True
        
        # Reset toast_shown only if duration is fully reset
        if mins == 0 and self.toast_shown:
            self.toast_shown = False

    def _handle_threshold_exceeded(self, minutes: float):
        """Handle signal from monitor thread about threshold met (Main Thread)."""
        if not self.is_paused and not self.enforcer.is_active:
            print(f"[ScrollMonitor] Threshold met: {minutes:.1f} minutes. Showing Overlay!")
            self.overlay.show_stage(1, scroll_minutes=minutes)

    def _setup_tray(self):
        """Setup the system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # Use a standard style icon
        standard_icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        self.tray_icon.setIcon(standard_icon)
        
        menu = QMenu()
        
        launch_action = QAction("Open Resolut", menu)
        launch_action.triggered.connect(self.enforcer._launch_resolut_app)
        menu.addAction(launch_action)
        
        menu.addSeparator()
        
        pause_action = QAction("Pause Monitoring", menu)
        pause_action.triggered.connect(self._toggle_pause)
        menu.addAction(pause_action)
        
        reset_action = QAction("Reset Timer", menu)
        reset_action.triggered.connect(self.monitor.reset_duration)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # Start with Windows
        self.startup_action = QAction("Start with Windows", menu, checkable=True)
        self.startup_action.setChecked(self._is_startup_enabled())
        self.startup_action.triggered.connect(self._toggle_startup)
        menu.addAction(self.startup_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
    def _is_startup_enabled(self) -> bool:
        """Check if the app is registered for Windows startup."""
        if sys.platform != 'win32':
            return False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "ResolutScrollMonitor")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def _toggle_startup(self, enabled: bool):
        """Enable or disable Windows auto-startup."""
        if sys.platform != 'win32':
            return
            
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            if enabled:
                # Use sys.executable if running as script, or just the path if bundled
                # When bundled, sys.executable is the .exe path
                app_path = f'"{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, "ResolutScrollMonitor", 0, winreg.REG_SZ, app_path)
                print(f"[Main] Startup enabled: {app_path}")
            else:
                try:
                    winreg.DeleteValue(key, "ResolutScrollMonitor")
                    print("[Main] Startup disabled")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[Main] Error toggling startup: {e}")
            # Revert UI state if failed
            self.startup_action.setChecked(not enabled)
        
    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        print(f"[Main] Monitoring {'paused' if self.is_paused else 'resumed'}")

    def run(self):
        """Start the scroll monitor application."""
        print("=" * 50)
        print("Resolut Scroll Monitor - UNIFIED STABLE VERSION")
        print("=" * 50)
        print(f"Detection Threshold: {SCROLL_DETECTION_THRESHOLD_MINUTES} minutes")
        print(f"Keywords: {', '.join(SOCIAL_MEDIA_KEYWORDS[:5])}...")
        print(f"Browsers: {', '.join(BROWSER_PROCESSES)}")
        print("=" * 50)
        print("Monitoring active... Check system tray.")
        print("")
        
        try:
            # Start monitoring
            self.monitor.start()
            
            # Run Qt event loop
            return self.app.exec()
        except Exception as e:
            print(f"[Main] Critical App Error: {e}")
            return 1


def main():
    """Entry point for scroll monitor."""
    # Allow Ctrl+C to stop the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = ScrollMonitor()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
