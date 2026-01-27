from typing import List, TypedDict


class PrereqInputState(TypedDict):
    topic: str
    focus_area: str
    prerequisites: List[str] | None
