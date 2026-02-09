import os
import datetime
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Ensure paths are absolute by using .resolve()
CALENDAR_DATA_DIR = Path(__file__).resolve().parent / "data" / "calendar"
TOKEN_PATH = CALENDAR_DATA_DIR / "token.json"
CREDENTIALS_PATH = CALENDAR_DATA_DIR / "credentials.json"

def _ensure_calendar_dir():
    CALENDAR_DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_calendar_service():
    """Gets the Google Calendar service, initiating OAuth flow if necessary."""
    try:
        print(f"[CALENDAR] Ensuring directory exists: {CALENDAR_DATA_DIR.absolute()}")
        _ensure_calendar_dir()
        creds = None
        
        if TOKEN_PATH.exists():
            print(f"[CALENDAR] Loading existing token from {TOKEN_PATH.absolute()}")
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("[CALENDAR] Token expired, refreshing...")
                creds.refresh(Request())
            else:
                print("[CALENDAR] Initiating new OAuth flow...")
                # Check for credentials in env vars first (seamless flow)
                client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
                client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
                
                if client_id and client_secret:
                    print("[CALENDAR] Using environment variables for credentials")
                    client_config = {
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                elif CREDENTIALS_PATH.exists():
                    print(f"[CALENDAR] Using credentials file from {CREDENTIALS_PATH.absolute()}")
                    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
                else:
                    error_msg = f"Google Calendar credentials missing. Searched: {CREDENTIALS_PATH.absolute()}"
                    print(f"[CALENDAR] ERROR: {error_msg}")
                    raise ValueError(error_msg)
                
                print("[CALENDAR] Starting local server for OAuth...")
                creds = flow.run_local_server(port=0)
                print("[CALENDAR] OAuth flow successful, saving token")
                
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"[CALENDAR] CRITICAL ERROR in get_calendar_service:")
        import traceback
        traceback.print_exc()
        raise e

def is_connected() -> bool:
    """Checks if the calendar is connected and credentials are valid."""
    try:
        if not TOKEN_PATH.exists():
            return False
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        return creds and creds.valid or (creds.expired and creds.refresh_token)
    except Exception:
        return False

def list_events(max_results: int = 10) -> List[Dict[str, Any]]:
    """List the next upcoming events."""
    try:
        service = get_calendar_service()
        # 'Z' indicates UTC time
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        print(f"Error listing events: {e}")
        return []

def create_event(summary: str, description: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Creates a calendar event.
    start_time and end_time should be in ISO format (e.g., '2024-05-28T09:00:00Z')
    """
    try:
        service = get_calendar_service()
        
        # Ensure UTC suffix if missing and not offset-aware
        if "T" in start_time and not any(z in start_time for z in ["Z", "+", "-"]):
            start_time += "Z"
        if "T" in end_time and not any(z in end_time for z in ["Z", "+", "-"]):
            end_time += "Z"

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
            'reminders': {
                'useDefault': True,
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return event
    except Exception as e:
        print(f"Error creating event: {e}")
        raise e

def get_free_slots(days_ahead: int = 2) -> List[Dict[str, str]]:
    """
    Finds free slots between 8 AM and 10 PM for the next N days.
    """
    try:
        service = get_calendar_service()
        now = datetime.datetime.now(datetime.timezone.utc)
        time_min = now.isoformat()
        time_max = (now + datetime.timedelta(days=days_ahead)).isoformat()

        print(f"[CALENDAR] Fetching freebusy info from {time_min} to {time_max}")
        
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": "primary"}]
        }
        
        freebusy_result = service.freebusy().query(body=body).execute()
        busy_slots = freebusy_result.get("calendars", {}).get("primary", {}).get("busy", [])

        # Define daily boundaries (8 AM - 10 PM)
        free_slots = []
        for d in range(days_ahead + 1):
            day_date = (now + datetime.timedelta(days=d)).date()
            day_start = datetime.datetime.combine(day_date, datetime.time(8, 0, tzinfo=datetime.timezone.utc))
            day_end = datetime.datetime.combine(day_date, datetime.time(22, 0, tzinfo=datetime.timezone.utc))

            # Skip if day_end is in the past
            if day_end < now:
                continue
            
            # Start search from now if day_start is in the past
            current_start = max(day_start, now)
            
            # Find gaps in busy_slots for this day
            for busy in busy_slots:
                b_start = datetime.datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                b_end = datetime.datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))

                if b_start > current_start:
                    gap_duration = (min(b_start, day_end) - current_start).total_seconds() / 60
                    if gap_duration >= 45: # Minimum 45 min slot
                        free_slots.append({
                            "start": current_start.isoformat(),
                            "end": min(b_start, day_end).isoformat()
                        })
                
                current_start = max(current_start, b_end)
                if current_start >= day_end:
                    break
            
            if current_start < day_end:
                gap_duration = (day_end - current_start).total_seconds() / 60
                if gap_duration >= 45:
                    free_slots.append({
                        "start": current_start.isoformat(),
                        "end": day_end.isoformat()
                    })

        return free_slots
    except Exception as e:
        print(f"Error getting free slots: {e}")
        return []
