import os
import io
import pytest
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

# Adjust path to import backend correctly
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.excel_loader import load_excel_sheets, REQUIRED_SHEETS_COLUMNS
from backend.app.data_cleaner import clean_data
from backend.app.join_engine import build_employee_profiles
from backend.app.structured_search import structured_search
from backend.app.semantic_search import semantic_search_engine
from backend.app.hybrid_search import hybrid_search
from backend.app.conversation_manager import session_manager

client = TestClient(app)

# ─── Mock Relational Data Helper ──────────────────────────────────────────────

def create_mock_relational_excel() -> bytes:
    """Helper to generate a valid 8-sheet Excel file bytes for testing."""
    sheets = {}
    
    # 1. Staff_Master
    sheets["Staff_Master"] = pd.DataFrame([
        {
            "PS No": 12345, "Staff Name": "Arun Kumar", "Email ID": "12345@lntecc.com",
            "Mobile": "9876543210", "Cadre": "S2", "Band": "S - Band", "Designation": "Civil Engineer",
            "Total Exp": 10.0, "Internal Exp": 6.0, "External Exp": 4.0, "Job Code": "LE123456",
            "Job Name": "LE123456", "Cluster": "Chennai", "BU": "Buildings & Factories",
            "SBG": "B&F SBG", "IS PS No": 54321, "IS Name": "Manager Rajesh", "IS Email ID": "54321@lntecc.com"
        },
        {
            "PS No": 67890, "Staff Name": "Priya Sharma", "Email ID": "67890@lntecc.com",
            "Mobile": "8765432109", "Cadre": "M2-A", "Band": "E - Band", "Designation": "Project Manager",
            "Total Exp": 15.0, "Internal Exp": 10.0, "External Exp": 5.0, "Job Code": "LE654321",
            "Job Name": "LE654321", "Cluster": "Bangalore", "BU": "Heavy Civil Infrastructure",
            "SBG": "HCI SBG", "IS PS No": 54321, "IS Name": "Manager Rajesh", "IS Email ID": "54321@lntecc.com"
        }
    ])
    
    # 2. Internal_Exp
    sheets["Internal_Exp"] = pd.DataFrame([
        {"PS No": 12345, "Org": "LE110120 - Kolkata", "From": "01-01-2020", "To": "01-01-2022"},
        {"PS No": 67890, "Org": "LE180988 - BIAL T2", "From": "01-01-2018", "To": "01-01-2023"}
    ])
    
    # 3. External_Exp
    sheets["External_Exp"] = pd.DataFrame([
        {"PS No": 12345, "Org": "SHAPOORJI PALLONJI", "Designation": "Site Supervisor", "From": "01-01-2016", "To": "01-01-2020"},
        {"PS No": 67890, "Org": "TATA PROJECTS", "Designation": "Planning Engineer", "From": "01-01-2013", "To": "01-01-2018"}
    ])
    
    # 4. Segment_Exposure
    sheets["Segment_Exposure"] = pd.DataFrame([
        {"PS No": 12345, "Segment": "Metro & Tunneling", "Sub-Segment": "Underground Metro"},
        {"PS No": 67890, "Segment": "Buildings & Factories", "Sub-Segment": "Airports"}
    ])
    
    # 5. Skill_Proficiency
    sheets["Skill_Proficiency"] = pd.DataFrame([
        {"PS No": 12345, "Staff Name": "Arun Kumar", "Skill": "Civil Engineering", "Sub-Skill": "Concrete Technology", "User_Declared_Proficiency": "Expert", "Reviewed_Proficiency": "Expert", "Is_Core_Skill": "Yes"},
        {"PS No": 67890, "Staff Name": "Priya Sharma", "Skill": "Project Management", "Sub-Skill": "PMP", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"}
    ])
    
    # 6. Job_Skill_Mapping
    sheets["Job_Skill_Mapping"] = pd.DataFrame([
        {"PS No": 12345, "Org": "LE110120 - Kolkata", "Skill": "Civil Engineering", "Sub-Skill": "Concrete Technology", "Role": "Trainee & Equivalent", "Reporting Count": "5", "Value": 100.0},
        {"PS No": 67890, "Org": "LE180988 - BIAL T2", "Skill": "Project Management", "Sub-Skill": "PMP", "Role": "Executive (E:Band) & Equivalent", "Reporting Count": "10", "Value": 500.0}
    ])
    
    # 7. Certification
    sheets["Certification"] = pd.DataFrame([
        {"PS No": 12345, "Certification": "Primavera P6 Certification"},
        {"PS No": 67890, "Certification": "PMP (Project Management Professional)"}
    ])
    
    # 8. Qualification
    sheets["Qualification"] = pd.DataFrame([
        {"PS No": 12345, "Year": 2012, "Description": "B.Tech in Civil Engineering"},
        {"PS No": 67890, "Year": 2008, "Description": "MBA in Project Management"}
    ])
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    return buffer.getvalue()

# ─── Ingestion & In-Memory Tests ──────────────────────────────────────────────

def test_load_and_validate_excel_valid():
    excel_bytes = create_mock_relational_excel()
    dfs, err = load_excel_sheets(excel_bytes)
    assert err is None
    assert dfs is not None
    assert len(dfs) == 8
    for sheet in REQUIRED_SHEETS_COLUMNS.keys():
        assert sheet in dfs

def test_load_excel_missing_sheet():
    # Write only a few sheets
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([{"PS No": 12}]).to_excel(writer, sheet_name="Staff_Master", index=False)
        
    dfs, err = load_excel_sheets(buffer.getvalue())
    assert err is not None
    assert "Missing required sheets" in err

def test_clean_and_join():
    excel_bytes = create_mock_relational_excel()
    dfs, _ = load_excel_sheets(excel_bytes)
    cleaned = clean_data(dfs)
    
    # Validate cleaning types
    assert cleaned["Staff_Master"]["PS No"].dtype == np.int32 or cleaned["Staff_Master"]["PS No"].dtype == np.int64
    
    profiles = build_employee_profiles(cleaned)
    assert len(profiles) == 2
    
    # Verify relations mapped correctly
    arun = next(p for p in profiles if p["ps_no"] == 12345)
    assert arun["staff_name"] == "Arun Kumar"
    assert arun["designation"] == "Civil Engineer"
    assert len(arun["skills"]) == 1
    assert arun["skills"][0]["Sub-Skill"] == "Concrete Technology"
    assert arun["certifications"] == ["Primavera P6 Certification"]
    assert arun["qualifications"][0]["Description"] == "B.Tech in Civil Engineering"

# ─── Search Engine Tests ──────────────────────────────────────────────────────

def test_structured_search_filtering():
    excel_bytes = create_mock_relational_excel()
    dfs, _ = load_excel_sheets(excel_bytes)
    profiles = build_employee_profiles(clean_data(dfs))
    
    # Filter by designation
    res1 = structured_search(profiles, {"designation": "Civil Engineer"})
    assert len(res1) == 1
    assert res1[0]["staff_name"] == "Arun Kumar"
    
    # Filter by min experience
    res2 = structured_search(profiles, {"experience_min": 12.0})
    assert len(res2) == 1
    assert res2[0]["staff_name"] == "Priya Sharma"

# ─── Endpoints Tests ──────────────────────────────────────────────────────────

def ensure_db_loaded():
    health = client.get("/health").json()
    if not health.get("database_loaded"):
        excel_bytes = create_mock_relational_excel()
        client.post(
            "/upload-workbook",
            files={"file": ("test_sheets.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

def test_api_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert "status" in r.json()

def test_api_upload_workbook():
    excel_bytes = create_mock_relational_excel()
    r = client.post(
        "/upload-workbook",
        files={"file": ("test_sheets.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert r.status_code == 200
    assert "profiles_count" in r.json()
    assert r.json()["profiles_count"] == 2

def test_api_chat_flow():
    ensure_db_loaded()
    # Reset session first
    sid = "test_user_session"
    client.post("/reset-session", json={"session_id": sid})
    
    # Send a query
    r = client.post(
        "/chat",
        json={"session_id": sid, "message": "show civil engineers in Chennai", "top_k": 5}
    )
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert "results" in data
    
    # Verify active filters
    assert data["active_filters"].get("designation") == "Civil Engineer"
    assert data["active_filters"].get("location") == "Chennai"


def test_api_greeting_intercept():
    ensure_db_loaded()
    sid = "test_greeting_session"
    client.post("/reset-session", json={"session_id": sid})
    
    # 1. Send search query to set state
    r1 = client.post(
        "/chat",
        json={"session_id": sid, "message": "show civil engineers in Chennai", "top_k": 5}
    )
    assert r1.status_code == 200
    
    # 2. Send "hello!" greeting
    r2 = client.post(
        "/chat",
        json={"session_id": sid, "message": "hello!"}
    )
    assert r2.status_code == 200
    data = r2.json()
    assert "Enterprise Workforce Intelligence Assistant" in data["message"]
    assert data["results"] == []
    assert data["active_filters"] == {}


def test_keyword_extraction_and_token_matching():
    # Test query_parser directly
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    # Setup custom keywords mimicking the user's dataset
    mock_profiles = [
        {
            "designation": "ENGINEER (CIVIL)",
            "cluster": "Mumbai",
            "certifications": ["PMP"],
            "qualifications": [{"Description": "B.Tech in Civil Engineering"}],
            "segment_exposure": [],
            "external_experience": []
        }
    ]
    update_keyword_lists(mock_profiles)
    
    # 1. Test query with word boundary & order matching: "civil engineer in mumbai"
    res = parse_query_rules("civil engineer in mumbai")
    
    # Designation should match "ENGINEER (CIVIL)" token-by-token
    assert res["designation"] == "Engineer (Civil)"
    # Location should match "Mumbai"
    assert res["location"] == "Mumbai"
    # "mba" (substring of mumbai) should NOT match as qualification
    assert res["qualification"] is None
    
    # 2. Verify structured search behaves correctly with token-based designation matching
    from backend.app.structured_search import structured_search
    
    full_mock_profile = {
        "ps_no": 99999,
        "staff_name": "Mumbai Engineer",
        "designation": "ENGINEER (CIVIL)",
        "cluster": "Mumbai",
        "total_exp": 5.0,
        "internal_exp_years": 3.0,
        "external_exp_years": 2.0,
        "band": "S - Band",
        "cadre": "S2",
        "bu": "Heavy Civil Infrastructure",
        "sbg": "HCI SBG",
        "certifications": [],
        "qualifications": [{"Description": "B.Tech in Civil Engineering"}],
        "segment_exposure": [],
        "internal_experience": [],
        "external_experience": [],
        "skills": []
    }
    
    # Exact match works
    results1 = structured_search([full_mock_profile], {"designation": "ENGINEER (CIVIL)"})
    assert len(results1) == 1
    
    # Out of order token-based match works
    results2 = structured_search([full_mock_profile], {"designation": "Civil Engineer"})
    assert len(results2) == 1
    
    # Partial word-match works
    results3 = structured_search([full_mock_profile], {"designation": "civil"})
    assert len(results3) == 1

    # 3. Test abbreviation extraction from parentheses
    mock_profiles_abbr = [
        {
            "designation": "Site Engineer",
            "cluster": "Delhi",
            "certifications": ["Project Management Professional (PMP)"],
            "qualifications": [{"Description": "Master of Business Administration (MBA)"}],
            "segment_exposure": [],
            "external_experience": []
        }
    ]
    update_keyword_lists(mock_profiles_abbr)
    
    # Query with PMP abbreviation should match the certification
    res_abbr = parse_query_rules("engineer with pmp")
    assert res_abbr["certification"] == "PMP"
    
    # Query with MBA abbreviation should match the qualification
    res_abbr_qual = parse_query_rules("engineer with mba")
    assert res_abbr_qual["qualification"] == "Mba"

    # 4. Test stripping of "certification" suffix & trailing punctuation
    mock_profiles_cleaning = [
        {
            "designation": "Site Engineer",
            "cluster": "Delhi",
            "certifications": ["PMP Certification:", "Project Management Professional (PMP)"],
            "qualifications": [{"Description": "MBA degree"}],
            "segment_exposure": [],
            "external_experience": []
        }
    ]
    update_keyword_lists(mock_profiles_cleaning)
    
    # Query with "pmp certification" should match "PMP"
    res_clean = parse_query_rules("people with pmp certification")
    assert res_clean["certification"] == "PMP"
    
    # MBA degree should match MBA (title-cased as Mba)
    res_clean_qual = parse_query_rules("engineer with mba degree")
    assert res_clean_qual["qualification"] == "Mba"

    # 5. Test sub-skill and sub-segment structured filtering
    from backend.app.structured_search import structured_search
    
    profile_with_sub = {
        "ps_no": 77777,
        "staff_name": "Test Sub",
        "designation": "Civil Engineer",
        "cluster": "Delhi",
        "total_exp": 10.0,
        "internal_exp_years": 5.0,
        "external_exp_years": 5.0,
        "band": "S - Band",
        "cadre": "S2",
        "bu": "Heavy Civil Infrastructure",
        "sbg": "HCI SBG",
        "certifications": [],
        "qualifications": [],
        "segment_exposure": [{"Segment": "Metro & Tunneling", "Sub-Segment": "Underground Metro"}],
        "internal_experience": [],
        "external_experience": [],
        "skills": [{"Skill": "Civil Engineering", "Sub-Skill": "Waterproofing", "User_Declared_Proficiency": "Expert", "Reviewed_Proficiency": "Expert", "Is_Core_Skill": "Yes"}]
    }
    
    # Filtering by "skill"="Waterproofing" should match the Sub-Skill
    res_skill = structured_search([profile_with_sub], {"skill": "Waterproofing"})
    assert len(res_skill) == 1
    
    # Filtering by "segment"="Underground Metro" should match the Sub-Segment
    res_seg = structured_search([profile_with_sub], {"segment": "Underground Metro"})
    assert len(res_seg) == 1


def test_multi_value_logical_filters():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    from backend.app.structured_search import structured_search
    from backend.app.response_formatter import format_search_response
    
    # 1. Update keywords to include PMP, RICS, Bangalore, Hyderabad
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Bangalore",
            "certifications": ["PMP", "RICS"],
            "qualifications": [],
            "segment_exposure": [],
            "external_experience": []
        },
        {
            "designation": "Civil Engineer",
            "cluster": "Hyderabad",
            "certifications": ["PMP"],
            "qualifications": [],
            "segment_exposure": [],
            "external_experience": []
        }
    ]
    update_keyword_lists(mock_profiles)
    
    # 2. Test Rule-based Parser on Locations (OR logic by default)
    res_loc = parse_query_rules("located in Bangalore or Hyderabad")
    assert isinstance(res_loc["location"], list)
    assert set(res_loc["location"]) == {"Bangalore", "Hyderabad"}
    assert res_loc["location_operator"] == "or"
    
    # 3. Test Rule-based Parser on Certifications (AND logic)
    res_cert_and = parse_query_rules("certifications in both PMP and RICS")
    assert isinstance(res_cert_and["certification"], list)
    assert set(res_cert_and["certification"]) == {"PMP", "RICS"}
    assert res_cert_and["certification_operator"] == "and"
    
    # 4. Test Rule-based Parser on Certifications (OR logic)
    res_cert_or = parse_query_rules("PMP or RICS certification")
    assert isinstance(res_cert_or["certification"], list)
    assert set(res_cert_or["certification"]) == {"PMP", "RICS"}
    assert res_cert_or["certification_operator"] == "or"
    
    # 5. Test Structured Search Logic
    p1 = {
        "ps_no": 111,
        "designation": "Civil Engineer",
        "cluster": "Bangalore",
        "certifications": ["PMP", "RICS"],
        "qualifications": [],
        "segment_exposure": [],
        "internal_experience": [],
        "external_experience": [],
        "skills": []
    }
    p2 = {
        "ps_no": 222,
        "designation": "Civil Engineer",
        "cluster": "Hyderabad",
        "certifications": ["PMP"],
        "qualifications": [],
        "segment_exposure": [],
        "internal_experience": [],
        "external_experience": [],
        "skills": []
    }
    p3 = {
        "ps_no": 333,
        "designation": "Civil Engineer",
        "cluster": "Chennai",
        "certifications": ["RICS"],
        "qualifications": [],
        "segment_exposure": [],
        "internal_experience": [],
        "external_experience": [],
        "skills": []
    }
    profiles = [p1, p2, p3]
    
    # Filtering for location ["Bangalore", "Hyderabad"] should return Bangalore and Hyderabad profiles (OR logic)
    res_search_loc = structured_search(profiles, {"location": ["Bangalore", "Hyderabad"], "location_operator": "or"})
    assert len(res_search_loc) == 2
    assert {p["ps_no"] for p in res_search_loc} == {111, 222}
    
    # Filtering for certifications ["PMP", "RICS"] with AND operator should only return profile 1 (has both)
    res_search_cert_and = structured_search(profiles, {"certification": ["PMP", "RICS"], "certification_operator": "and"})
    assert len(res_search_cert_and) == 1
    assert res_search_cert_and[0]["ps_no"] == 111
    
    # Filtering for certifications ["PMP", "RICS"] with OR operator should return all three profiles (each has at least one)
    res_search_cert_or = structured_search(profiles, {"certification": ["PMP", "RICS"], "certification_operator": "or"})
    assert len(res_search_cert_or) == 3
    
    # 6. Test Output Formatting
    formatted_and = format_search_response(
        [p1],
        {"certification": ["PMP", "RICS"], "certification_operator": "and", "location": ["Bangalore", "Hyderabad"], "location_operator": "or"}
    )
    # The message should format "PMP & RICS" and "Bangalore or Hyderabad"
    assert "Certification: PMP & RICS" in formatted_and["message"]
    assert "Location: Bangalore or Hyderabad" in formatted_and["message"]


def test_dotted_abbreviation_and_bracket_matching():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    from backend.app.structured_search import structured_search

    # Test profile with dotted abbreviation and bracket abbreviation
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Mumbai",
            "certifications": ["A.I.S.S.C.E", "Mentoring and Augmenting Planning Skills [MAPS]"],
            "qualifications": [{"Description": "B.Tech in Civil Engineering"}],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    update_keyword_lists(mock_profiles)

    # 1. Test local rule-based parser on dot-stripped query
    res = parse_query_rules("find candidates with aissce")
    assert res["certification"] == "A.I.S.S.C.E"

    # 2. Test local rule-based parser on bracket abbreviation
    res_maps = parse_query_rules("find candidates with maps")
    assert res_maps["certification"] == "MAPS"

    # 3. Test structured search with different formats
    p = {
        "ps_no": 90066,
        "designation": "Civil Engineer",
        "cluster": "Mumbai",
        "certifications": ["A.I.S.S.C.E", "Mentoring and Augmenting Planning Skills (MAPS)"],
        "qualifications": [{"Description": "B.Tech in Civil Engineering"}],
        "segment_exposure": [],
        "internal_experience": [],
        "external_experience": [],
        "skills": []
    }

    # Matches with dot-stripped
    res_search1 = structured_search([p], {"certification": "aissce"})
    assert len(res_search1) == 1

    # Matches with dotted
    res_search2 = structured_search([p], {"certification": "a.i.s.s.c.e"})
    assert len(res_search2) == 1

    # Matches with abbreviation MAPS
    res_search3 = structured_search([p], {"certification": "maps"})
    assert len(res_search3) == 1


def test_designation_modifiers():
    from backend.app.structured_search import structured_search
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    profiles = [
        {"ps_no": 1, "designation": "ASST.CONSTRUCTION MANAGER (CIVIL)", "skills": []},
        {"ps_no": 2, "designation": "CONSTRUCTION MANAGER (CIVIL)", "skills": []},
        {"ps_no": 3, "designation": "SR.CONSTRUCTION MANAGER (CIVIL)", "skills": []},
        {"ps_no": 4, "designation": "ASST.MANAGER (FINISHES)", "skills": []},
        {"ps_no": 5, "designation": "ASST. MANAGER (CIVIL)", "skills": []},
        {"ps_no": 6, "designation": "CONSTRUCTION MANAGER (MECH)", "skills": []}
    ]
    update_keyword_lists(profiles)
    
    # 1. Query has "asst manager(finishes)"
    parsed_finishes = parse_query_rules("asst manager(finishes)")
    assert parsed_finishes["designation"] == "Assistant Manager (Finishes)"
    res_finishes = structured_search(profiles, parsed_finishes)
    assert len(res_finishes) == 1
    assert res_finishes[0]["ps_no"] == 4
    
    # 2. Query has "asst manager"
    parsed_asst_mgr = parse_query_rules("asst manager")
    assert parsed_asst_mgr["designation"] == "Assistant Manager"
    res_asst_mgr = structured_search(profiles, parsed_asst_mgr)
    assert len(res_asst_mgr) == 3
    assert {r["ps_no"] for r in res_asst_mgr} == {1, 4, 5}
    
    # 3. Query has "sr construction manager in civil"
    parsed_sr = parse_query_rules("sr construction manager in civil")
    assert parsed_sr["designation"] == "Senior Construction Manager (Civil)"
    res_sr = structured_search(profiles, parsed_sr)
    assert len(res_sr) == 1
    assert res_sr[0]["ps_no"] == 3
    
    # 4. Query is general "construction manager"
    parsed_gen = parse_query_rules("construction manager")
    assert parsed_gen["designation"] == "Construction Manager"
    res_gen = structured_search(profiles, parsed_gen)
    assert len(res_gen) == 4
    assert {r["ps_no"] for r in res_gen} == {1, 2, 3, 6}

    # 5. Query has "construction manager in mechanical in delhi"
    parsed_mech = parse_query_rules("construction manager in mechanical in delhi")
    assert parsed_mech["designation"] == "Construction Manager (Mech)"
    assert parsed_mech["location"] == "Delhi"
    
    profiles_with_clusters = [
        {"ps_no": 1, "designation": "ASST.CONSTRUCTION MANAGER (CIVIL)", "cluster": "Chennai", "skills": []},
        {"ps_no": 2, "designation": "CONSTRUCTION MANAGER (CIVIL)", "cluster": "Delhi", "skills": []},
        {"ps_no": 3, "designation": "SR.CONSTRUCTION MANAGER (CIVIL)", "cluster": "Delhi", "skills": []},
        {"ps_no": 6, "designation": "CONSTRUCTION MANAGER (MECH)", "cluster": "Delhi", "skills": []}
    ]
    res_mech = structured_search(profiles_with_clusters, parsed_mech)
    assert len(res_mech) == 1
    assert res_mech[0]["ps_no"] == 6


def test_waterproofing_with_min_experience_extraction():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Delhi",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": [
                {"Skill": "Civil Engineering", "Sub-Skill": "Waterproofing", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"}
            ]
        }
    ]
    update_keyword_lists(mock_profiles)
    
    query = "show people with proficient waterproofing skills with min 5 years experience excluding the quality department"
    res = parse_query_rules(query)
    
    assert res["experience_min"] == 5.0
    assert res["exclude_department"] == "QUALITY"
    # sub_skill should be set for backward compat display
    assert res["sub_skill"] == "Waterproofing"
    # reviewed_proficiency is now captured per-skill in skill_requirements
    # (global reviewed_proficiency is no longer set when skill_requirements is populated)
    skill_reqs = res.get("skill_requirements") or []
    if skill_reqs:
        # Proficient should be found in at least one skill requirement
        assert any(
            "Proficient" in (r.get("proficiency") or [])
            for r in skill_reqs
        )
    else:
        # Fallback: reviewed_proficiency still set for simple queries
        assert res["reviewed_proficiency"] == "Proficient"


def test_department_extraction_rules():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Assistant Manager",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    update_keyword_lists(mock_profiles)
    
    query = "show assistant manager in the quality department with more than 25 years of experience in chennai"
    res = parse_query_rules(query)
    
    assert res["designation"] == "Assistant Manager"
    assert res["department"] == "QUALITY"
    assert res["location"] == "Chennai"
    assert res["experience_min"] == 25.0


def test_exclude_department_multiple_filtering():
    from backend.app.structured_search import structured_search
    
    profiles = [
        {"ps_no": 1, "department": "CIVIL", "total_exp": 10.0, "internal_exp_years": 5.0, "external_exp_years": 5.0, "skills": []},
        {"ps_no": 2, "department": "QA/QC", "total_exp": 10.0, "internal_exp_years": 5.0, "external_exp_years": 5.0, "skills": []},
        {"ps_no": 3, "department": "QUALITY", "total_exp": 10.0, "internal_exp_years": 5.0, "external_exp_years": 5.0, "skills": []},
        {"ps_no": 4, "department": "MECH", "total_exp": 10.0, "internal_exp_years": 5.0, "external_exp_years": 5.0, "skills": []}
    ]
    
    filters = {
        "exclude_department": ["QUALITY", "CIVIL"]
    }
    
    results = structured_search(profiles, filters)
    assert len(results) == 1
    assert results[0]["ps_no"] == 4


def test_qa_qc_department_variations_and_extraction():
    from backend.app.join_engine import extract_department
    from backend.app.query_parser import parse_query_rules
    
    # 1. Test join engine mapping
    assert extract_department("ASST.MANAGER-QA & QC") == "QA/QC"
    assert extract_department("QA/QC ENGINEER") == "QA/QC"
    assert extract_department("ASST. MANAGER (QA&QC)") == "QA/QC"
    assert extract_department("QA ENGINEER") == "QA/QC"
    assert extract_department("QC INSPECTOR") == "QA/QC"
    
    # 2. Test query parser mapping
    res = parse_query_rules("show people in the qa & qc department")
    assert res["department"] == "QA/QC"
    
    res2 = parse_query_rules("excluding qa&qc")
    assert res2["exclude_department"] == "QA/QC"


def test_exclude_and_positive_department_overlap():
    from backend.app.query_parser import parse_query_rules
    
    query = "show people with proficient waterproofing skills with min 5 years experience excluding the quality and civil department"
    res = parse_query_rules(query)
    
    assert res["department"] is None
    assert res["exclude_department"] == ["QUALITY", "CIVIL"]


def test_skill_specific_proficiency_and_stemming_and_aliases():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    from backend.app.structured_search import structured_search
    from backend.app.response_formatter import format_search_response
    
    # 1. Register mock profiles with skills having aliases and variations
    mock_profiles = [
        {
            "ps_no": 101,
            "staff_name": "John Doe",
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "total_exp": 6.0,
            "internal_exp_years": 4.0,
            "external_exp_years": 2.0,
            "band": "S - Band",
            "cadre": "S2",
            "bu": "Buildings & Factories",
            "sbg": "B&F SBG",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [],
            "internal_experience": [],
            "external_experience": [],
            "skills": [
                {"Skill": "Execution : Formwork", "Sub-Skill": "Formwork Systems", "User_Declared_Proficiency": "Role Model", "Reviewed_Proficiency": "Role Model", "Is_Core_Skill": "Yes"},
                {"Skill": "Quarry", "Sub-Skill": "Quarrying Operations", "User_Declared_Proficiency": "Basic", "Reviewed_Proficiency": "Basic", "Is_Core_Skill": "No"}
            ]
        },
        {
            "ps_no": 102,
            "staff_name": "Jane Smith",
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "total_exp": 8.0,
            "internal_exp_years": 5.0,
            "external_exp_years": 3.0,
            "band": "S - Band",
            "cadre": "S2",
            "bu": "Buildings & Factories",
            "sbg": "B&F SBG",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [],
            "internal_experience": [],
            "external_experience": [],
            "skills": [
                {"Skill": "Execution : Structural Steel", "Sub-Skill": "Structural Steelwork", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Finishes", "Sub-Skill": "Finishing", "User_Declared_Proficiency": "Intermediate", "Reviewed_Proficiency": "Intermediate", "Is_Core_Skill": "No"}
            ]
        }
    ]
    
    update_keyword_lists(mock_profiles)
    
    # 2. Test alias matching: "Execution" should match both "Execution : Formwork" and "Execution : Structural Steel"
    # Stem variation matching: "quarrying" matches "Quarry", "finishing" matches "Finishes"
    query = "Identify employees with proficient or role model Execution skills and intermediate Finishing skills"
    res = parse_query_rules(query)
    
    # Verify that the parsed filter contains skill_requirements
    assert res["skill_requirements"] is not None
    # With grouped OR logic, 'Execution' alias -> one req with skills list, 'Finishing' -> another
    assert len(res["skill_requirements"]) >= 2
    
    # Find the Execution group (should contain both Formwork and Structural Steel in `skills` list)
    req_exec = next(
        r for r in res["skill_requirements"]
        if any("Execution" in s for s in (r.get("skills") or [r.get("skill", "")]))
    )
    # Must have Proficient and/or Role Model
    assert set(req_exec["proficiency"]) & {"Proficient", "Role Model"}
    assert req_exec["operator"] == "or"
    # Both Execution variants should be in the group
    exec_skills = req_exec.get("skills") or [req_exec.get("skill")]
    assert any("Execution : Formwork" in s for s in exec_skills)
    assert any("Execution : Structural Steel" in s for s in exec_skills)
    
    # Find Finishes/Finishing group
    req_finishing = next(
        r for r in res["skill_requirements"]
        if any(s in ("Finishes", "Finishing") for s in (r.get("skills") or [r.get("skill", "")]))
    )
    assert req_finishing["proficiency"] == ["Intermediate"]
    
    # 3. Test structured search filtering
    filtered_results = structured_search(mock_profiles, res)
    # John Doe: has Execution:Formwork(Role Model) but no Finishing -> fails Finishing req
    # Jane Smith: has Execution:Structural Steel(Proficient) AND Finishes(Intermediate) -> MATCH
    assert len(filtered_results) == 1
    assert filtered_results[0]["ps_no"] == 102
    
    # 4. Test quarrying query: "people with quarrying skills"
    res_quarry = parse_query_rules("people with quarrying skills")
    assert res_quarry["skill_requirements"] is not None
    req_quarry = next(
        r for r in res_quarry["skill_requirements"]
        if any("Quarry" in s for s in (r.get("skills") or [r.get("skill", "")]))
    )
    assert req_quarry["proficiency"] is None  # no proficiency specified
    
    filtered_quarry = structured_search(mock_profiles, res_quarry)
    assert len(filtered_quarry) == 1
    assert filtered_quarry[0]["ps_no"] == 101
    
    # 5. Test output formatting
    formatted = format_search_response(filtered_results, res)
    skill_req_str = formatted["active_filters"]["skill_requirements"]
    # Finishes group should show Intermediate proficiency
    assert "Intermediate" in skill_req_str
    # Execution group should mention proficiency
    assert "Proficient" in skill_req_str or "Role Model" in skill_req_str


def test_execution_civil_query_without_qualification_greediness():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [{"Description": "B.Tech (Civil)"}],
            "segment_exposure": [],
            "external_experience": [],
            "skills": [
                {"Skill": "Execution : Civil", "Sub-Skill": "Civil Work Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : Formwork", "Sub-Skill": "Formwork Systems", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
            ]
        }
    ]
    update_keyword_lists(mock_profiles)
    
    res = parse_query_rules("find employees with proficient execution : civil skills")
    assert res["qualification"] is None
    assert res["sub_skill"] is None
    assert res["skill_requirements"] is not None
    assert len(res["skill_requirements"]) == 1
    req = res["skill_requirements"][0]
    assert req["skills"] == ["Execution : Civil"]
    assert req["proficiency"] == ["Proficient"]


def test_tier_1_query_does_not_extract_ti_segment():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Assistant Manager",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [{"Segment": "TI"}],
            "external_experience": [],
            "skills": []
        }
    ]
    update_keyword_lists(mock_profiles)
    
    res = parse_query_rules("show assistant manager in the quality department with more than 25 years of experience in chennai in tier 1 band")
    assert res["designation"] == "Assistant Manager"
    assert res["department"] == "QUALITY"
    assert res["location"] == "Chennai"
    assert res["band"] == "Tier 1"
    assert res["experience_min"] == 25.0
    assert res["segment"] is None


def test_execution_civil_skills_and_finishes_query_no_department_greediness():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [{"Segment": "Commercial Projects"}],
            "external_experience": [],
            "skills": [
                {"Skill": "Execution : Civil", "Sub-Skill": "Civil Work Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : Formwork", "Sub-Skill": "Formwork Systems", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : Structural Steel", "Sub-Skill": "Structural Steelwork", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : MEP", "Sub-Skill": "MEP Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "QC - Finishing - Water Proofing", "Sub-Skill": "Finishing Work", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution Commercial", "Sub-Skill": "Commercial Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"}
            ]
        }
    ]
    update_keyword_lists(mock_profiles)
    
    res = parse_query_rules("List candidates with Execution skills (Civil) and Execution skills( Finishes) worked in Commercial projects, AND are having over 10 years of experience")
    assert res["department"] is None
    assert res["experience_min"] == 10.0
    assert res["sbg"] == "Commercial & Residential Spaces"
    
    assert res["skill_requirements"] is not None
    matched_skills = []
    for req in res["skill_requirements"]:
        matched_skills.extend(req.get("skills") or [req.get("skill")])
        
    assert "Execution : Civil" in matched_skills
    assert "Finishing Work" in matched_skills
    assert "Execution Commercial" not in matched_skills


