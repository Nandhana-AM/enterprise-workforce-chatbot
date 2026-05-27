import pandas as pd

file_path = r"C:\Users\ASUS\Downloads\Skill_Data_Dump_R1_2026_05_25 - Copy.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    df_staff = xl.parse("Staff_Master")
    
    print("\nColumns in Staff_Master:")
    print(df_staff.columns.tolist())
    
    print("\nSample rows in Staff_Master (first 5):")
    print(df_staff.head(5).to_string())
    
    # Check if 'Hyderabad' appears anywhere in the entire Staff_Master sheet (case-insensitive)
    mask = df_staff.astype(str).apply(lambda x: x.str.contains("hyderabad", case=False)).any(axis=1)
    matching_rows = df_staff[mask]
    print(f"\nNumber of rows containing 'hyderabad' anywhere in Staff_Master: {len(matching_rows)}")
    if len(matching_rows) > 0:
        print("Sample matching rows:")
        print(matching_rows.head(3).to_string())
        
except Exception as e:
    print("Error:", str(e))
