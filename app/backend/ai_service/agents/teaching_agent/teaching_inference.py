import os
from typing import Dict, Any, List, Optional
from .teaching_agent import TeachingAgent

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
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    # We no longer use dynamic tools here, as context is pre-fetched by the local service.
    # device_callback_url is preserved in the signature for compatibility but ignored.

    agent = TeachingAgent(google_api_key=api_key)
    
    lesson_content = agent.generate_lesson(
        topic=topic,
        chapter_title=chapter_title,
        lesson_title=lesson_title,
        context_chunks=context or []
    )
    
    return lesson_content
