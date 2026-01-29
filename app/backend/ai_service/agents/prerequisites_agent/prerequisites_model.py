from pydantic import BaseModel, Field
from typing import List

class Prerequisites(BaseModel):
    prereqs: List[str] = Field(description="""A list of specific prerequisites
                               needed to learn the topic and focus area.""")