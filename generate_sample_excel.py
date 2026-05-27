"""
generate_sample_excel.py
Generates a realistic, synthetic relational Excel workbook for the enterprise workforce intelligence chatbot.
Output: synthetic_skill_dataset.xlsx
"""

import os
import random
import datetime
import numpy as np
import pandas as pd
from faker import Faker

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)
Faker.seed(42)

fake = Faker('en_IN')  # Use Indian names/details where supported

# ─── Configuration ────────────────────────────────────────────────────────────
NUM_EMPLOYEES = 1000

# ─── Keyword Banks ────────────────────────────────────────────────────────────
CADRES = [
    "S2", "M2-B", "M1-A", "O2", "M2-C", "M1-C", "TC3", "M1-B", "O1", "TC7", "TC8",
    "FTC", "M2-A", "M3-A", "S1", "M3-C", "TC10", "M3-B", "TC5", "TC2", "TC9", "TC6",
    "TC4", "M4-A", "M4-B", "TC11"
]

BANDS = [
    "S - Band", "Tier 2", "Tier 1", "E - Band", "E Band", "Non Sup", "Temp",
    "Tier 3", "FTC", "S Band", "TC", "Tier 4 & Above"
]

DESIGNATIONS = [
    "SITE ENGINEER", "PROJECT MANAGER", "CIVIL ENGINEER", "ELECTRICAL ENGINEER",
    "MECHANICAL ENGINEER", "CONSTRUCTION MANAGER", "SENIOR MANAGER - PROJECTS",
    "SR.ENGINEER", "DESIGN ENGINEER", "PLANNING ENGINEER", "GET",
    "GRADUATE ENGINEER TRAINEE", "ASSISTANT MANAGER", "DEPUTY GENERAL MANAGER",
    "GENERAL MANAGER", "STRUCTURAL ENGINEER", "QA/QC ENGINEER", "SAFETY ENGINEER",
    "ESTIMATION ENGINEER", "BILLING ENGINEER", "QUANTITY SURVEYOR", "SURVEYOR",
    "FOREMAN", "CAD ENGINEER", "SYSTEM ADMINISTRATOR", "EHS OFFICER",
    "GEOTECHNICAL ENGINEER", "COMMERCIAL MANAGER"
]

EXTERNAL_DESIGNATIONS = [
    "SITE SUPERVISOR", "SITE ENGINEER", "ASSISTANT ENGINEER", "CONSTRUCTION ENGINEER",
    "ENGINEERING ASST", "JR. SUPERVISOR", "ENGINEER", "DESIGN ENGINEER",
    "ASST.MANAGER (MECH)", "DRAUGHTSMAN", "ENGINEER - PLANNING", "SITE INCHARGE",
    "SUPERVISOR (CIVIL)", "JUNIOR ENGINEER", "BILLING ENGINEER", "FOREMAN (CIVIL)",
    "PROJECT ENGINEER", "PROJECT MANAGER", "CONSTRUCTION MANAGER", "CIVIL ENGINEER",
    "QUANTITY SURVEYOR", "QC ENGINEER", "LAND SURVEYOR", "ERECTION ENGINEER",
    "FOREMAN - ERECTION", "QA/QC ENGINEER", "TECHNICAL ASSISTANT"
]

BUS = [
    "Water & Effluent Treatment",
    "Transportation Infrastructure",
    "Buildings & Factories",
    "Heavy Civil Infrastructure",
    "Power Transmission & Distribution",
    "Metallurgical & Material Handling",
    "Smart World & Communication",
    "L&T GeoStructure"
]

SBGS = [
    "WET SBG", "TI SBG", "B&F SBG", "HCI SBG", "PT&D SBG", "MMH SBG", "SWC SBG", "LTGS SBG"
]

CLUSTERS = [
    "Mumbai", "Chennai", "Bangalore", "Delhi", "Kolkata", "Oman", "Qatar", "Saudi",
    "Mauritius", "UAE", "Noida", "Lucknow", "Ahmedabad", "Hyderabad", "Pune"
]

