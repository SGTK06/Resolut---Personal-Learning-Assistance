from typing import Dict, Any, List, Optional
from .teaching_agent import TeachingAgent

def run_teaching_agent(
    topic: str,
    chapter_title: str,
    lesson_title: str,
    context: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Run the teaching agent to generate lesson content.
    """
    agent = TeachingAgent()
    
    # If no context provided, we might want to have the agent search for it (tool use),
    # but for now we assume the caller passes context (RAG performed by Main Service or proxy)
    
    lesson_content = agent.generate_lesson(
        topic=topic,
        chapter_title=chapter_title,
        lesson_title=lesson_title,
        context_chunks=context or []
    )
    
    return lesson_content
