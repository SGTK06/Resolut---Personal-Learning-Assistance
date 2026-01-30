"""
Local Roadmap Storage
Simple JSON-based storage for generated roadmaps.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any

DATA_DIR = Path("data")
ROADMAPS_FILE = DATA_DIR / "roadmaps.json"

def _load_roadmaps() -> Dict[str, Any]:
    if not ROADMAPS_FILE.exists():
        return {}
    try:
        with open(ROADMAPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_roadmaps(roadmaps: Dict[str, Any]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(ROADMAPS_FILE, "w") as f:
        json.dump(roadmaps, f, indent=2)

def save_roadmap(topic: str, roadmap: Dict[str, Any]):
    roadmaps = _load_roadmaps()
    roadmaps[topic] = roadmap
    _save_roadmaps(roadmaps)

def get_roadmap(topic: str) -> Optional[Dict[str, Any]]:
    roadmaps = _load_roadmaps()
    return roadmaps.get(topic)

def delete_roadmap(topic: str):
    roadmaps = _load_roadmaps()
    if topic in roadmaps:
        del roadmaps[topic]
        _save_roadmaps(roadmaps)
