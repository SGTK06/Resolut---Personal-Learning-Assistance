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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
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
        # Window flags: Frameless, Always on Top, bypassing taskbar
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SplashScreen
        )
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set size constraints
        self.setMinimumSize(POPUP_WIDTH, POPUP_HEIGHT)
        self.setMaximumSize(POPUP_WIDTH, POPUP_HEIGHT)
        self.resize(POPUP_WIDTH, POPUP_HEIGHT)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container with styling
        self.container = QWidget()
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(15)
        
        # Progress Bar
        self.progress_container = QWidget()
        self.progress_container.setObjectName("progressBar")
        self.progress_container.setFixedWidth(POPUP_WIDTH - 100)
        self.progress_container.setFixedHeight(4)
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_indicator = QWidget()
        self.progress_indicator.setObjectName("progressIndicator")
        self.progress_indicator.setFixedHeight(4)
        progress_layout.addWidget(self.progress_indicator)
        progress_layout.addStretch()
        
        container_layout.addWidget(self.progress_container, 0, Qt.AlignmentFlag.AlignCenter)
        container_layout.addSpacing(10)
        
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
        
        # Apply stylesheet for Glassmorphism
        self.setStyleSheet("""
            #container {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(25, 25, 40, 200),
                    stop:1 rgba(40, 40, 60, 200)
                );
                border: 1px solid rgba(100, 180, 255, 0.3);
                border-radius: 24px;
            }
            #title {
                color: #ffffff;
                font-family: 'Outfit', 'Segoe UI', sans-serif;
                font-size: 24px;
                font-weight: 800;
                letter-spacing: -0.5px;
            }
            #body {
                color: rgba(255, 255, 255, 0.7);
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 15px;
                line-height: 1.5;
            }
            #acceptBtn {
                background: #00BAFF;
                color: white;
                border: none;
                border-radius: 14px;
                padding: 14px 24px;
                font-size: 15px;
                font-weight: bold;
                min-width: 140px;
            }
            #acceptBtn:hover {
                background: #33C7FF;
            }
            #declineBtn {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 14px;
                padding: 14px 24px;
                font-size: 14px;
                min-width: 140px;
            }
            #declineBtn:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            #progressBar {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 2px;
                height: 4px;
            }
            #progressIndicator {
                background: #00BAFF;
                border-radius: 2px;
            }
        """)

        # Entry Animation
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(400)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(500)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
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
        
        # Update progress bar
        progress_width = (POPUP_WIDTH - 100) * (stage / 3)
        self.progress_indicator.setFixedWidth(int(progress_width))
        
        self._center_on_screen()
        
        # Trigger Animations
        screen = QApplication.primaryScreen().geometry()
        center_y = (screen.height() - self.height()) // 2
        self.pos_anim.setStartValue(self.pos() + QPoint(0, 50))
        self.pos_anim.setEndValue(self.pos())
        
        self.show()
        self.setWindowOpacity(1.0)
        self.opacity_anim.start()
        self.pos_anim.start()
        
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


class ToastNotification(QWidget):
    """
    A small, glassmorphic toast notification for gentle nudges.
    Appears at the top-right and fades out.
    """
    
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen |
            Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.setFixedSize(300, 80)
        
        layout = QVBoxLayout(self)
        self.container = QWidget()
        self.container.setObjectName("toastContainer")
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        
        self.icon = QLabel("💡")
        self.icon.setFont(QFont("Segoe UI Emoji", 20))
        
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: white; font-family: 'Inter', sans-serif; font-size: 13px;")
        
        container_layout.addWidget(self.icon)
        container_layout.addWidget(self.label)
        layout.addWidget(self.container)
        
        self.setStyleSheet("""
            #toastContainer {
                background: rgba(40, 40, 50, 220);
                border: 1px solid rgba(100, 180, 255, 0.4);
                border-radius: 15px;
            }
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)
        
        # Animations
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(500)
        
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(500)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def show_toast(self):
        """Show the toast at top-right."""
        self.setWindowOpacity(0.0)
        screen = QApplication.primaryScreen().geometry()
        start_x = screen.width() - self.width() - 20
        start_y = -self.height()
        end_y = 40
        
        self.move(start_x, start_y)
        self.pos_anim.setStartValue(QPoint(start_x, start_y))
        self.pos_anim.setEndValue(QPoint(start_x, end_y))
        
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        self.pos_anim.start()
        self.opacity_anim.start()
        
        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.fade_out)
        
    def fade_out(self):
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self.close)
        self.opacity_anim.start()


# Test the overlay if run directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = NegotiationOverlay()
    overlay.accepted.connect(lambda: print("User accepted!"))
    overlay.declined.connect(lambda: print("User declined!"))
    overlay.lockdown_triggered.connect(lambda: print("Lockdown triggered!"))
    
    overlay.show_stage(1, scroll_minutes=5)
    
    sys.exit(app.exec())
