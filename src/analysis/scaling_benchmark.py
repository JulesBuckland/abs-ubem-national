import time
import psutil
import pandas as pd
import numpy as np
import os
import gc
from pathlib import Path
import logging
import sys
import pymc as pm
import colorama
import geopandas as gpd
import libpysal

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.config.settings import (
    PROCESSED_DIR, HEATING_DEFICIT_FILE, RAW_DIR, 
    setup_logging, RANDOM_SEED, BOUNDARIES_PATH,
    MSOA_CONFOUNDERS_NATIONAL
)

logger = setup_logging("ScalingBenchmark")

def get_peak_ram():
    """Captures current RSS memory usage in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024**3)

def profile_inference(msoa_subset_size):
    """Runs a REAL inference loop for a specific number of MSOAs."""
    logger.info(f"--- BENCHMARKING N={msoa_subset_size} ---")
    start_time = time.time()
    peak_ram = 0
    
    # 1. Setup Data - Dummy Data for Benchmark to avoid dependency on real files if missing
    # We will generate dummy synthetic data for the N MSOAs
    boundaries_path = BOUNDARIES_PATH
    if not boundaries_path.exists():
        logger.error(f"Missing boundaries at {boundaries_path}. Generating dummy grid...")
        # Fallback to generating dummy grid just for benchmark if needed
        # We rely on the fake city bounds if real ones aren't there.
        boundaries_path = RAW_DIR / "fake" / "fake_msoa_boundaries.gpkg"
        
    gdf = gpd.read_file(boundaries_path)
    code_col = 'MSOA21CD' if 'MSOA21CD' in gdf.columns else [c for c in gdf.columns if 'CD' in c.upper()][0]
    
    # Subset to N MSOAs
    subset_msoas = gdf[code_col].unique()[:msoa_subset_size]
    gdf_subset = gdf[gdf[code_col].isin(subset_msoas)].sort_values(code_col).reset_index(drop=True)
    N = len(gdf_subset)
    
    # Create Queen contiguity weights
    w_subset = libpysal.weights.Queen.from_dataframe(gdf_subset, ids=gdf_subset[code_col].tolist(), silence_warnings=True)
    
    node1, node2 = [], []
    for i, neighbors in w_subset.neighbors.items():
        for j in neighbors:
            if w_subset.id2i[i] < w_subset.id2i[j]:
                node1.append(w_subset.id2i[i])
                node2.append(w_subset.id2i[j])
    node1 = np.array(node1)
    node2 = np.array(node2)
    
    # Create mock data
    theory_log = np.random.normal(10, 1, N)
    income_z = np.random.normal(0, 1, N)
    y_obs = theory_log + np.random.normal(0, 0.5, N)
    T_var = np.zeros(N)
    
    with pm.Model() as chunk_model:
        # Simplified unified model for benchmarking scaling
        beta_th = pm.Normal("beta_th", mu=-0.3, sigma=0.1)
        beta_inc = pm.Normal("beta_inc", mu=0.0, sigma=0.5)
        
        rho = pm.Beta("rho", alpha=1.0, beta=1.0)
        sigma_spatial = pm.HalfNormal("sigma_spatial", sigma=0.5)
        
        # ICAR term using SPARSE edge-list formulation
        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))
        
        theta_raw = pm.Normal("theta_raw", mu=0.0, sigma=1.0, shape=N)
        theta = pm.Deterministic("theta", theta_raw - pm.math.mean(theta_raw))
        
        omega = sigma_spatial * (pm.math.sqrt(1 - rho) * theta + pm.math.sqrt(rho) * phi)
        
        mu = theory_log - (T_var / 2.0) + beta_th + beta_inc * income_z + omega
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        
        y = pm.Normal("y", mu=mu, sigma=sigma_err, observed=y_obs)
        
        # We use ADVI or a very short NUTS run to profile just the memory and overhead scaling
        pm.fit(n=100, method='advi', progressbar=False)
        
    peak_ram = max(peak_ram, get_peak_ram())
    gc.collect()
        
    duration = time.time() - start_time
    logger.info(f"N={msoa_subset_size} | Time={duration:.1f}s | Peak RAM={peak_ram:.2f}GB")
    return duration, peak_ram

def run_benchmark():
    test_points = [100, 200, 400] # Adjusting for fast benchmark execution
    results = []
    
    for N in test_points:
        duration, peak = profile_inference(N)
        results.append({"N": N, "Runtime_s": duration, "Peak_RAM_GB": peak})
        
    bench_df = pd.DataFrame(results)
    output_path = PROCESSED_DIR / "scaling_benchmark_results.csv"
    bench_df.to_csv(output_path, index=False)
    print(bench_df.to_string())
    logger.info(f"Benchmark results saved to {output_path}")

if __name__ == "__main__":
    run_benchmark()
