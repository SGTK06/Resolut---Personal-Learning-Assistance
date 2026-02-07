"""Lesson Learning Endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os

try:
    from ..rag import search_knowledge_base
    from ..lesson_storage import (
        save_lesson_content, get_lesson_content, get_progress,
        init_progress, update_progress, LessonContent
    )
    from ..lockdown_manager import get_lockdown_manager
except ImportError:
    from rag import search_knowledge_base
    from lesson_storage import (
        save_lesson_content, get_lesson_content, get_progress,
        init_progress, update_progress, LessonContent
    )
    from lockdown_manager import get_lockdown_manager

router = APIRouter(prefix="/api", tags=["Lessons"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001")
LOCAL_SERVICE_URL = os.getenv("LOCAL_SERVICE_URL", "http://127.0.0.1:8000")


class StartLessonRequest(BaseModel):
    topic: str
    chapter: str
    lesson: str


class CompleteLessonRequest(BaseModel):
    topic: str
    current_chapter: str
    current_lesson: str
    next_chapter: str
    next_lesson: str


@router.post("/lessons/start")
async def start_lesson(request: StartLessonRequest):
    """Start a lesson. Checks for local content first, generates if missing."""
    try:
        # Check for existing content
        existing_content = get_lesson_content(request.topic, request.chapter, request.lesson)
        if existing_content:
            return existing_content.model_dump()

        # Search for context
        try:
            search_query = f"{request.topic} {request.chapter} {request.lesson}"
            context_chunks = search_knowledge_base(search_query, top_k=5)
        except Exception as e:
            print(f"[LESSON] RAG search failed: {e}")
            context_chunks = []  # Continue without context

        # Generate lesson via AI service
        async with httpx.AsyncClient() as client:
            payload = {
                "topic": request.topic,
                "chapter_title": request.chapter,
                "lesson_title": request.lesson,
                "context": context_chunks,
                "device_callback_url": LOCAL_SERVICE_URL
            }
            try:
                response = await client.post(
                    f"{AI_SERVICE_URL}/api/ai/teaching",
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
            except httpx.ConnectError:
                raise HTTPException(status_code=503, detail="AI Service unavailable. Is it running on port 8001?")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")

            generated_data = response.json()

            # Parse response
            if "lesson_content" not in generated_data:
                raise HTTPException(status_code=500, detail=f"Invalid AI response: missing lesson_content. Got: {list(generated_data.keys())}")

            lesson_content = generated_data["lesson_content"]
            final_content = {
                "topic": request.topic,
                "chapter": request.chapter,
                "lesson_title": request.lesson,
                "content_markdown": lesson_content.get("content_markdown", ""),
                "questions": lesson_content.get("questions", [])
            }

            save_lesson_content(LessonContent.parse_obj(final_content))
            init_progress(request.topic, request.chapter, request.lesson)

            return final_content

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {str(e)}")


@router.get("/lessons/progress/{topic}")
async def get_topic_progress(topic: str):
    """Get learning progress for a topic."""
    progress = get_progress(topic)
    if not progress:
        return {"status": "not_started"}
    return progress.model_dump()


@router.post("/lessons/complete")
async def complete_lesson(request: CompleteLessonRequest):
    """Mark a lesson as complete and unlock the next one."""
    completed_id = f"{request.current_chapter}: {request.current_lesson}"
    update_progress(
        request.topic,
        request.next_chapter,
        request.next_lesson,
        completed_id
    )
    get_lockdown_manager().set_lockdown(False)
    return {"status": "success", "next_lesson": request.next_lesson}
