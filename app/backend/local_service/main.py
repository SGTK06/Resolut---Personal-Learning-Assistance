"""
Resolut Local Service

This service runs on the user's device and handles:
1. File uploads and local processing
2. RAG indexing (FAISS-based, all data stays local)
3. Exposing tools for the remote AI agent to call

PRIVACY: All file content and embeddings remain on-device.
The AI agent only receives retrieved text chunks, never raw files.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
import httpx
from pathlib import Path
import json
import datetime

# Import RAG modules
# Import RAG modules
try:
    from .rag import get_indexer, search_knowledge_base
    from .roadmap_storage import save_roadmap, get_roadmap, delete_roadmap, _load_roadmaps
    from .lesson_storage import (
        save_lesson_content, get_lesson_content, get_progress, 
        init_progress, update_progress
    )
    from .calendar_service import (
        is_connected, list_events, create_event, 
        get_calendar_service, get_free_slots, CREDENTIALS_PATH, CALENDAR_DATA_DIR
    )
except ImportError:
    # Fallback for running directly potentially
    from rag import get_indexer, search_knowledge_base
    from roadmap_storage import save_roadmap, get_roadmap, delete_roadmap, _load_roadmaps
    from lesson_storage import (
        save_lesson_content, get_lesson_content, get_progress, 
        init_progress, update_progress
    )
    from calendar_service import (
        is_connected, list_events, create_event, 
        get_calendar_service, get_free_slots, CREDENTIALS_PATH, CALENDAR_DATA_DIR
    )

app = FastAPI(title="Resolut Local Service")

# Enable CORS for frontend communication
# Note: When allow_credentials=True, allow_origins cannot be ["*"]
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

# Initialize indexer on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG indexer on service startup."""
    # This will load or create the FAISS index
    get_indexer(data_dir="data")
    print("Local RAG indexer initialized")


# =============================================================================
# Pydantic Models
# =============================================================================

class TopicRequest(BaseModel):
    topic: str
    focus_area: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    content: str
    source: str
    topic: str
    relevance_score: float
    chunk_id: int

class CalendarEventRequest(BaseModel):
    summary: str
    description: str
    start_time: str
    end_time: str

class ScheduleRequest(BaseModel):
    user_input: str
    topic: Optional[str] = "General Learning"

class SchedulingSettings(BaseModel):
    auto_schedule: bool = True
    trigger_time: str = "00:00"
    last_run: Optional[str] = None

SCHEDULING_SETTINGS_FILE = CALENDAR_DATA_DIR / "scheduling_settings.json"

