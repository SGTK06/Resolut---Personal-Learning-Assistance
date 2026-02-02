from typing import Dict, Any, List
import os
from .teaching_models import LessonOutput
from ..base_agent import BaseAgent

class TeachingAgent(BaseAgent):
    def __init__(self, google_api_key: str = None):
        # Use provided key or fallback to environment variable
        api_key = google_api_key or os.getenv("GEMINI_API_KEY")
        
        system_prompt = """You are an expert personalized tutor. Your goal is to create a comprehensive, engaging, and clear lesson for a student.
        
        Instructions:
        1. Content: Write a detailed lesson explanation in Markdown.
           - Use headings, bullet points, and code snippets (if applicable) to make it readable.
           - Explain concepts clearly with examples.
           - Keep the tone encouraging and professional.
        2. Quiz: Create 3-4 multiple-choice questions to test the user's understanding of THIS specific lesson.
           - Provide 4 options for each question.
           - Indicate the correct answer index.
           - Provide a brief explanation for the answer."""

        super().__init__(
            gemini_model="gemini-2.5-flash-lite",
            gemini_api_key=api_key,
            system_prompt=system_prompt,
            output_structure=LessonOutput
        )

    def generate_lesson(
        self, 
        topic: str, 
        chapter_title: str, 
        lesson_title: str,
        context_chunks: List[Dict[str, Any]]
    ) -> LessonOutput:
        
        context_str = ""
        for i, chunk in enumerate(context_chunks):
            context_str += f"\nSnippet {i+1} (Source: {chunk.get('source', 'Unknown')}):\n{chunk.get('content', '')}\n"

        user_input = f"""
        **Target Lesson:**
        - Topic: {topic}
        - Chapter: {chapter_title}
        - Lesson: {lesson_title}

        **Reference Material:**
        {context_str}
        
        Generate the lesson content and quiz questions based on the above information.
        """

        return self.invoke(user_input)
