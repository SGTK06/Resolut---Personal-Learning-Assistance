"""
AI Service Tool Client

This module enables the remote AI agent to call tools exposed by
the user's local device.

MULTI-USER ISOLATION:
- Each request includes a device_callback_url
- The agent uses this URL to call the correct user's tools
- No data is persisted; all tool outputs are ephemeral

SECURITY:
- Tool outputs are never logged
- Results are used only for the current request
- No cross-user data sharing
"""

import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ToolCallResult(BaseModel):
    """Result from a tool call to the user's device."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class DeviceToolClient:
    """
    HTTP client for calling tools on the user's local device.
    
    This client is instantiated per-request with the user's callback URL,
    ensuring complete isolation between users.
    """
    
    def __init__(self, device_callback_url: str, timeout: float = 30.0):
        """
        Initialize the tool client for a specific user's device.
        
        Args:
            device_callback_url: The URL of the user's local service
            timeout: Request timeout in seconds
        """
        self.base_url = device_callback_url.rstrip("/")
        self.timeout = timeout
    
    async def search_knowledge_base(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Call the user's local search_knowledge_base tool.
        
        This retrieves relevant chunks from the user's FAISS index.
        The index never leaves the user's device; only text chunks are returned.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/tools/search_knowledge_base",
                    json={"query": query, "top_k": top_k},
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                return result.get("results", [])
            except httpx.HTTPStatusError as e:
                print(f"Tool call failed: {e.response.status_code}")
                return []
            except Exception as e:
                print(f"Error calling search_knowledge_base: {e}")
                return []
    
    def search_knowledge_base_sync(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Sync version of search_knowledge_base."""
        with httpx.Client() as client:
            try:
                response = client.post(
                    f"{self.base_url}/api/tools/search_knowledge_base",
                    json={"query": query, "top_k": top_k},
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                return result.get("results", [])
            except Exception as e:
                print(f"Error calling search_knowledge_base_sync: {e}")
                return []
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the user's local FAISS index."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/tools/index_stats",
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error getting index stats: {e}")
                return {"error": str(e)}

    async def list_calendar_events(self, max_results: int = 10) -> Dict[str, Any]:
        """List upcoming events from the user's Google Calendar."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/tools/list_calendar_events",
                    params={"max_results": max_results},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error listing calendar events: {e}")
                return {"status": "error", "message": str(e)}

    async def create_calendar_event(self, summary: str, description: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Create a new event in the user's Google Calendar."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "summary": summary,
                    "description": description,
                    "start_time": start_time,
                    "end_time": end_time
                }
                response = await client.post(
                    f"{self.base_url}/api/tools/create_calendar_event",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error creating calendar event: {e}")
                return {"status": "error", "message": str(e)}


def create_tool_client(device_callback_url: str) -> DeviceToolClient:
    """
    Factory function to create a tool client for a user's device.
    
    This should be called once per request, using the device_callback_url
    provided in the request payload.
    
    Args:
        device_callback_url: The URL of the user's local service
        
    Returns:
        DeviceToolClient configured for the user's device
    """
    return DeviceToolClient(device_callback_url)
