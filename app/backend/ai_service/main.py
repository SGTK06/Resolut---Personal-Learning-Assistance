"""
Resolut AI Service

This service runs on a remote server and handles:
1. AI agent logic (prerequisites, planning, etc.)
2. Calling tools on the user's local device for RAG

MULTI-USER ISOLATION:
- Each request includes device_callback_url
- Tool calls are scoped to the requesting user's device
- No user data is persisted on the server

PRIVACY:
- Retrieved chunks are used only for the current request
- No logging of user document content
- Ephemeral processing only
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add the current directory to sys.path to allow importing agents
sys.path.append(str(Path(__file__).parent))

from agents.prerequisites_agent.prerequisite_inference import run_prerequisite_agent
from tool_client import create_tool_client

app = FastAPI(title="Resolut AI Service")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Pydantic Models
# =============================================================================

class TopicRequest(BaseModel):
    topic: str
    focus_area: str
    device_callback_url: Optional[str] = None

class QueryRequest(BaseModel):
    topic: str
    query: str
    context: Optional[List[Dict[str, Any]]] = None
    device_callback_url: Optional[str] = None


# =============================================================================
# AI Endpoints
# =============================================================================

@app.post("/api/ai/prerequisites")
async def get_prerequisites(request: TopicRequest):
    """
    Generate prerequisites for a learning topic.
    """
    try:
        # Run the prerequisite agent
        prerequisites = run_prerequisite_agent(
            request.topic, 
            request.focus_area
        )
        
        return {
            "prerequisites": prerequisites
        }
    except Exception as e:
        print(f"Error in AI Service get_prerequisites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/query")
async def query_with_context(request: QueryRequest):
    """
    Answer a query using provided context from the user's local knowledge base.
    
    This endpoint receives pre-retrieved context chunks and generates
    an answer tailored to the user's data.
    
    PRIVACY:
    - Context is used only for this request
    - No persistence of context data
    - Response is generated solely from provided context
    """
    try:
        context_text = ""
        sources = []
        
        if request.context:
            # Format context for the AI
            for i, chunk in enumerate(request.context):
                context_text += f"\n[Source {i+1}: {chunk.get('source', 'Unknown')}]\n"
                context_text += chunk.get('content', '') + "\n"
                if chunk.get('source'):
                    sources.append(chunk['source'])
        
        # If we need more context and have a callback URL
        if not request.context and request.device_callback_url:
            tool_client = create_tool_client(request.device_callback_url)
            chunks = await tool_client.search_knowledge_base(
                query=request.query,
                top_k=5
            )
            for i, chunk in enumerate(chunks):
                context_text += f"\n[Source {i+1}: {chunk.get('source', 'Unknown')}]\n"
                context_text += chunk.get('content', '') + "\n"
                if chunk.get('source'):
                    sources.append(chunk['source'])
        
        # Generate response using context
        # For now, return structured response; integrate with LLM agent as needed
        response = {
            "query": request.query,
            "topic": request.topic,
            "answer": f"Based on the provided context about {request.topic}:\n\n{context_text[:1000]}...",
            "sources": list(set(sources)),
            "context_chunks_used": len(request.context) if request.context else 0
        }
        
        return response
        
    except Exception as e:
        print(f"Error in AI Service query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai_service"}


from agents.planning_agent.planning_inference import run_planning_agent
from agents.teaching_agent.teaching_inference import run_teaching_agent

class PlanningRequest(BaseModel):
    topic: str
    focus_area: str
    prerequisites_known: List[str]
    prerequisites_unknown: List[str]
    device_callback_url: Optional[str] = None


@app.post("/api/ai/planning")
async def generate_roadmap(request: PlanningRequest):
    """
    Generate a learning roadmap using local RAG context.
    """
    try:
        context_chunks = []
        
        if request.device_callback_url:
            tool_client = create_tool_client(request.device_callback_url)
            # Search for broad context about the topic and focus area
            query = f"{request.topic} {request.focus_area} overview structure"
            context_chunks = await tool_client.search_knowledge_base(query, top_k=10)
        
        roadmap = run_planning_agent(
            request.topic,
            request.focus_area,
            request.prerequisites_known,
            request.prerequisites_unknown,
            context=context_chunks
        )
        
        # Validate that a roadmap was actually generated
        if roadmap is None or (isinstance(roadmap, dict) and len(roadmap) == 0):
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate roadmap. The AI service may be temporarily unavailable or rate-limited. Please try again in a few minutes."
            )
        
        return {
            "roadmap": roadmap,
            "context_used": len(context_chunks) > 0
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        print(f"Error in AI Service planning: {e}")
        raise HTTPException(status_code=500, detail=str(e))



class TeachingRequest(BaseModel):
    topic: str
    chapter_title: str
    lesson_title: str
    context: Optional[List[Dict[str, Any]]] = None
    device_callback_url: Optional[str] = None

@app.post("/api/ai/teaching")
async def generate_lesson_endpoint(request: TeachingRequest):
    """
    Generate lesson content using local RAG context.
    """
    try:
        context_chunks = request.context or []
        
        # If no context provided but we have a callback, could fetch more here 
        # (though Local Service usually provides it)
        if not context_chunks and request.device_callback_url:
             tool_client = create_tool_client(request.device_callback_url)
             query = f"{request.topic} {request.chapter_title} {request.lesson_title}"
             context_chunks = await tool_client.search_knowledge_base(query, top_k=5)

        # Run the teaching agent
        lesson_content = run_teaching_agent(
            request.topic,
            request.chapter_title,
            request.lesson_title,
            context=context_chunks
        )
        
        return {
            "lesson_content": lesson_content,
            "context_used": len(context_chunks) > 0
        }
    except Exception as e:
        print(f"Error in AI Service teaching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
