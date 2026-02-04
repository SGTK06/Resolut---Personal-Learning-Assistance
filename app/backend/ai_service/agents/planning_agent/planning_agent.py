from .roadmap_model import Roadmap
from ..base_agent import BaseAgent


class PlanningAgent(BaseAgent):
    def __init__(self, google_api_key):
        super().__init__(
            gemini_model="gemini-2.0-flash",
            gemini_api_key=google_api_key,
            system_prompt="""You are an expert educational consultant.
                Based on the user's topic and specific focus area, Create a learning
                roadmap for the user to follow. Create chapters in order and cover
                any prerequisites that are not known to the learner. Create as many
                chapters needed to learn the topic completely and make three to five
                lessons in each topic and describe the lesson concisely. Structure the
                roadmap in a way that allows user to complete the chapter in 1 day,
                the lessons can be completed in upto 5 minutes each, and the chapters
                have continuity""",
            output_structure=Roadmap
        )
