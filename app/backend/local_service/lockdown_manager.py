import json
import os
from pathlib import Path
from typing import Dict, Any

# Define where to store the settings
LOCKDOWN_DATA_DIR = Path("data")
LOCKDOWN_SETTINGS_FILE = LOCKDOWN_DATA_DIR / "lockdown_settings.json"

class LockdownManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LockdownManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.is_locked_down = False
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        if LOCKDOWN_SETTINGS_FILE.exists():
            try:
                with open(LOCKDOWN_SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading lockdown settings: {e}")
        
        # Default settings
        return {
            "warning_interval_seconds": 180,  # 3 minutes
            "negotiation_interval_seconds": 120, # 2 minutes
        }

    def save_settings(self, new_settings: Dict[str, Any]):
        LOCKDOWN_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.settings.update(new_settings)
        try:
            with open(LOCKDOWN_SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving lockdown settings: {e}")

    def get_settings(self) -> Dict[str, Any]:
        return self.settings

    def set_lockdown(self, active: bool):
        self.is_locked_down = active
        # Ideally, we might want to persist this state too in case of service restart
        # But for now, in-memory is okay for the session logic

    def get_status(self) -> bool:
        return self.is_locked_down

# Global accessor
def get_lockdown_manager():
    return LockdownManager()
