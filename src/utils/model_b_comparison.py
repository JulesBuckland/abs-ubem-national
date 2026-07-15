import pandas as pd
import numpy as np
import pymc as pm
import arviz as az
from pathlib import Path
import os
import sys
import logging
import gc

# Add root to path
sys.path.append(os.getcwd())
from src.config.settings import PROCESSED_DIR, HEATING_DEFICIT_FILE, RANDOM_SEED

# Silence spam
logging.getLogger("pymc").setLevel(logging.ERROR)
logging.getLogger("arviz").setLevel(logging.ERROR)

def run_comparison():
    print("--- V9 MODEL COMPARISON: PHYSICS PRIOR (A) VS. NO PHYSICS (B) ---")
    
    # 1. Load Data
    deficit_path = PROCESSED_DIR / HEATING_DEFICIT_FILE
    conf_path = PROCESSED_DIR / "msoa_confounders_national.csv"
    
    df = pd.read_csv(deficit_path).merge(pd.read_csv(conf_path), left_on='msoa21cd', right_on='msoa_cd')
    
    # Use a representative subset of 500 MSOAs for the comparison (Phase 1)
    df = df.sample(n=min(500, len(df)), random_state=RANDOM_SEED)
    print(f"Using {len(df)} MSOAs for the comparison pilot.")
    
    # Pre-process
    y_obs = np.log(df['empirical_gas_kwh'].values)
    theory_need_log = np.log(df['theoretical_gas_kwh'].values)
    income_score = df['income_dep_score'].values
    income_z = (income_score - income_score.mean()) / income_score.std()
    
    results = {}

    # --- MODEL A: WITH PHYSICS PRIOR ---
    print("\nRunning Model A (Physics Prior)...")
    with pm.Model() as model_a:
        beta_theory = pm.Normal("beta_theory", mu=-0.3, sigma=0.1)
        beta_income = pm.Normal("beta_income", mu=0.0, sigma=0.5)
        sigma = pm.HalfNormal("sigma", 0.5)
        
        mu = theory_need_log + beta_theory + beta_income * income_z
        y = pm.Normal("y", mu=mu, sigma=sigma, observed=y_obs)
        
        # Using fewer samples for speed in comparison
        trace_a = pm.sample(500, tune=500, chains=2, random_seed=RANDOM_SEED, progressbar=False, idata_kwargs={"log_likelihood": True})
        waic_a = az.waic(trace_a)
        results['Model A'] = waic_a
        
    gc.collect()

    # --- MODEL B: WITHOUT PHYSICS PRIOR ---
    print("\nRunning Model B (No Physics Prior)...")
    with pm.Model() as model_b:
        beta_intercept = pm.Normal("beta_intercept", mu=y_obs.mean(), sigma=1.0)
        beta_income = pm.Normal("beta_income", mu=0.0, sigma=0.5)
        sigma = pm.HalfNormal("sigma", 0.5)
        
        mu = beta_intercept + beta_income * income_z
        y = pm.Normal("y", mu=mu, sigma=sigma, observed=y_obs)
        
        trace_b = pm.sample(500, tune=500, chains=2, random_seed=RANDOM_SEED, progressbar=False, idata_kwargs={"log_likelihood": True})
        waic_b = az.waic(trace_b)
        results['Model B'] = waic_b

    # --- SUMMARY ---
    print("\n==========================================")
    print("Model Comparison Results (National Pilot)")
    print("==========================================")
    
    comparison = az.compare({'Model A (Physics)': trace_a, 'Model B (No Physics)': trace_b}, ic='waic')
    print(comparison)
    
    # Save to file
    out_path = PROCESSED_DIR / "v9_model_comparison_results.txt"
    with open(out_path, "w") as f:
        f.write("V9 Methodological Audit: Model Comparison\n")
        f.write("=========================================\n\n")
        f.write("Model A: mu = log(Tm) + beta_th + beta_inc * Z_inc\n")
        f.write("Model B: mu = beta_0 + beta_inc * Z_inc\n\n")
        f.write(comparison.to_string())
        f.write("\n\nConclusion: Model A significantly outperforms Model B if d_waic is positive and large.\n")
    
    print(f"\nResults saved to {out_path}")

if __name__ == "__main__":
    run_comparison()
