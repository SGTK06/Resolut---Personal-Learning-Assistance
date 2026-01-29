import os
from langgraph.graph import StateGraph, END
from .prerequisite_agent import PrerequisiteAgent
from .prerequisite_input_state import PrereqInputState
import opik
from dotenv import load_dotenv

load_dotenv()
# Opik for agent observation and call tracing
opik.configure()


def get_prerequisites_agent(state: PrereqInputState):
    #Check environment variables to get gemini API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")

    try:
        prereq_agent = PrerequisiteAgent(
            google_api_key=api_key
        )

        prereq_prompt = f"""What are the prerequisite topics needed
            to learn the Topic: {state['topic']} with focus: {state['focus_area']}"""

        response = prereq_agent.invoke(prereq_prompt)
        return {"prerequisites": response.prereqs}

    except Exception as e:
        print(f"Failed to use prerequisite agent: {str(e)}")
        return {"prerequisites": []}


# Define the Graph
workflow = StateGraph(PrereqInputState)
workflow.add_node("identify_prerequisites", get_prerequisites_agent)
workflow.set_entry_point("identify_prerequisites")
workflow.add_edge("identify_prerequisites", END)

prerequisite_app = workflow.compile()

@opik.track
def run_prerequisite_agent(topic: str, focus_area: str):
    try:
        inp_state: PrereqInputState = {
            "topic": topic,
            "focus_area": focus_area,
            "prerequisites": None
        }
        result = prerequisite_app.invoke(inp_state)
        return result["prerequisites"]
    except Exception as e:
        print(f"API call failed, using fallback prerequisites: {str(e)}")
        return []
