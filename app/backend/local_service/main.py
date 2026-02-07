"""
Resolut Local Service

This service runs on the user's device and handles:
1. File uploads and local processing
2. RAG indexing (FAISS-based, all data stays local)
3. Exposing tools for the remote AI agent to call

PRIVACY: All file content and embeddings remain on-device.
The AI agent only receives retrieved text chunks, never raw files.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
import os
import threading
import time
import datetime
import asyncio
import httpx

# Load environment variables from ../.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import RAG and storage modules
try:
    from .rag import get_indexer
    from .calendar_service import CALENDAR_DATA_DIR
except ImportError:
    from rag import get_indexer
    from calendar_service import CALENDAR_DATA_DIR

# Import route modules
try:
    from .routes import rag_routes, topic_routes, calendar_routes, lesson_routes, lockdown_routes, ai_proxy_routes
except ImportError:
    from routes import rag_routes, topic_routes, calendar_routes, lesson_routes, lockdown_routes, ai_proxy_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    get_indexer(data_dir="data")
    print("Local RAG indexer initialized")
    yield
    # Cleanup (if needed) goes here


app = FastAPI(title="Resolut Local Service", lifespan=lifespan)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001")
LOCAL_SERVICE_URL = os.getenv("LOCAL_SERVICE_URL", "http://127.0.0.1:8000")

# Include all route modules
app.include_router(rag_routes.router)
app.include_router(topic_routes.router)
app.include_router(calendar_routes.router)
app.include_router(lesson_routes.router)
app.include_router(lockdown_routes.router)
app.include_router(ai_proxy_routes.router)


# =============================================================================
# Background Scheduler
# =============================================================================

SCHEDULING_SETTINGS_FILE = CALENDAR_DATA_DIR / "scheduling_settings.json"


def log_scheduling_event(message: str):
    """Logs scheduling events to a dedicated file for verification."""
    log_file = CALENDAR_DATA_DIR / "scheduling_events.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[SCHEDULER] {message}")
    except Exception as e:
        print(f"Error logging event: {e}")


async def trigger_autonomous_scheduling(is_manual=False):
    """Triggers the remote AI Scheduling Agent."""
    import json
    now = datetime.datetime.now()
    current_date = now.date()

    log_scheduling_event(f"Triggering autonomous 24h scheduling (Manual: {is_manual})")

    async with httpx.AsyncClient() as client:
        payload = {
            "user_input": f"Autonomous Scheduling Trigger: Current day is {current_date.isoformat()}. Please check my calendar for the NEXT 24 HOURS. If No study session exists already, find a gap and book exactly ONE 1-hour session. DO NOT create duplicate sessions.",
            "device_callback_url": LOCAL_SERVICE_URL
        }
        try:
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/schedule",
                json=payload,
                timeout=180.0
            )
            log_scheduling_event(f"AI Service response: {response.status_code} - {response.text[:100]}")

            # Update last run
            settings = calendar_routes.load_scheduling_settings()
            settings.last_run = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            calendar_routes.save_scheduling_settings(settings)
            return True
        except Exception as e:
            log_scheduling_event(f"Failed to trigger AI: {e}")
            return False


def run_auto_scheduler():
    """Background thread that checks if it's time to auto-schedule study sessions."""
    log_scheduling_event("Auto-scheduler thread started.")
    last_triggered_date = None

    while True:
        try:
            settings = calendar_routes.load_scheduling_settings()
            if settings.auto_schedule:
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.date()

                if current_time == settings.trigger_time and current_date != last_triggered_date:
                    asyncio.run(trigger_autonomous_scheduling(is_manual=False))
                    last_triggered_date = current_date

            time.sleep(60)
        except Exception as e:
            log_scheduling_event(f"Error in scheduler loop: {e}")
            time.sleep(60)


# Start background thread
threading.Thread(target=run_auto_scheduler, daemon=True).start()


# Manual trigger endpoint
@app.post("/api/calendar/trigger-now")
async def manual_trigger_scheduling():
    """Manually triggers the autonomous AI scheduling agent."""
    log_scheduling_event("MANUAL TRIGGER: 'Schedule Now' button clicked in UI.")
    success = await trigger_autonomous_scheduling(is_manual=True)
    if success:
        return {"status": "success", "message": "Scheduling agent triggered successfully"}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to trigger scheduling agent")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
