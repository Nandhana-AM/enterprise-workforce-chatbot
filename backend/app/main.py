import os
import time
import uuid
import structlog
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn


from backend.app.config import settings
from backend.app.excel_loader import load_excel_sheets
from backend.app.data_cleaner import clean_data
from backend.app.join_engine import build_employee_profiles
from backend.app.semantic_search import semantic_search_engine
from backend.app.llm_router import route_query_llm
from backend.app.query_parser import update_keyword_lists
from backend.app.tool_orchestrator import orchestrate_search
from backend.app.conversation_manager import session_manager
from backend.app.response_formatter import format_search_response
from backend.app.validator import (
    ChatRequest, StructuredSearchRequest, SemanticSearchRequest, HybridSearchRequest
)

# Setup logging
structlog.configure()
logger = structlog.get_logger()

# Global store for loaded profiles
DATABASE = {
    "profiles": [],
    "loaded": False,
    "source_file": None
}

def load_initial_database():
    """Startup auto-loading of default excel dataset is disabled per user request."""
    logger.info("startup_db_load_disabled", msg="Default dataset auto-loading on startup is disabled. Awaiting upload.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_initial_database()
    yield

app = FastAPI(
    title="Enterprise Workforce Intelligence API",
    description="Conversational search backend over relational multi-sheet Excel data.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API prefix rewrite middleware for serving unified frontend/backend
@app.middleware("http")
async def rewrite_api_prefix(request, call_next):
    if request.url.path.startswith("/api/"):
        scope = request.scope
        scope["path"] = request.url.path[4:]
    response = await call_next(request)
    return response

# Dependency to check if database is loaded
def get_database():
    if not DATABASE["loaded"]:
        # Try once more in case file was generated post-startup
        load_initial_database()
        if not DATABASE["loaded"]:
            raise HTTPException(
                status_code=400, 
                detail="No workbook has been loaded. Please upload a valid workforce Excel workbook first."
            )
    return DATABASE["profiles"]

@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_loaded": DATABASE["loaded"],
        "source_file": DATABASE["source_file"],
        "profiles_count": len(DATABASE["profiles"])
    }

@app.post("/upload-workbook")
async def upload_workbook(file: UploadFile = File(...)):
    """Uploads a workforce workbook, cleans it, joins sheets, and indexes it in FAISS."""
    start_time = time.time()
    
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx or .xls) are supported.")
        
    try:
        contents = await file.read()
        dfs, err = load_excel_sheets(contents)
        if err:
            logger.error("upload_failed_parsing", error=err)
            raise HTTPException(status_code=422, detail=err)
            
        cleaned = clean_data(dfs)
        profiles = build_employee_profiles(cleaned)
        
        # Update rule-based parser keyword lists dynamically for this custom dataset
        update_keyword_lists(profiles)
        
        # Initialize/Rebuild semantic index
        semantic_search_engine.initialize(profiles)
        
        # Update global memory db
        DATABASE["profiles"] = profiles
        DATABASE["loaded"] = True
        DATABASE["source_file"] = file.filename
        
        # Reset all active chat sessions for the new dataset
        session_manager.sessions.clear()
        
        latency = time.time() - start_time
        logger.info("upload_success", filename=file.filename, profiles_count=len(profiles), latency=latency)
        
        return {
            "message": "Workbook loaded, cleaned, joined, and indexed successfully.",
            "filename": file.filename,
            "profiles_count": len(profiles)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_exception", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest, db: List[Dict[str, Any]] = Depends(get_database)):
    """Conversational endpoint supporting intent classification, search, and refinement."""
    start_time = time.time()
    req_id = str(uuid.uuid4())
    
    session = session_manager.get_or_create_session(request.session_id)
    
    logger.info("chat_request_received", 
                request_id=req_id,
                session_id=request.session_id, 
                message=request.message)
    
    # Check if message is a simple greeting
    import re
    cleaned = re.sub(r'[^\w\s]', '', request.message).strip().lower()
    if cleaned:
        words = cleaned.split()
        greeting_words = {
            "hi", "hello", "hey", "hola", "greetings", "morning", "afternoon", "evening", 
            "hiya", "yo", "howdy", "there", "good", "wasup", "whats", "up", "sup"
        }
        if len(words) <= 3 and all(w in greeting_words for w in words):
            session.reset()
            formatted = {
                "message": (
                    "Hello! I am your Enterprise Workforce Intelligence Assistant.\n\n"
                    "You can search and filter the employee database using natural language. For example:\n"
                    '- "show civil engineers in Chennai with 10+ years experience"\n'
                    '- "find PMP certified project managers with Siemens experience"\n'
                    '- "who knows electrical systems and has reviewed proficiency"'
                ),
                "results": [],
                "active_filters": {}
            }
            session.add_message("user", request.message)
            session.add_message("assistant", formatted["message"])
            
            latency = time.time() - start_time
            logger.info("chat_request_greeting_intercepted", 
                        request_id=req_id,
                        latency=latency)
            return JSONResponse(content=formatted)
            
    # 1. Route query using LLM Router
    router_resp = route_query_llm(request.message, session.history)
    
    intent = router_resp.get("intent", "UNKNOWN")
    new_filters = router_resp.get("filters", {})
    clarification = router_resp.get("clarification_message")
    
    logger.info("chat_intent_routing", 
                request_id=req_id,
                intent=intent, 
                search_mode=router_resp.get("search_mode"))
    
    # 2. Update session filters
    session.update_filters(intent, new_filters)
    
    # 3. Execute search with accumulated filters
    results = orchestrate_search(
        profiles=db, 
        router_response={
            "search_mode": router_resp.get("search_mode", "semantic"),
            "filters": session.accumulated_filters
        },
        query=request.message,
        top_k=request.top_k
    )
    
    # 4. Save state to session history
    session.last_results = results
    session.last_search_mode = router_resp.get("search_mode", "semantic")
    session.add_message("user", request.message)
    session.add_message("assistant", f"Found {len(results)} matches.", router_resp)
    
    # 5. Format output
    formatted = format_search_response(results, session.accumulated_filters, clarification)
    
    latency = time.time() - start_time
    logger.info("chat_request_completed", 
                request_id=req_id,
                results_count=len(results), 
                latency=latency)
                
    return JSONResponse(content=formatted)

@app.post("/structured-search")
def run_structured(request: StructuredSearchRequest, db: List[Dict[str, Any]] = Depends(get_database)):
    """Direct exact/attribute search bypassing LLM routing."""
    start_time = time.time()
    session = session_manager.get_or_create_session(request.session_id)
    
    filters_dict = request.filters.dict(exclude_none=True)
    session.accumulated_filters = filters_dict
    
    results = orchestrate_search(
        profiles=db,
        router_response={"search_mode": "structured", "filters": filters_dict},
        query=""
    )
    
    formatted = format_search_response(results, filters_dict)
    
    logger.info("direct_structured_search", count=len(results), latency=time.time() - start_time)
    return JSONResponse(content=formatted)

@app.post("/semantic-search")
def run_semantic(request: SemanticSearchRequest, db: List[Dict[str, Any]] = Depends(get_database)):
    """Direct vector semantic search bypassing LLM routing."""
    start_time = time.time()
    
    results = orchestrate_search(
        profiles=db,
        router_response={"search_mode": "semantic", "filters": {"skills_text": request.query}},
        query=request.query,
        top_k=request.top_k
    )
    
    formatted = format_search_response(results, {})
    
    logger.info("direct_semantic_search", count=len(results), latency=time.time() - start_time)
    return JSONResponse(content=formatted)

@app.post("/hybrid-search")
def run_hybrid(request: HybridSearchRequest, db: List[Dict[str, Any]] = Depends(get_database)):
    """Direct hybrid search combining custom filters and query bypassing LLM routing."""
    start_time = time.time()
    
    filters_dict = request.filters.dict(exclude_none=True)
    
    results = orchestrate_search(
        profiles=db,
        router_response={"search_mode": "hybrid", "filters": filters_dict},
        query=request.query,
        top_k=request.top_k
    )
    
    formatted = format_search_response(results, filters_dict)
    
    logger.info("direct_hybrid_search", count=len(results), latency=time.time() - start_time)
    return JSONResponse(content=formatted)

@app.post("/reset-session")
def reset_session(payload: Dict[str, str]):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id in payload.")
        
    session_manager.reset_session(session_id)
    logger.info("session_reset", session_id=session_id)
    return {"message": f"Session {session_id} has been reset successfully."}

from fastapi.staticfiles import StaticFiles

# Serve static frontend files if directory exists
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    # Alternative path for container environment
    container_static = "/app/static"
    if os.path.exists(container_static):
        app.mount("/", StaticFiles(directory=container_static, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

