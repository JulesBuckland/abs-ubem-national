import pandas as pd
import numpy as np
import pymc as pm
import pytensor.tensor as pt
import geopandas as gpd
import libpysal
import os
import joblib
import arviz as az

try:
    import psutil
except ImportError:
    psutil = None

from src.config.settings import (
    PROCESSED_DIR, RAW_DIR, 
    MCMC_SAMPLES, MCMC_TUNE, MCMC_CORES, MCMC_CHAINS,
    RANDOM_SEED, setup_logging
)

GP_MODEL_PATH = PROCESSED_DIR / "gp_emulator.pkl"
# GP input features — must match columns produced by 10c_gp_emulator.py
GP_FEATURES = ["floor_area", "wall_u", "ach", "wwr", "form_code", "hdd"]

logger = setup_logging("BayesianUnifiedNational")

def log_memory(stage_name: str) -> None:
    """Logs the current memory usage of the process.

    Args:
        stage_name (str): The name of the current pipeline stage.
    """
    if psutil is not None:
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        logger.info(f"[RAM USAGE - {stage_name}]: {mem_mb:.2f} MB")
    else:
        logger.info(f"[RAM USAGE - {stage_name}]: (psutil not installed, cannot track RAM)")

def _use_csv_baseline(df: pd.DataFrame) -> None:
    """Fallback: merge theoretical_gas_kwh from the analytical CSV baseline.

    Modifies the DataFrame in-place by adding a 'theoretical_gas_kwh' column
    based on the 'property_type' and 'property_age' archetype mapping.

    Args:
        df (pd.DataFrame): The household dataframe to modify.

    Raises:
        ValueError: If any archetype fails to map to the baseline CSV.
    """
    from src.config.settings import RAW_DIR
    archetypes_path = RAW_DIR / "physics" / "physics_archetypes_baseline.csv"
    archetypes = pd.read_csv(archetypes_path)
    archetypes = archetypes[["property_type", "property_age", "theoretical_gas_kwh"]].drop_duplicates()
    # Merge in-place (modifies the passed df via reference on column assignment)
    merged = df.merge(archetypes, on=["property_type", "property_age"], how="left")
    if merged["theoretical_gas_kwh"].isna().any():
        raise ValueError("FATAL: Failed to map CSV baseline to some archetypes! Missing values found.")
    df["theoretical_gas_kwh"] = merged["theoretical_gas_kwh"].values


