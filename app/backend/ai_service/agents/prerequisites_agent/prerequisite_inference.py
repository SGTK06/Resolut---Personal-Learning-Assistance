import os
from langgraph.graph import StateGraph, END
from .prerequisite_agent import PrerequisiteAgent
from .prerequisite_input_state import PrereqInputState
import opik
from dotenv import load_dotenv

load_dotenv()
# Opik for agent observation and call tracing
opik.configure()


# Check environment variables to get gemini API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # If not set here, it will fail during agent initialization or first call
    # But for a long-running service, we should ideally have it at startup
    pass

# Shared agent instance to preserve rate limiter across requests
_prereq_agent = None

def get_prerequisite_agent_instance():
    global _prereq_agent
    if _prereq_agent is None:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        _prereq_agent = PrerequisiteAgent(google_api_key=key)
    return _prereq_agent

def get_prerequisites_agent(state: PrereqInputState):
    try:
        prereq_agent = get_prerequisite_agent_instance()

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
