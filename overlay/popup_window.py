import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class PopupWindow(QWidget):
    dismissed = pyqtSignal()

    def __init__(self, title="Notification", message=""):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        width, height = 400, 200
        self.setGeometry(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2,
            width, height
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.container = QWidget()
        self.container.setObjectName("container")
        container_layout = QVBoxLayout(self.container)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.msg_label = QLabel(message)
        self.msg_label.setObjectName("message")
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.close_btn = QPushButton("Okay")
        self.close_btn.clicked.connect(self.close_and_emit)

        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.msg_label)
        container_layout.addWidget(self.close_btn)
        
        layout.addWidget(self.container)

        self.setStyleSheet("""
            #container {
                background-color: rgba(30, 30, 40, 240);
                border: 2px solid #ff5555;
                border-radius: 15px;
            }
            #title {
                color: #ff5555;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            #message {
                color: white;
                font-size: 14px;
                margin-bottom: 15px;
            }
            QPushButton {
                background-color: #ff5555;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff7777;
            }
        """)

    def update_message(self, title, message):
        self.title_label.setText(title)
        self.msg_label.setText(message)

    def close_and_emit(self):
        self.dismissed.emit()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PopupWindow("Scroll Mindfully!", "You've been scrolling for a while.\nTime to do something productive?")
    win.show()
    sys.exit(app.exec())
