import webview
import threading
import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# Add backend to path so we can import app
sys.path.append(str(Path(__file__).parent.parent / "backend"))

def start_backend():
    """Run the FastAPI backend using uvicorn."""
    print("Starting FastAPI backend...")
    # Using subprocess to run uvicorn as a separate process
    # This ensures we can manage its lifecycle
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]
    cwd = Path(__file__).parent.parent / "backend"
    
    return subprocess.Popen(cmd, cwd=cwd)

def run_desktop():
    backend_process = start_backend()
    
    # Wait a moment for the backend to start
    time.sleep(2)
    
    # Determine the URL to load
    # In dev, we point to the Vite server. In prod, we'd point to the built files.
    # For now, we'll favor the dev server if it's likely running.
    url = "http://localhost:5173"
    
    print(f"Launching desktop window pointing to {url}")
    
    window = webview.create_window(
        'Resolut Learning Assistant',
        url,
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    try:
        webview.start(debug=True)
    finally:
        print("Stopping backend process...")
        if backend_process:
            if sys.platform == 'win32':
                backend_process.terminate()
            else:
                os.kill(backend_process.pid, signal.SIGTERM)

if __name__ == "__main__":
    run_desktop()
