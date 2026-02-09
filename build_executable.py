import os
import subprocess
import shutil
import sys
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.absolute()
APP_DIR = ROOT_DIR / "app"
FRONTEND_DIR = APP_DIR / "frontend"
OVERLAY_DIR = ROOT_DIR / "overlay"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

def run_command(cmd, cwd=None, shell=True):
    print(f"Executing: {cmd} in {cwd or os.getcwd()}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(1)

def build_frontend():
    print("\n--- Building Frontend ---")
    if not (FRONTEND_DIR / "node_modules").exists():
        run_command("npm install", cwd=FRONTEND_DIR)
    run_command("npm run build", cwd=FRONTEND_DIR)

def bundle_executable():
    print("\n--- Bundling with PyInstaller ---")
    
    # Check if pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        run_command(f"{sys.executable} -m pip install pyinstaller")

    # Main entry point is the scroll monitor (which launches the rest)
    entry_point = OVERLAY_DIR / "scroll_monitor_main.py"
    
    # Build the command
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--name=Resolut",
        f"--paths={ROOT_DIR}",
        f"--add-data=\"{APP_DIR};app\"",
        f"--add-data=\"{OVERLAY_DIR};overlay\"",
        "--clean",
        "--noconfirm",
        str(entry_point)
    ]
    
    run_command(" ".join(cmd), cwd=ROOT_DIR)

def main():
    # 1. Clean previous builds
    if DIST_DIR.exists(): shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
    
    # 2. Build Frontend
    try:
        build_frontend()
    except Exception as e:
        print(f"Warning: Frontend build failed: {e}")
        print("Continuing with bundling (will use existing build if available)...")

    # 3. Bundle
    bundle_executable()
    
    print("\n--- Build Complete! ---")
    print(f"Executable found in: {DIST_DIR / 'Resolut'}")

if __name__ == "__main__":
    main()
