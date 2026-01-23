import ctypes
import win32gui
import win32con

def set_click_through(hwnd):
    """
    Sets the window to be click-through by adding the WS_EX_TRANSPARENT style.
    """
    print(f"Setting click-through for HWND: {hwnd}")
    try:
        # WS_EX_TRANSPARENT: The window should not be hit by mouse clicks.
        # WS_EX_LAYERED: Required for transparency and certain other effects.
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        print("Click-through set successfully.")
    except Exception as e:
        print(f"Error setting click-through: {e}")

def force_always_on_top(hwnd):
    """
    Ensures the window stays on top of almost everything.
    """
    try:
        win32gui.SetWindowPos(
            hwnd, 
            win32con.HWND_TOPMOST, 
            0, 0, 0, 0, 
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
    except Exception as e:
        # Silently fail for updates to avoid console flood, but log first time if needed
        pass
