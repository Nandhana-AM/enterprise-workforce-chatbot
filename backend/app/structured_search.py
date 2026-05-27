import re
from typing import List, Dict, Any

def normalize_val(val: Any) -> str:
    if val is None:
        return ""
    return re.sub(r"[\s\-\.]", "", str(val)).lower()

def stem_word(w: str) -> str:
    w = w.lower()
    if len(w) > 3:
        if w.endswith("ies"):
            return w[:-3] + "y"
        elif w.endswith("es") and not w.endswith("ss"):
            return w[:-2]
        elif w.endswith("s") and not w.endswith("ss"):
            return w[:-1]
    return w

def structured_search(profiles: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filters the unified list of employee profiles based on the provided filters.
    All filters applied are treated as 'AND' conditions.
    """
    filtered = []
    
    for p in profiles:
        match = True
        
        # 1. Designation Filter (case-insensitive substring and token-based fallback)
        if filters.get("designation"):
            desig_filter = filters["designation"]
            desig_queries = desig_filter if isinstance(desig_filter, list) else [desig_filter]
            desig_op = filters.get("designation_operator", "or")
            
            matches_list = []
            for dq in desig_queries:
                dq_lower = str(dq).lower().strip()
                p_desig = p["designation"].lower()
                single_match = False
                if dq_lower in p_desig:
                    single_match = True
                else:
                    query_words = re.findall(r"\b\w+\b", dq_lower)
                    p_words = re.findall(r"\b\w+\b", p_desig)
                    stemmed_p_words = {stem_word(pw) for pw in p_words}
                    if query_words and all(stem_word(qw) in stemmed_p_words for qw in query_words):
                        single_match = True
                matches_list.append(single_match)
                
            if desig_op == "and":
                if not all(matches_list):
                    match = False
            else:  # "or"
                if not any(matches_list):
                    match = False
                
        # 2. Band Filter (case-insensitive substring/normalized)
        if match and filters.get("band"):
            band_filter = filters["band"]
            band_queries = band_filter if isinstance(band_filter, list) else [band_filter]
            band_op = filters.get("band_operator", "or")
            
            matches_list = []
            for bq in band_queries:
                band_query_norm = normalize_val(bq)
                p_band = normalize_val(p.get("band"))
                p_cadre = normalize_val(p.get("cadre"))
                single_match = (band_query_norm in p_band) or (band_query_norm in p_cadre)
                matches_list.append(single_match)
                
            if band_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 3. Cadre Filter (case-insensitive substring/normalized)
        if match and filters.get("cadre"):
            cadre_filter = filters["cadre"]
            cadre_queries = cadre_filter if isinstance(cadre_filter, list) else [cadre_filter]
            cadre_op = filters.get("cadre_operator", "or")
            
            matches_list = []
            for cq in cadre_queries:
                cadre_query_norm = normalize_val(cq)
                p_band = normalize_val(p.get("band"))
                p_cadre = normalize_val(p.get("cadre"))
                single_match = (cadre_query_norm in p_cadre) or (cadre_query_norm in p_band)
                matches_list.append(single_match)
                
            if cadre_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 4. BU Filter (case-insensitive substring)
        if match and filters.get("bu"):
            bu_filter = filters["bu"]
            bu_queries = bu_filter if isinstance(bu_filter, list) else [bu_filter]
            bu_op = filters.get("bu_operator", "or")
            
            matches_list = []
            for buq in bu_queries:
                bu_query_clean = str(buq).lower().strip()
                single_match = bu_query_clean in p["bu"].lower()
                matches_list.append(single_match)
                
            if bu_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 5. SBG Filter (case-insensitive substring)
        if match and filters.get("sbg"):
            sbg_filter = filters["sbg"]
            sbg_queries = sbg_filter if isinstance(sbg_filter, list) else [sbg_filter]
            sbg_op = filters.get("sbg_operator", "or")
            
            matches_list = []
            for sbgq in sbg_queries:
                sbg_query_clean = str(sbgq).lower().strip()
                single_match = sbg_query_clean in p["sbg"].lower()
                matches_list.append(single_match)
                
            if sbg_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 6. Cluster Filter (case-insensitive substring/location, matches both Cluster and Job Name)
        # Often mapped as 'location' or 'cluster'
        cluster_query = filters.get("cluster") or filters.get("location")
        if match and cluster_query:
            cl_queries = cluster_query if isinstance(cluster_query, list) else [cluster_query]
            location_op = filters.get("location_operator", "or")
            
            matches_list = []
            for clq in cl_queries:
                cl_query_clean = str(clq).lower().strip()
                cluster_val = str(p.get("cluster", "")).lower()
                job_val = str(p.get("job_name", "")).lower()
                single_match = (cl_query_clean in cluster_val) or (cl_query_clean in job_val)
                matches_list.append(single_match)
                
            if location_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 7. Experience Filter (min/max years)
        if match and filters.get("experience_min") is not None:
            try:
                min_exp = float(filters["experience_min"])
                if p["total_exp"] < min_exp:
                    match = False
            except ValueError:
                pass
                
        if match and filters.get("experience_max") is not None:
            try:
                max_exp = float(filters["experience_max"])
                if p["total_exp"] > max_exp:
                    match = False
            except ValueError:
                pass
 
        # 8. Internal Experience Filter (min years or specific Org)
        if match and filters.get("internal_exp_min") is not None:
            try:
                min_int = float(filters["internal_exp_min"])
                if p["internal_exp_years"] < min_int:
                    match = False
            except ValueError:
                pass
                
        if match and filters.get("internal_org"):
            org_query = str(filters["internal_org"]).lower().strip()
            # Check if any internal experience matches the org
            org_match = any(org_query in exp.get("Org", "").lower() for exp in p["internal_experience"])
            if not org_match:
                match = False
 
        # 9. External Experience Filter (min years, specific Org or Designation)
        if match and filters.get("external_exp_min") is not None:
            try:
                min_ext = float(filters["external_exp_min"])
                if p["external_exp_years"] < min_ext:
                    match = False
            except ValueError:
                pass
                
        if match and filters.get("external_org"):
            org_query = str(filters["external_org"]).lower().strip()
            # Check if any external experience matches the org
            org_match = any(org_query in exp.get("Org", "").lower() for exp in p["external_experience"])
            if not org_match:
                match = False
 
        # 10. Certification Filter (case-insensitive contains, supporting AND/OR operators)
        if match and filters.get("certification"):
            cert_filter = filters["certification"]
            cert_queries = cert_filter if isinstance(cert_filter, list) else [cert_filter]
            cert_op = filters.get("certification_operator", "and")
            
            matches_list = []
            for cq in cert_queries:
                cq_clean = str(cq).lower().strip()
                single_match = any(normalize_val(cq_clean) in normalize_val(cert) for cert in p["certifications"])
                matches_list.append(single_match)
                
            if cert_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 11. Qualification Filter (case-insensitive description, supporting AND/OR operators)
        if match and filters.get("qualification"):
            qual_filter = filters["qualification"]
            qual_queries = qual_filter if isinstance(qual_filter, list) else [qual_filter]
            qual_op = filters.get("qualification_operator", "or")
            
            matches_list = []
            for qq in qual_queries:
                qq_clean = str(qq).lower().strip()
                single_match = any(normalize_val(qq_clean) in normalize_val(q["Description"]) for q in p["qualifications"])
                matches_list.append(single_match)
                
            if qual_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 12. Segment / Sub-Segment Filter (supporting AND/OR operators)
        if match and filters.get("segment"):
            seg_filter = filters["segment"]
            seg_queries = seg_filter if isinstance(seg_filter, list) else [seg_filter]
            seg_op = filters.get("segment_operator", "or")
            
            matches_list = []
            for sq in seg_queries:
                sq_clean = str(sq).lower().strip()
                single_match = any(
                    normalize_val(sq_clean) in normalize_val(s["Segment"]) or 
                    normalize_val(sq_clean) in normalize_val(s["Sub-Segment"]) 
                    for s in p["segment_exposure"]
                )
                matches_list.append(single_match)
                
            if seg_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        if match and filters.get("sub_segment"):
            sub_seg_query = str(filters["sub_segment"]).lower().strip()
            sub_seg_match = any(normalize_val(sub_seg_query) in normalize_val(s["Sub-Segment"]) for s in p["segment_exposure"])
            if not sub_seg_match:
                match = False
 
        # 13. Skill and Sub-Skill Filter (supporting AND/OR operators)
        if match and filters.get("skill"):
            sk_filter = filters["skill"]
            sk_queries = sk_filter if isinstance(sk_filter, list) else [sk_filter]
            skill_op = filters.get("skill_operator", "and")
            
            matches_list = []
            for skq in sk_queries:
                skq_clean = str(skq).lower().strip()
                single_match = any(
                    normalize_val(skq_clean) in normalize_val(s["Skill"]) or 
                    normalize_val(skq_clean) in normalize_val(s["Sub-Skill"]) 
                    for s in p["skills"]
                )
                matches_list.append(single_match)
                
            if skill_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        if match and filters.get("sub_skill"):
            sub_sk_query = str(filters["sub_skill"]).lower().strip()
            sub_sk_match = any(normalize_val(sub_sk_query) in normalize_val(s["Sub-Skill"]) for s in p["skills"])
            if not sub_sk_match:
                match = False
 
        # 14. Reviewed Proficiency Filter
        if match and filters.get("reviewed_proficiency"):
            prof_query = str(filters["reviewed_proficiency"]).lower().strip()
            # If the user wants 'reviewed proficiency only', they might mean ANY skill that has a reviewed proficiency,
            # or a specific proficiency level.
            if prof_query in ["yes", "true", "reviewed only", "reviewed"]:
                # Check if there is at least one skill with a non-empty reviewed proficiency
                prof_match = any(s.get("Reviewed_Proficiency") is not None and s.get("Reviewed_Proficiency") != "" for s in p["skills"])
            else:
                # Check for specific level (e.g. Expert) in reviewed proficiency
                prof_match = any(prof_query in str(s.get("Reviewed_Proficiency", "")).lower() for s in p["skills"])
            if not prof_match:
                match = False
 
        # 15. Core Skill Filter
        if match and filters.get("is_core_skill"):
            # Check if any skill is flagged as core
            core_match = any(s.get("Is_Core_Skill") == "Yes" for s in p["skills"])
            if not core_match:
                match = False
                
        if match:
            filtered.append(p)
            
    return filtered
