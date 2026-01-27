from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from agents.prerequisites_agent.prerequisite_inference import run_prerequisite_agent
from PyPDF2 import PdfReader
import opik

app = FastAPI(title="Resolut Learning Assistant")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TopicRequest(BaseModel):
    topic: str
    focus_area: str

@app.post("/api/prerequisites")
async def get_prerequisites(request: TopicRequest):
    try:
        prerequisites = run_prerequisite_agent(request.topic, request.focus_area)
        return {"prerequisites": prerequisites}
    except ValueError as e:
        # Missing API key or configuration error
        error_msg = str(e)
        print(f"Configuration error in get_prerequisites: {error_msg}")
        return {"error": error_msg, "prerequisites": []}
    except Exception as e:
        # API or model error
        error_msg = str(e)
        print(f"Error in get_prerequisites: {error_msg}")
        # Extract a more user-friendly error message
        if "NOT_FOUND" in error_msg or "404" in error_msg:
            friendly_msg = "The AI model is not available. Please check your API configuration."
        elif "API key" in error_msg.lower() or "authentication" in error_msg.lower():
            friendly_msg = "Invalid or missing API key. Please check your GOOGLE_API_KEY environment variable."
        else:
            friendly_msg = f"Error fetching prerequisites: {error_msg[:200]}"
        return {"error": friendly_msg, "prerequisites": []}

@app.post("/api/upload-materials")
async def upload_materials(
    topic: str = Form(...),
    files: List[UploadFile] = File(...)
):
    upload_dir = f"uploads/{topic}"
    os.makedirs(upload_dir, exist_ok=True)

    file_info = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Simple PDF processing example
        text_content = ""
        if file.filename.endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text_content += page.extract_text()

        file_info.append({
            "filename": file.filename,
            "path": file_path,
            "char_count": len(text_content)
        })

    return {
        "message": f"Successfully uploaded {len(files)} files for topic: {topic}",
        "files": file_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
