from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier for managing conversation state")
    message: str = Field(..., description="User message/query in natural language")
    top_k: Optional[int] = Field(default=500, description="Limit of search results to return")

from typing import Dict, Any, Optional, List, Union

class SearchFilters(BaseModel):
    designation: Optional[Union[str, List[str]]] = None
    designation_operator: Optional[str] = "or"
    department: Optional[Union[str, List[str]]] = None
    department_operator: Optional[str] = "or"
    location: Optional[Union[str, List[str]]] = None
    location_operator: Optional[str] = "or"
    band: Optional[Union[str, List[str]]] = None
    band_operator: Optional[str] = "or"
    cadre: Optional[Union[str, List[str]]] = None
    cadre_operator: Optional[str] = "or"
    bu: Optional[Union[str, List[str]]] = None
    bu_operator: Optional[str] = "or"
    sbg: Optional[Union[str, List[str]]] = None
    sbg_operator: Optional[str] = "or"
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    internal_exp_min: Optional[float] = None
    external_exp_min: Optional[float] = None
    certification: Optional[Union[str, List[str]]] = None
    certification_operator: Optional[str] = "and"
    certification_groups: Optional[List[List[str]]] = None   # [(A OR B) AND (C OR D)] style
    qualification: Optional[Union[str, List[str]]] = None
    qualification_operator: Optional[str] = "or"
    qualification_groups: Optional[List[List[str]]] = None   # [(A OR B) AND (C OR D)] style
    segment: Optional[Union[str, List[str]]] = None
    segment_operator: Optional[str] = "or"
    skill: Optional[Union[str, List[str]]] = None
    skill_operator: Optional[str] = "and"
    sub_skill: Optional[Union[str, List[str]]] = None
    sub_skill_operator: Optional[str] = "or"
    external_designation: Optional[Union[str, List[str]]] = None
    external_designation_operator: Optional[str] = "or"
    reviewed_proficiency: Optional[str] = None
    is_core_skill: Optional[bool] = None

class StructuredSearchRequest(BaseModel):
    session_id: str
    filters: SearchFilters
    top_k: Optional[int] = 500

class SemanticSearchRequest(BaseModel):
    session_id: str
    query: str
    top_k: Optional[int] = 500

class HybridSearchRequest(BaseModel):
    session_id: str
    query: str
    filters: SearchFilters
    top_k: Optional[int] = 500
