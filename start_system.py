import subprocess
import time
import sys
import os
import signal
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent
APP_DIR = ROOT_DIR / "app"
OVERLAY_DIR = ROOT_DIR / "overlay"

def run_system():
    print("Starting Resolut System...")

    # 1. Start Social Monitor (Independent Process)
    print("Starting Social Monitor...")
    monitor_process = subprocess.Popen(
        [sys.executable, "social_monitor.py"],
        cwd=OVERLAY_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE # Open in new window or keep hidden?
        # User might want to see logs? Or maybe keep it background.
        # "background" implies hidden usually, but for dev let's keep it visible or attached.
    )

    # 2. Start Desktop App (Blocking)
    print("Starting Desktop App (PyWebView)...")
    # run_app.py expects to be run from root or needs python path setup?
    # It imports from 'desktop.run_app', wait.
    # In package.json: "python desktop/run_app.py" executed from 'app' folder?
    # No, package.json is in 'app'. Scripts run from 'app' directory by default if run via npm.
    # But 'python desktop/run_app.py' implies we are in 'app'.
    # START_DIR for app should be APP_DIR.

    app_process = subprocess.Popen(
        [sys.executable, "desktop/run_app.py"],
        cwd=APP_DIR
    )

    try:
        # Wait for app to close
        app_process.wait()
    except KeyboardInterrupt:
        print("\nStopping system...")
    finally:
        # Cleanup
        if monitor_process:
            print("Stopping Social Monitor...")
            monitor_process.terminate()
        if app_process and app_process.poll() is None:
             app_process.terminate()

if __name__ == "__main__":
    run_system()
