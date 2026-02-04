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

## 📅 Google Calendar Setup (Developer)

To enable the seamless AI scheduling feature, you must configure Google Cloud credentials:

### 1. Create a Google Cloud Project
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project named **Resolut**.
- Search for and **Enable the Google Calendar API**.

### 2. Configure OAuth Consent Screen
- Select **External** user type.
- Add your email and the scope: `.../auth/calendar`.
- Add your own email as a **Test User**.

### 3. Create Credentials
- Go to **Credentials** -> **Create Credentials** -> **OAuth Client ID**.
- Application type: **Desktop App**.
- Copy the **Client ID** and **Client Secret**.

### 4. Set Environment Variables
Set the following variables in your development environment (or add them to `run_app.py`):
```bash
GOOGLE_CALENDAR_CLIENT_ID="your_client_id_here"
GOOGLE_CALENDAR_CLIENT_SECRET="your_client_secret_here"
```

---
*Built for the Encode Hackathon.*
