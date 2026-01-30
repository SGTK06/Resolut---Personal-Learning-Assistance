from typing import List, TypedDict, Optional, Dict, Any
from .roadmap_model import Roadmap


class CourseStatusInputState(TypedDict):
    topic: str
    focus_area: str
    prerequisites_known: List[str] | None
    prerequisites_unknown: List[str] | None
    learning_roadmap: Roadmap | None
    context: Optional[List[Dict[str, Any]]]  # RAG context chunks
