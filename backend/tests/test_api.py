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




