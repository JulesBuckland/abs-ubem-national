import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import os
import sys

# Add root to path
sys.path.append(os.getcwd())
from src.config.settings import PROCESSED_DIR, ETI_RESULTS_FILE

def run_real_ukhls_validation():
    print("--- V10.3 REAL UKHLS CONVERGENT VALIDATION (Wave 13) ---")
    
    # 1. Load Model Results
    eti_path = PROCESSED_DIR / ETI_RESULTS_FILE
    if not eti_path.exists():
        print(f"Error: ETI results not found at {eti_path}")
        return
    eti_df = pd.read_csv(eti_path)
    
    # Load Regional Lookup
    lookup_path = PROCESSED_DIR / "msoa_region_lookup.csv"
    if not lookup_path.exists():
        print("Error: Regional lookup not found. Attempting to recover from synthetic pop...")
        syn_path = PROCESSED_DIR / "national_synthetic_population_eti.csv"
        if os.path.exists(syn_path):
             # We don't have region in the synthetic pop from previous scripts, 
             # let's try to join with the national confounders which has region?
             conf_path = PROCESSED_DIR / "msoa_confounders_national.csv"
             if os.path.exists(conf_path):
                 lookup = pd.read_csv(conf_path)[['msoa_cd', 'region']].rename(columns={'msoa_cd': 'msoa21cd'})
             else:
                 print("Error: National confounders not found.")
                 return
        else:
            return
    else:
        lookup = pd.read_csv(lookup_path)
    
    eti_reg = eti_df.merge(lookup, on='msoa21cd')
    regional_eti = eti_reg.groupby('region')['empirical_thermal_index'].mean()
    
    # 2. Load Real UKHLS Wave 13 Data
    ukhls_path = Path("data/raw/ukhls_extracted/UKDA-6614-stata/stata/stata14_se/ukhls/m_hhresp.dta")
    if not ukhls_path.exists():
        print(f"Error: UKHLS Wave 13 data not found at {ukhls_path}")
        return
        
    print("Loading actual UKHLS Wave 13...")
    # m_xpgasy: Amount spent on gas (annual)
    # m_gor_dv: Region
    ukhls = pd.read_stata(ukhls_path, columns=['m_xpgasy', 'm_gor_dv', 'm_heatch'])
    
    # Clean gas spend
    # STATA often has negative values for missing/refusal
    ukhls['gas_spend'] = pd.to_numeric(ukhls['m_xpgasy'], errors='coerce')
    ukhls = ukhls[ukhls['gas_spend'] > 0]
    
    # Regional aggregation
    ukhls_reg = ukhls.groupby('m_gor_dv')['gas_spend'].mean()
    
    # Standardize Region Names for alignment
    # UKHLS: ['South East', 'North West', 'London', 'Scotland', 'East of England', 'South West', 'Yorkshire and the Humber', 'West Midlands', 'East Midlands', 'Wales', 'Northern Ireland', 'North East']
    # Model: ['East Midlands', 'East of England', 'London', 'North East', 'North West', 'South East', 'South West', 'West Midlands', 'Yorkshire and The Humber']
    
    ukhls_reg.index = ukhls_reg.index.astype(str)
    
    common_regions = list(set(regional_eti.index) & set(ukhls_reg.index))
    print(f"Aligning {len(common_regions)} English regions.")
    
    df_compare = pd.DataFrame({
        'Model_T_star': regional_eti.loc[common_regions],
        'UKHLS_Gas_Spend': ukhls_reg.loc[common_regions]
    }).dropna()
    
    # 3. Spearman Correlation
    corr, p = stats.spearmanr(df_compare['Model_T_star'], df_compare['UKHLS_Gas_Spend'])
    
    print(f"\nREAL Regional Spearman Correlation: r={corr:.4f}, p={p:.4f}")
    
    # 4. Save Report
    report_path = PROCESSED_DIR / "ukhls_validation_report.txt"
    with open(report_path, "w") as f:
        f.write("V10.3 Methodological Audit: Real UKHLS Wave 13 Validation\n")
        f.write("========================================================\n\n")
        f.write(f"UKHLS File: m_hhresp.dta\n")
        f.write(f"Variable: m_xpgasy (Annual Gas Spend)\n")
        f.write(f"Spearman r: {corr:.4f}\n")
        f.write(f"p-value: {p:.4f}\n\n")
        f.write("Data Table:\n")
        f.write(df_compare.to_string())
        
    print(f"Validation report saved to {report_path}")

if __name__ == "__main__":
    run_real_ukhls_validation()
