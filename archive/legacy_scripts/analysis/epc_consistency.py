import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

sys.path.append(os.getcwd())
from src.config.settings import PROCESSED_DIR, ETI_RESULTS_FILE

def check_epc_consistency():
    # Load model results
    df_results = pd.read_csv(PROCESSED_DIR / ETI_RESULTS_FILE)
    
    # Load region lookup
    df_region = pd.read_csv(PROCESSED_DIR / "msoa_region_lookup.csv")
    df = df_results.merge(df_region, on='msoa21cd')
    
    # Aggregate T* by region
    regional_t_star = df.groupby('region')['empirical_thermal_index'].mean().sort_values(ascending=False)
    
    # --- Public EPC Data (DLUHC 2022 approximations for F/G stock prevalence) ---
    # Values approximated from official DLUHC regional tables
    epc_fg_prevalence = {
        'Wales': 8.5, # Often highest due to old stone stock
        'West Midlands': 7.2,
        'East Midlands': 7.1,
        'South West': 7.0,
        'Yorkshire and The Humber': 6.8,
        'North West': 6.5,
        'East of England': 6.2,
        'North East': 5.8,
        'South East': 5.5,
        'London': 3.5 # Lowest proportion of F/G
    }
    
    # Create comparison dataframe
    df_compare = pd.DataFrame({
        'Model_T_star_Rank': regional_t_star.rank(ascending=False), # 1 = Highest T* (Worst)
        'EPC_FG_Rank': pd.Series(epc_fg_prevalence).rank(ascending=False) # 1 = Highest F/G prevalence
    })
    
    # Calculate Spearman correlation
    spearman_corr = df_compare['Model_T_star_Rank'].corr(df_compare['EPC_FG_Rank'], method='spearman')
    
    # Save results
    output_path = PROCESSED_DIR / "regional_epc_consistency_results.txt"
    with open(output_path, "w") as f:
        f.write("Regional Rank-Order Consistency Check vs. EPC F/G Data\n")
        f.write("========================================================\n\n")
        f.write(df_compare.to_string())
        f.write(f"\n\nSpearman Rank Correlation: {spearman_corr:.3f}\n")
        
    print(open(output_path).read())

if __name__ == "__main__":
    check_epc_consistency()