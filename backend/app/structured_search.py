import re
from typing import List, Dict, Any, Optional

NORMALIZE_RE = re.compile(r"[\s\-\.]")
WORD_RE = re.compile(r"\b\w+\b")
DESIGNATION_STOP_WORDS = {"in", "of", "for", "and", "or", "with"}

# Precompiled regular expressions for normalize_desig_abbreviations
PAREN_L_RE = re.compile(r"([^\s])\(")
PAREN_R_RE = re.compile(r"\)([^\s])")
DESIG_DOT_RE = re.compile(r"\b(asst|sr|jr|mgr|dgm|jgm)\.([a-zA-Z])")
HYPHEN_SPACE_RE = re.compile(r"([a-zA-Z])\-([a-zA-Z])")
ASST_RE = re.compile(r"\b(asst|assistant)\b\.?")
SR_RE = re.compile(r"\b(sr|senior)\b\.?")
JR_RE = re.compile(r"\b(jr|junior)\b\.?")
DGM_RE = re.compile(r"\bdgm\b")
JGM_RE = re.compile(r"\bjgm\b")
MGR_RE = re.compile(r"\bmgr\b")
MECH_RE = re.compile(r"\bmechanical\b")
ELEC_RE = re.compile(r"\belectrical\b")
IN_MECH_RE = re.compile(r"\bin\s+mech\b")
IN_ELEC_RE = re.compile(r"\bin\s+elec\b")
IN_CIVIL_RE = re.compile(r"\bin\s+civil\b")

def normalize_val(val: Any) -> str:
    if val is None:
        return ""
    return NORMALIZE_RE.sub("", str(val)).lower()

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

def normalize_desig_abbreviations(text: str) -> str:
    text = text.lower()
    # Insert space around parentheses if missing, e.g. "manager(finishes)" -> "manager (finishes)"
    text = PAREN_L_RE.sub(r"\1 (", text)
    text = PAREN_R_RE.sub(r") \1", text)
    
    # Normalize spaces after dot/hyphen first for designations
    text = DESIG_DOT_RE.sub(r"\1. \2", text)
    text = HYPHEN_SPACE_RE.sub(r"\1 - \2", text)
    
    # Replace abbreviations with standard forms
    text = ASST_RE.sub("assistant", text)
    text = SR_RE.sub("senior", text)
    text = JR_RE.sub("junior", text)
    text = DGM_RE.sub("deputy general manager", text)
    text = JGM_RE.sub("joint general manager", text)
    text = MGR_RE.sub("manager", text)
    
    # Map mechanical -> mech, electrical -> elec
    text = MECH_RE.sub("mech", text)
    text = ELEC_RE.sub("elec", text)
    
    # Map prepositions connecting designation to discipline
    text = IN_MECH_RE.sub(" (mech)", text)
    text = IN_ELEC_RE.sub(" (elec)", text)
    text = IN_CIVIL_RE.sub(" (civil)", text)
    return text





def check_modifier_match(query_text: str, target_desig: str) -> bool:
    query_norm = normalize_desig_abbreviations(query_text)
    target_norm = normalize_desig_abbreviations(target_desig)
    
    has_asst_query = "assistant" in query_norm
    has_sr_query = "senior" in query_norm
    
    if has_asst_query:
        if "assistant" not in target_norm:
            return False
            
    if has_sr_query:
        if "senior" not in target_norm:
            return False
            
    return True


