from typing import List
from pydantic import BaseModel, Field

class Question(BaseModel):
    question: str
    options: List[str]
    correct_option_index: int = Field(..., description="0-based index of the correct option")
    explanation: str

class LessonOutput(BaseModel):
    topic: str
    chapter_title: str
    lesson_title: str
    content_markdown: str = Field(..., description="The educational content in Markdown.")
    questions: List[Question] = Field(..., description="Quizzes to test understanding.")
