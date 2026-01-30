"""
Local RAG Retriever Module

Handles retrieval from the local FAISS index:
- Query the index with embeddings
- Return top-k relevant chunks
- All operations remain on-device

This module exposes the search_knowledge_base functionality.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from .indexer import get_indexer, LocalIndexer


class LocalRetriever:
    """
    Retrieves relevant chunks from the local FAISS index.
    Designed to be called by the remote AI agent via HTTP.
    """
    
    def __init__(self, indexer: Optional[LocalIndexer] = None):
        self.indexer = indexer or get_indexer()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the local knowledge base for relevant chunks.
        
        This is the core function exposed as a tool to the remote AI agent.
        The query is embedded locally and used to search the FAISS index.
        
        Args:
            query: The search query string
            top_k: Number of results to return
            
        Returns:
            List of retrieved chunks with content, source, and relevance score
        """
        if self.indexer.index is None or self.indexer.index.ntotal == 0:
            return []
        
        # Embed the query locally (never sent to remote server)
        query_embedding = self.indexer.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding).astype("float32")
        
        # Limit top_k to available vectors
        actual_k = min(top_k, self.indexer.index.ntotal)
        
        # Search FAISS index
        distances, indices = self.indexer.index.search(query_embedding, actual_k)  # type: ignore
        
        # Build results with metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.indexer.metadata):
                chunk_meta = self.indexer.metadata[idx]
                results.append({
                    "content": chunk_meta["content"],
                    "source": chunk_meta["source"],
                    "topic": chunk_meta.get("topic", ""),
                    "relevance_score": float(1 / (1 + distances[0][i])),  # Convert distance to similarity
                    "chunk_id": int(idx)
                })
        
        return results
    
    def search_by_topic(self, query: str, topic: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search within a specific topic.
        
        Args:
            query: The search query string
            topic: Filter results to this topic only
            top_k: Number of results to return
            
        Returns:
            List of retrieved chunks filtered by topic
        """
        # Get more results initially to filter by topic
        all_results = self.search(query, top_k=top_k * 3)
        
        # Filter by topic
        filtered = [r for r in all_results if r.get("topic") == topic]
        
        return filtered[:top_k]


# Singleton instance
_retriever_instance: Optional[LocalRetriever] = None


def get_retriever() -> LocalRetriever:
    """Get or create the singleton retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = LocalRetriever()
    return _retriever_instance


def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Primary tool function for searching the local knowledge base.
    
    This function is exposed to the remote AI agent via HTTP.
    All processing happens locally; only the retrieved text chunks
    are returned to the agent.
    
    Args:
        query: The search query
        top_k: Number of results to return
        
    Returns:
        List of relevant chunks with metadata
    """
    retriever = get_retriever()
    return retriever.search(query, top_k)