CANONICAL_QUAL_MAP = {
    "dce": "dce",
    "diplomaincivilengineering": "dce",
    
    "ssc": "ssc",
    "secondaryschoolcertificate": "ssc",
    "secondaryschool": "ssc",
    
    "ba": "ba",
    "bachelorofarts": "ba",
    
    "hsc": "hsc",
    "highersecondarycertificate": "hsc",
    "highersecondary": "hsc",
    
    "be": "be",
    "bachelorofengineering": "be",
    
    "btech": "btech",
    "bacheloroftechnology": "btech",
    
    "mtech": "mtech",
    "masteroftechnology": "mtech",
    
    "mba": "mba",
    "masterofbusinessadministration": "mba",
    "mbabusinessadministration": "mba",
    
    "phd": "phd",
    "doctorofphilosophy": "phd",
    "doctorate": "phd",
    
    "me": "me",
    "masterofengineering": "me",
    
    "barch": "barch",
    "bachelorofarchitecture": "barch",
    
    "msc": "msc",
    "masterofscience": "msc",
    "masterofscienceinengineering": "msc",
    "mscengg": "msc",
    "mscengineering": "msc",
    
    "bsc": "bsc",
    "bachelorofscience": "bsc",
    "bachelorofscienceengineering": "bsc",
    "bscengg": "bsc",
    
    "mcom": "mcom",
    "masterofcommerce": "mcom",
    
    "bcom": "bcom",
    "bachelorofcommerce": "bcom",
    
    "llb": "llb",
    "bacheloroflaws": "llb",
    "bacheloroflaw": "llb",
    
    "llm": "llm",
    "masteroflaws": "llm",
    "masteroflaw": "llm",
    
    "dme": "dme",
    "diplomainmechanicalengineering": "dme",
    
    "deee": "deee",
    "dee": "deee",
    "diplomainelectricalandelectronicsengineering": "deee",
    "diplomainelectricalengineering": "deee",
    "diplomaelectricalandelectronics": "deee",
    "diplomaelectricalelectronics": "deee",
    
    "dct": "dct",
    "diplomainconstructiontechnology": "dct",
    
    "lce": "lce",
    "licentiateincivilengineering": "lce",
    
    "bca": "bca",
    "bachelorofcomputerapplication": "bca",
    "bachelorofcomputerapplications": "bca",
    
    "mbl": "mbl",
    "masterofbusinesslaw": "mbl",
    
    "pgdcm": "pgdcm",
    "postgraduatediplomainconstructionmanagement": "pgdcm",
    
    "pgpacm": "pgpacm",
    "postgraduateprograminadvancedconstructionmanagement": "pgpacm",
    "postgraduateprogrammeinadvancedconstructionmanagement": "pgpacm",
    
    "pgdbm": "pgdbm",
    "postgraduatediplomainbusinessmanagement": "pgdbm",
    
    "pgdhrm": "pgdhrm",
    "postgraduatediplomainhumanresourcemanagement": "pgdhrm",
    
    "pgdpm": "pgdpm",
    "postgraduatediplomainprojectmanagement": "pgdpm",
    
    "pgppm": "pgppm",
    "postgraduateprograminprojectmanagement": "pgppm",
    "postgraduateprogrammeinprojectmanagement": "pgppm",
    
    "pgppem": "pgppem",
    "postgraduateprogrammeinprojectengineeringandmanagement": "pgppem",
    
    "pgpifdm": "pgpifdm",
    "postgraduateprogrammeininfrastructurefinancedevelopmentmanagement": "pgpifdm",
    
    "pgpqscm": "pgpqscm",
    "postgraduateprogrammeinquantitysurveyingandcontractmanagement": "pgpqscm",
    
    # ITI and trade qualifications
    "itifitter": "iti fitter",
    "fitter": "iti fitter",
    "itisurveyor": "iti surveyor",
    "ititradecertificate": "iti trade certificate",
    "itielectrician": "iti electrician",
    "itimotormechanic": "iti motor mechanic",
    "itimason": "iti mason",
    "itidraughtsman": "iti draughtsman",
    "itidraughtsmancivil": "iti draughtsman",
}