INTERNAL_ORGS = [
    "LE110120 - RB&F SBG - KOLKATA CLUSTER",
    "LE191024 - CIDCO Kharkopar",
    "LE180988 - BIAL T2",
    "LE200450 - Riyadh Metro Project",
    "LE210890 - Mumbai Coastal Road",
    "LE220112 - Delhi Meerut RRTS",
    "LE230987 - Chennai Metro Phase II",
    "LE240567 - Bullet Train C4 Package",
    "LE200119 - Vizag Water Supply Phase 1",
    "LE211234 - Bangalore High Rise Residential",
    "LE220389 - Mumbai Trans Harbour Link",
    "LE230491 - Oman Salalah Water Pipeline",
    "LE220911 - Delhi Airport Expansion T1",
    "LE230811 - Khavda Solar Power Evacuation",
    "LE240102 - Bihar Ganga Bridge Project"
]

EXTERNAL_ORGS = [
    "M/S.G.SREE RAMAMURTHY CONSTN.VIZAG",
    "M/S.JMC PROJECTS LTD",
    "SHAPOORJI PALLONJI",
    "PETRON ENGINEERING",
    "AFCONS INFRASTRUCTURE",
    "TATA PROJECTS",
    "GAMMON INDIA",
    "NCC LIMITED",
    "DILIP BUILDCON",
    "SIMPLEX INFRASTRUCTURES",
    "L&T INFRA",
    "SOMA ENTERPRISE"
]

SEGMENTS_MAP = {
    "Metro & Tunneling": ["Underground Metro", "Elevated Metro", "TBM Tunneling", "NATM Tunneling", "Underground Station"],
    "Water Infrastructure": ["Water Treatment Plant", "Wastewater Network", "Lift Irrigation", "Industrial Water Supply", "Desalination Plant"],
    "Buildings & Factories": ["High-rise Residential", "IT Parks", "Hospitals", "Airports", "Data Centers", "Automobile Factories"],
    "Roads & Runways": ["National Highways", "Expressways", "Airport Runways", "Elevated Corridors", "Toll Plazas"],
    "Heavy Civil & Hydro": ["Nuclear Power Plants", "Ports & Harbours", "Hydel Power", "Bridges & Flyovers", "Special Bridges"],
    "Power Transmission": ["Substations", "Transmission Lines", "Monopoles", "GIS Substations", "Underground Cabling"]
}

SKILLS_MAP = {
    "Civil Engineering": ["Structural Design", "Concrete Technology", "Geotechnical Engineering", "AutoCAD", "STAAD Pro", "Revit", "Foundation Design", "RCC Design", "Formwork Systems"],
    "Project Management": ["Project Scheduling", "PMP", "Agile", "Risk Management", "Cost Estimation", "Contract Administration", "MS Project", "Primavera P6", "Billing & Invoicing"],
    "Electrical Engineering": ["Power Systems", "Substation Design", "Lighting Systems", "SCADA", "Cabling", "HVAC Controls", "Electrical Safety", "Relay Coordination"],
    "Mechanical Engineering": ["HVAC Design", "Piping Engineering", "Fire Fighting Systems", "Plumbing Design", "Pumps & Valves", "Alignment & Erection", "Boiler Erection"],
    "Digital & IT": ["Python", "FastAPI", "Docker", "PostgreSQL", "React", "TypeScript", "Vite", "Kubernetes", "AWS", "Machine Learning", "NLP", "BIM Modeling"]
}

PROFICIENCIES = ["Basic", "Functional", "Proficient", "Expert", "Role Model"]

CERTIFICATIONS = [
    "PMP (Project Management Professional)",
    "IPMA Level C",
    "IPMA Level D",
    "LEED AP (Accredited Professional)",
    "IGBC AP",
    "Primavera P6 Certification",
    "AWS Certified Solutions Architect",
    "ASME Section IX Welding Certification",
    "Chartered Engineer (Ceng)",
    "NEBOSH IGC Safety Certification",
    "ASNT Level II NDT",
    "BIM Professional Certification"
]

QUALIFICATIONS = [
    "B.Tech in Civil Engineering",
    "M.Tech in Structural Engineering",
    "B.E. in Mechanical Engineering",
    "B.E. in Electrical Engineering",
    "MBA in Project Management",
    "Diploma in Civil Engineering",
    "M.Tech in Geotechnical Engineering",
    "Ph.D. in Concrete Materials",
    "B.Arch in Architecture",
    "M.Tech in Construction Technology & Management",
    "B.E. in Electronics & Instrumentation",
    "Diploma in Mechanical Engineering"
]

