from typing import List, Dict, Any, Optional

def format_search_response(
    results: List[Dict[str, Any]], 
    filters: Dict[str, Any], 
    clarification: Optional[str] = None
) -> Dict[str, Any]:
    """
    Formats the search results and filters into a chat-friendly structure.
    
    Returns:
        {
            "message": "Found 5 civil engineers in Chennai.",
            "results_count": 5,
            "active_filters": {"designation": "Civil Engineer", "location": "Chennai"},
            "results": [...]
        }
    """
    count = len(results)
    
    # 1. Build list of active filter strings for the UI
    active_filters_display = []
    active_filters_clean = {}
    
    has_requirements = bool(filters.get("skill_requirements"))
    for k, val in filters.items():
        if val is not None and val != "" and val != False and k != "skills_text":
            if k.endswith("_operator"):
                continue
            if has_requirements and k in ("skill", "sub_skill", "reviewed_proficiency"):
                continue

            if k == "skill_requirements":
                req_strs = []
                for req in val:
                    # Support both new `skills` list and legacy `skill` string
                    skill_list = req.get("skills") or ([req.get("skill")] if req.get("skill") else [])
                    profs = req.get("proficiency")
                    op = req.get("operator", "or")
                    skill_label = " or ".join(skill_list) if len(skill_list) > 1 else (skill_list[0] if skill_list else "")
                    if profs:
                        prof_str = f" ({f' {op} '.join(profs)})"
                    else:
                        prof_str = ""
                    req_strs.append(f"{skill_label}{prof_str}")
                display_str = " & ".join(req_strs)
                active_filters_clean[k] = display_str
                active_filters_display.append(f"Skills: {display_str}")
                continue

            # Handle grouped filters: qualification_groups / certification_groups
            if k in ("qualification_groups", "certification_groups"):
                is_cert_group = k == "certification_groups"
                group_parts = []
                for group in val:
                    formatted_items = [str(item).upper() if is_cert_group else str(item).title() for item in group]
                    group_parts.append("(" + " or ".join(formatted_items) + ")" if len(formatted_items) > 1 else formatted_items[0])
                display_str = " & ".join(group_parts)
                label = "Certification" if is_cert_group else "Qualification"
                active_filters_clean[k] = display_str
                active_filters_display.append(f"{label}: {display_str}")
                continue

            if isinstance(val, list):
                op = filters.get(f"{k}_operator")
                if not op:
                    op = "and" if k in ["certification", "skill"] else "or"
                connector = " & " if op == "and" else " or "
                active_filters_clean[k] = connector.join(str(item).upper() if k in ["certification", "department", "exclude_department"] else str(item).title() for item in val)
            else:
                if k in ["certification", "department", "exclude_department"]:
                    active_filters_clean[k] = str(val).upper()
                elif k in ["designation", "location", "qualification", "segment", "bu", "sbg", "cadre", "band", "skill", "sub_skill", "external_designation"]:
                    active_filters_clean[k] = str(val).title()
                else:
                    active_filters_clean[k] = val
            if k == "experience_min":
                active_filters_display.append(f"Min Exp: {val} years")
            elif k == "experience_max":
                active_filters_display.append(f"Max Exp: {val} years")
            elif k == "is_core_skill":
                active_filters_display.append("Core Skills Only")
            else:
                if isinstance(val, list):
                    op = filters.get(f"{k}_operator")
                    if not op:
                        op = "and" if k in ["certification", "skill"] else "or"
                    connector = " & " if op == "and" else " or "
                    formatted_val = connector.join(str(item).upper() if k in ["certification", "department", "exclude_department"] else str(item) for item in val)
                else:
                    formatted_val = str(val).upper() if k in ["certification", "department", "exclude_department"] else str(val)
                label = k.replace("_", " ").title()
                if label == "Sub Skill":
                    label = "Sub-Skill"
                active_filters_display.append(f"{label}: {formatted_val}")

                
    # 2. Build human-readable message
    filter_desc = ""
    if active_filters_display:
        filter_desc = " with " + ", ".join(active_filters_display)
        
    if count == 0:
        message = f"I couldn't find any matching employees{filter_desc}. Try broadening your search or resetting the filters."
    elif count == 1:
        message = f"Found 1 matching employee{filter_desc}:"
    else:
        message = f"Found {count} matching employees{filter_desc}:"
        
    # Append router warning/clarification if provided
    if clarification:
        message = f"{clarification.strip()}\n\n{message}"
        
    # 3. Clean results payload for safe serialization (handle any remaining NaNs)
    serialized_results = []
    for r in results:
        clean_r = _clean_profile_for_serialization(r)
        serialized_results.append(clean_r)
        
    return {
        "message": message,
        "results_count": count,
        "active_filters": active_filters_clean,
        "raw_filters": filters,
        "results": serialized_results
    }

def _clean_profile_for_serialization(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures profile dictionary contains no raw NaN float values that would break JSON parsing."""
    clean = {}
    for k, val in profile.items():
        if isinstance(val, float):
            # Check for NaN
            if val != val:  # NaN != NaN
                clean[k] = 0.0
            else:
                clean[k] = val
        elif isinstance(val, dict):
            clean[k] = _clean_profile_for_serialization(val)
        elif isinstance(val, list):
            clean_list = []
            for item in val:
                if isinstance(item, dict):
                    clean_list.append(_clean_profile_for_serialization(item))
                else:
                    clean_list.append(item)
            clean[k] = clean_list
        else:
            clean[k] = val
    return clean
