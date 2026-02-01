import sys
import signal
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush

class GeminiHalo(QWidget):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        thickness = 12
        rect = QRectF(thickness/2, thickness/2,
                      self.width() - thickness, self.height() - thickness)

        # Gemini Gradient
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(66, 133, 244))
        gradient.setColorAt(0.3, QColor(34, 211, 238))
        gradient.setColorAt(0.6, QColor(147, 197, 253))
        gradient.setColorAt(1.0, QColor(29, 78, 216))

        pen = QPen(QBrush(gradient), thickness)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        painter.setPen(pen)
        painter.drawRect(rect)

if __name__ == "__main__":
    # 1. Allow Ctrl+C to close the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    # 2. Use a timer to let the Python interpreter process signals
    # Without this, the app stays alive even if you hit Ctrl+C in some terminals
    timer = QTimer()
    timer.start(500)  # Check every 500ms
    timer.timeout.connect(lambda: None)

    window = GeminiHalo()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nHalting Halo... Goodbye!")
        sys.exit(0)