"""
Local RAG Indexer Module

Handles file ingestion for the local knowledge base:
- Parse uploaded files (PDF, TXT)
- Split into overlapping chunks
- Generate embeddings using a local model
- Store in FAISS index with metadata

All data remains on the user's device.
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


class LocalIndexer:
    """
    Manages the local FAISS index for RAG.
    All operations are performed on-device; no data leaves the user's machine.
    """
    
    def __init__(self, data_dir: str = "data", embedding_model: str = "all-MiniLM-L6-v2"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.data_dir / "faiss.index"
        self.metadata_path = self.data_dir / "metadata.pkl"
        
        # Load local embedding model (runs entirely on-device)
        print(f"Loading embedding model: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Load or create index
        self.index: Optional[faiss.IndexFlatL2] = None
        self.metadata: List[Dict[str, Any]] = []
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create a new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            print("Loading existing FAISS index...")
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            print(f"Loaded index with {self.index.ntotal} vectors")
        else:
            print("Creating new FAISS index...")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
    
    def _save_index(self):
        """Persist the index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from a file."""
        path = Path(file_path)
        
        if path.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
            except Exception as e:
                print(f"Error reading PDF {file_path}: {e}")
                return ""
        
        elif path.suffix.lower() in [".txt", ".md", ".py", ".js", ".json"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading text file {file_path}: {e}")
                return ""
        
        else:
            print(f"Unsupported file type: {path.suffix}")
            return ""
    
    def index_file(self, file_path: str, topic: str) -> Dict[str, Any]:
        """
        Index a single file into the local FAISS index.
        
        Args:
            file_path: Path to the file to index
            topic: Topic/category for the file
            
        Returns:
            Dict with indexing results
        """
        # Extract text
        text = self._extract_text_from_file(file_path)
        if not text.strip():
            return {"status": "error", "message": "No text extracted", "chunks": 0}
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return {"status": "error", "message": "No chunks created", "chunks": 0}
        
        # Generate embeddings locally
        embeddings = self.model.encode(chunks, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Store metadata for each chunk
        file_name = Path(file_path).name
        for i, chunk in enumerate(chunks):
            self.metadata.append({
                "chunk_id": start_idx + i,
                "content": chunk,
                "source": file_name,
                "topic": topic,
                "file_path": file_path
            })
        
        # Persist to disk
        self._save_index()
        
        return {
            "status": "success",
            "file": file_name,
            "chunks": len(chunks),
            "total_vectors": self.index.ntotal
        }
    
    def index_files(self, file_paths: List[str], topic: str) -> List[Dict[str, Any]]:
        """Index multiple files."""
        results = []
        for path in file_paths:
            result = self.index_file(path, topic)
            results.append(result)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_chunks": len(self.metadata),
            "embedding_dim": self.embedding_dim,
            "index_path": str(self.index_path),
            "index_exists": self.index_path.exists()
        }
    
    def clear_index(self):
        """Clear the entire index (use with caution)."""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.metadata = []
        self._save_index()
        return {"status": "cleared"}

    def delete_topic(self, topic: str):
        """
        Delete a topic and its associated files and vector data.
        
        Args:
            topic: The topic name to delete
        """
        try:
            # 1. Remove files
            topic_dir = Path("uploads") / topic
            if topic_dir.exists():
                import shutil
                shutil.rmtree(topic_dir)
                print(f"Deleted files for topic: {topic}")
            
            # 2. Filter metadata (keep only other topics)
            if not self.metadata:
                print(f"Index is empty, nothing to delete for topic: {topic}")
                return {"status": "success", "message": "Index already empty"}

            indices_to_keep = []
            new_metadata = []
            for i, meta in enumerate(self.metadata):
                if meta.get("topic") != topic:
                    indices_to_keep.append(i)
                    new_metadata.append(meta)
            
            if len(new_metadata) == len(self.metadata):
                print(f"Topic '{topic}' not found in index metadata.")
                return {"status": "not_found", "message": "Topic not found in index"}
                
            # 3. Rebuild Index
            print(f"Rebuilding index after deleting topic: {topic}")
            
            if not indices_to_keep:
                # All topics were the deleted one
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.metadata = []
                print("Index now empty after deletion.")
            else:
                # Create new index and migrate vectors
                new_index = faiss.IndexFlatL2(self.embedding_dim)
                kept_vectors_list = []
                for i in indices_to_keep:
                    try:
                        vec = self.index.reconstruct(i)
                        kept_vectors_list.append(vec)
                    except Exception as e:
                        print(f"Error reconstructing vector {i}: {e}")
                        continue
                
                if kept_vectors_list:
                    kept_vectors_np = np.array(kept_vectors_list).astype('float32')
                    new_index.add(kept_vectors_np)
                
                self.index = new_index
                self.metadata = new_metadata
                
                # Re-assign chunk_ids (FAISS IDs are sequential 0 to N-1 for Flat index)
                for i, meta in enumerate(self.metadata):
                    meta["chunk_id"] = i
            
            self._save_index()
            return {"status": "success", "message": f"Deleted topic {topic}"}
            
        except Exception as e:
            print(f"CRITICAL ERROR in delete_topic: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}


# Singleton instance for the local service
_indexer_instance: Optional[LocalIndexer] = None


def get_indexer(data_dir: str = "data") -> LocalIndexer:
    """Get or create the singleton indexer instance."""
    global _indexer_instance
    if _indexer_instance is None:
        _indexer_instance = LocalIndexer(data_dir=data_dir)
    return _indexer_instance
