import io
import re
import pandas as pd
from typing import Dict, Tuple, Optional, Union

REQUIRED_SHEETS_COLUMNS = {
    "Staff_Master": [
        "PS No", "Staff Name", "Email ID", "Mobile", "Cadre", "Band", "Designation",
        "Total Exp", "Internal Exp", "External Exp", "Job Code", "Job Name",
        "Cluster", "BU", "SBG", "IS PS No", "IS Name", "IS Email ID"
    ],
    "Internal_Exp": [
        "PS No", "Org", "From", "To"
    ],
    "External_Exp": [
        "PS No", "Org", "Designation", "From", "To"
    ],
    "Segment_Exposure": [
        "PS No", "Segment", "Sub-Segment"
    ],
    "Skill_Proficiency": [
        "PS No", "Staff Name", "Skill", "Sub-Skill", "User_Declared_Proficiency",
        "Reviewed_Proficiency", "Is_Core_Skill"
    ],
    "Job_Skill_Mapping": [
        "PS No", "Org", "Skill", "Sub-Skill", "Role", "Reporting Count", "Value"
    ],
    "Certification": [
        "PS No", "Certification"
    ],
    "Qualification": [
        "PS No", "Year", "Description"
    ]
}

# --- Helper Functions for Robust Normalization ---

def normalize_sheet_name(name: str) -> str:
    """Normalize sheet names to lower_snake_case and remove dots/spaces/dashes."""
    cleaned = str(name).strip().lower().replace(".", "")
    cleaned = re.sub(r'[\s\-_]+', '_', cleaned)
    return cleaned.strip('_')

# Specific common typo corrections
TYPO_MAPPING = {
    "desgination": "designation",
    "desig": "designation",
    "interal exp": "internal exp",
    "interal exp.": "internal exp",
    "internal exp.": "internal exp",
    "external exp.": "external exp",
    "total exp.": "total exp",
    "ps no.": "ps no",
}

def normalize_column_name(col: str) -> str:
    """Normalize column names to lowercase, remove dots, and replace delimiters with spaces."""
    cleaned = str(col).strip().lower().replace(".", "")
    cleaned = re.sub(r'[\s\-_]+', ' ', cleaned).strip()
    
    # Resolve known typos
    if cleaned in TYPO_MAPPING:
        cleaned = TYPO_MAPPING[cleaned]
        
    return cleaned

# Pre-build normalized mappings for sheets and columns
NORMALIZED_SHEETS = {normalize_sheet_name(sheet): sheet for sheet in REQUIRED_SHEETS_COLUMNS.keys()}

NORMALIZED_COLUMNS = {}
for sheet, cols in REQUIRED_SHEETS_COLUMNS.items():
    for col in cols:
        normalized = normalize_column_name(col)
        NORMALIZED_COLUMNS[normalized] = col

def load_excel_sheets(file_input: Union[bytes, str]) -> Tuple[Optional[Dict[str, pd.DataFrame]], Optional[str]]:
    """
    Load Excel file (either bytes or a path to file) and parse into a dictionary of DataFrames.
    Robustly validates sheets and columns by handling whitespace, dots, and typos.

    Returns:
        (Dict[sheet_name, DataFrame], None) on success.
        (None, error_message) on failure.
    """
    try:
        if isinstance(file_input, bytes):
            excel_file = pd.ExcelFile(io.BytesIO(file_input), engine="openpyxl")
        else:
            excel_file = pd.ExcelFile(file_input, engine="openpyxl")
            
        sheet_names = excel_file.sheet_names
        
        # Build mapping of normalized sheet name present in Excel -> actual sheet name in Excel
        excel_sheets_map = {}
        for sname in sheet_names:
            excel_sheets_map[normalize_sheet_name(sname)] = sname
            
        # Check if all required sheets exist (using normalized names)
        missing_sheets = []
        for req_sheet in REQUIRED_SHEETS_COLUMNS.keys():
            req_normalized = normalize_sheet_name(req_sheet)
            if req_normalized not in excel_sheets_map:
                missing_sheets.append(req_sheet)
                
        if missing_sheets:
            return None, f"Missing required sheets in Excel workbook: {', '.join(missing_sheets)}"
            
        dfs = {}
        for req_sheet, req_cols in REQUIRED_SHEETS_COLUMNS.items():
            req_normalized = normalize_sheet_name(req_sheet)
            actual_sheet_name = excel_sheets_map[req_normalized]
            
            # Load sheet into df
            df = excel_file.parse(actual_sheet_name)
            
            # Normalize column names in df (strip whitespace & match aliases/case-insensitively)
            rename_map = {}
            for col in df.columns:
                col_str = str(col).strip()
                col_normalized = normalize_column_name(col_str)
                if col_normalized in NORMALIZED_COLUMNS:
                    rename_map[col] = NORMALIZED_COLUMNS[col_normalized]
                else:
                    rename_map[col] = col_str
                    
            df.rename(columns=rename_map, inplace=True)
            
            # Check for missing columns
            missing_cols = []
            for col in req_cols:
                if col not in df.columns:
                    missing_cols.append(col)
                    
            if missing_cols:
                return None, f"Sheet '{actual_sheet_name}' is missing required columns: {', '.join(missing_cols)}"
                
            # Keep only the columns we expect
            df = df[req_cols]
            dfs[req_sheet] = df
            
        return dfs, None
        
    except Exception as e:
        return None, f"Failed to parse Excel workbook: {str(e)}"
