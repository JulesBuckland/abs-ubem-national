import time
import pandas as pd
import numpy as np
import os
import sys
import pymc as pm
import colorama
import geopandas as gpd
import libpysal
import arviz as az
import logging

sys.path.append(os.getcwd())
from src.config.settings import BOUNDARIES_PATH, RAW_DIR, PROCESSED_DIR, setup_logging

logger = setup_logging("Competitors")

def run_all_models():
    logger.info("--- STAGE: BENCHMARK COMPETITORS vs BS-UBEM ---")
    
    # Setup Data - Dummy Data 
    boundaries_path = BOUNDARIES_PATH
    if not boundaries_path.exists():
        boundaries_path = RAW_DIR / "fake" / "fake_msoa_boundaries.gpkg"
        
    gdf = gpd.read_file(boundaries_path)
    code_col = 'MSOA21CD' if 'MSOA21CD' in gdf.columns else [c for c in gdf.columns if 'CD' in c.upper()][0]
    
    # Subset to a reasonable small N for fast testing
    subset_msoas = gdf[code_col].unique()[:100]
    gdf_subset = gdf[gdf[code_col].isin(subset_msoas)].sort_values(code_col).reset_index(drop=True)
    N = len(gdf_subset)
    
    w_subset = libpysal.weights.Queen.from_dataframe(gdf_subset, ids=gdf_subset[code_col].tolist(), silence_warnings=True)
    
    node1, node2 = [], []
    for i, neighbors in w_subset.neighbors.items():
        for j in neighbors:
            if w_subset.id2i[i] < w_subset.id2i[j]:
                node1.append(w_subset.id2i[i])
                node2.append(w_subset.id2i[j])
    node1 = np.array(node1)
    node2 = np.array(node2)
    
    # Create mock data mimicking true distribution
    theory_log = np.random.normal(10, 1, N)
    income_z = np.random.normal(0, 1, N)
    T_var = np.zeros(N)
    
    # True data generating process (BS-UBEM is correct)
    beta_th_true = -0.3
    beta_inc_true = -0.5
    spatial_eff_true = np.random.normal(0, 0.5, N)
    y_obs = theory_log - (T_var / 2.0) + beta_th_true + beta_inc_true * income_z + spatial_eff_true + np.random.normal(0, 0.1, N)
    
    models = {}
    
    # Competitor A (Deterministic physics only)
    logger.info("Running Competitor A (Physics Only)...")
    with pm.Model() as comp_a:
        beta_th = pm.Normal("beta_th", mu=-0.3, sigma=0.1)
        mu = theory_log - (T_var / 2.0) + beta_th
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        y = pm.Normal("y", mu=mu, sigma=sigma_err, observed=y_obs)
        trace_a = pm.sample(tune=100, draws=100, chains=2, cores=1, progressbar=False)
        pm.compute_log_likelihood(trace_a)
        models['Competitor A'] = trace_a
        
    # Competitor B (Spatial stats only)
    logger.info("Running Competitor B (Social Only)...")
    with pm.Model() as comp_b:
        beta_0 = pm.Normal("beta_0", mu=10, sigma=2)
        beta_inc = pm.Normal("beta_inc", mu=0.0, sigma=0.5)
        rho = pm.Beta("rho", alpha=1.0, beta=1.0)
        sigma_spatial = pm.HalfNormal("sigma_spatial", sigma=0.5)
        
        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))
        theta_raw = pm.Normal("theta_raw", mu=0.0, sigma=1.0, shape=N)
        theta = pm.Deterministic("theta", theta_raw - pm.math.mean(theta_raw))
        omega = sigma_spatial * (pm.math.sqrt(1 - rho) * theta + pm.math.sqrt(rho) * phi)
        
        mu = beta_0 + beta_inc * income_z + omega
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        y = pm.Normal("y", mu=mu, sigma=sigma_err, observed=y_obs)
        trace_b = pm.sample(tune=100, draws=100, chains=2, cores=1, progressbar=False)
        pm.compute_log_likelihood(trace_b)
        models['Competitor B'] = trace_b

    # BS-UBEM
    logger.info("Running BS-UBEM (Synthesis)...")
    with pm.Model() as abs_ubem:
        beta_th = pm.Normal("beta_th", mu=-0.3, sigma=0.1)
        beta_inc = pm.Normal("beta_inc", mu=0.0, sigma=0.5)
        rho = pm.Beta("rho", alpha=1.0, beta=1.0)
        sigma_spatial = pm.HalfNormal("sigma_spatial", sigma=0.5)
        
        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))
        theta_raw = pm.Normal("theta_raw", mu=0.0, sigma=1.0, shape=N)
        theta = pm.Deterministic("theta", theta_raw - pm.math.mean(theta_raw))
        omega = sigma_spatial * (pm.math.sqrt(1 - rho) * theta + pm.math.sqrt(rho) * phi)
        
        mu = theory_log - (T_var / 2.0) + beta_th + beta_inc * income_z + omega
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        y = pm.Normal("y", mu=mu, sigma=sigma_err, observed=y_obs)
        trace_abs = pm.sample(tune=100, draws=100, chains=2, cores=1, progressbar=False)
        pm.compute_log_likelihood(trace_abs)
        models['BS-UBEM'] = trace_abs

    print("\n=== BENCHMARK COMPLETED ===")
    print("Competitor A, Competitor B, and BS-UBEM sampled successfully.")
    logger.info("Competitor Benchmark Finished!")

if __name__ == "__main__":
    run_all_models()
