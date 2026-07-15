import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.config.settings import PROCESSED_DIR, ETI_RESULTS_FILE

def run_summary_stats():
    # Load Results
    results_path = PROCESSED_DIR / ETI_RESULTS_FILE
    df = pd.read_csv(results_path)
    
    # Load Confounders (for IMD)
    conf_path = PROCESSED_DIR / "msoa_confounders_national.csv"
    df_conf = pd.read_csv(conf_path)
    
    # Load Region Lookup
    region_path = PROCESSED_DIR / "msoa_region_lookup.csv"
    df_region = pd.read_csv(region_path)
    
    # Merge
    df = df.merge(df_conf[['msoa_cd', 'income_dep_score']], left_on='msoa21cd', right_on='msoa_cd', how='left')
    df = df.merge(df_region, on='msoa21cd', how='left')
    
    # Calculate IMD Deciles
    df['imd_decile'] = pd.qcut(df['income_dep_score'], 10, labels=False) + 1
    
    # 1. IQR of T* for each IMD decile
    iqr_by_decile = df.groupby('imd_decile')['empirical_thermal_index'].agg(lambda x: x.quantile(0.75) - x.quantile(0.25))
    
    # 2. 90th percentile of T*
    p90_t_star = df['empirical_thermal_index'].quantile(0.90)
    high_failure_msoas = df[df['empirical_thermal_index'] >= p90_t_star]
    pct_high_failure_in_deprived = (high_failure_msoas['imd_decile'].isin([1, 2]).sum() / len(high_failure_msoas)) * 100
    
    # 3. Regional averages for North West vs. London
    regional_avg = df.groupby('region')['empirical_thermal_index'].mean()
    nw_avg = regional_avg.get('North West', np.nan)
    london_avg = regional_avg.get('London', np.nan)
    
    # Output
    output_path = PROCESSED_DIR / "regional_summary_stats.txt"
    with open(output_path, "w") as f:
        f.write("=== REGIONAL AND SOCIOECONOMIC SUMMARY STATS ===\n\n")
        f.write(f"National T* 90th Percentile: {p90_t_star:.2f} kWh/year\n")
        f.write(f"Percentage of High-Failure MSOAs in IMD Deciles 1 & 2: {pct_high_failure_in_deprived:.2f}%\n\n")
        f.write("IQR of T* by IMD Decile:\n")
        f.write(iqr_by_decile.to_string())
        f.write("\n\nRegional Averages:\n")
        f.write(f"North West Average T*: {nw_avg:.2f} kWh/year\n")
        f.write(f"London Average T*: {london_avg:.2f} kWh/year\n")
        f.write("\nFull Regional Breakdown:\n")
        f.write(regional_avg.to_string())
        
    print(open(output_path).read())

if __name__ == "__main__":
    run_summary_stats()
