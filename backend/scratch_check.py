import re
from typing import Dict, Any

class IntentType:
    UNKNOWN = "UNKNOWN"
    REFINEMENT = "REFINEMENT"

def parse_operator_refinements(q_clean: str, result: Dict[str, Any]):
    fields_mapping = {
        "qualification": r"qualifications?",
        "certification": r"certifications?|certs?",
        "location": r"locations?|places?|cities?",
        "designation": r"designations?|roles?|titles?",
        "department": r"departments?|depts?",
        "skill": r"skills?",
        "sub_skill": r"sub[-_]?skills?"
    }
    for field, pattern in fields_mapping.items():
        if re.search(rf"\b(?:{pattern})\b", q_clean):
            # Check for OR logic
            if re.search(rf"\b(?:{pattern})\b.*\b(or logic|operator\s+(?:to\s+)?or|use\s+or|logic\s+(?:to\s+)?or)\b", q_clean) or \
               re.search(rf"\b(or logic|operator\s+(?:to\s+)?or|use\s+or|logic\s+(?:to\s+)?or)\b.*\b(?:{pattern})\b", q_clean):
                result[f"{field}_operator"] = "or"
                result["intent"] = IntentType.REFINEMENT
            # Check for AND logic
            elif re.search(rf"\b(?:{pattern})\b.*\b(and logic|operator\s+(?:to\s+)?and|use\s+and|logic\s+(?:to\s+)?and)\b", q_clean) or \
                 re.search(rf"\b(and logic|operator\s+(?:to\s+)?and|use\s+and|logic\s+(?:to\s+)?and)\b.*\b(?:{pattern})\b", q_clean):
                result[f"{field}_operator"] = "and"
                result["intent"] = IntentType.REFINEMENT

queries = [
    "use OR logic for qualifications",
    "change qualification operator to OR",
    "change certification logic to AND",
    "use OR logic for places"
]

for q in queries:
    res = {
        "intent": IntentType.UNKNOWN,
        "qualification_operator": "or",
        "certification_operator": "and",
        "location_operator": "or"
    }
    parse_operator_refinements(q.lower().strip(), res)
    print(f"Query: '{q}'")
    print("  Intent:", res["intent"])
    print("  Qual Op:", res.get("qualification_operator"))
    print("  Cert Op:", res.get("certification_operator"))
    print("  Loc Op:", res.get("location_operator"))
