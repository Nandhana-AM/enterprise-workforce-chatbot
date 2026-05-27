# Enterprise Workforce Intelligence Chatbot

An enterprise-grade conversational AI assistant built over a relational Excel workbook containing 8 connected sheets. It supports **Structured Filtering**, **Semantic Search**, and **Hybrid Search** with **Multi-Turn Conversation Memory** (incremental refinement) and **LLM-powered Query Routing** using GPT-4o-mini and FAISS vector index.

---

## 🏗️ Enterprise Architecture Flow

```
User ──> React Chatbot UI (Port 3000/8000)
             │
             ▼
     FastAPI Backend (Port 8000)
             │
             ├──> Conversation Manager (Tracks session filter states & refinements)
             ├──> LLM Query Router (GPT-4o-mini: Classifies intent & extracts constraints)
             │      └── Fallback: Local rule-based parser (spaCy NER & Regex)
             ▼
     Search Orchestrator
             │
             ├──> Structured Search (Pandas/Python multi-key filters)
             ├──> Semantic Search (SentenceTransformers + FAISS Index)
             └──> Hybrid Search (Structured filters first, then semantic re-ranking)
                     │
                     ▼
       [Unified Employee Knowledge Profiles]
                     ▲
                     │ (Merged on PS No key)
       [Data Cleaner & Relational Join Engine]
                     ▲
                     │ (Loaded sheets)
     [Excel Ingestor: In-Memory / Upload Workbook]
```

---

## 📊 Relational Database Schema (8 Sheets)
All sheets are connected via the primary join key: `PS No`.
1. **Staff_Master**: Core details (Name, Cadre, Band, Designation, Exp, Cluster, BU, SBG, Manager).
2. **Internal_Exp**: Historical internal project postings (Org, From, To).
3. **External_Exp**: Past companies & external job histories (Org, Designation, From, To).
4. **Segment_Exposure**: Industry vertical domains (Segment, Sub-Segment).
5. **Skill_Proficiency**: Detailed skills and proficiency ratings (Skill, Sub-Skill, Declared & Reviewed Proficiency, Core Skill flag).
6. **Job_Skill_Mapping**: Skill metrics at work role levels (Org, Skill, Sub-Skill, Role, Reporting Count, Value).
7. **Certification**: Employee professional credentials.
8. **Qualification**: Academic degrees (Year, Description).

---

## 🚀 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | React (Vite) + TypeScript + Vanilla Premium CSS (Glassmorphism & animations) |
| **Backend** | FastAPI + Uvicorn |
| **Data Engine** | Pandas (data loading, relational merges, exact filters) |
| **Semantic Vectors** | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **Vector Database** | `FAISS` (CPU flat inner product index for cosine similarity) |
| **AI Router / LLM** | OpenAI API (`gpt-4o-mini`) |
| **Local Parser** | spaCy (`en_core_web_sm` model) + Regular Expressions |
| **Logging** | `structlog` (structured JSON logging for request tracing) |
| **Tests** | `pytest` + FastAPI `TestClient` |
| **Container** | Docker + Docker Compose (multi-stage build serving React static build via FastAPI) |

---

## 🛠️ Step-by-Step Installation & Run Guide

### Prerequisites
* Python 3.10+
* Docker (Optional for container run)

### 1. Setup Virtual Environment
```bash
# Create and activate environment
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Mac/Linux
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory (or in `backend/`):
```env
OPENAI_API_KEY=your-openai-api-key-here
LOG_LEVEL=info
```

### 3. Generate Synthetic Database
The project contains a generator to build a realistic 1000-employee relational dataset matching the target schema:
```bash
python generate_sample_excel.py
# Generates: synthetic_skill_dataset.xlsx
```

### 4. Run Locally
```bash
# Start FastAPI backend
python -m backend.app.main
```
The server starts on `http://localhost:8000`. If you run in this mode, it automatically serves the pre-generated `synthetic_skill_dataset.xlsx` database. You can inspect endpoints via Swagger at `/docs`.

---

## 🐳 Docker Deployment (Unified serving)

You can launch the entire unified application (React + FastAPI) in one container using Docker Compose:

```bash
# 1. Place your API Key in your terminal environment or .env file
export OPENAI_API_KEY="sk-..."

# 2. Boot container
docker-compose up --build
```
* Once booted, open `http://localhost:8000` in your browser.
* The container compiles the React app into static files, copies them to the runtime image, and mounts them inside the FastAPI server.

---

## 📬 API Specifications

### `GET /health`
Verifies server health and database load state.
```json
{
  "status": "ok",
  "database_loaded": true,
  "source_file": "synthetic_skill_dataset.xlsx",
  "profiles_count": 1000
}
```

### `POST /upload-workbook`
Upload a new relational multi-sheet Excel file.
* **Form-data**: `file`: (binary `.xlsx`)
```json
{
  "message": "Workbook loaded, cleaned, joined, and indexed successfully.",
  "filename": "custom_employees.xlsx",
  "profiles_count": 1000
}
```

### `POST /chat`
Main conversational endpoint.
* **Payload**:
```json
{
  "session_id": "session_abc123",
  "message": "show civil engineers in Chennai with 10+ years experience"
}
```
* **Response**:
```json
{
  "message": "Filtering for Civil Engineers in Chennai. Found 15 matching employees:",
  "results_count": 15,
  "active_filters": {
    "designation": "Civil Engineer",
    "location": "Chennai",
    "experience_min": 10
  },
  "results": [
    {
      "ps_no": 12345,
      "staff_name": "Arun Kumar",
      "designation": "Civil Engineer",
      "cluster": "Chennai",
      "total_exp": 12.5,
      "skills": [...],
      "certifications": [...],
      "qualifications": [...],
      "internal_experience": [...],
      "external_experience": [...]
    }
  ]
}
```

---

## 🧪 Running the Test Suite
We have custom tests checking relational loads, data sanitization, pandas merges, FAISS indices, and API workflows:
```bash
python -m pytest backend/tests/ -v
```
