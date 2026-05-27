import pandas as pd
import numpy as np
import re
from typing import Dict, Optional
import datetime

def clean_data(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Clean and normalize DataFrames in the workbook dictionary.
    
    Cleaning steps:
    1. Drop rows with missing primary key ('PS No').
    2. Convert 'PS No' to standard int type.
    3. Trim whitespace from all string values.
    4. Normalize date strings to standard 'DD-MM-YYYY'.
    5. Clean and normalize proficiency casings.
    6. Drop exact duplicates across each sheet.
    7. Standardize missing/empty values (convert NaN/None/empty strings to None or default values).
    """
    cleaned_dfs = {}
    
    for sheet_name, df in dfs.items():
        df_copy = df.copy()
        
        # 1. Handle primary key 'PS No' validation
        if "PS No" in df_copy.columns:
            df_copy["PS No"] = pd.to_numeric(df_copy["PS No"], errors="coerce")
            df_copy.dropna(subset=["PS No"], inplace=True)
            df_copy["PS No"] = df_copy["PS No"].astype(int)
            
        # 2. Trim whitespace and handle string columns
        for col in df_copy.columns:
            if df_copy[col].dtype == "object":
                df_copy[col] = df_copy[col].apply(lambda x: str(x).strip() if pd.notna(x) else None)
                
        # 3. Clean specific columns based on sheet type
        if sheet_name == "Staff_Master":
            # Clean experience numbers
            df_copy["Total Exp"] = pd.to_numeric(df_copy["Total Exp"], errors="coerce").fillna(0.0)
            df_copy["Internal Exp"] = pd.to_numeric(df_copy["Internal Exp"], errors="coerce").fillna(0.0)
            df_copy["External Exp"] = pd.to_numeric(df_copy["External Exp"], errors="coerce").fillna(0.0)
            
            # Supervisor PS No
            df_copy["IS PS No"] = pd.to_numeric(df_copy["IS PS No"], errors="coerce")
            df_copy["IS PS No"] = df_copy["IS PS No"].apply(lambda x: int(x) if pd.notna(x) else None)
            
        elif sheet_name in ["Internal_Exp", "External_Exp"]:
            # Clean dates to DD-MM-YYYY format
            for col in ["From", "To"]:
                if col in df_copy.columns:
                    df_copy[col] = df_copy[col].apply(_normalize_date)
                    
        elif sheet_name == "Skill_Proficiency":
            # Clean proficiencies to Title Case
            for col in ["User_Declared_Proficiency", "Reviewed_Proficiency"]:
                df_copy[col] = df_copy[col].apply(lambda x: str(x).strip().title() if x else None)
            # Normalize core skill flag
            df_copy["Is_Core_Skill"] = df_copy["Is_Core_Skill"].apply(
                lambda x: "Yes" if str(x).strip().lower() in ["yes", "y", "true", "1"] else ""
            )
            
        elif sheet_name == "Job_Skill_Mapping":
            # Value field clean
            df_copy["Value"] = pd.to_numeric(df_copy["Value"], errors="coerce").fillna(0.0)
            # Reporting Count clean: remove whitespace, convert to string
            df_copy["Reporting Count"] = df_copy["Reporting Count"].apply(
                lambda x: str(x).strip() if pd.notna(x) else "nil"
            )
            
        elif sheet_name == "Qualification":
            df_copy["Year"] = pd.to_numeric(df_copy["Year"], errors="coerce")
            df_copy["Year"] = df_copy["Year"].apply(lambda x: int(x) if pd.notna(x) else None)

        # 4. Remove duplicate rows
        df_copy.drop_duplicates(inplace=True)
        df_copy.reset_index(drop=True, inplace=True)
        
        cleaned_dfs[sheet_name] = df_copy
        
    return cleaned_dfs

def _normalize_date(date_val) -> Optional[str]:
    """Helper to convert date objects or strings of various formats into DD-MM-YYYY."""
    if pd.isna(date_val) or date_val is None:
        return None
        
    # If it is already a datetime or timestamp
    if isinstance(date_val, (pd.Timestamp, datetime.datetime, datetime.date)):
        return date_val.strftime("%d-%m-%Y")
        
    date_str = str(date_val).strip()
    if date_str.lower() in ["nan", "none", "null", ""]:
        return None
        
    # Attempt common regex patterns
    # 1. YYYY-MM-DD
    match_ymd = re.match(r"^(\d{4})[-/](\d{2})[-/](\d{2})", date_str)
    if match_ymd:
        y, m, d = match_ymd.groups()
        return f"{d}-{m}-{y}"
        
    # 2. DD-MM-YYYY
    match_dmy = re.match(r"^(\d{2})[-/](\d{2})[-/](\d{4})", date_str)
    if match_dmy:
        d, m, y = match_dmy.groups()
        return f"{d}-{m}-{y}"
        
    # Attempt general parsing
    try:
        dt = pd.to_datetime(date_str, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%d-%m-%Y")
    except Exception:
        pass
        
    return date_str
