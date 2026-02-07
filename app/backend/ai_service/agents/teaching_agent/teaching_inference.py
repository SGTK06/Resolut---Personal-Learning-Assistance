import os
from typing import Dict, Any, List, Optional
from .teaching_agent import TeachingAgent

# Shared agent instance to preserve rate limiter across requests
_teaching_agent = None

def get_teaching_agent_instance():
    global _teaching_agent
    if _teaching_agent is None:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
             # Let it fail inside the agent or handle as appropriate
             pass
        _teaching_agent = TeachingAgent(google_api_key=api_key)
    return _teaching_agent

def run_teaching_agent(
    topic: str,
    chapter_title: str,
    lesson_title: str,
    context: Optional[List[Dict[str, Any]]] = None,
    device_callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the teaching agent to generate lesson content.
    """
    # We no longer use dynamic tools here, as context is pre-fetched by the local service.
    # device_callback_url is preserved in the signature for compatibility but ignored.

    agent = get_teaching_agent_instance()
    
    lesson_content = agent.generate_lesson(
        topic=topic,
        chapter_title=chapter_title,
        lesson_title=lesson_title,
        context_chunks=context or []
    )
    
    return lesson_content
