from typing import Dict, Any, List, Optional
import time

class ChatSession:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.history: List[Dict[str, Any]] = []
        self.accumulated_filters: Dict[str, Any] = {}
        self.last_results: List[Dict[str, Any]] = []
        self.last_search_mode: str = "semantic"
        self.created_at: float = time.time()
        self.updated_at: float = time.time()

    def add_message(self, role: str, message: str, router_response: Optional[Dict[str, Any]] = None):
        """Append message to chat history."""
        self.history.append({
            "role": role,
            "message": message,
            "router_response": router_response,
            "timestamp": time.time()
        })
        self.updated_at = time.time()

    def update_filters(self, intent: str, new_filters: Dict[str, Any]):
        """
        Updates the accumulated filters based on query intent.
        
        - If intent is REFINEMENT, we merge new filters into accumulated filters.
        - Otherwise, we clear old filters and use only the new filters.
        """
        self.updated_at = time.time()
        
        if intent == "REFINEMENT":
            # Merge logic
            for k, val in new_filters.items():
                if val is not None and val != "" and val != False:
                    self.accumulated_filters[k] = val
        else:
            # New query topic: reset filters to the new query's filters
            self.accumulated_filters = {}
            for k, val in new_filters.items():
                if val is not None and val != "" and val != False:
                    self.accumulated_filters[k] = val

    def reset(self):
        """Reset conversation session."""
        self.history = []
        self.accumulated_filters = {}
        self.last_results = []
        self.last_search_mode = "semantic"
        self.updated_at = time.time()

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str) -> ChatSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].reset()

# Module level singleton
session_manager = SessionManager()
