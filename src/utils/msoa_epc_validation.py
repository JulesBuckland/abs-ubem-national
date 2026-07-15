import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import os
import sys

# Add root to path
sys.path.append(os.getcwd())
from src.config.settings import PROCESSED_DIR, RAW_DIR, ETI_RESULTS_FILE

def run_validation():
    print("--- V9 MSOA-LEVEL EPC VALIDATION ---")
    
    # 1. Load Model Results
    eti_path = PROCESSED_DIR / ETI_RESULTS_FILE
    if not eti_path.exists():
        print("Error: ETI results not found.")
        return
    eti_df = pd.read_csv(eti_path)
    
    # 2. Load IoD 2019 "Housing in poor condition" indicator (Proxy for EPC F/G)
    # This is the primary component of the Living Environment domain provided by DLUHC
    iod_path = Path(".temp downloads/File_8_-_IoD2019_Underlying_Indicators.xlsx")
    if not iod_path.exists():
        print("Error: IoD indicators file not found.")
        return
        
    print("Loading IoD Housing Indicators...")
    iod_df = pd.read_excel(iod_path, sheet_name='IoD2019 Living Env Domain')
    # Column: 'Housing in poor condition indicator'
    
    # 3. Load LSOA to MSOA lookup
    lookup_path = RAW_DIR / "spatial" / "lookup.csv"
    if not lookup_path.exists():
        lookup_path = RAW_DIR / "lookup.csv"
    
    lookup = pd.read_csv(lookup_path, usecols=['lsoa21cd', 'msoa21cd']).drop_duplicates()
    
    # 4. Aggregate to MSOA
    # Merge IoD with lookup
    # Note: IoD uses 2011 LSOA codes, but we usually have a mapping
    merged_iod = iod_df.merge(lookup, left_on='LSOA code (2011)', right_on='lsoa21cd')
    msoa_poor_housing = merged_iod.groupby('msoa21cd')['Housing in poor condition indicator'].mean().reset_index()
    
    # 5. Join with ETI Results
    final_df = eti_df.merge(msoa_poor_housing, on='msoa21cd')
    
    # 6. Correlate
    corr, p = stats.spearmanr(final_df['empirical_thermal_index'], final_df['Housing in poor condition indicator'])
    
    print(f"\nSpearman Correlation (MSOA Level): r={corr:.3f}, p={p:.3e}")
    print(f"Sample Size: {len(final_df)} MSOAs")
    
    # 7. Save results
    out_path = PROCESSED_DIR / "msoa_epc_validation.csv"
    final_df.to_csv(out_path, index=False)
    
    report_path = PROCESSED_DIR / "msoa_epc_validation_report.txt"
    with open(report_path, "w") as f:
        f.write("V9 Methodological Audit: MSOA-Level EPC Validation\n")
        f.write("================================================\n\n")
        f.write(f"Proxy: DLUHC 'Housing in poor condition' indicator (MSOA aggregated)\n")
        f.write(f"Spearman Correlation: {corr:.3f}\n")
        f.write(f"P-value: {p:.3e}\n")
        f.write(f"N: {len(final_df)} MSOAs\n")
    
    print(f"Validation report saved to {report_path}")

if __name__ == "__main__":
    run_validation()
