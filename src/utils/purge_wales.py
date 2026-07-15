import pandas as pd
from pathlib import Path
import os

PROCESSED_DIR = Path("data/processed")

def purge_wales():
    files = [
        "msoa_heating_deficit_results.csv",
        "msoa_confounders_national.csv",
        "msoa_lad_lookup.csv"
    ]
    
    # MASTER LIST from IMD
    imd_path = Path("data/raw/imd/imd_2019_msoa.csv")
    if not imd_path.exists():
        print("IMD Master list not found.")
        return
    
    imd_msoas = set(pd.read_csv(imd_path).iloc[:, 0].unique())
    print(f"Master IMD MSOA count: {len(imd_msoas)}")

    for file_name in files:
        path = PROCESSED_DIR / file_name
        if not path.exists():
            print(f"File not found: {path}")
            continue
            
        print(f"Purging {file_name} to match IMD master list...")
        df = pd.read_csv(path)
        
        # Identify the MSOA column
        msoa_col = None
        for col in df.columns:
            if 'msoa' in col.lower() or 'cd' in col.lower():
                msoa_col = col
                break
        
        if msoa_col is None:
            print(f"Could not find MSOA column in {file_name}. Skipping.")
            continue
            
        initial_len = len(df)
        # Filter to only keep MSOAs in the IMD master list
        df = df[df[msoa_col].isin(imd_msoas)].copy()
        final_len = len(df)
        
        df.to_csv(path, index=False)
        print(f"Purged {initial_len - final_len} rows. New count: {final_len}")

if __name__ == "__main__":
    purge_wales()