def test_exact_matches_prioritized_over_stem_matches():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": [
                {"Skill": "Civil Engineering", "Sub-Skill": "Finishes"},
                {"Skill": "Civil Engineering", "Sub-Skill": "QC - Civil, Finishes"},
                {"Skill": "Civil Engineering", "Sub-Skill": "QC - Finishing - Water Proofing"},
                {"Skill": "Civil Engineering", "Sub-Skill": "Execution : Civil"},
                {"Skill": "Civil Engineering", "Sub-Skill": "Execution : Formwork"}
            ]
        }
    ]
    update_keyword_lists(mock_profiles)
    
    res = parse_query_rules("show people with execution: civil and finishes skills")
    assert res["department"] is None
    
    assert res["skill_requirements"] is not None
    matched_skills = []
    for req in res["skill_requirements"]:
        matched_skills.extend(req.get("skills") or [req.get("skill")])
        
    assert "Execution : Civil" in matched_skills
    assert "Finishes" in matched_skills
    assert "QC - Civil, Finishes" not in matched_skills
    assert "QC - Finishing - Water Proofing" not in matched_skills


def test_response_formatter_skips_legacy_skills_when_requirements_present():
    from backend.app.response_formatter import format_search_response
    
    filters = {
        "experience_min": 10.0,
        "skill": ["Execution : Civil", "QC - Finishing - Water Proofing"],
        "skill_operator": "and",
        "sub_skill": "Rebar : Execution",
        "reviewed_proficiency": "Proficient",
        "skill_requirements": [
            {"skills": ["Execution : Civil"], "proficiency": None, "operator": "or"},
            {"skills": ["QC - Finishing - Water Proofing"], "proficiency": None, "operator": "or"}
        ]
    }
    
    formatted = format_search_response([], filters)
    message = formatted["message"]
    
    assert "Min Exp: 10.0 years" in message
    assert "Skills: Execution : Civil & QC - Finishing - Water Proofing" in message
    assert "Skill:" not in message
    assert "Sub-Skill:" not in message
    assert "Reviewed Proficiency:" not in message