ROLE_DEPLOYMENTS = [
    "Trainee & Equivalent",
    "Supervisory (S:Band) & Equivalent",
    "Tier 1 & Equivalent",
    "Tier 2 & Equivalent",
    "Executive (E:Band) & Equivalent",
    "Technician Band & Equivalent",
    "Contract & Equivalent",
    "Tier 3 & Equivalent"
]

REPORTING_COUNTS = [
    "0", "1", "2", "5", "10", "15", "20", "30", "50", "100", "200", "300",
    "nil", "NA", "varies", "lot", "3 to 12", "5-6", ">75"
]

# ─── Helper Functions ─────────────────────────────────────────────────────────

def random_date_range(years_back_start, duration_years):
    """Generate a start date and an end date based on years ago and duration."""
    start_days_ago = int(years_back_start * 365)
    duration_days = int(duration_years * 365)
    
    start_date = datetime.date.today() - datetime.timedelta(days=start_days_ago)
    end_date = start_date + datetime.timedelta(days=duration_days)
    
    # Format to DD-MM-YYYY
    return start_date.strftime("%d-%m-%Y"), end_date.strftime("%d-%m-%Y")


# ─── Data Generation ──────────────────────────────────────────────────────────

print("Generating synthetic relational workforce dataset...")

# Step 1: Generate Staff Master
staff_master_rows = []
internal_exp_rows = []
external_exp_rows = []
segment_exposure_rows = []
skill_proficiency_rows = []
job_skill_mapping_rows = []
certification_rows = []
qualification_rows = []

used_ps_nos = set()

# Pre-generate some supervisors to assign realistically
supervisors = []
for _ in range(50):
    sup_ps = random.randint(20000, 99999)
    sup_name = fake.name_male() if random.random() > 0.3 else fake.name_female()
    supervisors.append((sup_ps, sup_name))

