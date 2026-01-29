from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import shutil
import httpx
from PyPDF2 import PdfReader

app = FastAPI(title="Resolut Local Service")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001")

class TopicRequest(BaseModel):
    topic: str
    focus_area: str

@app.post("/api/prerequisites")
async def proxy_prerequisites(request: TopicRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AI_SERVICE_URL}/api/ai/prerequisites",
                json=request.dict(),
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI Service error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI Service: {e}")

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

        text_content = ""
        if file.filename.endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text_content += page.extract_text()
            except Exception as e:
                print(f"Error reading PDF {file.filename}: {e}")

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
