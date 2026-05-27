import pandas as pd
from typing import Dict, List, Any

def build_employee_profiles(cleaned_dfs: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """
    Join all 8 sheets on 'PS No' and build unified employee knowledge profiles.
    Also generates a rich text representation of the profile for semantic search.
    """
    staff_df = cleaned_dfs["Staff_Master"]
    internal_df = cleaned_dfs["Internal_Exp"]
    external_df = cleaned_dfs["External_Exp"]
    segment_df = cleaned_dfs["Segment_Exposure"]
    skills_df = cleaned_dfs["Skill_Proficiency"]
    job_map_df = cleaned_dfs["Job_Skill_Mapping"]
    cert_df = cleaned_dfs["Certification"]
    qual_df = cleaned_dfs["Qualification"]

    # 1. Group relational tables by 'PS No' for quick lookup
    # Helper to convert a dataframe to a dictionary of records grouped by PS No
    def get_grouped_records(df: pd.DataFrame) -> Dict[int, List[Dict[str, Any]]]:
        grouped = {}
        for ps, group in df.groupby("PS No"):
            records = group.drop(columns=["PS No"], errors="ignore").to_dict(orient="records")
            # Strip PS No from nested structures if present
            grouped[int(ps)] = records
        return grouped

    internal_grouped = get_grouped_records(internal_df)
    external_grouped = get_grouped_records(external_df)
    segment_grouped = get_grouped_records(segment_df)
    skills_grouped = get_grouped_records(skills_df)
    job_map_grouped = get_grouped_records(job_map_df)
    
    # Certifications grouped as a list of strings
    cert_grouped = {}
    for ps, group in cert_df.groupby("PS No"):
        cert_grouped[int(ps)] = group["Certification"].dropna().tolist()
        
    qual_grouped = get_grouped_records(qual_df)

    # 2. Iterate Staff Master and assemble profiles
    profiles = []
    for _, row in staff_df.iterrows():
        ps_no = int(row["PS No"])
        
        # Pull grouped records or return default empty list
        internal_exp = internal_grouped.get(ps_no, [])
        external_exp = external_grouped.get(ps_no, [])
        segments = segment_grouped.get(ps_no, [])
        skills = skills_grouped.get(ps_no, [])
        job_mappings = job_map_grouped.get(ps_no, [])
        certifications = cert_grouped.get(ps_no, [])
        qualifications = qual_grouped.get(ps_no, [])
        
        # Build unified record
        profile = {
            "ps_no": ps_no,
            "staff_name": row["Staff Name"],
            "email_id": row["Email ID"],
            "mobile": row["Mobile"],
            "cadre": row["Cadre"],
            "band": row["Band"],
            "designation": row["Designation"],
            "total_exp": float(row["Total Exp"]),
            "internal_exp_years": float(row["Internal Exp"]),
            "external_exp_years": float(row["External Exp"]),
            "job_code": row["Job Code"],
            "job_name": row["Job Name"],
            "cluster": row["Cluster"],
            "bu": row["BU"],
            "sbg": row["SBG"],
            "manager": {
                "ps_no": int(row["IS PS No"]) if pd.notna(row["IS PS No"]) else None,
                "name": row["IS Name"],
                "email_id": row["IS Email ID"]
            },
            "internal_experience": internal_exp,
            "external_experience": external_exp,
            "segment_exposure": segments,
            "skills": skills,
            "job_skill_mappings": job_mappings,
            "certifications": certifications,
            "qualifications": qualifications,
        }
        
        # 3. Generate Semantic Text Summary for this profile
        profile["semantic_text"] = _generate_semantic_summary(profile)
        profiles.append(profile)
        
    return profiles

def _generate_semantic_summary(profile: Dict[str, Any]) -> str:
    """
    Builds a rich, descriptive string representing the entire employee profile.
    This string is vectorized for semantic vector search.
    """
    parts = []
    
    # Name and Role info
    parts.append(f"Name: {profile['staff_name']}.")
    parts.append(f"Designation: {profile['designation']}.")
    parts.append(f"Cadre: {profile['cadre']}. Band: {profile['band']}.")
    parts.append(f"BU: {profile['bu']}. SBG: {profile['sbg']}. Cluster: {profile['cluster']}.")
    parts.append(f"Total Experience: {profile['total_exp']} years (Internal: {profile['internal_exp_years']} years, External: {profile['external_exp_years']} years).")
    
    # Skills
    if profile["skills"]:
        skill_strings = []
        for s in profile["skills"]:
            skill_info = f"{s['Skill']} - {s['Sub-Skill']}"
            if s.get("Reviewed_Proficiency"):
                skill_info += f" ({s['Reviewed_Proficiency']} Proficiency)"
            elif s.get("User_Declared_Proficiency"):
                skill_info += f" ({s['User_Declared_Proficiency']} Declared)"
            if s.get("Is_Core_Skill") == "Yes":
                skill_info += " [Core Skill]"
            skill_strings.append(skill_info)
        parts.append("Skills: " + ", ".join(skill_strings) + ".")
        
    # Segment Exposure
    if profile["segment_exposure"]:
        seg_strings = [f"{seg['Segment']} ({seg['Sub-Segment']})" for seg in profile["segment_exposure"]]
        parts.append("Segment Exposure: " + ", ".join(seg_strings) + ".")
        
    # Certifications
    if profile["certifications"]:
        parts.append("Certifications: " + ", ".join(profile["certifications"]) + ".")
        
    # Qualifications
    if profile["qualifications"]:
        qual_strings = [f"{q['Description']} ({q['Year']})" for q in profile["qualifications"]]
        parts.append("Qualifications: " + ", ".join(qual_strings) + ".")
        
    # Internal projects/orgs
    if profile["internal_experience"]:
        internal_orgs = list(set([exp["Org"] for exp in profile["internal_experience"] if exp.get("Org")]))
        parts.append("Internal Project Experience: " + ", ".join(internal_orgs) + ".")
        
    # External companies/orgs
    if profile["external_experience"]:
        ext_strings = []
        for exp in profile["external_experience"]:
            entry = exp["Org"]
            if exp.get("Designation"):
                entry += f" as {exp['Designation']}"
            ext_strings.append(entry)
        parts.append("External Work History: " + ", ".join(ext_strings) + ".")
        
    return " ".join(parts)