for i in range(NUM_EMPLOYEES):
    # Unique PS No
    ps_no = random.randint(10000, 99999)
    while ps_no in used_ps_nos:
        ps_no = random.randint(10000, 99999)
    used_ps_nos.add(ps_no)
    
    # Staff Name
    gender_is_male = random.random() > 0.25
    staff_name = fake.name_male() if gender_is_male else fake.name_female()
    
    # Email
    email_id = f"{ps_no}@lntecc.com"
    
    # Mobile
    mobile = "".join([str(random.randint(0, 9)) for _ in range(10)])
    if mobile.startswith("0"):
        mobile = "9" + mobile[1:]  # Start with valid mobile prefix
    mobile = int(mobile)
        
    # Cadre & Band
    cadre = random.choice(CADRES)
    band = random.choice(BANDS)
    
    # Designation
    designation = random.choice(DESIGNATIONS)
    
    # Job Code / Name
    job_code = f"LE{random.randint(100000, 999999)}"
    job_name = job_code
    
    # Cluster, BU, SBG
    cluster = random.choice(CLUSTERS)
    bu = random.choice(BUS)
    sbg = random.choice(SBGS)
    
    # Supervisor
    is_ps, is_name = random.choice(supervisors)
    is_email = f"{is_ps}@lntecc.com"
    
    # Experience (Total, Internal, External)
    # Junior designations have less exp, senior have more
    if any(keyword in designation for keyword in ["GET", "TRAINEE", "GET", "SURVEYOR", "FOREMAN"]):
        # Junior
        external_exp = round(random.uniform(0.0, 3.0), 2)
        internal_exp = round(random.uniform(3.83, 6.0), 2)
    elif any(keyword in designation for keyword in ["MANAGER", "DGM", "GENERAL MANAGER", "SENIOR MANAGER"]):
        # Senior
        external_exp = round(random.uniform(2.0, 20.0), 2)
        internal_exp = round(random.uniform(10.0, 30.0), 2)
    else:
        # Mid
        external_exp = round(random.uniform(0.0, 10.0), 2)
        internal_exp = round(random.uniform(4.0, 15.0), 2)
        
    total_exp = round(internal_exp + external_exp + random.uniform(-0.1, 0.1), 2)
    total_exp = max(3.83, total_exp)  # Total exp min is 3.83 as per constraint
    
    staff_master_rows.append({
        "PS No": ps_no,
        "Staff Name": staff_name,
        "Email ID": email_id,
        "Mobile": mobile,
        "Cadre": cadre,
        "Band": band,
        "Designation": designation,
        "Total Exp": total_exp,
        "Internal Exp": internal_exp,
        "External Exp": external_exp,
        "Job Code": job_code,
        "Job Name": job_name,
        "Cluster": cluster,
        "BU": bu,
        "SBG": sbg,
        "IS PS No": is_ps,
        "IS Name": is_name,
        "IS Email ID": is_email
    })
    
    # --- Internal Exp Sheet ---
    # Number of internal postings correlates with internal experience duration
    num_internal = max(1, int(internal_exp / 4))
    remaining_years = internal_exp
    current_years_ago = internal_exp
    
    for idx in range(num_internal):
        org = random.choice(INTERNAL_ORGS)
        duration = round(random.uniform(1.0, max(2.0, remaining_years)), 2)
        if idx == num_internal - 1:
            duration = round(remaining_years, 2)
        
        if duration > 0.1:
            frm, to = random_date_range(current_years_ago, duration)
            internal_exp_rows.append({
                "PS No": ps_no,
                "Org": org,
                "From": frm,
                "To": to
            })
            current_years_ago -= duration
            remaining_years -= duration
            
    # --- External Exp Sheet ---
    if external_exp > 0.5:
        num_external = max(1, int(external_exp / 4))
        remaining_ext = external_exp
        current_ext_ago = total_exp  # External experience happened before internal
        
        for idx in range(num_external):
            org = random.choice(EXTERNAL_ORGS)
            ext_desig = random.choice(EXTERNAL_DESIGNATIONS)
            duration = round(random.uniform(0.5, max(1.0, remaining_ext)), 2)
            if idx == num_external - 1:
                duration = round(remaining_ext, 2)
                
            if duration > 0.1:
                frm, to = random_date_range(current_ext_ago, duration)
                external_exp_rows.append({
                    "PS No": ps_no,
                    "Org": org,
                    "Designation": ext_desig,
                    "From": frm,
                    "To": to
                })
                current_ext_ago -= duration
                remaining_ext -= duration

    # --- Segment Exposure Sheet ---
    # Pick 1 to 3 random segments
    num_segments = random.randint(1, 3)
    selected_segments = random.sample(list(SEGMENTS_MAP.keys()), num_segments)
    for seg in selected_segments:
        sub_segs = random.sample(SEGMENTS_MAP[seg], random.randint(1, min(2, len(SEGMENTS_MAP[seg]))))
        for sub_seg in sub_segs:
            segment_exposure_rows.append({
                "PS No": ps_no,
                "Segment": seg,
                "Sub-Segment": sub_seg
            })
            
    # --- Skill Proficiency Sheet ---
    # Pick 2 to 6 random skills based on Designation
    designation_lower = designation.lower()
    focused_skill_domains = []
    if "civil" in designation_lower or "structural" in designation_lower or "planning" in designation_lower or "quantity" in designation_lower:
        focused_skill_domains.append("Civil Engineering")
    if "electrical" in designation_lower:
        focused_skill_domains.append("Electrical Engineering")
    if "mechanical" in designation_lower:
        focused_skill_domains.append("Mechanical Engineering")
    if "manager" in designation_lower or "project" in designation_lower or "commercial" in designation_lower:
        focused_skill_domains.append("Project Management")
    if "system" in designation_lower or "cad" in designation_lower:
        focused_skill_domains.append("Digital & IT")
        
    if not focused_skill_domains:
        focused_skill_domains = ["Civil Engineering", "Project Management"]
        
    num_skills = random.randint(2, 6)
    for _ in range(num_skills):
        # Weighted selection of category
        category = random.choice(focused_skill_domains) if random.random() > 0.2 else random.choice(list(SKILLS_MAP.keys()))
        sub_skill = random.choice(SKILLS_MAP[category])
        
        dec_prof = random.choice(PROFICIENCIES)
        # Reviewed proficiency matches or is adjacent to declared proficiency
        if random.random() > 0.3:
            rev_prof = dec_prof
        else:
            rev_prof = random.choice(PROFICIENCIES)
            
        is_core = "Yes" if random.random() > 0.6 else ""
        
        skill_proficiency_rows.append({
            "PS No": ps_no,
            "Staff Name": staff_name,
            "Skill": category,
            "Sub-Skill": sub_skill,
            "User_Declared_Proficiency": dec_prof,
            "Reviewed_Proficiency": rev_prof,
            "Is_Core_Skill": is_core
        })
        
        # --- Skill Deployment / Job Skill Mapping Sheet ---
        # Add 1 deployment entry for this skill/sub-skill
        org_dep = random.choice(INTERNAL_ORGS)
        role_dep = random.choice(ROLE_DEPLOYMENTS)
        rep_count = random.choice(REPORTING_COUNTS)
        val_dep = round(random.uniform(5.0, 1200.0), 2)
        
        job_skill_mapping_rows.append({
            "PS No": ps_no,
            "Org": org_dep,
            "Skill": category,
            "Sub-Skill": sub_skill,
            "Role": role_dep,
            "Reporting Count": rep_count,
            "Value": val_dep
        })
        
    # --- Certification Sheet ---
    # 0 to 3 certifications
    num_certs = random.choice([0, 1, 1, 2, 3])
    if num_certs > 0:
        selected_certs = random.sample(CERTIFICATIONS, num_certs)
        for cert in selected_certs:
            certification_rows.append({
                "PS No": ps_no,
                "Certification": cert
            })
            
    # --- Qualification Sheet ---
    # 1 or 2 qualifications
    num_quals = random.choice([1, 1, 2])
    grad_year = 2026 - int(total_exp)
    selected_quals = random.sample(QUALIFICATIONS, num_quals)
    for q_idx, qual in enumerate(selected_quals):
        year = grad_year + (q_idx * 3)  # Masters happened later
        qualification_rows.append({
            "PS No": ps_no,
            "Year": year,
            "Description": qual
        })

