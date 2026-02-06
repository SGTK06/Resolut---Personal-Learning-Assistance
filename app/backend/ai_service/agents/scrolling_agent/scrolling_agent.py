from typing import Dict, Any, List, Optional
import os
from pydantic import BaseModel
from ..base_agent import BaseAgent

class NegotiationOutput(BaseModel):
    message: str
    tone: str
    suggested_action: str

class ScrollingAgent(BaseAgent):
    def __init__(self, google_api_key: str = None):
        # Use provided key or fallback to environment variables
        api_key = google_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        system_prompt = """You are a persuasive and slightly strict digital wellbeing assistant.
        Your goal is to convince the user to stop mindlessly scrolling on social media and return to learning.
        
        You have detected that the user has been scrolling for too long.
        
        Instructions:
        1.  Acknowledge the user's behavior (scrolling).
        2.  Use a tone that varies from "Concerned Friend" to "Strict Coach" depending on the context (though for this interaction start with 'Firm but Encouraging').
        3.  Suggest they switch to the Resolut app to learn something quickly instead.
        4.  Keep the message short (under 2 sentences) as it will appear in a popup.
        
        Your output must be structured as a JSON with keys: 'message', 'tone', 'suggested_action'."""

        super().__init__(
            gemini_model="gemini-2.0-flash-lite",
            gemini_api_key=api_key,
            system_prompt=system_prompt,
            output_structure=NegotiationOutput
        )

    def negotiate(self, current_app: str, duration_minutes: float) -> NegotiationOutput:
        user_input = f"""
        The user has been using {current_app} for approximately {int(duration_minutes)} minutes.
        Convince them to stop and open the Resolut learning app.
        """
        return self.invoke(user_input)
