from typing import List, TypedDict
from roadmap_model import Roadmap


class CourseStatusInputState(TypedDict):
    topic: str
    focus_area: str
    prerequisites_known: List[str] | None
    prerequisites_unknown: List[str] | None
    learning_roadmap: Roadmap | None
