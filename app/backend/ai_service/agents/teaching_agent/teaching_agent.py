from typing import Dict, Any, List, Optional
import google.generativeai as genai
import os
import json
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

class TeachingAgent:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # Fallback or error if key not present, though usually it is in environment
            print("!!! NO API KEY FOUND IN ENV !!!")
        else:
            print(f"!!! API KEY FOUND: {api_key[:5]}... !!!")
        
        genai.configure(api_key=api_key)
        try:
            print("Listing models from inside TeachingAgent:")
            for m in genai.list_models():
                print(f"- {m.name}")
        except Exception as e:
            print(f"Failed to list models: {e}")
        genai.configure(api_key=api_key)
        gemini_model="gemini-2.5-flash"
        self.model = genai.GenerativeModel(gemini_model)

    def generate_lesson(
        self, 
        topic: str, 
        chapter_title: str, 
        lesson_title: str,
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        context_str = ""
        for i, chunk in enumerate(context_chunks):
            context_str += f"\nSnippet {i+1} (Source: {chunk.get('source', 'Unknown')}):\n{chunk.get('content', '')}\n"

        prompt = f"""
        You are an expert personalized tutor. Your goal is to create a comprehensive, engaging, and clear lesson for a student learning about "{topic}".
        
        **Target Lesson:**
        - Chapter: {chapter_title}
        - Lesson: {lesson_title}

        **Reference Material:**
        Use the following retrieved context to inform your lesson content. If the context is insufficient, rely on your general knowledge but prioritize the specific details from the context.
        
        {context_str}

        **Instructions:**
        1. **Content**: Write a detailed lesson explanation in Markdown.
           - Use headings, bullet points, and code snippets (if applicable) to make it readable.
           - Explain concepts clearly with examples.
           - Keep the tone encouraging and professional.
        2. **Quiz**: Create 3-4 multiple-choice questions to test the user's understanding of THIS specific lesson.
           - Provide 4 options for each question.
           - Indicate the correct answer index.
           - Provide a brief explanation for the answer.

        **Output Format:**
        Return strictly valid JSON conforming to the following structure:
        {{
            "topic": "{topic}",
            "chapter_title": "{chapter_title}",
            "lesson_title": "{lesson_title}",
            "content_markdown": "markdown string...",
            "questions": [
                {{
                    "question": "Question text?",
                    "options": ["A", "B", "C", "D"],
                    "correct_option_index": 0,
                    "explanation": "Why this is correct."
                }}
            ]
        }}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in TeachingAgent: {e}")
            # Return a fallback error structure or re-raise
            raise e
