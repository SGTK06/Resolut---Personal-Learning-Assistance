"""
Negotiation Overlay - Center Screen Popup

Displays a popup notification to negotiate with the user about their
social media usage. Features three stages of negotiation before lockdown.
"""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

try:
    from .config import (
        MESSAGES, POPUP_WIDTH, POPUP_HEIGHT,
        NEGOTIATION_WAIT_MINUTES
    )
except ImportError:
    from config import (
        MESSAGES, POPUP_WIDTH, POPUP_HEIGHT,
        NEGOTIATION_WAIT_MINUTES
    )


class NegotiationOverlay(QWidget):
    """
    A center-screen popup that negotiates with the user about social media usage.
    
    Stages:
    1. Reminder - Gentle nudge to complete a lesson
    2. Warning - Time's almost up
    3. Lockdown - Enforces the lesson requirement
    
    Signals:
        accepted: User clicked accept button
        declined: User clicked decline button
        lockdown_triggered: Stage 3 reached, lockdown should activate
    """
    
    accepted = pyqtSignal()
    declined = pyqtSignal()
    lockdown_triggered = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_stage = 0
        self.negotiation_timer = None
        self.scroll_minutes = 0
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        # Window flags: Frameless, Always on Top, Tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set size
        self.setFixedSize(POPUP_WIDTH, POPUP_HEIGHT)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container with styling
        self.container = QWidget()
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(15)
        
        # Icon/Emoji label
        self.icon_label = QLabel("📱")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 36))
        
        # Title
        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        
        # Body text
        self.body_label = QLabel()
        self.body_label.setObjectName("body")
        self.body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body_label.setWordWrap(True)
        
        # Buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.decline_button = QPushButton()
        self.decline_button.setObjectName("declineBtn")
        self.decline_button.clicked.connect(self._on_decline)
        self.decline_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.accept_button = QPushButton()
        self.accept_button.setObjectName("acceptBtn")
        self.accept_button.clicked.connect(self._on_accept)
        self.accept_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        buttons_layout.addWidget(self.decline_button)
        buttons_layout.addWidget(self.accept_button)
        
        # Add to container
        container_layout.addWidget(self.icon_label)
        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.body_label)
        container_layout.addStretch()
        container_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(self.container)
        
        # Apply shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        # Apply stylesheet
        self.setStyleSheet("""
            #container {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 30, 45, 245),
                    stop:1 rgba(45, 45, 70, 245)
                );
                border: 2px solid rgba(100, 180, 255, 0.5);
                border-radius: 20px;
            }
            #title {
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 20px;
                font-weight: bold;
            }
            #body {
                color: rgba(255, 255, 255, 0.85);
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                line-height: 1.4;
            }
            #acceptBtn {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50,
                    stop:1 #45a049
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            #acceptBtn:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5CBF60,
                    stop:1 #55b059
                );
            }
            #declineBtn {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                min-width: 120px;
            }
            #declineBtn:hover {
                background: rgba(255, 255, 255, 0.2);
                color: white;
            }
        """)
        
    def show_stage(self, stage: int, scroll_minutes: float = 0):
        """
        Show a specific negotiation stage.
        
        Args:
            stage: 1, 2, or 3
            scroll_minutes: How long user has been scrolling
        """
        self.current_stage = stage
        self.scroll_minutes = scroll_minutes
        
        if stage == 1:
            self.icon_label.setText("👋")
            self.title_label.setText(MESSAGES["stage1_title"])
            self.body_label.setText(
                MESSAGES["stage1_body"].format(minutes=int(scroll_minutes))
            )
            self.accept_button.setText(MESSAGES["stage1_accept"])
            self.decline_button.setText(MESSAGES["stage1_decline"])
            self.decline_button.setVisible(True)
            
        elif stage == 2:
            self.icon_label.setText("⏰")
            self.title_label.setText(MESSAGES["stage2_title"])
            self.body_label.setText(MESSAGES["stage2_body"])
            self.accept_button.setText(MESSAGES["stage2_accept"])
            self.decline_button.setText(MESSAGES["stage2_decline"])
            self.decline_button.setVisible(True)
            
        elif stage == 3:
            self.icon_label.setText("📚")
            self.title_label.setText(MESSAGES["stage3_title"])
            self.body_label.setText(MESSAGES["stage3_body"])
            self.accept_button.setText(MESSAGES["stage3_button"])
            self.decline_button.setVisible(False)
        
        self._center_on_screen()
        self.show()
        self.raise_()
        self.activateWindow()
        
    def _center_on_screen(self):
        """Center the popup on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def _on_accept(self):
        """Handle accept button click."""
        self.hide()
        self.accepted.emit()
        
        if self.current_stage == 3:
            self.lockdown_triggered.emit()
            
    def _on_decline(self):
        """Handle decline button click."""
        self.hide()
        self.declined.emit()
        
        # Start timer for next stage
        if self.current_stage < 3:
            wait_ms = int(NEGOTIATION_WAIT_MINUTES * 60 * 1000)
            self.negotiation_timer = QTimer()
            self.negotiation_timer.setSingleShot(True)
            self.negotiation_timer.timeout.connect(
                lambda: self.show_stage(self.current_stage + 1, self.scroll_minutes)
            )
            self.negotiation_timer.start(wait_ms)
            
    def trigger_lockdown(self):
        """Force trigger lockdown (called from stage 3)."""
        self.show_stage(3, self.scroll_minutes)
        self.lockdown_triggered.emit()
        
    def reset(self):
        """Reset the negotiation state."""
        self.current_stage = 0
        if self.negotiation_timer:
            self.negotiation_timer.stop()
            self.negotiation_timer = None
        self.hide()


# Test the overlay if run directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = NegotiationOverlay()
    overlay.accepted.connect(lambda: print("User accepted!"))
    overlay.declined.connect(lambda: print("User declined!"))
    overlay.lockdown_triggered.connect(lambda: print("Lockdown triggered!"))
    
    overlay.show_stage(1, scroll_minutes=5)
    
    sys.exit(app.exec())