def load_scheduling_settings() -> SchedulingSettings:
    if SCHEDULING_SETTINGS_FILE.exists():
        try:
            with open(SCHEDULING_SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return SchedulingSettings(**data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return SchedulingSettings()

def save_scheduling_settings(settings: SchedulingSettings):
    try:
        CALENDAR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULING_SETTINGS_FILE, 'w') as f:
            json.dump(settings.dict(), f)
    except Exception as e:
        print(f"Error saving settings: {e}")


# =============================================================================
# RAG Tool Endpoints (Called by Remote AI Agent)
# =============================================================================

@app.post("/api/tools/search_knowledge_base")
async def tool_search_knowledge_base(request: SearchRequest):
    """
    Tool: search_knowledge_base
    
    Called by the remote AI agent to retrieve relevant chunks from
    the user's local FAISS index.
    
    PRIVACY: This endpoint only returns text chunks, never raw file data.
    The FAISS index never leaves the device.
    """
    try:
        results = search_knowledge_base(request.query, request.top_k)
        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/tools/index_stats")
async def tool_index_stats():
    """Get statistics about the local FAISS index."""
    indexer = get_indexer()
    return indexer.get_stats()


# =============================================================================
# Google Calendar Endpoints
# =============================================================================

@app.get("/api/calendar/connect")
async def connect_calendar():
    """
    Initiates the Google Calendar OAuth flow.
    This will open a browser on the user's device.
    """
    try:
        print("[API] Initiating Google Calendar connection...")
        # This will block until the user completes the flow
        get_calendar_service()
        print("[API] Google Calendar connection completed successfully")
        return {"status": "success", "message": "Calendar connected successfully"}
    except Exception as e:
        print(f"[API] CRITICAL ERROR in connect_calendar: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/calendar/status")
async def calendar_status():
    """Returns the connection status of the calendar."""
    return {"connected": is_connected()}

@app.get("/api/calendar/config-status")
async def calendar_config_status():
    """Checks if credentials are configured via environment or file."""
    import os
    try:
        has_env = bool(os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"))
        has_file = CREDENTIALS_PATH.exists()
        print(f"[API] Checking for credentials at: {CREDENTIALS_PATH.absolute()} - Found: {has_file}")
        return {"has_credentials": has_env or has_file}
    except Exception as e:
        print(f"[API] ERROR in config-status: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"has_credentials": False, "error": str(e)}

@app.get("/api/tools/list_calendar_events")
async def tool_list_calendar_events(max_results: int = 10):
    """
    Tool: list_calendar_events
    
    Called by the remote AI agent to see the user's upcoming schedule.
    """
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

# Removed /api/calendar/free-slots as manual UI selection is disabled

@app.get("/api/settings/scheduling")
async def get_scheduling_settings_endpoint():
    return load_scheduling_settings()

@app.post("/api/settings/scheduling")
async def update_scheduling_settings_endpoint(settings: SchedulingSettings):
    save_scheduling_settings(settings)
    return {"status": "success", "settings": settings}

@app.get("/api/calendar/sessions")
async def get_study_sessions():
    """Returns scheduled study sessions for the next 48 hours."""
    if not is_connected():
        return {"status": "error", "message": "Calendar not connected"}
    
    try:
        events = list_events(max_results=50) # Fetch more to filter
        now = datetime.datetime.now(datetime.timezone.utc)
        limit = now + datetime.timedelta(days=1)
        
        study_sessions = []
        for e in events:
            # Handle both 'dateTime' (specific time) and 'date' (all-day)
            start_data = e.get("start", {})
            start_str = start_data.get("dateTime") or start_data.get("date")
            if not start_str: continue
            
            try:
                # Handle all-day events (YYYY-MM-DD) vs timed events
                if "T" not in start_str:
                    # All-day event: convert to midnight UTC datetime
                    start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
                else:
                    start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                
                # Ensure start_dt is timezone-aware for comparison
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
            except Exception as parse_err:
                print(f"[API] Skipping event due to parse error: {parse_err} (Data: {start_str})")
                continue
        
        return {"status": "success", "sessions": sorted(study_sessions, key=lambda x: x["start"])}
    except Exception as e:
        print(f"[API] Error in get_study_sessions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calendar/trigger-now")
async def manual_trigger_scheduling():
    """Manually triggers the autonomous AI scheduling agent."""
    log_scheduling_event("MANUAL TRIGGER: 'Schedule Now' button clicked in UI.")
    success = await trigger_autonomous_scheduling(is_manual=True)
    if success:
        return {"status": "success", "message": "Scheduling agent triggered successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to trigger scheduling agent")

@app.post("/api/tools/create_calendar_event")
async def tool_create_calendar_event(request: CalendarEventRequest):
    """
    Tool: create_calendar_event
    
    Called by the remote AI agent to schedule a study session.
    """
    if not is_connected():
        return {"status": "error", "message": "Calendar not connected"}
    
    try:
        log_scheduling_event(f"AI AGENT ACTION: Creating event '{request.summary}' from {request.start_time} to {request.end_time}")
        event = create_event(
            request.summary,
            request.description,
            request.start_time,
            request.end_time
        )
        log_scheduling_event(f"AI AGENT SUCCESS: Event created with ID {event.get('id')}")
        return {"status": "success", "event_id": event.get("id"), "htmlLink": event.get("htmlLink")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Background Scheduler
# =============================================================================

import threading
import time
import asyncio
import httpx

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
    """Shares the logic to trigger the remote AI Scheduling Agent."""
    settings = load_scheduling_settings()
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
            settings.last_run = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_scheduling_settings(settings)
            return True
        except Exception as e:
            log_scheduling_event(f"Failed to trigger AI: {e}")
            return False

def run_auto_scheduler():
    """
    Background thread that checks if it's time to auto-schedule study sessions.
    Runs every minute.
    """
    log_scheduling_event("Auto-scheduler thread started.")
    last_triggered_date = None
    
    while True:
        try:
            settings = load_scheduling_settings()
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


# =============================================================================
# File Upload & Indexing
# =============================================================================

@app.post("/api/upload-materials")
async def upload_materials(
    topic: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload files and index them into the local FAISS index.
    
    This endpoint:
    1. Saves files to local storage
    2. Extracts text content
    3. Splits into chunks
    4. Generates embeddings locally
    5. Stores in FAISS index
    
    All processing happens on-device.
    """
    upload_dir = Path("uploads") / topic
    upload_dir.mkdir(parents=True, exist_ok=True)

    indexer = get_indexer()
    file_info = []
    
    for file in files:
        file_path = upload_dir / file.filename
        
        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Index the file
        index_result = indexer.index_file(str(file_path), topic)
        
        file_info.append({
            "filename": file.filename,
            "path": str(file_path),
            "index_status": index_result["status"],
            "chunks_created": index_result.get("chunks", 0)
        })

    return {
        "message": f"Successfully uploaded and indexed {len(files)} files for topic: {topic}",
        "files": file_info,
        "total_vectors": indexer.get_stats()["total_vectors"]
    }


# =============================================================================
# AI Service Proxy (with device callback URL)
# =============================================================================

@app.post("/api/prerequisites")
async def proxy_prerequisites(request: TopicRequest):
    """
    Proxy prerequisites request to the AI service.
    Includes the device callback URL for tool invocation.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Include local service URL so AI agent can call back for tools
            payload = {
                **request.dict(),
                "device_callback_url": LOCAL_SERVICE_URL
            }
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/prerequisites",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, 
                detail=f"AI Service error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to connect to AI Service: {e}"
            )



class RoadmapData(BaseModel):
    topic: str
    roadmap: Dict[str, Any]

@app.post("/api/roadmaps")
async def save_roadmap_endpoint(data: RoadmapData):
    """Save a generated roadmap."""
    save_roadmap(data.topic, data.roadmap)
    return {"status": "success"}

@app.get("/api/roadmaps/{topic_name}")
async def get_roadmap_endpoint(topic_name: str):
    """Get a saved roadmap."""
    roadmap = get_roadmap(topic_name)
    if roadmap is None:
         raise HTTPException(status_code=404, detail="Roadmap not found")
    return {"roadmap": roadmap}

@app.get("/api/topics")
async def list_topics():
    """List all topics (from both index and saved roadmaps)."""
    import traceback
    topics = set()
    try:
        indexer = get_indexer()
        # from index: metadata is a list of dicts; guard against None or wrong type
        meta_list = indexer.metadata if indexer.metadata is not None else []
        if not isinstance(meta_list, list):
            meta_list = []
        for meta in meta_list:
            if isinstance(meta, dict) and "topic" in meta:
                topics.add(meta["topic"])
    except Exception:
        traceback.print_exc()
        # Continue with roadmaps only so we don't 500

    try:
        saved = _load_roadmaps()
        if isinstance(saved, dict):
            topics.update(saved.keys())
    except Exception:
        traceback.print_exc()

    return {"topics": list(topics)}


@app.delete("/api/topics/{topic_name}")
async def delete_topic_endpoint(topic_name: str):
    """Delete a topic and all associated data."""
    indexer = get_indexer()
    
    # Delete from index and files
    idx_result = indexer.delete_topic(topic_name)
    
    # Delete saved roadmap
    delete_roadmap(topic_name)
    
    return {
        "index_status": idx_result["status"],
        "message": f"Topic {topic_name} deleted (files, index, and roadmap)"
    }


@app.post("/api/query")
async def query_with_rag(topic: str = Form(...), query: str = Form(...)):
    """
    Query the AI with RAG context from local knowledge base.
    
    This endpoint:
    1. Retrieves relevant chunks from local FAISS index
    2. Sends query + context to AI service
    3. Returns AI-generated response
    """
    # Get relevant context from local index
    context_results = search_knowledge_base(query, top_k=5)
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "topic": topic,
                "query": query,
                "context": context_results,
                "device_callback_url": LOCAL_SERVICE_URL
            }
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/query",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"AI Service error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to AI Service: {e}"
            )


@app.post("/api/planning")
async def proxy_planning(request: dict):
    """
    Proxy planning request to AI service.
    Injects device_callback_url automatically.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Inject callback URL
            request["device_callback_url"] = LOCAL_SERVICE_URL
            
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/planning",
                json=request,
                timeout=180.0 # Longer timeout for planning
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI Service: {e}")

@app.post("/api/ai/schedule")
async def proxy_scheduling(request: ScheduleRequest):
    """
    Proxy scheduling request to AI service.
    """
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "user_input": request.user_input,
                "device_callback_url": LOCAL_SERVICE_URL
            }
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/schedule",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI Service: {e}")

# =============================================================================
# Lesson Learning Endpoints
# =============================================================================

class StartLessonRequest(BaseModel):
    topic: str
    chapter: str
    lesson: str

@app.post("/api/lessons/start")
async def start_lesson(request: StartLessonRequest):
    """
    Start a lesson.
    Checks for local content first. If missing, calls AI service to generate it.
    """
    print(f"DEBUG: Starting lesson request for topic='{request.topic}', chapter='{request.chapter}', lesson='{request.lesson}'")
    try:
        # 1. Check if lesson exists locally
        existing_content = get_lesson_content(request.topic, request.chapter, request.lesson)
        if existing_content:
            return existing_content.dict()
        
        # 2. If not, generate it via AI Service
        # First, get context about the lesson topic
        search_query = f"{request.topic} {request.chapter} {request.lesson}"
        context_chunks = search_knowledge_base(search_query, top_k=5)
        
        async with httpx.AsyncClient() as client:
            payload = {
                "topic": request.topic,
                "chapter_title": request.chapter,
                "lesson_title": request.lesson,
                "context": context_chunks,
                "device_callback_url": LOCAL_SERVICE_URL
            }
            
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/teaching",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            generated_data = response.json()
            
            # 3. Save to local storage
            lesson_content = generated_data["lesson_content"]
            
            final_content = {
                "topic": request.topic,
                "chapter": request.chapter,
                "lesson_title": request.lesson,
                "content_markdown": lesson_content.get("content_markdown", ""),
                "questions": lesson_content.get("questions", [])
            }
            
            # Save it
            from lesson_storage import LessonContent
            save_lesson_content(LessonContent.parse_obj(final_content))
            
            # Initialize progress if first time
            init_progress(request.topic, request.chapter, request.lesson)
            
            return final_content
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating lesson: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {str(e)}")


@app.get("/api/lessons/progress/{topic}")
async def get_topic_progress(topic: str):
    """Get learning progress for a topic."""
    progress = get_progress(topic)
    if not progress:
        return {"status": "not_started"}
    return progress.dict()


class CompleteLessonRequest(BaseModel):
    topic: str
    current_chapter: str
    current_lesson: str
    next_chapter: str
    next_lesson: str

@app.post("/api/lessons/complete")
async def complete_lesson(request: CompleteLessonRequest):
    """
    Mark a lesson as complete and unlock the next one.
    """
    # Create a unique ID for the completed lesson
    completed_id = f"{request.current_chapter}: {request.current_lesson}"
    
    update_progress(
        request.topic,
        request.next_chapter,
        request.next_lesson,
        completed_id
    )
    return {"status": "success", "next_lesson": request.next_lesson}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
