from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Add the current directory to sys.path to allow importing agents
sys.path.append(str(Path(__file__).parent))

from agents.prerequisites_agent.prerequisite_inference import run_prerequisite_agent

app = FastAPI(title="Resolut AI Service")

class TopicRequest(BaseModel):
    topic: str
    focus_area: str

@app.post("/api/ai/prerequisites")
async def get_prerequisites(request: TopicRequest):
    try:
        prerequisites = run_prerequisite_agent(request.topic, request.focus_area)
        return {"prerequisites": prerequisites}
    except Exception as e:
        print(f"Error in AI Service get_prerequisites: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
