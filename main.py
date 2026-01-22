import sys
from PyQt6.QtWidgets import QApplication
from hud_window import HUDWindow

def main():
    print("Starting application...")
    app = QApplication(sys.argv)
    
    print("Initializing HUDWindow...")
    try:
        hud = HUDWindow()
        print("HUDWindow initialized. Showing...")
        hud.show()
        print("HUDWindow shown. Entering event loop...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
