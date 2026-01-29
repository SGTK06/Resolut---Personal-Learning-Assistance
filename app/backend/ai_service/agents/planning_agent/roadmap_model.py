from pydantic import BaseModel, Field
from typing import Dict


class Roadmap(BaseModel):
    roadmap: Dict[str, Dict[str, str]] = Field(
        description="""A strictly structured learning roadmap with chapters,
        lessons and lesson descriptions for each chapter.

        Structure:
        {
            "Chapter Name": {
                "Lesson Name": "Lesson description"
            }
        }

        Rules:
        - Top-level keys MUST be chapter titles (strings).
        - Chapter values MUST be dictionaries.
        - Inner dictionary keys MUST be lesson titles (strings).
        - Inner dictionary values MUST be lesson descriptions (strings).
        - No lists, no optional fields, no additional nesting.
        """
    )