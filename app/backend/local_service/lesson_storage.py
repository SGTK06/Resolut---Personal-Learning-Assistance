"""
Local Lesson Storage & Progress Tracking
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

DATA_DIR = Path("data")
LESSONS_DIR = DATA_DIR / "lessons"
PROGRESS_FILE = DATA_DIR / "progress.json"

class LessonContent(BaseModel):
    topic: str
    chapter: str
    lesson_title: str
    content_markdown: str
    questions: List[Dict[str, Any]]

class TopicProgress(BaseModel):
    current_chapter: str
    current_lesson: str
    completed_lessons: List[str]  # List of "Chapter Name: Lesson Name"

def _ensure_dirs():
    LESSONS_DIR.mkdir(parents=True, exist_ok=True)
    if not PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "w") as f:
            json.dump({}, f)

def _get_lesson_path(topic: str, chapter: str, lesson: str) -> Path:
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_', '-')).strip()
    safe_chapter = "".join(c for c in chapter if c.isalnum() or c in (' ', '_', '-')).strip()
    safe_lesson = "".join(c for c in lesson if c.isalnum() or c in (' ', '_', '-')).strip()
    return LESSONS_DIR / safe_topic / safe_chapter / f"{safe_lesson}.json"

def save_lesson_content(content: LessonContent):
    _ensure_dirs()
    path = _get_lesson_path(content.topic, content.chapter, content.lesson_title)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.json())

def get_lesson_content(topic: str, chapter: str, lesson: str) -> Optional[LessonContent]:
    path = _get_lesson_path(topic, chapter, lesson)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return LessonContent.parse_raw(f.read())
    except Exception:
        return None

def get_progress(topic: str) -> Optional[TopicProgress]:
    _ensure_dirs()
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            all_progress = json.load(f)
            if topic in all_progress:
                return TopicProgress.parse_obj(all_progress[topic])
    except Exception:
        pass
    return None

def init_progress(topic: str, first_chapter: str, first_lesson: str):
    _ensure_dirs()
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            all_progress = json.load(f)
    except Exception:
        all_progress = {}
    
    if topic not in all_progress:
        new_progress = TopicProgress(
            current_chapter=first_chapter,
            current_lesson=first_lesson,
            completed_lessons=[]
        )
        all_progress[topic] = new_progress.model_dump()
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_progress, f, indent=2)

def update_progress(topic: str, next_chapter: str, next_lesson: str, completed_lesson_id: str):
    _ensure_dirs()
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            all_progress = json.load(f)
    except Exception:
        all_progress = {}
        
    if topic in all_progress:
        progress = all_progress[topic]
        if completed_lesson_id not in progress["completed_lessons"]:
            progress["completed_lessons"].append(completed_lesson_id)
        
        progress["current_chapter"] = next_chapter
        progress["current_lesson"] = next_lesson
        
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_progress, f, indent=2)
