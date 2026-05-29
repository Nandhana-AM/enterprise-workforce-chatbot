from typing import List, Dict, Any, Optional
from backend.app.structured_search import structured_search
from backend.app.semantic_search import semantic_search_engine

def hybrid_search(
    profiles: List[Dict[str, Any]], 
    query: str, 
    filters: Dict[str, Any], 
    top_k: Optional[int] = 500
) -> List[Dict[str, Any]]:
    """
    Intelligently combines structured filters and semantic search.
    
    Workflow:
    1. Filter the entire database of profiles using the structured filters.
    2. Get semantic similarity scores for all profiles against the query.
    3. Map the similarity scores to the structurally filtered profiles.
    4. Sort the filtered profiles by their similarity score in descending order.
    5. Return the top_k results.
    """
    # 1. Apply structured filters
    filtered_profiles = structured_search(profiles, filters)
    
    # If no profiles match the structured constraints, return empty immediately
    if not filtered_profiles:
        return []
        
    # 2. Get similarity scores for all employees in the index
    # We pass the semantic portion of the query, or fallback to the full query if needed
    semantic_query = filters.get("skills_text") or query
    
    # Calculate scores if the semantic engine is initialized
    if semantic_search_engine.is_initialized:
        scores_dict = semantic_search_engine.get_similarity_scores_dict(semantic_query)
        
        # 3. Attach similarity scores
        for p in filtered_profiles:
            p["similarity_score"] = scores_dict.get(p["ps_no"], 0.0)
            
        # 4. Rank by similarity score
        filtered_profiles.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
    else:
        # Fallback: if semantic engine is not ready, default similarity_score to 0
        for p in filtered_profiles:
            p["similarity_score"] = 0.0
            
    # Return top_k
    if top_k is not None:
        return filtered_profiles[:top_k]
    return filtered_profiles
