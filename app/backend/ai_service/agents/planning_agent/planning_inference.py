import os
from langgraph.graph import StateGraph, END
from .planning_agent import PlanningAgent
from .course_status_input import CourseStatusInputState
import opik
from dotenv import load_dotenv

load_dotenv()
opik.configure()

def get_planning_agent(state: CourseStatusInputState):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    try:
        planning_agent = PlanningAgent(google_api_key=api_key)
        
        # Construct prompt with RAG context if available
        context_str = ""
        if state.get("context"):
            context_str = "\n\nRefer to the following context from the user's uploaded materials:\n"
            for chunk in state["context"]:
                source = chunk.get("source", "Unknown")
                content = chunk.get("content", "")
                context_str += f"[Source: {source}]\n{content}\n"
        
        planning_prompt = f"""
        Create a detailed learning roadmap for:
        Topic: {state['topic']}
        Focus Area: {state['focus_area']}
        
        Prerequisites already known: {', '.join(state['prerequisites_known'] or [])}
        Prerequisites to learn: {', '.join(state['prerequisites_unknown'] or [])}
        
        {context_str}
        
        Ensure the roadmap covers the unknown prerequisites and the main topic.
        """
        
        response = planning_agent.invoke(planning_prompt)
        return {"learning_roadmap": response.roadmap}
        
    except Exception as e:
        print(f"Failed to use planning agent: {str(e)}")
        return {"learning_roadmap": None}

# Define the Graph
workflow = StateGraph(CourseStatusInputState)
workflow.add_node("generate_roadmap", get_planning_agent)
workflow.set_entry_point("generate_roadmap")
workflow.add_edge("generate_roadmap", END)

planning_app = workflow.compile()

@opik.track
def run_planning_agent(
    topic: str, 
    focus_area: str, 
    prerequisites_known: list[str], 
    prerequisites_unknown: list[str],
    context: list = None
):
    try:
        inp_state: CourseStatusInputState = {
            "topic": topic,
            "focus_area": focus_area,
            "prerequisites_known": prerequisites_known,
            "prerequisites_unknown": prerequisites_unknown,
            "learning_roadmap": None,
            "context": context
        }
        result = planning_app.invoke(inp_state)
        return result["learning_roadmap"]
    except Exception as e:
        print(f"Planning API call failed: {str(e)}")
        raise  # Re-raise the exception so it's properly reported to the user
