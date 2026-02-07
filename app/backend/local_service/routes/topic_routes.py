"""Topic and Roadmap Endpoints."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
import shutil

try:
    from ..rag import get_indexer
    from ..roadmap_storage import save_roadmap, get_roadmap, delete_roadmap, _load_roadmaps
except ImportError:
    from rag import get_indexer
    from roadmap_storage import save_roadmap, get_roadmap, delete_roadmap, _load_roadmaps

router = APIRouter(prefix="/api", tags=["Topics"])


class RoadmapData(BaseModel):
    topic: str
    roadmap: Dict[str, Any]


@router.post("/upload-materials")
async def upload_materials(
    topic: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Upload files and index them into the local FAISS index."""
    upload_dir = Path("uploads") / topic
    upload_dir.mkdir(parents=True, exist_ok=True)

    indexer = get_indexer()
    file_info = []

    for file in files:
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        index_result = indexer.index_file(str(file_path), topic)
        file_info.append({
            "filename": file.filename,
            "path": str(file_path),
            "index_status": index_result["status"],
            "chunks_created": index_result.get("chunks", 0)
        })

    return {
        "message": f"Successfully uploaded and indexed {len(files)} files for topic: {topic}",
        "files": file_info,
        "total_vectors": indexer.get_stats()["total_vectors"]
    }


@router.post("/roadmaps")
async def save_roadmap_endpoint(data: RoadmapData):
    """Save a generated roadmap."""
    save_roadmap(data.topic, data.roadmap)
    return {"status": "success"}


@router.get("/roadmaps/{topic_name}")
async def get_roadmap_endpoint(topic_name: str):
    """Get a saved roadmap."""
    roadmap = get_roadmap(topic_name)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return {"roadmap": roadmap}


@router.get("/topics")
async def list_topics():
    """List all topics (from both index and saved roadmaps)."""
    topics = set()
    try:
        indexer = get_indexer()
        meta_list = indexer.metadata if indexer.metadata is not None else []
        if isinstance(meta_list, list):
            for meta in meta_list:
                if isinstance(meta, dict) and "topic" in meta:
                    topics.add(meta["topic"])
    except Exception:
        pass

    try:
        saved = _load_roadmaps()
        if isinstance(saved, dict):
            topics.update(saved.keys())
    except Exception:
        pass

    return {"topics": list(topics)}


@router.delete("/topics/{topic_name}")
async def delete_topic_endpoint(topic_name: str):
    """Delete a topic and all associated data."""
    indexer = get_indexer()
    idx_result = indexer.delete_topic(topic_name)
    delete_roadmap(topic_name)
    return {
        "index_status": idx_result["status"],
        "message": f"Topic {topic_name} deleted (files, index, and roadmap)"
    }