def test_execution_civil_and_execution_formwork_query_backtrack_matching():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": [
                {"Skill": "Execution : Civil", "Sub-Skill": "Civil Work Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : Formwork", "Sub-Skill": "Formwork Systems", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : Structural Steel", "Sub-Skill": "Structural Steelwork", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Execution : MEP", "Sub-Skill": "MEP Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"},
                {"Skill": "Rebar : Execution", "Sub-Skill": "Rebar Execution", "User_Declared_Proficiency": "Proficient", "Reviewed_Proficiency": "Proficient", "Is_Core_Skill": "Yes"}
            ]
        }
    ]
    update_keyword_lists(mock_profiles)
    
    res = parse_query_rules("List candidates with Execution : civil skills and execution : formwork skills")
    assert res["skill_requirements"] is not None
    assert len(res["skill_requirements"]) == 2
    
    matched_skills = []
    for req in res["skill_requirements"]:
        matched_skills.extend(req.get("skills") or [req.get("skill")])
        
    assert set(matched_skills) == {"Execution : Civil", "Execution : Formwork"}


def test_qualification_logical_filters():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    from backend.app.structured_search import structured_search
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [
                {"Description": "B.E. in Civil Engineering"},
                {"Description": "Diploma in Civil Engineering (DCE)"},
                {"Description": "SSC"}
            ],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        },
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [
                {"Description": "B.Tech in Civil Engineering"}
            ],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    update_keyword_lists(mock_profiles)
    
    # 1. Test OR logic for qualifications (with comma)
    res_or = parse_query_rules("find people with BE, DCE or SSC qualification")
    assert isinstance(res_or["qualification"], list)
    assert set(res_or["qualification"]) == {"B.E.", "Dce", "Ssc"}
    assert res_or["qualification_operator"] == "or"
    
    # 2. Test AND logic for qualifications
    res_and = parse_query_rules("find people with both BE and DCE qualification")
    assert isinstance(res_and["qualification"], list)
    assert set(res_and["qualification"]) == {"B.E.", "Dce"}
    assert res_and["qualification_operator"] == "and"
    
    # 3. Test list structure under structured search
    # B.E. (BE), DCE, SSC -> Employee 1 has DCE and B.E., Employee 2 has B.Tech
    p1 = {
        "ps_no": 1,
        "qualifications": [{"Description": "B.E. in Civil Engineering"}, {"Description": "DCE"}],
    }
    p2 = {
        "ps_no": 2,
        "qualifications": [{"Description": "B.Tech"}],
    }
    
    # Filter for ["B.E.", "Dce"] with AND operator -> p1 has both, so it matches
    results_and = structured_search([p1, p2], {"qualification": ["B.E.", "Dce"], "qualification_operator": "and"})
    assert len(results_and) == 1
    assert results_and[0]["ps_no"] == 1
    
    # Filter for ["B.E.", "Dce"] with OR operator -> p1 matches
    results_or = structured_search([p1, p2], {"qualification": ["B.E.", "Dce"], "qualification_operator": "or"})
    assert len(results_or) == 1
    assert results_or[0]["ps_no"] == 1


