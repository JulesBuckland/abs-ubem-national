import pandas as pd
import numpy as np
import pymc as pm
import pytensor.tensor as pt
import geopandas as gpd
import libpysal
import os

try:
    import psutil
except ImportError:
    psutil = None

from src.config.settings import (
    PROCESSED_DIR, RAW_DIR, 
    MCMC_SAMPLES, MCMC_TUNE, MCMC_CORES, MCMC_CHAINS,
    setup_logging
)

logger = setup_logging("BayesianUnifiedNational")

def log_memory(stage_name):
    if psutil is not None:
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(f"[RAM USAGE - {stage_name}]: {mem_mb:.2f} MB")
    else:
        logger.info(f"[RAM USAGE - {stage_name}]: (psutil not installed, cannot track RAM)")

def run_national_unified_model():
    logger.info("--- STAGE 3: UNIFIED NATIONAL BAYESIAN MODEL ---")
    log_memory("Initialization")
    
    # 1. Load Data
    data_path = PROCESSED_DIR / "national_synthetic_population_eti.parquet"
    if not data_path.exists():
        logger.error(f"Missing data at {data_path}")
        return
        
    df = pd.read_parquet(data_path)
    
    # Dynamically merge Theoretical Physics Archetypes (E+) to avoid re-running Stage 1
    archetypes_path = RAW_DIR / "physics" / "physics_archetypes_baseline.csv"
    if archetypes_path.exists():
        archetypes = pd.read_csv(archetypes_path)
        # Drop duplicates just in case there are multiple entries per age/type
        archetypes = archetypes[['property_type', 'property_age', 'theoretical_gas_kwh']].drop_duplicates()
        df = df.merge(archetypes, on=['property_type', 'property_age'], how='left')
        
        # Fallback for any unmapped households (e.g. edge cases)
        n_missing = df['theoretical_gas_kwh'].isna().sum()
        if n_missing > 0:
            logger.warning(f"CRITICAL WARNING: {n_missing} ({n_missing/len(df):.2%}) households missing theoretical gas! Patching with median...")
            assert n_missing / len(df) < 0.05, "CRITICAL: >5% missing theoretical_gas_kwh!"
        df['theoretical_gas_kwh'] = df['theoretical_gas_kwh'].fillna(df['theoretical_gas_kwh'].median())
    else:
        logger.error(f"Archetypes not found at {archetypes_path}")
        return
    
    # Load confounders for Z_inc
    conf_path = PROCESSED_DIR / "msoa_confounders_national.csv"
    confounders = pd.read_csv(conf_path).set_index('msoa_cd')
    
    # Pre-aggregate to MSOA level (preserving arithmetic mean for mass conservation)
    # We aggregate empirical_thermal_kwh (which includes electric heating now!)
    msoa_stats = df.groupby('msoa21cd').agg(
        y_mean=('empirical_thermal_kwh', 'mean'),
        T_mean=('theoretical_gas_kwh', 'mean'), # Using E+ as baseline
        T_var=('theoretical_gas_kwh', lambda x: np.var(np.log(x + 1e-6))) # For Jensen's correction
    ).reset_index()
    
    msoa_stats = msoa_stats.merge(confounders.reset_index(), left_on='msoa21cd', right_on='msoa_cd', how='inner')
    
    msoa_stats = msoa_stats.dropna(subset=['y_mean', 'T_mean', 'income_dep_score'])
    
    logger.info(f"Aggregated {len(df)} households into {len(msoa_stats)} MSOAs.")
    log_memory("Post-Aggregation Data Load")

    # 2. Build Sparse Spatial Adjacency Matrix
    boundaries_path = RAW_DIR / "spatial" / "msoa dec 2021 boundaries.gpkg"
    gdf = gpd.read_file(boundaries_path)
    
    # Align GDF and MSOA stats perfectly
    gdf = gdf[gdf['MSOA21CD'].isin(msoa_stats['msoa21cd'])].sort_values('MSOA21CD').reset_index(drop=True)
    msoa_stats = msoa_stats.sort_values('msoa21cd').reset_index(drop=True)
    
    # Build Queen contiguity weights
    w = libpysal.weights.Queen.from_dataframe(gdf, ids=gdf['MSOA21CD'].tolist(), silence_warnings=True)
    
    # Convert to node1, node2 lists for PyMC ICAR (extremely RAM efficient)
    node1, node2 = [], []
    for i, neighbors in w.neighbors.items():
        for j in neighbors:
            if w.id2i[i] < w.id2i[j]:
                node1.append(w.id2i[i])
                node2.append(w.id2i[j])
                
    node1 = np.array(node1)
    node2 = np.array(node2)
    
    logger.info(f"Built spatial graph: {len(msoa_stats)} nodes, {len(node1)} edges. No chunking required!")
    log_memory("Sparse Graph Contiguity Built")

    # Prepare Tensors
    y_obs = np.log(msoa_stats['y_mean'].values)
    theory_log = np.log(msoa_stats['T_mean'].values)
    T_var = msoa_stats['T_var'].values
    
    # Z_inc standardization
    income_z = (msoa_stats['income_dep_score'].values - msoa_stats['income_dep_score'].mean()) / msoa_stats['income_dep_score'].std()

    # 3. Restricted Spatial Regression (RSR) Projection Matrix
    # We project out Z from the ICAR to prevent Hodges-Reich confounding.
    Z = income_z.reshape(-1, 1)
    Z_pinv = np.linalg.pinv(Z.T @ Z)
    P_Z = Z @ Z_pinv @ Z.T
    P_Z_perp = np.eye(len(msoa_stats)) - P_Z
    
    log_memory("RSR Orthogonal Projection Created")
    
    # 4. Bayesian Model Definition
    with pm.Model() as unified_model:
        # Behavioral De-rating (Absorbs the 54% archetype error)
        f_zone = pm.Beta("f_zone", alpha=2, beta=2) # e.g. mean 0.5 (heating 50% of the house)
        f_time = pm.Beta("f_time", alpha=2, beta=2) # e.g. mean 0.5 (heating 12h instead of 24h)
        
        # Pure Physics Bias (Now protected from behavioral garbage-in)
        beta_phys = pm.Normal("beta_phys", mu=0.0, sigma=0.1)
        
        # Socioeconomic Rationing Elasticity
        beta_inc = pm.Normal("beta_inc", mu=-0.05, sigma=0.05)
        
        # Spatial Components (BYM2)
        rho = pm.Beta("rho", alpha=0.5, beta=0.5)
        sigma_spatial = pm.HalfNormal("sigma_spatial", sigma=0.5)
        
        # ICAR term via exact CAR formulation
        # Note: we use CAR rather than raw normal for proper precision matrix
        # For simplicity in ADVI, we can use the ICAR specification with node1/node2, 
        # but PyMC's CAR model natively supports W matrices.
        # Alternatively, we build the unconstrained ICAR:
        phi_raw = pm.Normal("phi_raw", mu=0.0, sigma=1.0, shape=len(msoa_stats))
        phi_centered = phi_raw - pm.math.mean(phi_raw)
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi_centered[node1] - phi_centered[node2])**2))
        
        # Unstructured spatial noise
        theta = pm.Normal("theta", mu=0.0, sigma=1.0, shape=len(msoa_stats))
        
        # The mixture
        omega = sigma_spatial * (pm.math.sqrt(1 - rho) * theta + pm.math.sqrt(rho) * phi_centered)
        
        # Apply Restricted Spatial Regression (RSR) Projection to the spatial effect
        # This prevents omega from stealing variance from income_z
        omega_star = pt.dot(P_Z_perp, omega)
        
        # Unified Structural Mean
        # theory_log is deterministic E+ prior. We add the log of behavioral deratings.
        adjusted_theory_log = theory_log + pm.math.log(f_zone) + pm.math.log(f_time) + beta_phys
        
        # Final linear predictor
        mu = adjusted_theory_log + beta_inc * income_z + omega_star
        
        # 5. Jensen's Second-Order Correction Likelihood
        # By subtracting (T_var / 2), we mathematically cancel the arithmetic mean right-skew bias.
        corrected_mu = mu - (T_var / 2.0)
        
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        
        y = pm.Normal("y", mu=corrected_mu, sigma=sigma_err, observed=y_obs)
        
        # Inference (NUTS)
        logger.info("Starting NUTS on full graph...")
        log_memory("Pre-NUTS Memory Peak")
        trace = pm.sample(tune=10, draws=10, chains=2, cores=1, progressbar=False)
        
    logger.info("Model fitted successfully! Saving Trace...")
    trace.to_netcdf(PROCESSED_DIR / "national_unified_trace.nc")
    
    # 6. Extract Output and Compute True Decoupled T*
    # We extract the posterior means
    b_inc_mean = trace.posterior['beta_inc'].mean().item()
    
    # Partial Residualization: We ONLY subtract behavioral rationing. We KEEP omega_star (unobserved physics)
    # T*_m = exp( log(y_m) - beta_inc * (Z - Z_ref) )
    # Let Z_ref = 0 (average income)
    T_star = np.exp(y_obs - b_inc_mean * income_z)
    
    msoa_stats['T_star_kwh'] = T_star
    msoa_stats.to_csv(PROCESSED_DIR / "msoa_unified_results.csv", index=False)
    logger.info("Saved true empirically decoupled T* results.")
    log_memory("Final Exit")

if __name__ == "__main__":
    run_national_unified_model()
