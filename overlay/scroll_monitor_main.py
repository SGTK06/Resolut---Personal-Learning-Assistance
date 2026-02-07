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
from pathlib import Path

# Add overlay directory to path for imports
overlay_dir = Path(__file__).parent
if str(overlay_dir) not in sys.path:
    sys.path.insert(0, str(overlay_dir))

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QAction

from activity_monitor import ActivityMonitor
from negotiation_overlay import NegotiationOverlay
from lockdown_enforcer import LockdownEnforcer
from config import SCROLL_DETECTION_THRESHOLD_MINUTES, NEGOTIATION_WAIT_MINUTES


class ScrollMonitorApp:
    """
    Main application that orchestrates all scroll monitoring components.
    
    Flow:
    1. ActivityMonitor detects X minutes of social media scrolling
    2. NegotiationOverlay shows stage 1 popup
    3. If user declines, wait Y minutes then show stage 2
    4. If user declines again, show stage 3 and activate lockdown
    5. LockdownEnforcer blocks social media until lesson completed
    6. Reset and repeat
    """
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Initialize components
        self.monitor = ActivityMonitor()
        self.overlay = NegotiationOverlay()
        self.enforcer = LockdownEnforcer()
        
        # Wire up callbacks
        self._setup_callbacks()
        
        # Setup system tray
        self._setup_tray()
        
        # Status
        self.is_paused = False
        
    def _setup_callbacks(self):
        """Connect all component signals and callbacks."""
        
        # When scrolling threshold exceeded, show stage 1
        def on_threshold_exceeded(minutes: float):
            if not self.is_paused and not self.enforcer.is_active:
                print(f"[ScrollMonitor] Threshold exceeded: {minutes:.1f} minutes")
                self.overlay.show_stage(1, scroll_minutes=minutes)
                
        self.monitor.on_threshold_exceeded = on_threshold_exceeded
        
        # When user accepts (clicks Open Resolut)
        def on_accepted():
            print("[ScrollMonitor] User accepted - opening Resolut")
            self.monitor.reset_duration()
            
            # If at stage 3, activate lockdown
            if self.overlay.current_stage == 3:
                topics = self._get_available_topics()
                topic = topics[0] if topics else None
                self.enforcer.activate(topic)
            else:
                # Just open the app without lockdown
                self.enforcer._launch_resolut_app()
                
        self.overlay.accepted.connect(on_accepted)
        
        # When user declines
        def on_declined():
            print(f"[ScrollMonitor] User declined at stage {self.overlay.current_stage}")
            # Timer for next stage is handled in NegotiationOverlay
            
        self.overlay.declined.connect(on_declined)
        
        # When lockdown is triggered (stage 3)
        def on_lockdown():
            print("[ScrollMonitor] Lockdown triggered")
            topics = self._get_available_topics()
            topic = topics[0] if topics else None
            self.enforcer.activate(topic)
            
        self.overlay.lockdown_triggered.connect(on_lockdown)
        
        # When lockdown is lifted
        def on_lockdown_lifted():
            print("[ScrollMonitor] Lockdown lifted - lesson completed!")
            self.monitor.reset_duration()
            self.overlay.reset()
            
        self.enforcer.on_lockdown_lifted = on_lockdown_lifted
        
    def _setup_tray(self):
        """Setup system tray icon with menu."""
        # Create a simple icon (blue circle)
        from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setBrush(QBrush(QColor(100, 180, 255)))
        painter.setPen(QColor(100, 180, 255))
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        
        icon = QIcon(pixmap)
        
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip("Resolut Scroll Monitor")
        
        # Create menu
        menu = QMenu()
        
        pause_action = QAction("Pause Monitoring", menu)
        pause_action.setCheckable(True)
        pause_action.triggered.connect(self._toggle_pause)
        menu.addAction(pause_action)
        self.pause_action = pause_action
        
        menu.addSeparator()
        
        status_action = QAction("Status: Active", menu)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        self.status_action = status_action
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
        
        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)
        
    def _toggle_pause(self, checked: bool):
        """Toggle monitoring pause state."""
        self.is_paused = checked
        if checked:
            print("[ScrollMonitor] Monitoring paused")
            self.status_action.setText("Status: Paused")
        else:
            print("[ScrollMonitor] Monitoring resumed")
            self.monitor.reset_duration()
            self.status_action.setText("Status: Active")
            
    def _update_status(self):
        """Update tray status text."""
        if self.is_paused:
            return
            
        data = self.monitor.current_data
        if not data:
            return
            
        if self.enforcer.is_active:
            self.status_action.setText("Status: 🔒 Lockdown Active")
        elif data.get("is_social"):
            mins = data.get("continuous_minutes", 0)
            self.status_action.setText(f"Status: ⚠️ Social Media ({mins:.1f}m)")
        else:
            self.status_action.setText("Status: ✅ Focused")
            
    def _get_available_topics(self) -> list:
        """Get list of available topics from backend."""
        try:
            import requests
            from config import BACKEND_URL
            response = requests.get(f"{BACKEND_URL}/api/topics", timeout=5)
            if response.status_code == 200:
                return response.json().get("topics", [])
        except Exception:
            pass
        return []
        
    def _quit(self):
        """Quit the application."""
        print("[ScrollMonitor] Quitting...")
        self.monitor.stop()
        self.enforcer.deactivate()
        self.tray.hide()
        self.app.quit()
        
    def run(self):
        """Start the scroll monitor application."""
        print("=" * 50)
        print("Resolut Scroll Monitor")
        print("=" * 50)
        print(f"Detection threshold: {SCROLL_DETECTION_THRESHOLD_MINUTES} minutes")
        print(f"Negotiation wait: {NEGOTIATION_WAIT_MINUTES} minutes")
        print("=" * 50)
        print("Starting monitoring... (check system tray)")
        print("")
        
        # Start monitoring
        self.monitor.start()
        
        # Run Qt event loop
        return self.app.exec()


def main():
    """Entry point for scroll monitor."""
    app = ScrollMonitorApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