def test_qualification_false_positives():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    
    mock_profiles = [
        {
            "designation": "Civil Engineer",
            "cluster": "Chennai",
            "certifications": [],
            "qualifications": [
                {"Description": "B.E. in Civil Engineering"},
                {"Description": "M.E. in Structural Engineering"}
            ],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    update_keyword_lists(mock_profiles)
    
    # 1. Test "me" as pronoun is skipped
    res_pronoun = parse_query_rules("show me people with B.Tech and M.Tech")
    assert isinstance(res_pronoun["qualification"], list)
    assert set(res_pronoun["qualification"]) == {"B.Tech", "M.Tech"}
    
    # 2. Test "me" as qualification is matched
    res_qual = parse_query_rules("people with ME qualification")
    assert res_qual["qualification"] in ("M.E.", "M.E")
    
    # 3. Test "be" as auxiliary verb is skipped
    res_verb = parse_query_rules("who should be site engineer")
    assert res_verb["qualification"] is None
    
    # 4. Test "be" as qualification is matched
    res_be_qual = parse_query_rules("people with BE qualification")
    assert res_be_qual["qualification"] == "B.E."


def test_qualification_refinements_and_compounds():
    from backend.app.query_parser import parse_query_rules, update_keyword_lists
    from backend.app.structured_search import structured_search

    # 1. Test logic override refinement parsing
    res_ref_or = parse_query_rules("use OR logic for qualifications")
    assert res_ref_or["intent"] == "REFINEMENT"
    assert res_ref_or["qualification_operator"] == "or"

    res_ref_and = parse_query_rules("use AND logic for qualifications")
    assert res_ref_and["intent"] == "REFINEMENT"
    assert res_ref_and["qualification_operator"] == "and"

    res_ref_cert_or = parse_query_rules("use OR operator for certifications")
    assert res_ref_cert_or["intent"] == "REFINEMENT"
    assert res_ref_cert_or["certification_operator"] == "or"

    # 2. Test compound hyphenated/slashed qualifications
    mock_profiles = [
        {
            "ps_no": 101,
            "designation": "Civil Engineer",
            "qualifications": [
                {"Description": "MTech-Construction Engineering & Management"}
            ],
            "certifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        },
        {
            "ps_no": 102,
            "designation": "Civil Engineer",
            "qualifications": [
                {"Description": "B.Tech/B.E."}
            ],
            "certifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    update_keyword_lists(mock_profiles)

    # Parser should match "mtech" because we split hyphenated words during dynamic list rebuild
    res_mtech = parse_query_rules("people with mtech")
    assert res_mtech["qualification"] == "M.Tech"

    # Structured search should match mtech-construction profile against query filter "mtech" or "Mtech"
    matched_mtech = structured_search(mock_profiles, {"qualification": "mtech", "qualification_operator": "or"})
    assert len(matched_mtech) == 1
    assert matched_mtech[0]["ps_no"] == 101

    # Structured search should match B.Tech/B.E. profile against query filter "be" or "B.E."
    matched_be = structured_search(mock_profiles, {"qualification": "be", "qualification_operator": "or"})
    assert len(matched_be) == 1
    assert matched_be[0]["ps_no"] == 102

    # 3. Test parenthesized abbreviations like (DCE), (SSC), (BA)
    mock_parentheses_profiles = [
        {
            "ps_no": 201,
            "designation": "Civil Engineer",
            "qualifications": [
                {"Description": "Diploma in Civil Engineering (DCE)"},
                {"Description": "Secondary School Certificate (SSC)"},
                {"Description": "Bachelor of Arts (BA)"}
            ],
            "certifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        },
        {
            "ps_no": 202,
            "designation": "Civil Engineer",
            "qualifications": [
                {"Description": "Bachelor of Arts (BA)"}
            ],
            "certifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    matched_and = structured_search(mock_parentheses_profiles, {"qualification": ["dce", "ssc", "ba"], "qualification_operator": "and"})
    assert len(matched_and) == 1
    assert matched_and[0]["ps_no"] == 201

    # 4. Test alias expansion without parentheses
    mock_alias_profiles = [
        {
            "ps_no": 301,
            "designation": "Civil Engineer",
            "qualifications": [
                {"Description": "Diploma in Civil Engineering"},
                {"Description": "Secondary School Certificate"},
                {"Description": "Bachelor of Arts"}
            ],
            "certifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    # Check that querying via abbreviation "dce" matches "Diploma in Civil Engineering"
    matched_alias = structured_search(mock_alias_profiles, {"qualification": ["dce", "ssc", "ba"], "qualification_operator": "and"})
    assert len(matched_alias) == 1
    assert matched_alias[0]["ps_no"] == 301

    # Check that querying via full name "diploma in civil engineering" matches a profile with just "DCE"
    mock_dce_only = [{"ps_no": 302, "qualifications": [{"Description": "DCE"}], "certifications": [], "segment_exposure": [], "external_experience": [], "skills": []}]
    matched_full_name = structured_search(mock_dce_only, {"qualification": "diploma in civil engineering"})
    assert len(matched_full_name) == 1
    assert matched_full_name[0]["ps_no"] == 302


def test_qualification_dots_spaces_and_missing_staff():
    # 1. Test space after dot query normalization
    from backend.app.query_parser import parse_query_rules
    res = parse_query_rules("find people with B. Tech and B. E. and M. Tech")
    assert set(res["qualification"]) == {"B.Tech", "B.E.", "M.Tech"}

    # 2. Test ITI Fitter & SSC matching
    mock_profiles = [
        {
            "ps_no": 9901,
            "staff_name": "Test Fitter",
            "qualifications": [
                {"Description": "ITI Fitter"},
                {"Description": "Secondary School Certificate (SSC)"}
            ],
            "certifications": [],
            "segment_exposure": [],
            "external_experience": [],
            "skills": []
        }
    ]
    # Match using "iti fitter" and "ssc" with AND operator
    matched = structured_search(mock_profiles, {"qualification": ["iti fitter", "ssc"], "qualification_operator": "and"})
    assert len(matched) == 1
    assert matched[0]["ps_no"] == 9901

    # Match using just "fitter" and "ssc" with AND operator
    matched_fitter_ssc = structured_search(mock_profiles, {"qualification": ["fitter", "ssc"], "qualification_operator": "and"})
    assert len(matched_fitter_ssc) == 1

    # 3. Test join engine for missing staff master record
    import pandas as pd
    from backend.app.join_engine import build_employee_profiles
    cleaned_dfs = {
        "Staff_Master": pd.DataFrame(columns=["PS No", "Staff Name", "Email ID", "Mobile", "Cadre", "Band", "Designation",
                                             "Total Exp", "Internal Exp", "External Exp", "Job Code", "Job Name",
                                             "Cluster", "BU", "SBG", "IS PS No", "IS Name", "IS Email ID"]),
        "Internal_Exp": pd.DataFrame(columns=["PS No", "Org", "From", "To"]),
        "External_Exp": pd.DataFrame(columns=["PS No", "Org", "Designation", "From", "To"]),
        "Segment_Exposure": pd.DataFrame(columns=["PS No", "Segment", "Sub-Segment"]),
        "Skill_Proficiency": pd.DataFrame(columns=["PS No", "Staff Name", "Skill", "Sub-Skill", "User_Declared_Proficiency",
                                                   "Reviewed_Proficiency", "Is_Core_Skill"]),
        "Job_Skill_Mapping": pd.DataFrame(columns=["PS No", "Org", "Skill", "Sub-Skill", "Role", "Reporting Count", "Value"]),
        "Certification": pd.DataFrame(columns=["PS No", "Certification"]),
        "Qualification": pd.DataFrame([
            {"PS No": 11121, "Year": 2003, "Description": "Diploma in Civil Engineering (DCE)"},
            {"PS No": 11121, "Year": 2000, "Description": "Secondary School Certificate (SSC)"}
        ])
    }
    profiles = build_employee_profiles(cleaned_dfs)
    assert len(profiles) == 1
    assert profiles[0]["ps_no"] == 11121
    assert profiles[0]["staff_name"] == "Employee 11121"
    assert len(profiles[0]["qualifications"]) == 2













