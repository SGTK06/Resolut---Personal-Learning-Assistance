# Resolut: Personal Learning Assistance

Resolut is a privacy-first, RAG-powered learning assistant designed to transform your local documents into structured, personalized learning paths.

## 🚀 Key Features

### 1. **Content-Aware Roadmap Generation**
Upload textbooks, research papers, or course materials. Resolut uses **Retrieval-Augmented Generation (RAG)** to index your local content and generate a curriculum that is strictly grounded in your provided materials.

### 2. **Privacy-Centered Architecture**
- **Local FAISS Index**: Your files are indexed locally on your device.
- **On-Device Storage**: All uploaded materials and generated roadmaps remain on your machine.
- **Selective Context sharing**: Only the necessary text chunks are shared with the AI agent for reasoning, never your raw files.

### 3. **Topic Dashboard**
Manage multiple subjects from a single interface. Create new topics, search through your library, and delete learning paths (and all associated data) with a single click.

### 4. **Interactive Roadmap UI**
- **Lesson Tracking**: Check off lessons as you master them.
- **Progress Monitoring**: Real-time progress bars for each chapter and the overall curriculum.
- **Premium Aesthetics**: A sleek, dark-mode inspired interface with intuitive interactions.

### 5. **Hybrid AI System**
Resolut splits the workload between a **Local Service** (data management/indexing) and an **AI Service** (reasoning/planning), providing a fast yet powerful experience while maintaining data sovereignty.

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r app/backend/requirements.txt
cd app/frontend && npm install
```

### 2. Launch the Application
Start the unified desktop environment:
```bash
python app/desktop/run_app.py
```
*This will automatically launch the Local Backend (Port 8000), AI Backend (Port 8001), and the Desktop Window.*

---
*Built for the Encode Hackathon.*
