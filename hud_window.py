import sys
import psutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QPalette, QFont
from win_utils import set_click_through, force_always_on_top

class HUDWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_pos = QPoint()
        self.init_ui()
        
    def init_ui(self):
        # Window flags: Frameless, Always on Top, Tool window (no taskbar icon)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Attribute to enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set geometry (top right corner roughly)
        screen = QApplication.primaryScreen().geometry()
        width, height = 300, 150
        self.setGeometry(screen.width() - width - 20, 40, width, height)
        
        # Layout and Widgets
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Styling
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container_layout = QVBoxLayout(self.container)
        
        self.title_label = QLabel("Windows Overlay")
        self.title_label.setObjectName("title")
        
        
        self.container_layout.addWidget(self.title_label)
        layout.addWidget(self.container)
        
        self.setStyleSheet("""
            #container {
                background-color: rgba(20, 20, 30, 200);
                border: 2px solid #00d2ff;
                border-radius: 50px;
            }
            #title {
                color: #00d2ff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        
        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
    def update_stats(self):
        pass
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        # Click-through is disabled to allow dragging
        # set_click_through(int(self.winId()))
