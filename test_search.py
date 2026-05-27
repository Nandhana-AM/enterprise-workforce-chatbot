import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.app.excel_loader import load_excel_sheets
from backend.app.data_cleaner import clean_data
from backend.app.join_engine import build_employee_profiles
from backend.app.query_parser import parse_query_rules, update_keyword_lists

with open("synthetic_skill_dataset.xlsx", "rb") as f:
    excel_bytes = f.read()

dfs, err = load_excel_sheets(excel_bytes)
if err:
    print("Error loading excel:", err)
    sys.exit(1)

cleaned = clean_data(dfs)
profiles = build_employee_profiles(cleaned)

# Extract and print unique skills in the dataset
skills = set()
for p in profiles:
    for s in p["skills"]:
        skills.add(s["Skill"])
print("Unique skills in database:")
print(sorted(list(skills))[:15])

# Print query parser output for the query
update_keyword_lists(profiles)
parsed = parse_query_rules("find people skilled in waterproofing with atleast 5 years experience")
print("\nParsed filters for 'find people skilled in waterproofing with atleast 5 years experience':")
for k, v in parsed.items():
    if v is not None and v != "" and v != False:
        print(f"  {k}: {v}")
