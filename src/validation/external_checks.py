import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import logging
from src.config.settings import RAW_DIR, PROCESSED_DIR, ETI_RESULTS_FILE, setup_logging
import os

logger = setup_logging("ExternalValidation")

def run_external_validation():
    logger.info("--- STAGE 5c: EXTERNAL VALIDATION (LAD LEVEL) ---")
    
    # 1. Load T* (Behaviorally-Adjusted Thermal Requirement) Results
    eti_path = PROCESSED_DIR / ETI_RESULTS_FILE
    if not eti_path.exists():
        logger.error(f"Results not found at {eti_path}.")
        return
    results_df = pd.read_csv(eti_path)
    
    # 2. Load MSOA to LAD lookup
    lookup_path = PROCESSED_DIR / "msoa_lad_lookup.csv"
    if not lookup_path.exists():
        logger.error(f"Lookup not found at {lookup_path}.")
        return
    lookup_df = pd.read_csv(lookup_path)
    
    # Merge and aggregate to LAD
    df = results_df.merge(lookup_df, left_on='msoa21cd', right_on='msoa21cd', how='inner')
    lad_df = df.groupby('ladcd').agg({'empirical_thermal_index': 'mean'}).reset_index()
    lad_df.rename(columns={'empirical_thermal_index': 'T_star_mean'}, inplace=True)
    
    # 3. Load Real External Data (IMD Income Score as proxy for Energy Vulnerability/LILEE)
    imd_path = RAW_DIR / "imd" / "imd_2019_msoa.csv"
    if not imd_path.exists():
        logger.error(f"IMD data not found at {imd_path}.")
        return
    imd_df = pd.read_csv(imd_path)
    
    # Aggregate IMD to LAD
    df_with_imd = df.merge(imd_df, on='msoa21cd')
    lad_validation = df_with_imd.groupby('ladcd').agg({
        'empirical_thermal_index': 'mean',
        'income_score': 'mean'
    }).reset_index()
    
    # 4. Correlate
    # Spearman is preferred for rank-based validation against deprivation indices
    corr, p = stats.spearmanr(lad_validation['empirical_thermal_index'], lad_validation['income_score'])
    
    logger.info(f"Spearman Correlation with IMD Income Score (LAD Level): r={corr:.3f}, p={p:.3e}")
    
    # 5. Output Results
    results_path = PROCESSED_DIR / "external_validation_results.csv"
    lad_validation.to_csv(results_path, index=False)
    
    report_path = PROCESSED_DIR / "external_validation_report.txt"
    with open(report_path, "w") as f:
        f.write("=== EXTERNAL VALIDATION (LAD LEVEL) ===\n")
        f.write(f"Proxy: IMD Income Score (LAD-aggregated)\n")
        f.write(f"Correlation: Spearman r={corr:.3f}, p={p:.3e}\n")
        f.write(f"Observations: {len(lad_validation)} Local Authorities\n")
    logger.info(f"Validation report saved to {report_path}")

if __name__ == "__main__":
    run_external_validation()
