from .prerequisites_model import Prerequisites
from ..base_agent import BaseAgent


class PrerequisiteAgent(BaseAgent):
    def __init__(self, google_api_key):
        super().__init__(
            gemini_model="gemini-2.5-flash",
            gemini_api_key=google_api_key,
            system_prompt="""You are an expert educational consultant.
                Based on the user's topic and specific focus area, identify the key
                technical or conceptual prerequisites they should know before starting.
                Be concise and list only the most essential prerequisites.""",
            output_structure=Prerequisites
        )
