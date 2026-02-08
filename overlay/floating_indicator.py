"""
Floating R Icon Overlay

A small, always-on-top floating circle with "R" logo that:
- Shows green when focused (not on social media)
- Turns red when social media is detected
- Displays the time spent on social media
"""

import sys
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont


class FloatingIndicator(QWidget):
    """
    A small floating circle with 'R' that indicates monitoring status.
    
    - Green: User is focused (not on social media)
    - Red: Social media detected, shows time
    """
    
    SIZE = 60  # Diameter of the circle
    
    def __init__(self):
        super().__init__()
        
        self.is_on_social = False
        self.social_minutes = 0.0
        self.drag_pos = QPoint()
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        # Window flags: Frameless, Always on Top, Tool window, Stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set size
        self.setFixedSize(self.SIZE, self.SIZE)
        
        # Position in top-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.SIZE - 20, 100)
        
        # Timer label for showing time
        self.time_label = QLabel("", self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("""
            color: white;
            font-size: 9px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)
        self.time_label.setGeometry(0, 42, self.SIZE, 15)
        
    def update_data(self, data):
        """Update the indicator state from external data."""
        if data:
            self.is_on_social = data.get("is_social", False)
            self.social_minutes = data.get("continuous_minutes", 0.0)
            
            if self.is_on_social:
                mins = int(self.social_minutes)
                secs = int((self.social_minutes - mins) * 60)
                self.time_label.setText(f"{mins}:{secs:02d}")
            else:
                self.time_label.setText("")
                
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        """Custom paint for the circular indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Choose color based on state
        if self.is_on_social:
            # Red gradient for social media
            color = QColor(220, 50, 50)
            border_color = QColor(180, 30, 30)
        else:
            # Green gradient for focused
            color = QColor(50, 180, 80)
            border_color = QColor(30, 140, 60)
        
        # Draw shadow
        shadow_color = QColor(0, 0, 0, 50)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, self.SIZE - 8, self.SIZE - 8)
        
        # Draw main circle
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(border_color, 2))
        painter.drawEllipse(2, 2, self.SIZE - 8, self.SIZE - 8)
        
        # Draw "R" letter
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(2, 2, self.SIZE - 8, self.SIZE - 12, 
                        Qt.AlignmentFlag.AlignCenter, "R")
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
            
    def closeEvent(self, event):
        """Clean up on close."""
        event.accept()
