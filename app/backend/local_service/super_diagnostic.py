import os
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv

def run_super_diagnostic():
    print("=== RESOLUT CALENDAR SUPER DIAGNOSTIC ===")
    
    # 1. Environment Info
    print(f"CWD: {os.getcwd()}")
    print(f"File: {__file__}")
    
    # 2. Path Discoveries
    local_service_path = Path(__file__).resolve().parent
    backend_path = local_service_path.parent
    project_root = backend_path.parent
    
    print(f"Detected Backend Dir: {backend_path}")
    
    # 3. .env Check
    env_candidate = backend_path / ".env"
    print(f"\nChecking .env at: {env_candidate}")
    if env_candidate.exists():
        print("FOUND .env")
        load_dotenv(dotenv_path=env_candidate)
        cid = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
        sec = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
        print(f"Env Client ID: {'Set' if cid else 'MISSING'}")
        print(f"Env Client Secret: {'Set' if sec else 'MISSING'}")
    else:
        print("NOT FOUND .env")

    # 4. credentials.json Check
    creds_path = local_service_path / "data" / "calendar" / "credentials.json"
    print(f"\nChecking credentials.json at: {creds_path}")
    if creds_path.exists():
        print("FOUND credentials.json")
        try:
            with open(creds_path, 'r') as f:
                data = json.load(f)
                if 'installed' in data or 'web' in data:
                    print("Format: VALID")
                else:
                    print(f"Format: INVALID (Keys found: {list(data.keys())})")
        except Exception as e:
            print(f"Read error: {e}")
    else:
        print("NOT FOUND credentials.json")

    # 5. token.json Check
    token_path = local_service_path / "data" / "calendar" / "token.json"
    print(f"\nChecking token.json at: {token_path}")
    if token_path.exists():
        print(f"FOUND token.json ({token_path.stat().st_size} bytes)")
        try:
            with open(token_path, 'r') as f:
                data = json.load(f)
                print(f"Token keys: {list(data.keys())}")
                expiry = data.get('expiry')
                if expiry:
                    print(f"Expiry: {expiry}")
        except Exception as e:
            print(f"Read error: {e}")
    else:
        print("NOT FOUND token.json")

    # 6. Final Status check logic (Matches main.py)
    has_env = bool(os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"))
    has_file = creds_path.exists()
    print(f"\n--- Result ---")
    print(f"Final has_credentials: {has_env or has_file}")

if __name__ == "__main__":
    run_super_diagnostic()
