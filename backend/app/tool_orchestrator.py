from typing import List, Dict, Any, Optional
from backend.app.structured_search import structured_search
from backend.app.semantic_search import semantic_search_engine
from backend.app.hybrid_search import hybrid_search

# Keys that represent hard structured filters (not semantic hints)
HARD_FILTER_KEYS = {
    "designation", "location", "cluster", "band", "cadre", "bu", "sbg",
    "experience_min", "experience_max", "internal_exp_min", "external_exp_min",
    "internal_org", "external_org", "certification", "certification_groups",
    "qualification", "qualification_groups",
    "segment", "skill", "sub_skill", "sub_skill_operator",
    "external_designation", "external_designation_operator",
    "reviewed_proficiency", "is_core_skill", "department",
}

def _has_active_structured_filters(filters: Dict[str, Any]) -> bool:
    """Returns True if any meaningful hard filter is set (non-null, non-false)."""
    for key in HARD_FILTER_KEYS:
        val = filters.get(key)
        if val is not None and val is not False and val != "" and val != []:
            return True
    return False

def orchestrate_search(
    profiles: List[Dict[str, Any]], 
    router_response: Dict[str, Any],
    query: str,
    top_k: Optional[int] = 500
) -> List[Dict[str, Any]]:
    """
    Executes the appropriate search strategy based on router_response:
    - structured: exact/attribute-based filtering.
    - semantic: sentence-embedding similarity.
    - hybrid: attribute-based filtering with similarity ranking.

    Auto-promotes semantic -> hybrid when hard filters are present, so filters
    extracted by the LLM are never silently ignored even if the LLM classified
    the query as SEMANTIC_SEARCH (e.g. 'filter for resources with MBA qualification').
    """
    search_mode = str(router_response.get("search_mode", "semantic")).lower().strip()
    filters = router_response.get("filters", {})
    
    # If no filters block is found, default to empty
    if not filters:
        filters = {}

    # Auto-upgrade: if the LLM said 'semantic' but there are hard structured filters,
    # treat it as hybrid so the filters actually get applied.
    if search_mode == "semantic" and _has_active_structured_filters(filters):
        search_mode = "hybrid"
        
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