def qual_token_match(query_term: str, description: str) -> bool:
    """
    Checks if a qualification term matches a description using TOKEN-LEVEL comparison,
    supporting stripping parentheses/punctuation, alias mapping, and splitting compound tokens.
    """
    q_norm = normalize_val(query_term)
    if not q_norm:
        return False
        
    q_canon = CANONICAL_QUAL_MAP.get(q_norm, q_norm)
    
    # 1. Check full description canonical match first
    desc_norm = normalize_val(description)
    desc_canon = CANONICAL_QUAL_MAP.get(desc_norm, desc_norm)
    if desc_canon == q_canon:
        return True
        
    # 2. Check token-level match
    # Split description by whitespace
    for word in description.lower().split():
        # Strip parentheses, brackets, and other common punctuation from the token first
        word_clean = word.strip("()[]{}.,;:?!\"'")
        # Split token by hyphens and slashes (e.g. "mtech-construction" -> ["mtech", "construction"])
        sub_words = re.split(r"[\-/]", word_clean)
        for sw in sub_words:
            sw_norm = normalize_val(sw)
            sw_canon = CANONICAL_QUAL_MAP.get(sw_norm, sw_norm)
            if sw_canon == q_canon or sw_norm == q_norm:
                return True
    return False


def prof_match_record(s: Dict[str, Any], prof_query: str) -> bool:
    rp = s.get("Reviewed_Proficiency")
    if not rp:
        return False
    rp_lower = str(rp).lower().strip()
    if not rp_lower:
        return False
    if prof_query in ["yes", "true", "reviewed only", "reviewed"]:
        return True
    return prof_query in rp_lower


