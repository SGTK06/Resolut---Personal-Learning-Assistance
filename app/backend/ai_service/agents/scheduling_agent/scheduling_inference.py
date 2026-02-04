import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from .scheduling_agent import SchedulingAgent
from tool_client import create_tool_client

def get_scheduling_tools(device_callback_url: str):
    tool_client = create_tool_client(device_callback_url)

    @tool
    async def list_calendar_events(max_results: int = 10) -> str:
        """
        Retrieves upcoming events from the user's Google Calendar.
        Use this to see when the user is busy before scheduling.
        """
        try:
            result = await tool_client.list_calendar_events(max_results)
            if result.get("status") == "success":
                events = result.get("events", [])
                if not events:
                    return "No upcoming events found."
                
                output = "Upcoming Events:\n"
                for e in events:
                    output += f"- {e['summary']} ({e['start']} to {e['end']})\n"
                return output
            else:
                return f"Error: {result.get('message')}"
        except Exception as e:
            return f"Error calling calendar: {str(e)}"

    @tool
    async def create_calendar_event(summary: str, description: str, start_time: str, end_time: str) -> str:
        """
        Creates a new event in the user's Google Calendar.
        start_time and end_time MUST be in ISO format (e.g., '2024-05-28T09:00:00Z').
        """
        try:
            result = await tool_client.create_calendar_event(summary, description, start_time, end_time)
            if result.get("status") == "success":
                return f"Successfully created event: {summary}. Link: {result.get('htmlLink')}"
            else:
                return f"Failed to create event: {result.get('message')}"
        except Exception as e:
            return f"Error creating event: {str(e)}"

    return [list_calendar_events, create_calendar_event]

async def run_scheduling_agent(user_input: str, device_callback_url: str):
    """
    Runs the scheduling agent with tools.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("AI Service API Key not found")
        
    tools = get_scheduling_tools(device_callback_url)
    agent = SchedulingAgent(api_key, tools=tools)
    
    return await agent.ainvoke(user_input)