def run_national_unified_model() -> az.InferenceData:
    """Executes the National Unified Bayesian Inference Model.

    This function performs the following pipeline:
    1. Loads the synthetic household population and aggregates it to the MSOA level.
    2. Applies the Gaussian Process (GP) emulator for theoretical heating loads.
    3. Builds a sparse Queen contiguity spatial matrix (O(E) complexity).
    4. Projects the income confounder to create a Restricted Spatial Regression (RSR) 
       orthogonal component.
    5. Executes a PyMC NUTS sampler (1D ICAR via edge-lists) to decouple 
       socioeconomic rationing from physical building efficiency.
    6. Saves the MCMC trace and the decoupled energy metric (T*).

    Returns:
        az.InferenceData: The generated PyMC posterior trace.
    """
    logger.info("--- STAGE 3: UNIFIED NATIONAL BAYESIAN MODEL ---")
    log_memory("Initialization")
    
    # 1. Load Data
    target_lad = os.environ.get("E2E_TARGET_LAD")
    target_region = os.environ.get("E2E_TARGET_REGION")
    if target_lad or target_region:
        subset_name = target_lad or target_region
        logger.info(f"*** SUBSET MODE: Reading data for {subset_name} ***")
        data_path = PROCESSED_DIR / "tests" / "e2e_outputs" / "national_synthetic_population_eti.parquet"
    else:
        data_path = PROCESSED_DIR / "national_synthetic_population_eti.parquet"
        
    if not data_path.exists():
        logger.error(f"Missing data at {data_path}")
        return
        
    df = pd.read_parquet(data_path)

    # -----------------------------------------------------------------------
    # GP Emulator: replace power-law HLC scaling with a trained surrogate.
    # Requires columns [floor_area, wall_u, ach, wwr, form_code] in the parquet
    # (added by 01_population_synthesis.py after Step 6 modifications).
    # Falls back to the CSV baseline if the GP model file does not exist.
    # -----------------------------------------------------------------------
    if GP_MODEL_PATH.exists():
        logger.info(f"Loading GP emulator from {GP_MODEL_PATH}...")
        payload = joblib.load(GP_MODEL_PATH)
        gp_model  = payload["gp"]
        gp_scaler = payload["scaler"]

        # Check all required feature columns are present
        missing_cols = [c for c in GP_FEATURES if c not in df.columns]
        if missing_cols:
            logger.warning(
                f"GP feature columns missing from parquet: {missing_cols}.\n"
                "Ensure 01_population_synthesis.py has been updated (Step 6).\n"
                "Falling back to CSV archetype baseline."
            )
            _use_csv_baseline(df)
        else:
            logger.info(f"Running GP predictions for {len(df):,} households...")
            X_hh = df[GP_FEATURES].values.astype(float)
            X_hh_s = gp_scaler.transform(X_hh)
            
            # ZERO TRUST PROTOCOL: Batch predictions to prevent 10GB RAM OOM crash
            BATCH_SIZE = 20000
            T_preds, T_stds = [], []
            import math
            n_batches = math.ceil(len(X_hh_s) / BATCH_SIZE)
            for i in range(0, len(X_hh_s), BATCH_SIZE):
                batch_X = X_hh_s[i:i+BATCH_SIZE]
                pred, std = gp_model.predict(batch_X, return_std=True)
                T_preds.append(pred)
                T_stds.append(std)
                
            T_pred = np.concatenate(T_preds)
            T_std = np.concatenate(T_stds)
            
            # Zero Trust: Clamp Gaussian regression tails to prevent negative energy
            T_pred = np.maximum(0.0, T_pred)
            
            df["theoretical_gas_kwh"] = T_pred * 277.778
            df["T_std_kwh"]           = T_std * 277.778
            
            # E2E Inline Assertion: Bounds Check
            assert (df["theoretical_gas_kwh"] >= 0).all(), "FATAL: Negative theoretical gas prediction detected!"
            
            log_memory("Post-GP Prediction")
    else:
        logger.warning(
            f"GP emulator not found at {GP_MODEL_PATH}. "
            "Falling back to analytical CSV baseline (power-law HLC scaling)."
        )
        _use_csv_baseline(df)
    
    # Load confounders for Z_inc
    from src.config.settings import MSOA_CONFOUNDERS_NATIONAL
    conf_path = MSOA_CONFOUNDERS_NATIONAL
    confounders = pd.read_csv(conf_path).set_index('msoa_cd')
    
    # Pre-aggregate to MSOA level (preserving arithmetic mean for mass conservation)
    # We aggregate empirical_thermal_kwh (which includes electric heating now!)
    # Pre-aggregate to MSOA level (preserving arithmetic mean for mass conservation)
    # T_var uses GP predictive variance if available, else empirical within-MSOA log-variance
    if "T_std_kwh" in df.columns:
        # GP predictive variance: propagate per-household GP uncertainty to MSOA mean
        # We use the Delta method approximation for Var(log T) ≈ (sigma / mu)^2
        df['log_T_var'] = (df['T_std_kwh'] / df['theoretical_gas_kwh'].clip(lower=1)) ** 2
        msoa_stats = df.groupby('msoa21cd').agg(
            y_mean=('empirical_thermal_kwh', 'mean'),
            T_mean=('theoretical_gas_kwh', 'mean'),
            T_var =('log_T_var', 'mean')
        ).reset_index()
        logger.info("Using GP predictive variance for Jensen's correction.")
    else:
        # Fallback: empirical within-MSOA log-variance (original method)
        msoa_stats = df.groupby('msoa21cd').agg(
            y_mean=('empirical_thermal_kwh', 'mean'),
            T_mean=('theoretical_gas_kwh', 'mean'),
            T_var =('empirical_thermal_kwh', lambda x: np.var(np.log(x + 1e-6)))
        ).reset_index()
        logger.info("Using empirical within-MSOA variance for Jensen's correction (GP fallback).")
    
    msoa_stats = msoa_stats.merge(confounders.reset_index(), left_on='msoa21cd', right_on='msoa_cd', how='inner')
    # (Dynamic PySAL spatial indices are generated later, so no predefined node_idx drop needed)
    
    # -------------------------------------------------------------
    # DATA LINEAGE TRACKING
    # -------------------------------------------------------------
    from src.utils.tracker import log_distribution
    log_distribution(df, 'theoretical_gas_kwh', '02a_bayesian_input', logger)
    log_distribution(df, 'empirical_thermal_kwh', '02a_bayesian_input', logger)
    
    initial_len = len(msoa_stats)
    msoa_stats = msoa_stats.dropna(subset=['y_mean', 'T_mean', 'income_dep_score'])
    assert len(msoa_stats) / initial_len > 0.99, "CRITICAL: Spatial merge dropped >1% of data!"
    
    logger.info(f"Aggregated {len(df)} households into {len(msoa_stats)} MSOAs.")
    log_memory("Post-Aggregation Data Load")

    # 2. Build Sparse Spatial Adjacency Matrix
    from src.config.settings import BOUNDARIES_PATH
    boundaries_path = BOUNDARIES_PATH
    gdf = gpd.read_file(boundaries_path)
    
    # Align GDF and MSOA stats perfectly
    gdf = gdf[gdf['MSOA21CD'].isin(msoa_stats['msoa21cd'])].sort_values('MSOA21CD').reset_index(drop=True)
    msoa_stats = msoa_stats.sort_values('msoa21cd').reset_index(drop=True)
    
    # E2E Inline Assertion: Matrix Dimension Match
    assert len(gdf) == len(msoa_stats), f"FATAL: Dimension mismatch! GDF has {len(gdf)} but stats has {len(msoa_stats)}"
    if len(gdf) == 0:
        raise ValueError("FATAL: GeoDataFrame is empty after filtering! Check spatial boundary data.")
    
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
    
    # -------------------------------------------------------------
    # SHAPE ASSERTIONS
    # -------------------------------------------------------------
    assert node1.ndim == 1 and node2.ndim == 1, "FATAL: Graph arrays must be 1D vectors"
    assert node1.shape == node2.shape, "FATAL: node1 and node2 graph connectivity arrays have mismatched shapes!"
    
    # Ensure node1 and node2 only contain valid indices
    assert np.all((node1 >= 0) & (node1 < len(msoa_stats))), "FATAL: node1 contains out-of-bounds indices"
    assert np.all((node2 >= 0) & (node2 < len(msoa_stats))), "FATAL: node2 contains out-of-bounds indices"
    
    T_var = msoa_stats['T_var'].values
    
    # Z_inc standardization
    std_val = msoa_stats['income_dep_score'].std()
    if np.isnan(std_val) or std_val == 0:
        income_z = np.zeros(len(msoa_stats))
    else:
        income_z = (msoa_stats['income_dep_score'].values - msoa_stats['income_dep_score'].mean()) / std_val

    # 3. Restricted Spatial Regression (RSR) Projection Matrix
    # We project out Z from the ICAR to prevent Hodges-Reich confounding.
    # To prevent O(N^2) dense matrix multiplication in the MCMC loop, we use O(N) scalar math:
    Z = income_z.reshape(-1, 1)
    Zt_Z_inv_scalar = np.linalg.pinv(Z.T @ Z)[0, 0]
    
    log_memory("RSR Orthogonal Projection Created")
    
    # 4. Bayesian Model Definition
    with pm.Model() as unified_model:
        # Pure Physics Bias
        beta_th = pm.Normal("beta_th", mu=-0.3, sigma=0.1)
        
        # Socioeconomic Rationing Elasticity
        beta_inc = pm.Normal("beta_inc", mu=0.0, sigma=0.5)
        
        # Spatial Components (BYM2)
        rho = pm.Beta("rho", alpha=1.0, beta=1.0)
        sigma_spatial = pm.HalfNormal("sigma_spatial", sigma=0.5)
        
        # ICAR term via SPARSE edge-list formulation (O(E) memory, not O(N²))
        # Mathematically identical to pm.ICAR but avoids the 374MB dense matrix.
        N = len(msoa_stats)
        n_edges = len(node1)
        
        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        
        # Zero-mean centering (same as before)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))
        
        # Unstructured spatial noise
        theta_raw = pm.Normal("theta_raw", mu=0.0, sigma=1.0, shape=N)
        theta = pm.Deterministic("theta", theta_raw - pm.math.mean(theta_raw))
        
        # The mixture
        omega = sigma_spatial * (pm.math.sqrt(1 - rho) * theta + pm.math.sqrt(rho) * phi)
        
        # Apply Restricted Spatial Regression (RSR) Projection to the spatial effect
        # This prevents omega from stealing variance from income_z
        # O(N) algebraic optimization: omega_star = omega - Z * (Z'Z)^-1 * (Z' omega)
        Z_tensor = pt.as_tensor_variable(Z[:, 0])
        Zt_omega = pt.sum(Z_tensor * omega)
        projection = Z_tensor * (Zt_Z_inv_scalar * Zt_omega)
        omega_star = omega - projection
        
        # Unified Structural Mean with Variance Correction
        mu = theory_log - (T_var / 2.0) + beta_th + beta_inc * income_z + omega_star
        
        # 5. Likelihood
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        
        y = pm.Normal("y", mu=mu, sigma=sigma_err, observed=y_obs)
        
        # Inference
        logger.info("Starting Sampler...")
        log_memory("Pre-NUTS Memory Peak")
        
        # Determine run mode: PILOT_MODE controls MCMC draws independently of data subsetting
        is_pilot = os.environ.get("PILOT_MODE") == "1"
        
        draws = 10 if is_pilot else MCMC_SAMPLES
        tune = 10 if is_pilot else MCMC_TUNE
        chains = 2 if is_pilot else MCMC_CHAINS
        # Sparse implementation still requires sequential execution (cores=1) to stay within 8GB RAM limit
        cores = 1
        
    # --- Sampling: PyMC NUTS with sequential chains for 8GB RAM ---
    with unified_model:
        sample_kwargs = {
            "draws": draws, "tune": tune, 
            "chains": chains, "cores": cores, 
            "random_seed": RANDOM_SEED, "target_accept": 0.99
        }
        logger.info(f"Sampling with PyMC NUTS: {draws} draws, {tune} tune, {chains} chains, {cores} cores")
        trace = pm.sample(**sample_kwargs)
        
    logger.info("Model fitted successfully! Saving Trace FIRST...")
    trace_path = PROCESSED_DIR / "national_unified_trace.nc"
    if trace_path.exists():
        trace_path.unlink() # Idempotency: Overwrite cleanly
    trace.to_netcdf(trace_path)

    logger.info("Computing Log Likelihood...")
    with unified_model:
        pm.compute_log_likelihood(trace)
    
    logger.info("Computing WAIC...")
    import arviz as az
    try:
        waic_result = az.waic(trace)
        waic_str = str(waic_result)
    except AttributeError:
        waic_str = "WAIC not available in this ArviZ version."
    
    summary = az.summary(trace)
    
    with open(PROCESSED_DIR / "nuts_waic.txt", "w") as f:
        f.write("--- WAIC ---\n")
        f.write(waic_str + "\n\n")
        f.write("--- DIAGNOSTICS ---\n")
        f.write(str(summary[['ess_bulk', 'ess_tail', 'r_hat']]) + "\n")

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
    
    return trace

if __name__ == "__main__":
    run_national_unified_model()