def skill_match_record(s: Dict[str, Any], query_val: str, check_sub_only: bool, prof_query: Optional[str]) -> bool:
    query_val_norm = normalize_val(query_val)
    if not query_val_norm:
        return False
    
    # Check skill name match
    name_match = False
    if check_sub_only:
        name_match = query_val_norm in normalize_val(s.get("Sub-Skill"))
    else:
        name_match = (query_val_norm in normalize_val(s.get("Skill"))) or (query_val_norm in normalize_val(s.get("Sub-Skill")))
        
    if not name_match:
        return False
        
    # If prof_query is provided, we must also match the proficiency on the same record
    if prof_query:
        return prof_match_record(s, prof_query)
        
    return True


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
                
                # Normalize spaces and abbreviations for both to match reliably
                dq_norm = normalize_desig_abbreviations(dq_lower)
                p_desig_norm = normalize_desig_abbreviations(p_desig)
                
                single_match = False
                if dq_norm in p_desig_norm:
                    single_match = True
                else:
                    query_words = [qw for qw in WORD_RE.findall(dq_norm) if qw not in DESIGNATION_STOP_WORDS]
                    p_words = WORD_RE.findall(p_desig_norm)
                    stemmed_p_words = {stem_word(pw) for pw in p_words}
                    if query_words and all(stem_word(qw) in stemmed_p_words for qw in query_words):
                        single_match = True
                        
                # Apply modifier constraints (asst / sr)
                if single_match:
                    query_text = str(filters.get("skills_text") or filters.get("original_query") or "").lower()
                    if not check_modifier_match(query_text, p["designation"]):
                        single_match = False
                        
                matches_list.append(single_match)
                
            if desig_op == "and":
                if not all(matches_list):
                    match = False
            else:  # "or"
                if not any(matches_list):
                    match = False
                
        # 1b. External Designation Filter (case-insensitive substring and token-based fallback on external experience)
        if match and filters.get("external_designation"):
            ext_desig_filter = filters["external_designation"]
            ext_desig_queries = ext_desig_filter if isinstance(ext_desig_filter, list) else [ext_desig_filter]
            ext_desig_op = filters.get("external_designation_operator", "or")
            
            matches_list = []
            for edq in ext_desig_queries:
                edq_lower = str(edq).lower().strip()
                single_match = False
                for exp in p.get("external_experience", []):
                    exp_desig = str(exp.get("Designation", "")).lower()
                    
                    # Normalize spaces and abbreviations
                    edq_norm = normalize_desig_abbreviations(edq_lower)
                    exp_desig_norm = normalize_desig_abbreviations(exp_desig)
                    
                    sub_match = False
                    if edq_norm in exp_desig_norm:
                        sub_match = True
                    else:
                        query_words = [qw for qw in WORD_RE.findall(edq_norm) if qw not in DESIGNATION_STOP_WORDS]
                        p_words = WORD_RE.findall(exp_desig_norm)
                        stemmed_p_words = {stem_word(pw) for pw in p_words}
                        if query_words and all(stem_word(qw) in stemmed_p_words for qw in query_words):
                            sub_match = True
                            
                    # Apply modifier constraints to external experience designation
                    if sub_match:
                        query_text = str(filters.get("skills_text") or filters.get("original_query") or "").lower()
                        if not check_modifier_match(query_text, exp_desig):
                            sub_match = False
                            
                    if sub_match:
                        single_match = True
                        break
                matches_list.append(single_match)
                
            if ext_desig_op == "and":
                if not all(matches_list):
                    match = False
            else:  # "or"
                if not any(matches_list):
                    match = False

        # 1c. Department Filter (case-insensitive substring/equality match on extracted department)
        if match and filters.get("department"):
            dept_filter = filters["department"]
            dept_queries = dept_filter if isinstance(dept_filter, list) else [dept_filter]
            dept_op = filters.get("department_operator", "or")
            
            dept_map = {
                "CIVIL": "CIVIL",
                "MECHANICAL": "MECH",
                "MECH": "MECH",
                "ELECTRICAL": "ELEC",
                "ELEC": "ELEC",
                "QUALITY": "QUALITY",
                "QUALITY CONTROL": "QA/QC",
                "QUALITY ASSURANCE": "QA/QC",
                "QA/QC": "QA/QC",
                "QA": "QA/QC",
                "QC": "QA/QC",
                "QA & QC": "QA/QC",
                "QA&QC": "QA/QC",
                "QA/ QC": "QA/QC",
            }
            
            matches_list = []
            for dq in dept_queries:
                dq_norm = str(dq).upper().strip()
                dq_mapped = dept_map.get(dq_norm, dq_norm)
                p_dept = str(p.get("department", "")).upper()
                
                if dq_mapped == "QUALITY":
                    # General Quality query matches both QUALITY and QA/QC departments
                    single_match = (p_dept == "QUALITY") or (p_dept == "QA/QC")
                else:
                    single_match = (dq_mapped == p_dept) or (dq_mapped in p_dept)
                matches_list.append(single_match)
                
            if dept_op == "and":
                if not all(matches_list):
                    match = False
            else:  # "or"
                if not any(matches_list):
                    match = False

        # 1d. Exclude Department Filter (case-insensitive substring/equality match on extracted department)
        if match and filters.get("exclude_department"):
            ex_dept_filter = filters["exclude_department"]
            ex_dept_queries = ex_dept_filter if isinstance(ex_dept_filter, list) else [ex_dept_filter]
            ex_dept_op = filters.get("exclude_department_operator", "or")
            
            dept_map = {
                "CIVIL": "CIVIL",
                "MECHANICAL": "MECH",
                "MECH": "MECH",
                "ELECTRICAL": "ELEC",
                "ELEC": "ELEC",
                "QUALITY": "QUALITY",
                "QUALITY CONTROL": "QA/QC",
                "QUALITY ASSURANCE": "QA/QC",
                "QA/QC": "QA/QC",
                "QA": "QA/QC",
                "QC": "QA/QC",
                "QA & QC": "QA/QC",
                "QA&QC": "QA/QC",
                "QA/ QC": "QA/QC",
            }
            
            matches_list = []
            for eq in ex_dept_queries:
                eq_norm = str(eq).upper().strip()
                eq_mapped = dept_map.get(eq_norm, eq_norm)
                p_dept = str(p.get("department", "")).upper()
                
                # Check if employee belongs to this excluded department
                if eq_mapped == "QUALITY":
                    is_in_ex_dept = (p_dept == "QUALITY") or (p_dept == "QA/QC")
                else:
                    is_in_ex_dept = (eq_mapped == p_dept) or (eq_mapped in p_dept)
                matches_list.append(is_in_ex_dept)
                
            # If the employee belongs to any of the excluded departments, exclude them
            if any(matches_list):
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
                
        # 4. BU Filter — keyword-based match (each filter word must appear in p["bu"])
        if match and filters.get("bu"):
            bu_filter = filters["bu"]
            bu_queries = bu_filter if isinstance(bu_filter, list) else [bu_filter]
            bu_op = filters.get("bu_operator", "or")
            
            matches_list = []
            for buq in bu_queries:
                bu_query_clean = NORMALIZE_RE.sub("", str(buq).lower().strip())
                profile_bu_norm = NORMALIZE_RE.sub("", p["bu"].lower()) if p.get("bu") else ""
                # Canonical exact match (after stripping spaces/dashes/dots)
                single_match = bu_query_clean in profile_bu_norm
                matches_list.append(single_match)
                
            if bu_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        # 5. SBG Filter — keyword-based match
        if match and filters.get("sbg"):
            sbg_filter = filters["sbg"]
            sbg_queries = sbg_filter if isinstance(sbg_filter, list) else [sbg_filter]
            sbg_op = filters.get("sbg_operator", "or")
            
            matches_list = []
            for sbgq in sbg_queries:
                sbg_query_norm = NORMALIZE_RE.sub("", str(sbgq).lower().strip())
                profile_sbg_norm = NORMALIZE_RE.sub("", p["sbg"].lower()) if p.get("sbg") else ""
                # Canonical exact match after normalisation
                single_match = sbg_query_norm in profile_sbg_norm
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

        # 10b. Certification Groups Filter: [(A OR B) AND (C OR D)] logic
        # Each inner list is OR'd; outer list groups are AND'd.
        if match and filters.get("certification_groups"):
            for group in filters["certification_groups"]:
                group_match = any(
                    any(normalize_val(str(g).lower().strip()) in normalize_val(cert) for cert in p["certifications"])
                    for g in group
                )
                if not group_match:
                    match = False
                    break

        # 11. Qualification Filter — token-level matching to prevent short abbreviations
        # (e.g. 'me' for M.E.) from falsely matching inside longer words ('Mechanical').
        if match and filters.get("qualification"):
            qual_filter = filters["qualification"]
            qual_queries = qual_filter if isinstance(qual_filter, list) else [qual_filter]
            qual_op = filters.get("qualification_operator", "or")

            matches_list = []
            for qq in qual_queries:
                qq_clean = str(qq).lower().strip()
                single_match = any(qual_token_match(qq_clean, q["Description"]) for q in p["qualifications"])
                matches_list.append(single_match)

            if qual_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False

        # 11b. Qualification Groups Filter: [(A OR B) AND (C OR D)] logic
        # Each inner list is OR'd; outer list groups are AND'd.
        # Uses token-level matching to avoid short-abbreviation false positives.
        if match and filters.get("qualification_groups"):
            for group in filters["qualification_groups"]:
                group_match = any(
                    any(qual_token_match(str(g).lower().strip(), q["Description"]) for q in p["qualifications"])
                    for g in group
                )
                if not group_match:
                    match = False
                    break

                
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
 
        # 13. Skill and Sub-Skill Filter (supporting AND/OR operators, linked with Reviewed Proficiency if present)
        # NOTE: When skill_requirements is present, it supersedes the legacy skill/sub_skill filters
        # because skill_requirements uses per-group OR logic (alias expansions) rather than flat AND.
        prof_query = filters.get("reviewed_proficiency")
        prof_query_clean = str(prof_query).lower().strip() if prof_query else None
        _use_legacy_skill_filter = not filters.get("skill_requirements")

        if match and _use_legacy_skill_filter and filters.get("skill"):
            sk_filter = filters["skill"]
            sk_queries = sk_filter if isinstance(sk_filter, list) else [sk_filter]
            skill_op = filters.get("skill_operator", "and")
            
            matches_list = []
            for skq in sk_queries:
                single_match = any(
                    skill_match_record(s, skq, check_sub_only=False, prof_query=prof_query_clean)
                    for s in p["skills"]
                )
                matches_list.append(single_match)
                
            if skill_op == "and":
                if not all(matches_list):
                    match = False
            else:
                if not any(matches_list):
                    match = False
                
        if match and _use_legacy_skill_filter and filters.get("sub_skill"):
            sub_sk_filter = filters["sub_skill"]
            sub_sk_queries = sub_sk_filter if isinstance(sub_sk_filter, list) else [sub_sk_filter]
            sub_sk_op = filters.get("sub_skill_operator", "or")
            
            matches_list = []
            for sub_skq in sub_sk_queries:
                single_match = any(
                    skill_match_record(s, sub_skq, check_sub_only=True, prof_query=prof_query_clean)
                    for s in p["skills"]
                )
                matches_list.append(single_match)
                
            if sub_sk_op == "and":
                if not all(matches_list):
                    match = False
            else:  # "or"
                if not any(matches_list):
                    match = False
  
        # 14. Reviewed Proficiency Filter (run only if not already evaluated as part of skill/sub_skill)
        if match and filters.get("reviewed_proficiency"):
            if not filters.get("skill") and not filters.get("sub_skill"):
                prof_query_val = str(filters["reviewed_proficiency"]).lower().strip()
                if prof_query_val in ["yes", "true", "reviewed only", "reviewed"]:
                    prof_match = any(s.get("Reviewed_Proficiency") is not None and s.get("Reviewed_Proficiency") != "" for s in p["skills"])
                else:
                    prof_match = any(prof_query_val in str(s.get("Reviewed_Proficiency", "")).lower() for s in p["skills"])
                if not prof_match:
                    match = False
 
        # 15. Core Skill Filter
        if match and filters.get("is_core_skill"):
            # Check if any skill is flagged as core
            core_match = any(s.get("Is_Core_Skill") == "Yes" for s in p["skills"])
            if not core_match:
                match = False
                
        # 16. Skill Requirements Filter
        if match and filters.get("skill_requirements"):
            reqs = filters["skill_requirements"]
            for req in reqs:
                # Support new `skills` list (OR-group of alias expansions) and legacy `skill` string
                req_skill_list = req.get("skills") or ([req.get("skill")] if req.get("skill") else [])
                req_profs = req.get("proficiency")
                req_op = req.get("operator", "or")
                
                # Employee must match ANY skill in the group (OR across alias expansions)
                # and satisfy the proficiency constraint for that matched skill record
                has_matching_skill = False
                for req_skill in req_skill_list:
                    if has_matching_skill:
                        break
                    for s in p.get("skills", []):
                        # Check skill name match
                        if skill_match_record(s, req_skill, check_sub_only=False, prof_query=None):
                            # If proficiencies are specified, we must match them
                            if req_profs:
                                prof_matches = [
                                    prof_match_record(s, p_level.lower().strip())
                                    for p_level in req_profs
                                ]
                                if req_op == "and":
                                    if all(prof_matches):
                                        has_matching_skill = True
                                        break
                                else: # "or"
                                    if any(prof_matches):
                                        has_matching_skill = True
                                        break
                            else:
                                # No proficiency constraint, matching the skill name is enough
                                has_matching_skill = True
                                break
                            
                if not has_matching_skill:
                    match = False
                    break

        if match:
            filtered.append(p)
            
    return filtered
