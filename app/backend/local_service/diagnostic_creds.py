import os
import json
from pathlib import Path
from dotenv import load_dotenv

def run_diagnostic():
    print("--- Google Calendar Configuration Diagnostic ---")
    
    # 1. Check Paths
    current_file = Path(__file__).resolve()
    local_service_dir = current_file.parent
    backend_dir = local_service_dir.parent
    project_root = backend_dir.parent
    
    print(f"Current file: {current_file}")
    print(f"Local Service Dir: {local_service_dir}")
    print(f"Backend Dir: {backend_dir}")
    
    # 2. Check .env file
    env_path = backend_dir / ".env"
    print(f"\nChecking .env at: {env_path}")
    print(f"Exists: {env_path.exists()}")
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
        print(f"GOOGLE_CALENDAR_CLIENT_ID: {'SET' if client_id else 'NOT SET'}")
        print(f"GOOGLE_CALENDAR_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'}")
    
    # 3. Check credentials.json
    calendar_data_dir = local_service_dir / "data" / "calendar"
    credentials_path = calendar_data_dir / "credentials.json"
    print(f"\nChecking credentials.json at: {credentials_path}")
    print(f"Exists: {credentials_path.exists()}")
    
    if credentials_path.exists():
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                has_installed = "installed" in creds
                print(f"Valid format ('installed' key): {has_installed}")
        except Exception as e:
            print(f"Error reading credentials.json: {e}")

if __name__ == "__main__":
    run_diagnostic()
