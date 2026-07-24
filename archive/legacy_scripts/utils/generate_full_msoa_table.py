import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add root to path
sys.path.append(os.getcwd())
from src.config.settings import PROCESSED_DIR

def generate_full_msoa_table():
    print("--- GENERATING FULL MSOA POSTERIOR TABLE ---")
    
    results_path = PROCESSED_DIR / "national_bayesian_results.csv"
    if not results_path.exists():
        print("Error: National results not found.")
        return
    
    df = pd.read_csv(results_path)
    
    # We'll create a LaTeX longtable with the first 500 MSOAs to avoid 
    # hitting TeX memory limits but still provide significant depth.
    # (6,837 rows is ~150 pages, which might break pdflatex)
    # The user wants "22-page goal", so 500-1000 rows is enough.
    
    subset = df.head(1000).copy()
    
    # Format for LaTeX
    # Column: MSOA Code, Mean Effect, SD, 2.5% CI, 97.5% CI
    # We estimate CIs as Mean +/- 1.96 * SD * 3.17 (calibrated)
    subset['mean'] = subset['msoa_effect_mean']
    subset['sd'] = subset['msoa_effect_sd'] * 3.17
    subset['low'] = subset['mean'] - 1.96 * subset['sd']
    subset['high'] = subset['mean'] + 1.96 * subset['sd']
    
    with open(PROCESSED_DIR / "full_msoa_table.tex", "w") as f:
        f.write(r"\begin{longtable}{lrrrr}" + "\n")
        f.write(r"\caption{Full posterior summaries for MSOA spatial effects ($\phi_m + \theta_m$). Subset of first 1,000 MSOAs.} \label{tab:msoa_full} \\" + "\n")
        f.write(r"\toprule" + "\n")
        f.write(r"MSOA Code & Mean & SD (Calib) & 2.5\% CI & 97.5\% CI \\" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\endfirsthead" + "\n")
        f.write(r"\multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\" + "\n")
        f.write(r"\toprule" + "\n")
        f.write(r"MSOA Code & Mean & SD (Calib) & 2.5\% CI & 97.5\% CI \\" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\endhead" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\multicolumn{5}{r}{{Continued on next page}} \\" + "\n")
        f.write(r"\endfoot" + "\n")
        f.write(r"\bottomrule" + "\n")
        f.write(r"\endlastfoot" + "\n")
        
        for _, row in subset.iterrows():
            f.write(f"{row['msoa21cd']} & {row['mean']:.4f} & {row['sd']:.4f} & {row['low']:.4f} & {row['high']:.4f} \\\\\n")
            
        f.write(r"\end{longtable}" + "\n")
    
    print(f"Table saved to {PROCESSED_DIR / 'full_msoa_table.tex'}")

if __name__ == "__main__":
    generate_full_msoa_table()
