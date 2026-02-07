"""AI Service Proxy Endpoints."""
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os

try:
    from ..rag import search_knowledge_base
except ImportError:
    from rag import search_knowledge_base

router = APIRouter(prefix="/api", tags=["AI Proxy"])

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001")
LOCAL_SERVICE_URL = os.getenv("LOCAL_SERVICE_URL", "http://127.0.0.1:8000")


class TopicRequest(BaseModel):
    topic: str
    focus_area: str


class ScheduleRequest(BaseModel):
    user_input: str
    topic: Optional[str] = "General Learning"


@router.post("/prerequisites")
async def proxy_prerequisites(request: TopicRequest):
    """Proxy prerequisites request to the AI service."""
    async with httpx.AsyncClient() as client:
        try:
            payload = {**request.model_dump(), "device_callback_url": LOCAL_SERVICE_URL}
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/prerequisites",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI Service: {e}")


@router.post("/query")
async def query_with_rag(topic: str = Form(...), query: str = Form(...)):
    """Query the AI with RAG context from local knowledge base."""
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
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI Service: {e}")


@router.post("/planning")
async def proxy_planning(request: dict):
    """Proxy planning request to AI service."""
    async with httpx.AsyncClient() as client:
        try:
            request["device_callback_url"] = LOCAL_SERVICE_URL
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/planning",
                json=request,
                timeout=180.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI Service: {e}")


@router.post("/ai/schedule")
async def proxy_scheduling(request: ScheduleRequest):
    """Proxy scheduling request to AI service."""
    async with httpx.AsyncClient() as client:
        try:
            payload = {"user_input": request.user_input, "device_callback_url": LOCAL_SERVICE_URL}
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
