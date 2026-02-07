"""Google Calendar Endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import datetime
import json

try:
    from ..calendar_service import (
        is_connected, list_events, create_event,
        get_calendar_service, CREDENTIALS_PATH, CALENDAR_DATA_DIR
    )
except ImportError:
    from calendar_service import (
        is_connected, list_events, create_event,
        get_calendar_service, CREDENTIALS_PATH, CALENDAR_DATA_DIR
    )

router = APIRouter(prefix="/api", tags=["Calendar"])


class CalendarEventRequest(BaseModel):
    summary: str
    description: str
    start_time: str
    end_time: str


class SchedulingSettings(BaseModel):
    auto_schedule: bool = True
    trigger_time: str = "00:00"
    last_run: Optional[str] = None


SCHEDULING_SETTINGS_FILE = CALENDAR_DATA_DIR / "scheduling_settings.json"


def load_scheduling_settings() -> SchedulingSettings:
    if SCHEDULING_SETTINGS_FILE.exists():
        try:
            with open(SCHEDULING_SETTINGS_FILE, 'r') as f:
                return SchedulingSettings(**json.load(f))
        except Exception:
            pass
    return SchedulingSettings()


def save_scheduling_settings(settings: SchedulingSettings):
    try:
        CALENDAR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULING_SETTINGS_FILE, 'w') as f:
            json.dump(settings.model_dump(), f)
    except Exception as e:
        print(f"Error saving settings: {e}")


@router.get("/calendar/connect")
async def connect_calendar():
    """Initiates the Google Calendar OAuth flow."""
    try:
        get_calendar_service()
        return {"status": "success", "message": "Calendar connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/status")
async def calendar_status():
    """Returns the connection status of the calendar."""
    return {"connected": is_connected()}


@router.get("/calendar/config-status")
async def calendar_config_status():
    """Checks if credentials are configured."""
    import os
    has_env = bool(os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"))
    has_file = CREDENTIALS_PATH.exists()
    return {"has_credentials": has_env or has_file}


@router.get("/tools/list_calendar_events")
async def tool_list_calendar_events(max_results: int = 10):
    """List upcoming calendar events."""
    if not is_connected():
        return {"status": "error", "message": "Calendar not connected"}
    events = list_events(max_results)
    return {
        "status": "success",
        "events": [
            {
                "summary": e.get("summary"),
                "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
                "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
                "description": e.get("description", "")
            }
            for e in events
        ]
    }


@router.get("/settings/scheduling")
async def get_scheduling_settings_endpoint():
    return load_scheduling_settings()


@router.post("/settings/scheduling")
async def update_scheduling_settings_endpoint(settings: SchedulingSettings):
    save_scheduling_settings(settings)
    return {"status": "success", "settings": settings}


@router.get("/calendar/sessions")
async def get_study_sessions():
    """Returns scheduled study sessions for the next 48 hours."""
    if not is_connected():
        return {"status": "error", "message": "Calendar not connected"}

    try:
        events = list_events(max_results=50)
        now = datetime.datetime.now(datetime.timezone.utc)
        limit = now + datetime.timedelta(days=1)

        study_sessions = []
        for e in events:
            start_data = e.get("start", {})
            start_str = start_data.get("dateTime") or start_data.get("date")
            if not start_str:
                continue

            try:
                if "T" not in start_str:
                    start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
                else:
                    start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))

                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)

                if now <= start_dt <= limit:
                    summary = e.get("summary", "").lower()
                    if "study" in summary or "learning" in summary:
                        study_sessions.append({
                            "summary": e.get("summary"),
                            "start": start_str,
                            "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")
                        })
            except Exception:
                continue

        return {"status": "success", "sessions": sorted(study_sessions, key=lambda x: x["start"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/create_calendar_event")
async def tool_create_calendar_event(request: CalendarEventRequest):
    """Create a calendar event."""
    if not is_connected():
        return {"status": "error", "message": "Calendar not connected"}

    try:
        event = create_event(request.summary, request.description, request.start_time, request.end_time)
        return {"status": "success", "event_id": event.get("id"), "htmlLink": event.get("htmlLink")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
