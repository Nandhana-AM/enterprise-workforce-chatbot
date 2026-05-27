from typing import List, Dict, Any
from backend.app.structured_search import structured_search
from backend.app.semantic_search import semantic_search_engine
from backend.app.hybrid_search import hybrid_search

def orchestrate_search(
    profiles: List[Dict[str, Any]], 
    router_response: Dict[str, Any],
    query: str,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Executes the appropriate search strategy based on router_response:
    - structured: exact/attribute-based filtering.
    - semantic: sentence-embedding similarity.
    - hybrid: attribute-based filtering with similarity ranking.
    """
    search_mode = str(router_response.get("search_mode", "semantic")).lower().strip()
    filters = router_response.get("filters", {})
    
    # If no filters block is found, default to empty
    if not filters:
        filters = {}
        
    # Extract query text for semantic operations
    semantic_query = filters.get("skills_text") or query
    
    if search_mode == "structured":
        results = structured_search(profiles, filters)
        # Default similarity score to 1.0 since it was an exact filter
        for r in results:
            r["similarity_score"] = 1.0
        return results
        
    elif search_mode == "semantic":
        if not semantic_query:
            # Default to return top_k profiles with 0 score
            default_res = profiles[:top_k]
            for r in default_res:
                r["similarity_score"] = 0.0
            return default_res
        return semantic_search_engine.search(semantic_query, top_k=top_k)
        
    elif search_mode == "hybrid":
        return hybrid_search(profiles, semantic_query, filters, top_k=top_k)
        
    else:
        # Default fallback
        return semantic_search_engine.search(semantic_query or query, top_k=top_k)