# Create DataFrames
df_staff_master = pd.DataFrame(staff_master_rows)
df_internal_exp = pd.DataFrame(internal_exp_rows)
df_external_exp = pd.DataFrame(external_exp_rows)
df_segment_exposure = pd.DataFrame(segment_exposure_rows)
df_skill_proficiency = pd.DataFrame(skill_proficiency_rows)
df_job_skill_mapping = pd.DataFrame(job_skill_mapping_rows)
df_certification = pd.DataFrame(certification_rows)
df_qualification = pd.DataFrame(qualification_rows)

# Export to single Excel workbook with sheets
output_file = "synthetic_skill_dataset.xlsx"
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_staff_master.to_excel(writer, sheet_name="Staff_Master", index=False)
    df_internal_exp.to_excel(writer, sheet_name="Internal_Exp", index=False)
    df_external_exp.to_excel(writer, sheet_name="External_Exp", index=False)
    df_segment_exposure.to_excel(writer, sheet_name="Segment_Exposure", index=False)
    df_skill_proficiency.to_excel(writer, sheet_name="Skill_Proficiency", index=False)
    df_job_skill_mapping.to_excel(writer, sheet_name="Job_Skill_Mapping", index=False)
    df_certification.to_excel(writer, sheet_name="Certification", index=False)
    df_qualification.to_excel(writer, sheet_name="Qualification", index=False)

print(f"Relational workbook generated successfully: {output_file}")
print(f"Generated data statistics:")
print(f" - Staff Master rows: {len(df_staff_master)}")
print(f" - Internal Experience rows: {len(df_internal_exp)}")
print(f" - External Experience rows: {len(df_external_exp)}")
print(f" - Segment Exposure rows: {len(df_segment_exposure)}")
print(f" - Skill Proficiency rows: {len(df_skill_proficiency)}")
print(f" - Job Skill Mapping / Skill Deployment rows: {len(df_job_skill_mapping)}")
print(f" - Certification rows: {len(df_certification)}")
print(f" - Qualification rows: {len(df_qualification)}")
