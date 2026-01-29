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

def start_service(name, main_path, port):
    """Run a FastAPI service using uvicorn."""
    print(f"Starting {name} on port {port}...")
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)]
    cwd = Path(__file__).parent.parent / "backend" / main_path
    return subprocess.Popen(cmd, cwd=cwd)

def run_desktop():
    local_process = start_service("Local Service", "local_service", 8000)
    ai_process = start_service("AI Service", "ai_service", 8001)
    
    # Wait a moment for the services to start
    time.sleep(3)
    
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
        print("Stopping backend processes...")
        for p in [local_process, ai_process]:
            if p:
                if sys.platform == 'win32':
                    p.terminate()
                else:
                    os.kill(p.pid, signal.SIGTERM)

if __name__ == "__main__":
    run_desktop()
