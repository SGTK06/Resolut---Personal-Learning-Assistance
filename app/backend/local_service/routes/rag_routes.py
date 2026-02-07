"""RAG Tool Endpoints - Called by Remote AI Agent."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from ..rag import get_indexer, search_knowledge_base
except ImportError:
    from rag import get_indexer, search_knowledge_base

router = APIRouter(prefix="/api", tags=["RAG Tools"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/tools/search_knowledge_base")
async def tool_search_knowledge_base(request: SearchRequest):
    """
    Search the user's local FAISS index.
    PRIVACY: Only returns text chunks, never raw file data.
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


@router.get("/tools/index_stats")
async def tool_index_stats():
    """Get statistics about the local FAISS index."""
    indexer = get_indexer()
    return indexer.get_stats()
