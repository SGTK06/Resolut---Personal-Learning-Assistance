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

# Import RAG modules
# Import RAG modules
try:
    from .rag import get_indexer, search_knowledge_base
    from .roadmap_storage import save_roadmap, get_roadmap, delete_roadmap, _load_roadmaps
except ImportError:
    # Fallback for running directly potentially
    from rag import get_indexer, search_knowledge_base
    from roadmap_storage import save_roadmap, get_roadmap, delete_roadmap, _load_roadmaps

app = FastAPI(title="Resolut Local Service")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
