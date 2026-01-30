import webview
import threading
import os
import sys
import time
import subprocess
import signal
import requests
from pathlib import Path

# Base project directory
ROOT_DIR = Path(__file__).parent.parent

def kill_port_process(port):
    """Kill process listening on the given port (Windows only for now)."""
    try:
        if sys.platform == 'win32':
            # findstr returns exit code 1 if not found, check_output raises CalledProcessError
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.splitlines():
                if "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    print(f"Cleaning up port {port} (killing PID {pid})...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass # Port not in use
    except Exception as e:
        print(f"Error killing port {port}: {e}")

def start_backend_service(name, folder, port):
    """Run a FastAPI service using uvicorn."""
    kill_port_process(port)
    print(f"Starting {name} on port {port}...")
    log_file = open(ROOT_DIR / "desktop" / f"{name.lower().replace(' ', '_')}.log", "w")
    
    # Use 'python -m uvicorn' to ensure it uses the current env
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)]
    cwd = ROOT_DIR / "backend" / folder
    
    return subprocess.Popen(cmd, cwd=cwd, stdout=log_file, stderr=log_file)

def start_frontend_service():
    """Start Vite dev server."""
    # Common Vite ports
    for port in [5173, 5174, 5175]:
        kill_port_process(port)
        
    print("Starting Vite frontend...")
    cwd = ROOT_DIR / "frontend"
    
    # Use shell=True for npm on Windows
    cmd = "npm run dev"
    return subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_frontend_url(timeout=30):
    """Wait for Vite to start and return the URL it's using."""
    print("Waiting for frontend to be ready...")
    start_time = time.time()
    # Vite usually uses 5173 or 5174
    ports = [5173, 5174, 5175]
    
    while time.time() - start_time < timeout:
        for port in ports:
            url = f"http://localhost:{port}"
            try:
                # Use a small timeout for the request itself
                response = requests.get(url, timeout=0.5)
                if response.status_code == 200:
                    print(f"Frontend detected at {url}")
                    return url
            except requests.exceptions.ConnectionError:
                continue
        time.sleep(1)
    
    # Fallback to default
    print("Timed out waiting for frontend. Falling back to http://localhost:5173")
    return "http://localhost:5173"

def wait_for_backend(ports, timeout=30):
    """Wait for all backend services to be healthy."""
    print(f"Waiting for backend services on ports {ports}...")
    start_time = time.time()
    pending_ports = list(ports)
    
    while time.time() - start_time < timeout and pending_ports:
        for port in list(pending_ports):
            # Try health endpoint for AI service, root for local service
            endpoint = "/api/ai/health" if port == 8001 else "/api/topics"
            url = f"http://127.0.0.1:{port}{endpoint}"
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    print(f"Service on port {port} is healthy!")
                    pending_ports.remove(port)
            except requests.exceptions.ConnectionError:
                continue
        if pending_ports:
            time.sleep(1)
            
    if pending_ports:
        print(f"Warning: Timed out waiting for ports {pending_ports}. Services might still be starting.")
    else:
        print("All backend services are ready.")

def run_desktop():
    # 1. Start all processes
    local_process = start_backend_service("Local Service", "local_service", 8000)
    ai_process = start_backend_service("AI Service", "ai_service", 8001)
    frontend_process = start_frontend_service()
    
    # 2. Wait for services to be ready
    wait_for_backend([8000, 8001])
    url = get_frontend_url()
    
    # 3. Create desktop window
    print(f"Launching desktop window: {url}")
    window = webview.create_window(
        'Resolut Learning Assistant',
        url,
        width=1280,
        height=900,
        resizable=True,
        min_size=(1000, 700)
    )
    
    try:
        webview.start(debug=False)
    finally:
        print("\nShutting down all services...")
        # Gracefully stop processes
        # On Windows, we need to kill the process tree for npm/vite
        processes = [
            ("Local", local_process), 
            ("AI", ai_process), 
            ("Frontend", frontend_process)
        ]
        
        for name, p in processes:
            if p:
                print(f"Stopping {name}...")
                if sys.platform == 'win32':
                    # Use taskkill /T to kill the process tree (important for Vite)
                    subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, capture_output=True)
                else:
                    p.terminate()
        
        print("Done.")

if __name__ == "__main__":
    try:
        run_desktop()
    except KeyboardInterrupt:
        pass
