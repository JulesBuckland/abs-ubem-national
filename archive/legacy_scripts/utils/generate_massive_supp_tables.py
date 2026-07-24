import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add root to path
sys.path.append(os.getcwd())
from src.config.settings import PROCESSED_DIR, RAW_DIR

def generate_massive_supp_tables():
    print("--- V10.3: GENERATING MASSIVE SUPPLEMENTARY TABLES (FIXED) ---")
    
    # 1. Convergence Diagnostics (Longtable for first 100 MSOAs)
    # Target Marginals
    ts044_path = RAW_DIR / "census" / "ts044_extracted" / "census2021-ts044-msoa.csv"
    if not ts044_path.exists(): ts044_path = RAW_DIR / "census" / "census2021-ts044-msoa.csv"
    ts044 = pd.read_csv(ts044_path)
    
    # Synthetic population
    syn = pd.read_csv(PROCESSED_DIR / "national_synthetic_population_eti.csv")
    syn_counts = syn.groupby(['msoa21cd', 'property_type']).size().unstack(fill_value=0)
    
    msoas = syn['msoa21cd'].unique()[:100] # First 100
    
    with open(PROCESSED_DIR / "supp_convergence_table.tex", "w") as f:
        f.write(r"\begin{longtable}{lrrr}" + "\n")
        f.write(r"\caption{MSOA-level Synthesis Marginal Validation (Top 100). Reported as Absolute Percentage Error (APE) relative to Census 2021.} \label{tab:supp_conv} \\" + "\n")
        f.write(r"\toprule" + "\n")
        f.write(r"MSOA Code & House APE (\%) & Flat APE (\%) & Total MSOA MAPE (\%) \\" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\endfirsthead" + "\n")
        f.write(r"\multicolumn{4}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\" + "\n")
        f.write(r"\toprule" + "\n")
        f.write(r"MSOA Code & House APE (\%) & Flat APE (\%) & Total MSOA MAPE (\%) \\" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\endhead" + "\n")
        f.write(r"\bottomrule" + "\n")
        f.write(r"\endfoot" + "\n")
        
        for msoa in msoas:
            if msoa not in ts044['geography code'].values: continue
            target = ts044[ts044['geography code'] == msoa].iloc[0]
            t_house = target['Accommodation type: Detached'] + target['Accommodation type: Semi-detached'] + target['Accommodation type: Terraced']
            t_flat = target['Accommodation type: In a purpose-built block of flats or tenement'] + target['Accommodation type: Part of a converted or shared house, including bedsits']
            total = t_house + t_flat + target['Accommodation type: A caravan or other mobile or temporary structure']
            if total == 0: continue
            
            t_house_p = (t_house / total) * 100
            t_flat_p = (t_flat / total) * 100
            
            s_house = syn_counts.loc[msoa, 'House'] if 'House' in syn_counts.columns else 0
            s_flat = syn_counts.loc[msoa, 'Flat'] if 'Flat' in syn_counts.columns else 0
            
            ape_house = np.abs(t_house_p - s_house)
            ape_flat = np.abs(t_flat_p - s_flat)
            mape = (ape_house + ape_flat) / 2
            
            f.write(f"{msoa} & {ape_house:.4f} & {ape_flat:.4f} & {mape:.4f} \\\\\n")
            
        f.write(r"\bottomrule" + "\n")
        f.write(r"\end{longtable}" + "\n")

    # 2. Full Posterior Summary (Longtable for first 200 spatial random effects)
    res = pd.read_csv(PROCESSED_DIR / "national_bayesian_results.csv")
    subset = res.head(200).copy()
    subset['sd_calib'] = subset['msoa_effect_sd'] * 3.17
    subset['low'] = subset['msoa_effect_mean'] - 1.96 * subset['sd_calib']
    subset['high'] = subset['msoa_effect_mean'] + 1.96 * subset['sd_calib']
    
    with open(PROCESSED_DIR / "supp_posterior_spatial.tex", "w") as f:
        f.write(r"\begin{longtable}{lrrrr}" + "\n")
        f.write(r"\caption{Posterior summaries for MSOA spatial effects ($\phi_m + \theta_m$) with 3.17x ADVI-NUTS calibration. (First 200 MSOAs).} \label{tab:supp_post_phi} \\" + "\n")
        f.write(r"\toprule" + "\n")
        f.write(r"MSOA Code & Mean & SD (Calib) & 2.5\% CI & 97.5\% CI \\" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\endfirsthead" + "\n")
        f.write(r"\toprule" + "\n")
        f.write(r"MSOA Code & Mean & SD (Calib) & 2.5\% CI & 97.5\% CI \\" + "\n")
        f.write(r"\midrule" + "\n")
        f.write(r"\endhead" + "\n")
        f.write(r"\bottomrule" + "\n")
        f.write(r"\endfoot" + "\n")
        
        for _, row in subset.iterrows():
            f.write(f"{row['msoa21cd']} & {row['msoa_effect_mean']:.4f} & {row['sd_calib']:.4f} & {row['low']:.4f} & {row['high']:.4f} \\\\\n")
            
        f.write(r"\bottomrule" + "\n")
        f.write(r"\end{longtable}" + "\n")

    print("Supp tables generated.")

if __name__ == "__main__":
    generate_massive_supp_tables()
