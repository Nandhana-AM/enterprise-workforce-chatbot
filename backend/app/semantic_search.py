import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
from backend.app.config import settings

class SemanticSearchEngine:
    def __init__(self):
        self.model = None
        self.index = None
        self.profiles_map = []  # Index maps to profile objects
        self.is_initialized = False

    def initialize(self, profiles: List[Dict[str, Any]]):
        """
        Builds the FAISS index from the given list of employee profiles.
        """
        if not profiles:
            self.is_initialized = False
            return
            
        # 1. Load the SentenceTransformer model
        if self.model is None:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
        # 2. Extract semantic texts
        semantic_texts = [p["semantic_text"] for p in profiles]
        self.profiles_map = list(profiles)
        
        # 3. Generate embeddings
        embeddings = self.model.encode(semantic_texts, show_progress_bar=False, convert_to_numpy=True)
        
        # Normalize vectors for cosine similarity (Inner Product flat index)
        faiss.normalize_L2(embeddings)
        
        # 4. Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        
        self.is_initialized = True

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search over the indexed profiles.
        Adds 'similarity_score' field to the returned profiles.
        """
        if not self.is_initialized or self.index is None or not self.profiles_map:
            return []
            
        if self.model is None:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
        # 1. Vectorize query
        query_vector = self.model.encode([query], show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(query_vector)
        
        # 2. Search FAISS index
        k = min(top_k, len(self.profiles_map))
        scores, indices = self.index.search(query_vector, k)
        
        results = []
        for rank in range(k):
            idx = indices[0][rank]
            score = float(scores[0][rank])
            
            # FAISS returns -1 if there are not enough matches
            if idx == -1 or idx >= len(self.profiles_map):
                continue
                
            profile = self.profiles_map[idx].copy()
            profile["similarity_score"] = score
            results.append(profile)
            
        return results

    def get_similarity_scores_dict(self, query: str) -> Dict[int, float]:
        """
        Helper method to compute similarity scores for ALL indexed profiles.
        Returns a mapping from PS No -> Cosine Similarity Score.
        Used by the Hybrid Search engine.
        """
        if not self.is_initialized or self.index is None or not self.profiles_map:
            return {}
            
        if self.model is None:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
        query_vector = self.model.encode([query], show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(query_vector)
        
        # Search for all elements
        k = len(self.profiles_map)
        scores, indices = self.index.search(query_vector, k)
        
        scores_dict = {}
        for rank in range(k):
            idx = indices[0][rank]
            score = float(scores[0][rank])
            
            if idx == -1 or idx >= len(self.profiles_map):
                continue
                
            ps_no = self.profiles_map[idx]["ps_no"]
            scores_dict[ps_no] = score
            
        return scores_dict

# Module level singleton
semantic_search_engine = SemanticSearchEngine()
